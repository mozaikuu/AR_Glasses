from collections import deque
import heapq

class IndoorNavigator:
    def __init__(self, graph: dict, heuristic: dict = None):
        self.graph = graph
        self.heuristic = heuristic or {}

    # ---------- BFS ----------
    def bfs(self, start, goal):
        queue = deque([[start]])
        visited = set()

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == goal:
                return path

            if node not in visited:
                visited.add(node)
                for neighbor in self.graph.get(node, {}):
                    queue.append(path + [neighbor])

        return None

    # ---------- DFS ----------
    def dfs(self, start, goal, path=None, visited=None):
        if path is None:
            path = [start]
        if visited is None:
            visited = set()

        if start == goal:
            return path

        visited.add(start)

        for neighbor in self.graph.get(start, {}):
            if neighbor not in visited:
                result = self.dfs(neighbor, goal, path + [neighbor], visited)
                if result:
                    return result

        return None

    # ---------- Dijkstra ----------
    def dijkstra(self, start, goal):
        pq = [(0, start, [start])]
        visited = set()

        while pq:
            cost, node, path = heapq.heappop(pq)

            if node == goal:
                return path, cost

            if node in visited:
                continue
            visited.add(node)

            for neighbor, weight in self.graph.get(node, {}).items():
                heapq.heappush(pq, (cost + weight, neighbor, path + [neighbor]))

        return None, float("inf")

    # ---------- A* ----------
    def astar(self, start, goal):
        pq = [(0, start, [start], 0)]
        visited = set()

        while pq:
            f, node, path, g = heapq.heappop(pq)

            if node == goal:
                return path, g

            if node in visited:
                continue
            visited.add(node)

            for neighbor, weight in self.graph.get(node, {}).items():
                h = self.heuristic.get(neighbor, 0)
                heapq.heappush(
                    pq,
                    (g + weight + h, neighbor, path + [neighbor], g + weight)
                )

        return None, float("inf")


with open("indoor_graph.py") as f:
    exec(f.read())  # loads 'graph' and 'heuristic' variables
    

def path_to_instructions(path, graph):
    instructions = []

    for i in range(len(path) - 1):
        src = path[i]
        dst = path[i + 1]
        step = graph[src][dst]["instruction"]
        instructions.append(step)

    instructions.append(f"You have arrived at {path[-1]}")
    return instructions

instructions = path_to_instructions(path, graph)

for sentence in instructions:
    tts.speak(sentence)  # your TTS module

