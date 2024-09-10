from flask import Flask, render_template, request, jsonify
import networkx as nx
import json
from community import community_louvain

app = Flask(__name__)

class NeurosymbolicKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node, attributes=None):
        self.graph.add_node(node, **attributes if attributes else {})

    def add_edge(self, node1, node2, attributes=None):
        self.graph.add_edge(node1, node2, **attributes if attributes else {})

    def query(self, node):
        if node not in self.graph:
            return f"Node '{node}' not found in the graph."
        
        neighbors = list(self.graph.neighbors(node))
        node_data = self.graph.nodes[node]
        edges = self.graph.edges(node, data=True)
        
        result = f"Node: {node}\n"
        result += f"Attributes: {node_data}\n"
        result += f"Neighbors: {neighbors}\n"
        result += "Edges:\n"
        for edge in edges:
            result += f"  - {edge[0]} -> {edge[1]}: {edge[2]}\n"
        
        return result

    def save_graph(self, filename='knowledge_graph.json'):
        data = nx.node_link_data(self.graph)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_graph(self, filename='knowledge_graph.json'):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            # Convert 'edges' to 'links' if necessary
            if 'edges' in data and 'links' not in data:
                data['links'] = data.pop('edges')
            self.graph = nx.node_link_graph(data)
            print(f"Graph loaded from {filename}")
        except FileNotFoundError:
            print(f"File {filename} not found. Starting with an empty graph.")

    def export_to_mermaid(self):
        mermaid_output = "graph TD\n"
        for edge in self.graph.edges(data=True):
            source, target = edge[0], edge[1]
            relation = edge[2].get('relation', '')
            mermaid_output += f"    {source.replace(' ', '_')} -->|{relation}| {target.replace(' ', '_')}\n"
        return mermaid_output

    def page_rank(self):
        return nx.pagerank(self.graph)

    def detect_communities(self):
        return community_louvain.best_partition(self.graph)

kg = NeurosymbolicKnowledgeGraph()
kg.load_graph()  # Load existing graph if available

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json
    node = data.get('node')
    attributes = data.get('attributes', {})
    kg.add_node(node, attributes)
    kg.save_graph()  # Save the graph after adding a node
    return jsonify({"message": f"Node '{node}' added successfully"})

@app.route('/add_edge', methods=['POST'])
def add_edge():
    data = request.json
    node1 = data.get('node1')
    node2 = data.get('node2')
    relation = data.get('relation')
    kg.add_edge(node1, node2, {"relation": relation})
    kg.save_graph()  # Save the graph after adding an edge
    return jsonify({"message": f"Edge from '{node1}' to '{node2}' added successfully"})

@app.route('/query_node', methods=['GET'])
def query_node():
    node = request.args.get('node')
    result = kg.query(node)
    return jsonify({"result": result})

@app.route('/visualize', methods=['GET'])
def visualize():
    mermaid_graph = kg.export_to_mermaid()
    return jsonify({"mermaid_graph": mermaid_graph})

@app.route('/page_rank', methods=['GET'])
def page_rank():
    ranks = kg.page_rank()
    return jsonify(ranks)

@app.route('/detect_communities', methods=['GET'])
def detect_communities():
    communities = kg.detect_communities()
    return jsonify(communities)

@app.route('/load_graph', methods=['POST'])
def load_graph():
    try:
        file_content = request.json.get('file_content')
        print(f"Received file content: {file_content[:100]}...")  # Print first 100 characters
        data = json.loads(file_content)
        print(f"Parsed JSON data structure:")
        print(json.dumps(data, indent=2)[:500])  # Print first 500 characters of formatted JSON
        if 'edges' in data and 'links' not in data:
            data['links'] = data.pop('edges')
        if 'nodes' not in data or 'links' not in data:
            raise KeyError("JSON data must contain both 'nodes' and 'links' (or 'edges') keys")
        print(f"Creating networkx graph with {len(data['nodes'])} nodes and {len(data['links'])} links")
        kg.graph = nx.node_link_graph(data)
        print(f"NetworkX graph created successfully with {len(kg.graph.nodes)} nodes and {len(kg.graph.edges)} edges")
        kg.save_graph()  # Save the newly loaded graph
        return jsonify({"message": "Graph loaded successfully", "nodes": len(kg.graph.nodes), "edges": len(kg.graph.edges)})
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400
    except KeyError as e:
        print(f"KeyError: {str(e)}")
        return jsonify({"error": f"Missing key in JSON: {str(e)}"}), 400
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
