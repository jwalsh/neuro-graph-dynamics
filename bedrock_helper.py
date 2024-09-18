import boto3
import json
import os
import traceback
import logging
from typing import List, Dict
from botocore.exceptions import ClientError, NoRegionError
from database import create_database, save_response
from pydantic import BaseModel, Field
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class KnowledgeBaseResult(BaseModel):
    relation: str
    source: str
    target: str
    key: int

class EnrichedNodeInfo(BaseModel):
    enriched_content: str

def list_bedrock_models():
    try:
        client = boto3.client('bedrock', 
                              aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                              region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
        response = client.list_foundation_models()
        return [model['modelId'] for model in response['modelSummaries']]
    except Exception as e:
        logging.error(f"Error listing Bedrock models: {str(e)}")
        return []

def invoke_bedrock_model(model_id: str, prompt: str, system_prompt: str = ""):
    try:
        client = boto3.client('bedrock-runtime', 
                              aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                              region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
        
        if model_id.startswith('anthropic.'):
            payload = {
                "prompt": f"{system_prompt}\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 300,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        elif model_id.startswith('ai21.'):
            payload = {
                "prompt": f"{system_prompt}\n\n{prompt}",
                "maxTokens": 300,
                "temperature": 0.7,
                "topP": 0.9,
            }
        elif model_id.startswith('amazon.'):
            payload = {
                "inputText": f"{system_prompt}\n\n{prompt}",
                "textGenerationConfig": {
                    "maxTokenCount": 300,
                    "temperature": 0.7,
                    "topP": 0.9,
                }
            }
        else:
            raise ValueError(f"Unsupported model ID: {model_id}")

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload)
        )
        response_body = json.loads(response['body'].read())
        
        if model_id.startswith('anthropic.'):
            return response_body['completion']
        elif model_id.startswith('ai21.'):
            return response_body['completions'][0]['data']['text']
        elif model_id.startswith('amazon.'):
            return response_body['results'][0]['outputText']
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logging.error(f"AWS Error ({error_code}): {error_message}")
        if 'ValidationException' in str(e):
            logging.error(f"Validation error details: {e.response['Error']['Message']}")
        return f"Error: {str(e)}"
    except Exception as e:
        logging.error(f"Error invoking Bedrock model: {str(e)}")
        return f"Error: {str(e)}"

def query_bedrock_kb(query: str) -> str:
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime',
                                      aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                                      aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                                      region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
        
        # Prepare the request payload
        payload = {
            "inputText": query,
            "maxTokens": 200,
            "temperature": 0.7,
            "topP": 1,
            "stopSequences": [],
            "countPenalty": {"scale": 0},
            "presencePenalty": {"scale": 0},
            "frequencyPenalty": {"scale": 0}
        }
        
        # Invoke the Bedrock model
        response = bedrock_client.invoke_model(
            modelId='amazon.titan-text-express-v1',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(payload)
        )
        
        # Parse and return the response
        response_body = json.loads(response['body'].read())
        return response_body['results'][0]['outputText']
    except Exception as e:
        logging.error(f"Error querying Bedrock knowledge base: {str(e)}")
        return f"Error: {str(e)}"

def enrich_node_info(node_name: str, attributes: Dict, connections: List[str]) -> EnrichedNodeInfo:
    try:
        query = f"Provide additional information about the philosopher {node_name}, known for {attributes.get('school', 'philosophy')}. Include key ideas, major works, and historical context."
        bedrock_info = query_bedrock_kb(query)
        
        enriched_content = f"Additional information from Bedrock:\n{bedrock_info}\n\nOriginal Attributes: {attributes}\nConnections: {connections}"
        return EnrichedNodeInfo(enriched_content=enriched_content)
    except Exception as e:
        logging.error(f"Error enriching node info for {node_name}: {str(e)}")
        return EnrichedNodeInfo(enriched_content=f"Error enriching node info: {str(e)}")

def query_knowledge_base(query: str, max_results: int = 5, max_retries: int = 3, base_delay: float = 1.0) -> List[KnowledgeBaseResult]:
    knowledgeBaseId = 'aif-c01-knowledge-base-quick-start-4uy41'  # Ensure this is correct
    
    for attempt in range(max_retries):
        try:
            client = boto3.client('bedrock-agent-runtime', 
                                  aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                                  aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                                  region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
            
            logging.info(f"Querying knowledge base with: {query}")
            payload = {
                "knowledgeBaseId": knowledgeBaseId,
                "retrievalQuery": {
                    "text": query
                },
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": max_results
                    }
                }
            }
            
            logging.debug(f"Bedrock API payload: {json.dumps(payload, indent=2)}")
            
            response = client.retrieve(**payload)
            
            logging.info(f"Successfully queried knowledge base. Results: {len(response['retrievalResults'])}")
            
            results = []
            for i, result in enumerate(response['retrievalResults']):
                # Parse the content to extract relation, source, and target
                # This is a placeholder implementation; adjust based on actual content structure
                parts = result['content'].split()
                if len(parts) >= 3:
                    results.append(KnowledgeBaseResult(
                        relation=parts[1],
                        source=parts[0],
                        target=parts[2],
                        key=i
                    ))
            
            return results[:5]  # Return only the top 5 results
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"AWS Error ({error_code}): {error_message}")
            if 'ValidationException' in str(e):
                logging.error(f"Validation error details: {e.response['Error']['Message']}")
            
            if error_code in ['ThrottlingException', 'RequestLimitExceeded']:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logging.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
            
            return []
        except Exception as e:
            logging.error(f"Error querying knowledge base: {str(e)}")
            logging.debug(f"Stack trace: {traceback.format_exc()}")
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            
            return []
    
    logging.error(f"Failed to query knowledge base after {max_retries} attempts")
    return []

if __name__ == "__main__":
    logging.info("Running Bedrock helper tests...")
    
    # Test list_bedrock_models function
    models = list_bedrock_models()
    logging.info(f"Available Bedrock models: {models}")
    
    # Test invoke_bedrock_model function with different model types
    anthropic_response = invoke_bedrock_model("anthropic.claude-v2", "What is the capital of France?")
    logging.info(f"Anthropic model response: {anthropic_response}")
    
    ai21_response = invoke_bedrock_model("ai21.j2-ultra-v1", "What is the capital of Germany?")
    logging.info(f"AI21 model response: {ai21_response}")
    
    amazon_response = invoke_bedrock_model("amazon.titan-text-express-v1", "What is the capital of Italy?")
    logging.info(f"Amazon model response: {amazon_response}")
    
    # Test query_knowledge_base function
    kb_results = query_knowledge_base("arch relation")
    logging.info(f"Top 5 arch relations:")
    for result in kb_results:
        logging.info(json.dumps(result.dict(), indent=2))
    
    # Test enrich_node_info function with 'Descartes' node
    descartes_attributes = {
        "label": "René Descartes (1596-1650)",
        "school": "Rationalism"
    }
    descartes_connections = ["Spinoza", "Leibniz"]
    enriched_info = enrich_node_info("Descartes", descartes_attributes, descartes_connections)
    logging.info(f"Enriched information for Descartes:\n{enriched_info.enriched_content}")
