import json
import heapq
from typing import Dict, List

from fastmcp import FastMCP
mcp = FastMCP("navigation")




import os

BASE_DIR = os.path.dirname(__file__)
GRAPH_PATH = os.path.join(BASE_DIR, "navigationGraph.json")



def load_graph() -> Dict:
    with open(GRAPH_PATH, "r") as f:
        return json.load(f)

@mcp.tool()
def NavigateAStar(graph: Dict, start: str, goal: str):
    def heuristic(a, b):
        # No coordinates yet → admissible zero heuristic
        return 0

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {node: float("inf") for node in graph}
    g_score[start] = 0

    f_score = {node: float("inf") for node in graph}
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))

        for neighbor, meta in graph.get(current, {}).items():
            tentative = g_score[current] + meta["distance"]

            if tentative < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score[neighbor] = tentative + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None
