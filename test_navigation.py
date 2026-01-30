"""Test script for the indoor navigation system."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.navigation.navigation import (
    load_graph,
    get_all_locations,
    navigate,
    astar,
    format_directions,
    visualize_graph
)


def test_load_graph():
    """Test loading the navigation graph."""
    print("=" * 60)
    print("TEST: Load Graph")
    print("=" * 60)
    graph = load_graph()
    print(f"Loaded graph with {len(graph)} locations")
    assert len(graph) > 0, "Graph should have locations"
    print("PASSED\n")
    return graph


def test_get_locations(graph):
    """Test getting all locations."""
    print("=" * 60)
    print("TEST: Get All Locations")
    print("=" * 60)
    locations = get_all_locations(graph)
    print(f"Found {len(locations)} locations:")
    for loc in sorted(locations):
        print(f"  - {loc}")
    assert len(locations) > 0, "Should have locations"
    print("PASSED\n")
    return locations


def test_navigation(graph, start, destination, expected_path=True):
    """Test navigation between two points."""
    print("=" * 60)
    print(f"TEST: Navigate from '{start}' to '{destination}'")
    print("=" * 60)

    result = navigate(start, destination)

    print(f"Success: {result['success']}")
    print(f"Path length: {len(result.get('path', []))} nodes")
    print(f"Total distance: {result.get('total_distance', 0)} steps")

    if result['success']:
        print(f"\nPath: {' -> '.join(result['path'])}")
        print("\nDirections:")
        print(result['directions'])

        # Verify path is connected
        for i in range(len(result['path']) - 1):
            from_node = result['path'][i]
            to_node = result['path'][i + 1]
            assert to_node in graph.get(from_node, {}), \
                f"Edge should exist from {from_node} to {to_node}"

        if expected_path:
            assert len(result['path']) > 1, "Path should have multiple nodes"
            assert len(result['steps']) > 0, "Should have steps"
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

    print("PASSED\n")
    return result


def test_no_path(graph):
    """Test navigation with no possible path."""
    print("=" * 60)
    print("TEST: No Path Case")
    print("=" * 60)

    # This should work (same location)
    result = navigate("Entrance", "Entrance")
    print(f"Same location test - Success: {result['success']}")
    print(f"Path: {result.get('path', [])}")
    assert result['success'], "Same location should be valid"
    print("PASSED\n")


def test_invalid_location(graph):
    """Test navigation with invalid location."""
    print("=" * 60)
    print("TEST: Invalid Location")
    print("=" * 60)

    result = navigate("Invalid Place", "Dean Office")
    print(f"Invalid start - Success: {result['success']}")
    print(f"Error: {result.get('error', 'Unknown error')}")
    assert not result['success'], "Invalid location should fail"
    assert "available_locations" in result, "Should return available locations"
    print("PASSED\n")


def test_astar_algorithm(graph):
    """Test A* algorithm directly."""
    print("=" * 60)
    print("TEST: A* Algorithm")
    print("=" * 60)

    path, distance, steps = astar(graph, "Entrance", "TA Office")
    print(f"Path found: {len(path)} nodes")
    print(f"Distance: {distance}")
    print(f"Steps: {len(steps)}")
    assert len(path) > 0, "Should find a path"
    assert path[0] == "Entrance", "Should start at Entrance"
    assert path[-1] == "TA Office", "Should end at TA Office"
    print(f"Path: {' -> '.join(path)}")
    print("PASSED\n")
    return path


def run_interactive_test():
    """Run interactive navigation test."""
    print("\n" + "=" * 60)
    print("INTERACTIVE NAVIGATION TEST")
    print("=" * 60)

    graph = load_graph()
    locations = get_all_locations(graph)

    print(f"\nAvailable locations: {', '.join(sorted(locations))}")

    print("\nEnter your route (or press Enter to use default):")
    try:
        start = input("  Start location [Entrance]: ").strip() or "TA Office"
        dest = input("  Destination [Section 2-1-52]: ").strip() or "Section 2-1-52"
    except EOFError:
        # Non-interactive mode - use defaults
        start = "TA Office"
        dest = "Section 2-1-52"
        print(f"  Using defaults: {start} -> {dest}")

    result = navigate(start, dest)
    print("\n" + result['directions'])

    return result


def run_all_tests():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# INDOOR NAVIGATION SYSTEM - TEST SUITE")
    print("#" * 60)

    graph = test_load_graph()
    locations = test_get_locations(graph)

    # Test valid routes (that exist in the graph)
    test_navigation(graph, "Entrance", "Floor 1", expected_path=True)
    test_navigation(graph, "Floor 1", "TA Office", expected_path=True)
    test_navigation(graph, "TA Office", "Section 2-1-52", expected_path=True)
    test_navigation(graph, "Section 2-1-52", "Hall 2-1-45", expected_path=True)
    test_navigation(graph, "Right Corridor", "Hall 2-1-76", expected_path=True)
    test_navigation(graph, "Stairs G", "Elevator G", expected_path=True)

    # Test same location
    test_no_path(graph)

    # Test invalid location
    test_invalid_location(graph)

    path = test_astar_algorithm(graph)

    # Generate visualization
    print("=" * 60)
    print("Generating visualization...")
    print("=" * 60)
    visualize_graph(graph, path=path, save_path="navigation_visualization.png")
    print(f"Saved visualization to: navigation_visualization.png")

    # Interactive mode
    run_interactive_test()

    print("\n" + "#" * 60)
    print("# ALL TESTS COMPLETED SUCCESSFULLY")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()