import networkx as nx
import matplotlib.pyplot as plt
import json
from community import community_louvain

class NeurosymbolicKnowledgeGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node, attributes=None, lifetime=None):
        """Add a new node to the graph with optional attributes and lifetime."""
        node_attrs = attributes or {}
        if lifetime:
            node_attrs['lifetime'] = lifetime
        self.graph.add_node(node, **node_attrs)

    def add_edge(self, node1, node2, attributes=None):
        """Add a new edge between two nodes with optional attributes."""
        self.graph.add_edge(node1, node2, **attributes if attributes else {})

    def visualize(self):
        """Visualize the current state of the graph."""
        pos = nx.spring_layout(self.graph)
        plt.figure(figsize=(12, 8))
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', 
                node_size=500, font_size=10, font_weight='bold')
        edge_labels = nx.get_edge_attributes(self.graph, 'relation')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
        plt.title("Neurosymbolic Knowledge Graph")
        plt.axis('off')
        plt.tight_layout()
        plt.show()

    def query(self, node):
        """Retrieve information about a node and its neighbors."""
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
        """Save the graph to a JSON file."""
        data = nx.node_link_data(self.graph)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Graph saved to {filename}")

    def load_graph(self, filename='knowledge_graph.json'):
        """Load the graph from a JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
            print(f"Graph loaded from {filename}")
        except FileNotFoundError:
            print(f"File {filename} not found. Starting with an empty graph.")

    def export_to_mermaid(self):
        """Export the graph to Mermaid format."""
        mermaid_output = "graph TD\n"
        for edge in self.graph.edges(data=True):
            source, target = edge[0], edge[1]
            relation = edge[2].get('relation', '')
            mermaid_output += f"    {source.replace(' ', '_')} -->|{relation}| {target.replace(' ', '_')}\n"
        return mermaid_output

    def shortest_path(self, source, target):
        """Find the shortest path between two nodes."""
        try:
            path = nx.shortest_path(self.graph, source, target)
            return f"Shortest path from {source} to {target}: {' -> '.join(path)}"
        except nx.NetworkXNoPath:
            return f"No path exists between {source} and {target}"

    def page_rank(self):
        """Calculate PageRank for all nodes in the graph."""
        return nx.pagerank(self.graph)

    def detect_communities(self):
        """Detect communities using the Louvain method."""
        return community_louvain.best_partition(self.graph)

    def update_contemporary_philosophers(self):
        """Update the graph with contemporary philosophers and their connections."""
        # Add new nodes
        self.add_node("Singer", {"label": "Peter Singer (1946-)", "school": "Utilitarianism"})
        self.add_node("West", {"label": "Cornel West (1953-)", "school": "Pragmatism, Critical Theory"})

        # Update existing nodes
        self.graph.nodes["Nussbaum"]["label"] = "Martha Nussbaum (1947-)"
        self.graph.nodes["Habermas"]["label"] = "Jürgen Habermas (1929-)"
        self.graph.nodes["Butler"]["label"] = "Judith Butler (1956-)"

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

        print("Contemporary philosophers and their connections have been added to the graph.")

def main():
    kg = NeurosymbolicKnowledgeGraph()
    kg.load_graph()  # Load existing graph if available

    # Update the graph with contemporary philosophers
    kg.update_contemporary_philosophers()

    while True:
        print("\nNeurosymbolic Knowledge Graph Operations:")
        print("1. Add Node")
        print("2. Add Edge")
        print("3. Visualize Graph")
        print("4. Query Node")
        print("5. Save Graph")
        print("6. Export to Mermaid")
        print("7. Find Shortest Path")
        print("8. Calculate PageRank")
        print("9. Detect Communities")
        print("10. Exit")

        choice = input("Enter your choice (1-10): ")

        if choice == '1':
            node = input("Enter node name: ")
            attributes = input("Enter node attributes (as JSON, press Enter for none): ")
            lifetime = input("Enter node lifetime (optional, press Enter to skip): ")
            attributes = json.loads(attributes) if attributes else None
            kg.add_node(node, attributes, lifetime)
        elif choice == '2':
            node1 = input("Enter first node name: ")
            node2 = input("Enter second node name: ")
            relation = input("Enter relation (press Enter for none): ")
            attributes = {"relation": relation} if relation else None
            kg.add_edge(node1, node2, attributes)
        elif choice == '3':
            kg.visualize()
        elif choice == '4':
            node = input("Enter node to query: ")
            print(kg.query(node))
        elif choice == '5':
            kg.save_graph()
        elif choice == '6':
            mermaid_graph = kg.export_to_mermaid()
            print("Mermaid Graph:")
            print(mermaid_graph)
        elif choice == '7':
            source = input("Enter source node: ")
            target = input("Enter target node: ")
            print(kg.shortest_path(source, target))
        elif choice == '8':
            page_rank = kg.page_rank()
            print("PageRank for all nodes:")
            for node, rank in sorted(page_rank.items(), key=lambda x: x[1], reverse=True):
                print(f"{node}: {rank:.4f}")
        elif choice == '9':
            communities = kg.detect_communities()
            print("Detected communities:")
            for node, community_id in communities.items():
                print(f"{node}: Community {community_id}")
        elif choice == '10':
            print("Exiting... Don't forget to save your changes!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
