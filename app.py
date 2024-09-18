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
            # Update node attributes to ensure 'label' is set correctly
            for node, attrs in self.graph.nodes(data=True):
                if 'label' not in attrs:
                    attrs['label'] = node
            print(f"Graph loaded from {filename}")
        except FileNotFoundError:
            print(f"File {filename} not found. Starting with an empty graph.")

    def get_graph_data(self):
        return nx.node_link_data(self.graph)

    def get_all_nodes(self):
        return list(self.graph.nodes)

    def add_node(self, node, attributes=None, lifetime=None):
        node_attrs = attributes or {}
        if lifetime:
            node_attrs['lifetime'] = lifetime
        self.graph.add_node(node, **node_attrs)

    def add_edge(self, node1, node2, attributes=None):
        self.graph.add_edge(node1, node2, **attributes if attributes else {})

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

    def update_contemporary_philosophers(self):
        """Update the graph with contemporary philosophers and their connections."""
        # Add new nodes
        self.add_node("Singer", {"label": "Peter Singer", "school": "Utilitarianism", "lifetime": "1946-"})
        self.add_node("West", {"label": "Cornel West", "school": "Pragmatism, Critical Theory", "lifetime": "1953-"})

        # Update existing nodes
        self.graph.nodes["Nussbaum"]["label"] = "Martha Nussbaum"
        self.graph.nodes["Habermas"]["label"] = "Jürgen Habermas"
        self.graph.nodes["Butler"]["label"] = "Judith Butler"

        # Add new connections
        self.add_edge("Singer", "Nussbaum", {"relation": "collaborated"})
        self.add_edge("Singer", "Rawls", {"relation": "influenced by"})
        self.add_edge("West", "Dewey", {"relation": "influenced by"})
        self.add_edge("West", "Marx", {"relation": "influenced by"})
        self.add_edge("Habermas", "West", {"relation": "debated"})
        self.add_edge("Butler", "Foucault", {"relation": "influenced by"})
        self.add_edge("Butler", "Derrida", {"relation": "influenced by"})
        self.add_edge("Nussbaum", "Rawls", {"relation": "influenced by"})
        self.add_edge("Nussbaum", "Sen", {"relation": "collaborated"})

        return "Contemporary philosophers and their connections have been added to the graph."

kg = NeurosymbolicKnowledgeGraph()
kg.load_graph()  # Load existing graph if available

@app.route('/')
def index():
    return render_template('index.html', additional_links=[
        {'url': '/visualize', 'text': 'Graph Visualization'},
        {'url': '/philosophers_pagerank', 'text': 'Philosophers PageRank'},
        {'url': '/top_nodes_distances', 'text': 'Top Nodes Similarity'}
    ])

@app.route('/export_json', methods=['GET'])
def export_json():
    graph_data = kg.get_graph_data()
    return jsonify(graph_data)

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

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json
    node_name = data.get('node_name')
    attributes = data.get('attributes')
    lifetime = data.get('lifetime')
    
    if not node_name:
        return jsonify({"error": "Missing node_name"}), 400
    
    kg.add_node(node_name, attributes, lifetime)
    return jsonify({"success": True, "message": f"Node '{node_name}' added successfully"})

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

@app.route('/update_contemporary_philosophers', methods=['POST'])
def update_contemporary_philosophers():
    result = kg.update_contemporary_philosophers()
    return jsonify({"message": result})

@app.route('/debug')
def debug_page():
    return render_template('debug.html')

@app.route('/reload_db', methods=['POST'])
def reload_db():
    filename = request.form.get('filename', 'knowledge_graph.json')
    kg.load_graph(filename)
    return jsonify({"message": f"Database reloaded from {filename}"})

@app.route('/check_bedrock', methods=['POST'])
def check_bedrock():
    model_id = request.form.get('model_id', 'anthropic.claude-v2')
    prompt = request.form.get('prompt', 'What is the capital of France?')
    response = invoke_bedrock_model(model_id, prompt)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
