import json
import networkx as nx
import matplotlib.pyplot as plt

def add_edges(graph, data, parent=None):
    """Recursively traverse the JSON data and add nodes and edges to the graph."""
    if isinstance(data, dict):
        for key, value in data.items():
            graph.add_node(key)
            if parent:
                graph.add_edge(parent, key)
            add_edges(graph, value, key)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            item_key = f'{parent}_item{i}'
            graph.add_node(item_key)
            graph.add_edge(parent, item_key)
            add_edges(graph, item, item_key)
    else:
        # For leaf nodes, create a unique key based on parent and data
        leaf_key = f'{parent}_{data}'
        graph.add_node(leaf_key, label=str(data))
        graph.add_edge(parent, leaf_key)

# Sample JSON data
json_data = {
    "name": "root",
    "children": [
        {"name": "child1", "value": 1},
        {"name": "child2", "children": [
            {"name": "grandchild1", "value": 2},
            {"name": "grandchild2", "value": 3}
        ]}
    ]
}

# Create a directed graph
G = nx.DiGraph()

# Add edges to the graph based on the JSON structure
add_edges(G, json_data)

# Draw the graph
pos = nx.spring_layout(G)  # positions for all nodes
nx.draw(G, pos, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold")
plt.show()