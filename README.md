# Neuro-Graph Dynamics

Neuro-Graph Dynamics is a knowledge graph application that explores the dynamics of philosophical influence over time, with a focus on neurosymbolic AI and the relationships between major Western philosophers. The project aims to provide a platform for visualizing, analyzing, and querying the complex web of intellectual influence that has shaped Western philosophy.

## Prerequisites

- Python 3.7 or later
- pip (Python package installer)

## Installation

1. Clone the repository:

```
git clone https://github.com/your-username/neuro-graph-dynamics.git
```

2. Navigate to the project directory:

```
cd neuro-graph-dynamics
```

3. Create and activate a virtual environment (optional but recommended):

```
python -m venv env
source env/bin/activate  # On Windows, use `env\Scripts\activate`
```

4. Install the required packages:

```
pip install -r requirements.txt
```

## Usage

1. Run the Flask app:

```
python app.py
```

2. The app will be available at `http://localhost:5000`.

You can use tools like `curl` or web browsers to interact with the API endpoints:

- `GET /`: Render the index page
- `POST /add_node`: Add a new node to the graph
  - Request body: `{ "node": "Node Label", "attributes": { ... } }`
- `POST /add_edge`: Add a new edge between nodes
  - Request body: `{ "node1": "Node 1", "node2": "Node 2", "relation": "Relation Type" }`
- `GET /query_node?node=<node_id>`: Query information about a node
- `GET /visualize`: Get the graph visualization in Mermaid format
- `GET /page_rank`: Calculate PageRank for all nodes
- `GET /detect_communities`: Detect communities in the graph
- `POST /load_graph`: Load a new graph from JSON data
  - Request body: `{ "file_content": "..." }`

The `main.py` script provides a command-line interface for working with the graph directly.

## Data

The `knowledge_graph.json` file contains a knowledge graph representing the influence relationships between major Western philosophers over the past 500 years. Each node represents a philosopher, with attributes like their name, years lived, and philosophical school. Edges between nodes indicate influence, with various relation types like `:influenced`, `:debated`, `:collaborated`, etc.

This graph can be used for analysis, visualization, and exploration of the complex web of intellectual influence that has shaped Western philosophy.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository and create a new branch for your feature or bug fix.
2. Write clear, concise, and well-documented code.
3. Test your changes thoroughly.
4. Submit a pull request with a detailed description of your changes.

## License

This project is licensed under the [MIT License](LICENSE).
