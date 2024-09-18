import json
import os
from datetime import datetime

import networkx as nx
from community import community_louvain
from flask import Flask, jsonify, render_template, request

from bedrock_helper import (enrich_node_info, invoke_bedrock_model,
                            list_bedrock_models, query_knowledge_base)
from database import create_database, save_graph_to_db, load_graph_from_db

class NeurosymbolicKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def load_graph(self, filename="knowledge_graph.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            
            # Check if the data is in the expected format
            if "nodes" in data and "edges" in data:
                # Create graph from nodes and edges
                self.graph = nx.Graph()
                for node in data["nodes"]:
                    self.graph.add_node(node["id"], **node)
                for edge in data["edges"]:
                    self.graph.add_edge(edge["source"], edge["target"], **edge)
            elif "nodes" in data and "links" in data:
                # Use node_link_graph if the format matches
                self.graph = nx.node_link_graph(data)
            else:
                print(f"Unexpected data format in {filename}. Starting with an empty graph.")
                self.graph = nx.Graph()

            print(f"Graph loaded from {filename}")
            
            # Sync the loaded graph with the database
            save_graph_to_db(self.graph)
        except FileNotFoundError:
            print(f"File {filename} not found. Attempting to load from database.")
            self.load_graph_from_db()
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {filename}. Starting with an empty graph.")
            self.graph = nx.Graph()
        except Exception as e:
            print(f"An error occurred while loading the graph: {str(e)}. Starting with an empty graph.")
            self.graph = nx.Graph()

    def load_graph_from_db(self):
        self.graph = load_graph_from_db()
        if self.graph.number_of_nodes() > 0:
            print("Graph loaded from database")
        else:
            print("No existing graph found in database. Starting with an empty graph.")

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
        self.graph.nodes[node_name]["enriched_info"] = enriched_info.enriched_content

        # Save the updated graph to the database
        save_graph_to_db(self.graph)

        return {
            "original_info": str(attributes),
            "enriched_info": enriched_info.enriched_content,
        }

def create_app():
    app = Flask(__name__)
    
    # Initialize database and load graph
    try:
        create_database()
    except Exception as e:
        print(f"Error creating database: {str(e)}")

    kg = NeurosymbolicKnowledgeGraph()
    kg.load_graph()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/visualize")
    def visualize():
        graph_data = kg.get_graph_data()
        return render_template("visualize.html", graph_data=graph_data)

    @app.route("/philosophers_pagerank")
    def philosophers_pagerank():
        pagerank = nx.pagerank(kg.graph)
        sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        return render_template("philosophers_pagerank.html", pagerank=sorted_pagerank)

    @app.route("/top_nodes_distances")
    def top_nodes_distances():
        pagerank = nx.pagerank(kg.graph)
        top_20_nodes = sorted(pagerank, key=pagerank.get, reverse=True)[:20]

        distances = {}
        for node1 in top_20_nodes:
            distances[node1] = {}
            for node2 in top_20_nodes:
                if node1 != node2:
                    try:
                        distances[node1][node2] = nx.shortest_path_length(
                            kg.graph, node1, node2
                        )
                    except nx.NetworkXNoPath:
                        distances[node1][node2] = float("inf")

        return render_template(
            "top_nodes_distances.html", nodes=top_20_nodes, distances=distances
        )

    @app.route("/debug")
    def debug():
        debug_info = {
            "graph_nodes": len(kg.graph.nodes),
            "graph_edges": len(kg.graph.edges),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return render_template("debug.html", debug_info=debug_info)

    @app.route("/export_json", methods=["GET"])
    def export_json():
        graph_data = kg.get_graph_data()
        return jsonify(graph_data)

    @app.route("/bedrock_models", methods=["GET"])
    def get_bedrock_models():
        models = list_bedrock_models()
        return jsonify(models)

    @app.route("/bedrock_invoke", methods=["POST"])
    def invoke_bedrock():
        data = request.json
        model_id = data.get("model_id")
        prompt = data.get("prompt")
        system_prompt = data.get("system_prompt", "")

        if not model_id or not prompt:
            return jsonify({"error": "Missing model_id or prompt"}), 400

        response = invoke_bedrock_model(model_id, prompt, system_prompt)
        return jsonify({"response": response})

    @app.route("/reset_database", methods=["POST"])
    def reset_database():
        try:
            # Load the original graph data from JSON
            with open("knowledge_graph.json", "r") as f:
                data = json.load(f)
        
                # Reset the graph
                kg.graph = nx.Graph()
                for node in data["nodes"]:
                    kg.graph.add_node(node["id"], **node)
                    for edge in data["edges"]:
                        kg.graph.add_edge(edge["source"], edge["target"], **edge)
        
                # Save the reset graph to the database
                save_graph_to_db(kg.graph)
        
                # Get updated graph statistics
                node_count = kg.graph.number_of_nodes()
                edge_count = kg.graph.number_of_edges()
                last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
                return jsonify({
                    "message": "Database reset to original philosophers data.",
                    "graph_nodes": node_count,
                    "graph_edges": edge_count,
                    "last_updated": last_updated
                })
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/graph_data", methods=["GET"])
    def get_graph_data():
        return jsonify(kg.get_graph_data())

    @app.route("/get_nodes", methods=["GET"])
    def get_nodes():
        return jsonify(kg.get_all_nodes())

    @app.route("/enrich_node", methods=["POST"])
    def enrich_node():
        data = request.json
        node_name = data.get("node_name")

        if not node_name:
            return jsonify({"error": "Missing node_name"}), 400

        node_info = kg.enrich_node(node_name)
        return jsonify(node_info)

    @app.route("/query_knowledge_base", methods=["POST"])
    def query_kb():
        data = request.json
        query = data.get("query")
        max_results = data.get("max_results", 5)

        if not query:
            return jsonify({"error": "Missing query"}), 400

        kb_results = query_knowledge_base(query, max_results)
        return jsonify([result.dict() for result in kb_results])

    @app.route("/test_bedrock", methods=["POST"])
    def test_bedrock():
        data = request.json
        model_id = data.get("model_id", "anthropic.claude-v2")
        prompt = data.get("prompt", "What is the capital of France?")
        system_prompt = data.get("system_prompt", "")

        response = invoke_bedrock_model(model_id, prompt, system_prompt)
        return jsonify({"response": response})

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
