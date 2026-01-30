"""Indoor navigation tool using A* algorithm with graph visualization."""
import json
import heapq
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import os

# Node positions for visualization (x, y coordinates)
NODE_POSITIONS = {
    "Entrance": (0, 0),
    "Hall 2-0-25": (10, 0),
    "Hall 2-0-16": (0, 5),
    "Stairs G": (25, 0),
    "Elevator G": (20, 0),
    "Floor 1": (20, 10),
    "Left Corridor": (15, 10),
    "Elevator F1": (12, 10),
    "TA Office": (10, 10),
    "Section 2-1-52": (8, 10),
    "Hall 2-1-47": (7, 11),
    "Hall 2-1-46": (6, 10),
    "Hall 2-1-45": (4, 10),
    "Section 2-1-41": (2, 10),
    "Section 2-1-40": (0, 10),
    "Right Corridor": (25, 10),
    "Hall 2-1-76": (30, 10),
    "Hall 2-1-77": (33, 10),
    "Hall 2-1-83": (43, 10),
    "Hall 2-1-84": (45, 10),
    "Dean Office": (50, 12),
}


def load_graph(json_path: str = None) -> dict:
    """Load navigation graph from JSON file."""
    if json_path is None:
        json_path = Path(__file__).parent / "navigationGraph.json"

    with open(json_path, 'r') as f:
        return json.load(f)


def get_all_locations(graph: dict) -> list:
    """Get all available locations from the graph."""
    return list(graph.keys())


def heuristic(node: str, goal: str, positions: dict = NODE_POSITIONS) -> float:
    """Calculate Euclidean distance heuristic for A*."""
    if node not in positions or goal not in positions:
        return 0
    x1, y1 = positions[node]
    x2, y2 = positions[goal]
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def astar(graph: dict, start: str, goal: str) -> tuple[list[str], float, list[dict]]:
    """A* algorithm to find shortest path from start to goal.

    Returns:
        Tuple of (path, total_distance, steps)
    """
    if start not in graph:
        return [], 0, [{"error": f"Start location '{start}' not found in graph"}]

    if goal not in graph:
        return [], 0, [{"error": f"Destination '{goal}' not found in graph"}]

    if start == goal:
        return [start], 0, [{"step": 1, "location": start, "instruction": "You are already at your destination"}]

    # Priority queue: (f_score, node)
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    visited = set()

    steps = []

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            # Reconstruct path
            path = []
            total_distance = 0
            while current in came_from:
                path.append(current)
                prev = came_from[current]
                # Get distance
                if prev in graph and current in graph[prev]:
                    total_distance += graph[prev][current].get("distance", 0)
                current = prev
            path.append(start)
            path.reverse()

            # Add instructions for each step
            for i in range(len(path) - 1):
                from_node = path[i]
                to_node = path[i + 1]
                if from_node in graph and to_node in graph[from_node]:
                    step_info = {
                        "step": i + 1,
                        "from": from_node,
                        "to": to_node,
                        "instruction": graph[from_node][to_node].get("instruction", ""),
                        "distance": graph[from_node][to_node].get("distance", 0)
                    }
                    steps.append(step_info)

            return path, total_distance, steps

        # Only process neighbors if current is in graph
        if current not in graph:
            continue

        for neighbor in graph[current]:
            # Skip if neighbor is not in graph
            if neighbor not in graph:
                continue
            if neighbor in visited:
                continue
            if neighbor not in g_score:
                g_score[neighbor] = float('inf')

            tentative_g = g_score[current] + graph[current][neighbor].get("distance", 0)

            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return [], 0, [{"error": f"No path found from '{start}' to '{goal}'"}]


def format_directions(path: list[str], steps: list[dict]) -> str:
    """Format the navigation steps as human-readable directions."""
    if not path:
        return "No path found."

    if len(path) == 1:
        return "You are already at your destination."

    result = f"Route from {path[0]} to {path[-1]}:\n\n"
    result += f"Total steps: {len(steps)}\n\n"

    for step in steps:
        if "error" in step:
            result += f"Error: {step['error']}\n"
        else:
            result += f"Step {step['step']}: {step['from']}\n"
            result += f"   -> {step['instruction']}\n"
            result += f"   (Distance: {step['distance']} steps)\n\n"

    return result


def visualize_graph(graph: dict, path: list[str] = None, save_path: str = None, show: bool = False):
    """Visualize the navigation graph with optional path highlight.

    Args:
        graph: The navigation graph
        path: Optional list of nodes to highlight as the path
        save_path: Optional path to save the figure
        show: Whether to display the figure
    """
    plt.figure(figsize=(16, 12))

    # Get all nodes that exist in the graph
    graph_nodes = set(graph.keys())

    # Create positions dict - only for nodes in the graph
    positions = {}
    for node in graph_nodes:
        if node in NODE_POSITIONS:
            positions[node] = NODE_POSITIONS[node]
        else:
            # Auto-generate position for unknown nodes
            # Use a hash-like placement
            import random
            random.seed(hash(node) % 10000)
            positions[node] = (random.randint(0, 50), random.randint(0, 20))

    # Create NetworkX graph for visualization
    G = nx.Graph()

    # Add all nodes from graph
    for node in graph_nodes:
        G.add_node(node)

    # Add edges
    for node in graph:
        for neighbor in graph[node]:
            if neighbor in graph_nodes and not G.has_edge(node, neighbor):
                G.add_edge(node, neighbor)

    # Color nodes
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if path and node in path:
            node_colors.append('#00FF00')  # Green for path
            node_sizes.append(2000)
        elif node in NODE_POSITIONS:
            node_colors.append('#87CEEB')  # Light blue for known nodes
            node_sizes.append(1500)
        else:
            node_colors.append('#D3D3D3')  # Gray for auto-positioned nodes
            node_sizes.append(1000)

    # Draw the graph
    nx.draw_networkx_nodes(G, positions, node_color=node_colors, node_size=node_sizes, alpha=0.9)
    nx.draw_networkx_labels(G, positions, font_size=8, font_weight='bold')

    # Highlight path edges
    if path:
        path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        # Only draw edges that exist in the graph
        existing_path_edges = [e for e in path_edges if G.has_edge(e[0], e[1])]
        if existing_path_edges:
            nx.draw_networkx_edges(G, positions, edgelist=existing_path_edges, edge_color='#00FF00', width=3)

    # Draw all edges
    all_edges = list(G.edges())
    if all_edges:
        nx.draw_networkx_edges(G, positions, edgelist=all_edges, edge_color='gray', width=1, alpha=0.5)

    # Add edge labels (distances) only for path edges
    if path:
        path_edge_labels = {}
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            if from_node in graph and to_node in graph[from_node]:
                path_edge_labels[(from_node, to_node)] = f"{graph[from_node][to_node].get('distance', 0)}m"
        if path_edge_labels:
            nx.draw_networkx_edge_labels(G, positions, edge_labels=path_edge_labels, font_size=7)

    path_title = " -> ".join(path) if path else ""
    plt.title(f"Navigation Graph" + (f" - Path: {path_title}" if path else ""))

    # Add legend
    legend_elements = [
        mpatches.Patch(color='#00FF00', label='Path'),
        mpatches.Patch(color='#87CEEB', label='Known Location'),
        mpatches.Patch(color='#D3D3D3', label='Other Location'),
    ]
    plt.legend(handles=legend_elements, loc='upper left')

    plt.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Graph saved to: {save_path}")

    if show:
        plt.show()

    plt.close()


def navigate(start: str, destination: str) -> dict:
    """Navigate from start to destination using A* algorithm.

    Args:
        start: Starting location
        destination: Target destination

    Returns:
        Dictionary with path, steps, and directions
    """
    graph = load_graph()

    # Verify locations exist
    all_locations = get_all_locations(graph)
    if start not in all_locations:
        return {
            "success": False,
            "error": f"Start location '{start}' not found",
            "available_locations": all_locations
        }

    if destination not in all_locations:
        return {
            "success": False,
            "error": f"Destination '{destination}' not found",
            "available_locations": all_locations
        }

    path, distance, steps = astar(graph, start, destination)

    if not path:
        return {
            "success": False,
            "error": f"No path found from '{start}' to '{destination}'",
            "start": start,
            "destination": destination
        }

    directions = format_directions(path, steps)

    return {
        "success": True,
        "start": start,
        "destination": destination,
        "path": path,
        "total_distance": distance,
        "steps": steps,
        "directions": directions
    }


def navigate_steps(start: str, destination: str) -> dict:
    """Navigate from start to destination, returning structured step data.

    This function provides the same functionality as navigate() but is designed
    for step-by-step navigation where each step is delivered individually
    (e.g., for voice/audio guidance).

    Args:
        start: Starting location
        destination: Target destination

    Returns:
        Dictionary with path, steps, and navigation data optimized for
        step-by-step delivery to glasses
    """
    graph = load_graph()

    # Verify locations exist
    all_locations = get_all_locations(graph)
    if start not in all_locations:
        return {
            "success": False,
            "error": f"Start location '{start}' not found",
            "available_locations": all_locations
        }

    if destination not in all_locations:
        return {
            "success": False,
            "error": f"Destination '{destination}' not found",
            "available_locations": all_locations
        }

    path, distance, steps = astar(graph, start, destination)

    if not path:
        return {
            "success": False,
            "error": f"No path found from '{start}' to '{destination}'",
            "start": start,
            "destination": destination
        }

    # Format each step with audio-ready text
    audio_steps = []
    for i, step in enumerate(steps):
        audio_step = {
            "step_number": i + 1,
            "from_location": step.get("from"),
            "to_location": step.get("to"),
            "instruction": step.get("instruction", ""),
            "distance": step.get("distance", 0),
            "audio_text": f"Step {i + 1}: {step.get('instruction', '')}"
        }
        audio_steps.append(audio_step)

    return {
        "success": True,
        "start": start,
        "destination": destination,
        "path": path,
        "total_distance": distance,
        "total_steps": len(audio_steps),
        "steps": audio_steps,
        "arrival_message": f"You have arrived at {destination}"
    }


def get_step_by_index(path: list, steps: list, index: int) -> dict:
    """Get a specific step by index for step-by-step navigation.

    Args:
        path: List of location names in order
        steps: List of step dictionaries
        index: Step index (0-based)

    Returns:
        Step information for the requested index
    """
    if index < 0:
        return {"error": "Invalid step index"}

    if index == 0:
        # Welcome/ready message
        if path:
            return {
                "step": 0,
                "type": "ready",
                "instruction": f"Ready to navigate from {path[0]} to {path[-1]}",
                "from": path[0] if path else None,
                "distance": 0
            }
        return {"error": "No path available"}

    step_index = index - 1  # Convert to 0-based for steps list
    if step_index < len(steps):
        step = steps[step_index]
        return {
            "step": index,
            "type": "navigation",
            "from": step.get("from"),
            "to": step.get("to"),
            "instruction": step.get("instruction", ""),
            "distance": step.get("distance", 0)
        }
    elif step_index == len(steps) and path:
        # Arrival message
        return {
            "step": index,
            "type": "arrival",
            "instruction": f"You have arrived at {path[-1]}",
            "from": path[-1]
        }
    else:
        return {"error": f"Step {index} does not exist"}


if __name__ == "__main__":
    # Test the navigation
    print("=" * 60)
    print("INDOOR NAVIGATION SYSTEM - TEST")
    print("=" * 60)

    # Load graph
    graph = load_graph()
    locations = get_all_locations(graph)

    print(f"\nAvailable locations ({len(locations)}):")
    for loc in sorted(locations):
        print(f"  - {loc}")

    # Test navigation
    print("\n" + "=" * 60)
    print("TEST 1: Entrance to Dean Office")
    print("=" * 60)
    result = navigate("Entrance", "Dean Office")
    print(result["directions"])

    # Test another route
    print("=" * 60)
    print("TEST 2: TA Office to Hall 2-1-84")
    print("=" * 60)
    result = navigate("TA Office", "Hall 2-1-84")
    print(result["directions"])

    # Generate visualization
    print("\n" + "=" * 60)
    print("Generating visualization...")
    print("=" * 60)
    visualize_graph(graph, path=result["path"], save_path="navigation_test.png")