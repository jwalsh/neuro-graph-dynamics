import json
import sys
import time

import requests

from database import create_database, save_response

OLLAMA_API_URL = "http://localhost:11434/api"


def is_ollama_server_running():
    try:
        response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_ollama_models(max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            else:
                print(
                    f"Attempt {attempt + 1}: Failed to get models. Status code: {response.status_code}"
                )
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}: Error connecting to Ollama API: {str(e)}")

        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    print("Failed to get Ollama models after all retries.")
    return []


def get_ollama_help(model_name, query, system_prompt=""):
    try:
        payload = {
            "model": model_name,
            "prompt": query,
            "system": system_prompt,
            "stream": False,
        }
        response = requests.post(f"{OLLAMA_API_URL}/generate", json=payload, timeout=30)
        response.raise_for_status()
        help_text = response.json().get("response", "No help available.")

        save_response(
            architecture_name="Neurosymbolic Knowledge Graph",
            provider="Ollama",
            model=model_name,
            user_text=query,
            front_content=system_prompt,
            back_content=help_text,
            system_prompt=system_prompt,
        )

        return help_text
    except requests.exceptions.Timeout:
        return f"Error: Request timed out when getting help for model {model_name}"
    except requests.exceptions.HTTPError as e:
        return (
            f"Error: HTTP error occurred: {e.response.status_code} - {e.response.text}"
        )
    except requests.exceptions.RequestException as e:
        return f"Error: An unexpected error occurred: {str(e)}"


def main():
    create_database()
    if not is_ollama_server_running():
        print("Error: Ollama server is not running or not accessible.")
        return

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "get_models":
            models = get_ollama_models()
            print(json.dumps(models))
        elif command == "get_help" and len(sys.argv) > 3:
            model_name = sys.argv[2]
            query = sys.argv[3]
            system_prompt = sys.argv[4] if len(sys.argv) > 4 else ""
            help_text = get_ollama_help(model_name, query, system_prompt)
            print(json.dumps({"help": help_text}))
        else:
            print(
                "Usage: python ollama_helper.py [get_models | get_help <model_name> <query> [system_prompt]]"
            )
    else:
        print("Attempting to get Ollama models...")
        models = get_ollama_models()
        print("Available Ollama models:", models)

        model_name = "llama2:latest"
        query = "How to use this model?"
        system_prompt = "You are an AI assistant specializing in explaining AI models."
        print(f"Getting help for {model_name}...")
        try:
            help_text = get_ollama_help(model_name, query, system_prompt)
            print(f"Help for {model_name}:")
            print(help_text)
        except Exception as e:
            print(f"An error occurred while getting help for {model_name}: {str(e)}")


if __name__ == "__main__":
    main()
