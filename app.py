import networkx as nx
import json
from community import community_louvain
from flask import Flask, render_template, request, jsonify
from bedrock_helper import list_bedrock_models, invoke_bedrock_model, enrich_node_info, query_knowledge_base

app = Flask(__name__)

class NeurosymbolicKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def load_graph(self, filename='knowledge_graph.json'):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
            print(f"Graph loaded from {filename}")
        except FileNotFoundError:
            print(f"File {filename} not found. Starting with an empty graph.")

    def get_graph_data(self):
        return nx.node_link_data(self.graph)

    def get_all_nodes(self):
        return list(self.graph.nodes)

    def enrich_node(self, node_name):
        if node_name not in self.graph:
            return {"error": f"Node '{node_name}' not found in the graph."}
        
        attributes = self.graph.nodes[node_name]
        connections = list(self.graph.neighbors(node_name))
        enriched_info = enrich_node_info(node_name, attributes, connections)
        
        # Update the node with the enriched information
        self.graph.nodes[node_name]['enriched_info'] = enriched_info.enriched_content
        
        return {
            "original_info": str(attributes),
            "enriched_info": enriched_info.enriched_content
        }

kg = NeurosymbolicKnowledgeGraph()
kg.load_graph()  # Load existing graph if available

@app.route('/')
def index():
    return render_template('index.html', additional_links=[
        {'url': '/philosophers_pagerank', 'text': 'Philosophers PageRank'},
        {'url': '/top_nodes_distances', 'text': 'Top Nodes Distances'}
    ])

@app.route('/bedrock_models', methods=['GET'])
def get_bedrock_models():
    models = list_bedrock_models()
    return jsonify(models)

@app.route('/bedrock_invoke', methods=['POST'])
def invoke_bedrock():
    data = request.json
    model_id = data.get('model_id')
    prompt = data.get('prompt')
    system_prompt = data.get('system_prompt', '')
    
    if not model_id or not prompt:
        return jsonify({"error": "Missing model_id or prompt"}), 400
    
    response = invoke_bedrock_model(model_id, prompt, system_prompt)
    return jsonify({"response": response})

@app.route('/graph_data', methods=['GET'])
def get_graph_data():
    return jsonify(kg.get_graph_data())

@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    return jsonify(kg.get_all_nodes())

@app.route('/enrich_node', methods=['POST'])
def enrich_node():
    data = request.json
    node_name = data.get('node_name')
    
    if not node_name:
        return jsonify({"error": "Missing node_name"}), 400
    
    node_info = kg.enrich_node(node_name)
    return jsonify(node_info)

@app.route('/query_knowledge_base', methods=['POST'])
def query_kb():
    data = request.json
    query = data.get('query')
    max_results = data.get('max_results', 5)
    
    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    kb_results = query_knowledge_base(query, max_results)
    return jsonify([result.dict() for result in kb_results])

@app.route('/test_bedrock', methods=['POST'])
def test_bedrock():
    data = request.json
    model_id = data.get('model_id', 'anthropic.claude-v2')
    prompt = data.get('prompt', 'What is the capital of France?')
    system_prompt = data.get('system_prompt', '')

    response = invoke_bedrock_model(model_id, prompt, system_prompt)
    return jsonify({"response": response})

@app.route('/philosophers_pagerank')
def philosophers_pagerank():
    pagerank = nx.pagerank(kg.graph)
    sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    return render_template('philosophers_pagerank.html', pagerank=sorted_pagerank)

@app.route('/top_nodes_distances')
def top_nodes_distances():
    pagerank = nx.pagerank(kg.graph)
    top_20_nodes = sorted(pagerank, key=pagerank.get, reverse=True)[:20]
    
    distances = {}
    for node1 in top_20_nodes:
        distances[node1] = {}
        for node2 in top_20_nodes:
            if node1 != node2:
                try:
                    distances[node1][node2] = nx.shortest_path_length(kg.graph, node1, node2)
                except nx.NetworkXNoPath:
                    distances[node1][node2] = float('inf')
    
    return render_template('top_nodes_distances.html', nodes=top_20_nodes, distances=distances)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
