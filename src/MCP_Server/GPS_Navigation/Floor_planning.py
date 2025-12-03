import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import heapq
import math
from collections import deque

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------- Config ----------
GRID_N = 40         # Grid size (20x20)
CELL_PX = 30        # Pixels per cell
CANVAS_W = GRID_N * CELL_PX
CANVAS_H = GRID_N * CELL_PX
WALL_WIDTH = 4
CLICK_TOLERANCE = 10 # Distance to edge to detect wall click

# Colors
COLOR_WALL = "#2B2B2B"
COLOR_GRID = "#E0E0E0"
COLOR_PATH = "#FFD700"  # Gold
COLOR_PATH_MARKER = "#FF4500" # OrangeRed

def random_color():
    import random
    # Generate pastel-ish colors
    r = random.randint(150, 255)
    g = random.randint(150, 255)
    b = random.randint(150, 255)
    return f"#{r:02x}{g:02x}{b:02x}"

# -------------------------
# Data Model
# -------------------------
class FloorData:
    def __init__(self, name):
        self.name = name
        self.rows = GRID_N
        self.cols = GRID_N
        
        # Rooms: name -> {"cells": set((r,c)), "color": hex}
        self.rooms = {}
        
        # Walls:
        # h_walls: set((r, c)) -> Wall exists BELOW cell (r,c) (between row r and r+1)
        # v_walls: set((r, c)) -> Wall exists to RIGHT of cell (r,c) (between col c and c+1)
        self.h_walls = set()
        self.v_walls = set()
        
        # Connections
        self.stairs = set()   # set((r,c))
        self.elevators = set() # set((r,c))

    def add_room_cell(self, room_name, r, c, color):
        # Ensure room entry exists
        if room_name not in self.rooms:
            self.rooms[room_name] = {"cells": set(), "color": color}
        
        # Connectivity check: strictly enforce contiguous rooms
        current_cells = self.rooms[room_name]["cells"]
        if current_cells:
            is_neighbor = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (r + dr, c + dc) in current_cells:
                    is_neighbor = True
                    break
            if not is_neighbor:
                return False # Reject painting disconnected cells
        
        # Remove from other rooms if present
        for other_name in list(self.rooms.keys()):
            if other_name == room_name: continue
            if (r, c) in self.rooms[other_name]["cells"]:
                self.rooms[other_name]["cells"].remove((r, c))
                # Update walls for the old room (it lost a cell)
                self._update_perimeter(other_name, (r,c), remove=True)
                if not self.rooms[other_name]["cells"]:
                    del self.rooms[other_name]

        self.rooms[room_name]["cells"].add((r, c))
        self._update_perimeter(room_name, (r, c), remove=False)
        return True

    def _update_perimeter(self, room_name, cell, remove=False):
        """
        Intelligent Auto-Walling:
        1. If adding a cell: Ensure walls exist between this cell and non-room neighbors.
           Remove walls between this cell and same-room neighbors.
        2. If removing a cell (overwritten): We don't necessarily delete walls unless 
           manually triggered, but we ensure the old room's boundary is respected.
           (Simplified: We just rebuild walls for the target room context).
        """
        if remove: return # Simplification: Walls stick around until toggled or overwritten

        r, c = cell
        room_cells = self.rooms[room_name]["cells"]

        # Check neighbor: UP (r-1, c)
        if (r-1, c) in room_cells:
            self.h_walls.discard((r-1, c)) # Remove wall strictly between them
        else:
            if r > 0: self.h_walls.add((r-1, c)) # Add wall above (which is h_wall of cell above)
            
        # Check neighbor: DOWN (r+1, c)
        if (r+1, c) in room_cells:
            self.h_walls.discard((r, c))
        else:
            if r < GRID_N - 1: self.h_walls.add((r, c))

        # Check neighbor: LEFT (r, c-1)
        if (r, c-1) in room_cells:
            self.v_walls.discard((r, c-1))
        else:
            if c > 0: self.v_walls.add((r, c-1))

        # Check neighbor: RIGHT (r, c+1)
        if (r, c+1) in room_cells:
            self.v_walls.discard((r, c))
        else:
            if c < GRID_N - 1: self.v_walls.add((r, c))


# -------------------------
# Main Application
# -------------------------
class MultiFloorPlanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("3D Floor Planner & Navigator")
        self.geometry("1400x900")
        
        # State
        self.floors = [] # List of FloorData
        self.current_floor_index = 0
        
        # Tool State
        self.mode = "VIEW" # VIEW, PAINT, WALL, STAIR, ELEVATOR
        self.current_room_name = ""
        self.current_room_color = random_color()
        self.path_result = [] # List of (floor_idx, r, c)
        
        self._setup_ui()
        self.add_floor() # Start with Floor 1

    def _setup_ui(self):
        # --- Left Sidebar (Controls) ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        ctk.CTkLabel(self.sidebar, text="FLOOR PLANNER", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        # TabView for Floor Selection
        self.floor_tabs = ctk.CTkTabview(self.sidebar, height=60, command=self._on_tab_change)
        self.floor_tabs.pack(fill="x", padx=10)
        
        # Add/Del Floor Buttons
        frm_fl = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frm_fl.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(frm_fl, text="+ Floor", width=100, command=self.add_floor).pack(side="left", padx=2)
        ctk.CTkButton(frm_fl, text="- Floor", width=100, fg_color="#C0392B", command=self.delete_floor).pack(side="right", padx=2)

        ctk.CTkLabel(self.sidebar, text="-- Editor Tools --").pack(pady=(20,5))
        
        # Room Painting
        self.entry_room = ctk.CTkEntry(self.sidebar, placeholder_text="Room Name (e.g. Kitchen)")
        self.entry_room.pack(padx=10, fill="x")
        
        self.btn_paint = ctk.CTkButton(self.sidebar, text="Paint Room (Drag)", command=self.set_mode_paint)
        self.btn_paint.pack(padx=10, pady=5, fill="x")
        
        # Walls & Connections
        self.btn_wall = ctk.CTkButton(self.sidebar, text="Toggle Walls (Click Edge)", fg_color="#555", command=self.set_mode_wall)
        self.btn_wall.pack(padx=10, pady=5, fill="x")
        
        frm_conn = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frm_conn.pack(fill="x", padx=10, pady=5)
        self.btn_stair = ctk.CTkButton(frm_conn, text="Stairs", width=90, fg_color="#2980B9", command=self.set_mode_stair)
        self.btn_stair.pack(side="left", padx=2)
        self.btn_elev = ctk.CTkButton(frm_conn, text="Elevator", width=90, fg_color="#8E44AD", command=self.set_mode_elevator)
        self.btn_elev.pack(side="right", padx=2)
        
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Mode: View", text_color="yellow")
        self.lbl_status.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="-- Navigation --").pack(pady=(20,5))
        
        # Pathfinding Inputs
        self.combo_start = ctk.CTkOptionMenu(self.sidebar, values=["(Select Room)"])
        self.combo_start.pack(padx=10, pady=5, fill="x")
        self.combo_end = ctk.CTkOptionMenu(self.sidebar, values=["(Select Room)"])
        self.combo_end.pack(padx=10, pady=5, fill="x")
        
        ctk.CTkButton(self.sidebar, text="Find Path (3D A*)", fg_color="#27AE60", command=self.calculate_path).pack(padx=10, pady=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Show Distance Graph", command=self.show_distance_graph).pack(padx=10, pady=5, fill="x")

        # Save/Load
        ctk.CTkLabel(self.sidebar, text="-- Project --").pack(pady=(20,5))
        ctk.CTkButton(self.sidebar, text="Save JSON", command=self.save_project).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Load JSON", command=self.load_project).pack(padx=10, pady=5, fill="x")

        # --- Right Side (Canvas) ---
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", width=CANVAS_W, height=CANVAS_H, highlightthickness=0)
        self.canvas.pack(expand=True)
        
        # Bindings
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

    # -------------------------
    # Logic: Floors
    # -------------------------
    def add_floor(self):
        count = len(self.floors)
        name = f"Floor {count + 1}"
        self.floors.append(FloorData(name))
        self.floor_tabs.add(name)
        self.floor_tabs.set(name) # Auto switch
        self.current_floor_index = count
        self.update_room_dropdowns()
        self.redraw()

    def delete_floor(self):
        if len(self.floors) <= 1:
            return
        
        # Remove current
        idx = self.current_floor_index
        name = self.floors[idx].name
        self.floor_tabs.delete(name)
        self.floors.pop(idx)
        
        # Adjust index
        if self.current_floor_index >= len(self.floors):
            self.current_floor_index = len(self.floors) - 1
        
        # Rename remaining tabs for consistency? (Optional, let's keep simple)
        self.floor_tabs.set(self.floors[self.current_floor_index].name)
        self.update_room_dropdowns()
        self.redraw()

    def _on_tab_change(self):
        selected_name = self.floor_tabs.get()
        for i, floor in enumerate(self.floors):
            if floor.name == selected_name:
                self.current_floor_index = i
                break
        self.redraw()

    # -------------------------
    # Logic: Tools
    # -------------------------
    def set_mode_paint(self):
        name = self.entry_room.get().strip()
        if not name:
            messagebox.showwarning("Input", "Please enter a Room Name first.")
            return
        self.mode = "PAINT"
        self.current_room_name = name
        # If room exists, use its color, else new color
        floor = self.floors[self.current_floor_index]
        if name in floor.rooms:
            self.current_room_color = floor.rooms[name]["color"]
        else:
            self.current_room_color = random_color()
        self.lbl_status.configure(text=f"Mode: Painting '{name}'")

    def set_mode_wall(self):
        self.mode = "WALL"
        self.lbl_status.configure(text="Mode: Wall Edit (Click Edges)")

    def set_mode_stair(self):
        self.mode = "STAIR"
        self.lbl_status.configure(text="Mode: Place/Remove Stairs")

    def set_mode_elevator(self):
        self.mode = "ELEVATOR"
        self.lbl_status.configure(text="Mode: Place/Remove Elevator")

    # -------------------------
    # Logic: Canvas Interactions
    # -------------------------
    def get_cell_rc(self, x, y):
        c = x // CELL_PX
        r = y // CELL_PX
        if 0 <= r < GRID_N and 0 <= c < GRID_N:
            return r, c
        return None, None

    def on_canvas_click(self, event):
        self.handle_interaction(event.x, event.y, is_drag=False)

    def on_canvas_drag(self, event):
        self.handle_interaction(event.x, event.y, is_drag=True)

    def handle_interaction(self, x, y, is_drag):
        floor = self.floors[self.current_floor_index]
        r, c = self.get_cell_rc(x, y)
        
        if self.mode == "PAINT":
            if r is not None:
                success = floor.add_room_cell(self.current_room_name, r, c, self.current_room_color)
                if not success and not is_drag:
                    messagebox.showinfo("Connectivity", "New cells must be adjacent to existing room cells.")
                self.path_result = [] # Clear path on edit
                self.update_room_dropdowns()
                self.redraw()

        elif self.mode == "WALL" and not is_drag:
            # Determine if click is near vertical or horizontal edge
            cx = c * CELL_PX
            cy = r * CELL_PX
            dx = x % CELL_PX
            dy = y % CELL_PX
            
            # Logic to find nearest edge
            # Check vertical edge at c+1
            if dx > CELL_PX - CLICK_TOLERANCE:
                # Toggle V wall at (r, c)
                if (r, c) in floor.v_walls: floor.v_walls.remove((r, c))
                else: floor.v_walls.add((r, c))
            elif dx < CLICK_TOLERANCE and c > 0:
                # Toggle V wall at (r, c-1)
                if (r, c-1) in floor.v_walls: floor.v_walls.remove((r, c-1))
                else: floor.v_walls.add((r, c-1))
            elif dy > CELL_PX - CLICK_TOLERANCE:
                # Toggle H wall at (r, c)
                if (r, c) in floor.h_walls: floor.h_walls.remove((r, c))
                else: floor.h_walls.add((r, c))
            elif dy < CLICK_TOLERANCE and r > 0:
                # Toggle H wall at (r-1, c)
                if (r-1, c) in floor.h_walls: floor.h_walls.remove((r-1, c))
                else: floor.h_walls.add((r-1, c))
            self.path_result = []
            self.redraw()

        elif self.mode == "STAIR" and not is_drag:
            if r is not None:
                if (r, c) in floor.stairs: floor.stairs.remove((r, c))
                else: floor.stairs.add((r, c))
                self.redraw()

        elif self.mode == "ELEVATOR" and not is_drag:
            if r is not None:
                if (r, c) in floor.elevators: floor.elevators.remove((r, c))
                else: floor.elevators.add((r, c))
                self.redraw()

    # -------------------------
    # Logic: Drawing
    # -------------------------
    def redraw(self):
        self.canvas.delete("all")
        floor = self.floors[self.current_floor_index]

        # 1. Draw Grid
        for i in range(GRID_N + 1):
            p = i * CELL_PX
            self.canvas.create_line(p, 0, p, CANVAS_H, fill=COLOR_GRID)
            self.canvas.create_line(0, p, CANVAS_W, p, fill=COLOR_GRID)

        # 2. Draw Rooms
        for name, data in floor.rooms.items():
            color = data["color"]
            for (r, c) in data["cells"]:
                x1 = c * CELL_PX
                y1 = r * CELL_PX
                self.canvas.create_rectangle(x1, y1, x1+CELL_PX, y1+CELL_PX, fill=color, outline="")
            
            # Draw label at centroid
            if data["cells"]:
                avg_r = sum(c[0] for c in data["cells"]) / len(data["cells"])
                avg_c = sum(c[1] for c in data["cells"]) / len(data["cells"])
                self.canvas.create_text(avg_c*CELL_PX + CELL_PX/2, avg_r*CELL_PX + CELL_PX/2, 
                                        text=name, fill="black", font=("Arial", 10, "bold"))

        # 3. Draw Connectors
        for (r, c) in floor.stairs:
            x, y = c * CELL_PX + CELL_PX/2, r * CELL_PX + CELL_PX/2
            self.canvas.create_text(x, y, text="S", font=("Arial", 14, "bold"), fill="white")
            self.canvas.create_rectangle(c*CELL_PX+2, r*CELL_PX+2, (c+1)*CELL_PX-2, (r+1)*CELL_PX-2, outline="white", width=2)

        for (r, c) in floor.elevators:
            x, y = c * CELL_PX + CELL_PX/2, r * CELL_PX + CELL_PX/2
            self.canvas.create_text(x, y, text="E", font=("Arial", 14, "bold"), fill="blue")
            self.canvas.create_oval(c*CELL_PX+2, r*CELL_PX+2, (c+1)*CELL_PX-2, (r+1)*CELL_PX-2, outline="blue", width=2)

        # 4. Draw Walls
        # V Walls: at (r,c) means right side of col c
        for (r, c) in floor.v_walls:
            x = (c + 1) * CELL_PX
            y1 = r * CELL_PX
            y2 = (r + 1) * CELL_PX
            self.canvas.create_line(x, y1, x, y2, fill=COLOR_WALL, width=WALL_WIDTH, capstyle="round")

        # H Walls: at (r,c) means bottom side of row r
        for (r, c) in floor.h_walls:
            y = (r + 1) * CELL_PX
            x1 = c * CELL_PX
            x2 = (c + 1) * CELL_PX
            self.canvas.create_line(x1, y, x2, y, fill=COLOR_WALL, width=WALL_WIDTH, capstyle="round")

        # 5. Draw Path
        if self.path_result:
            self._draw_path(floor)

    def _draw_path(self, current_floor_obj):
        # Filter path nodes that are on the current floor
        # path node: (floor_idx, r, c)
        
        path_on_floor = [node for node in self.path_result if node[0] == self.current_floor_index]
        
        if not path_on_floor:
            # Maybe path starts/ends on another floor, indicate that
            pass
            return

        # Draw lines
        if len(path_on_floor) > 1:
            points = []
            for _, r, c in path_on_floor:
                points.append(c*CELL_PX + CELL_PX/2)
                points.append(r*CELL_PX + CELL_PX/2)
            # This draws a single line connecting contiguous points. 
            # Note: If the path jumps (teleports via elevator not showing intermediate frames), line might look weird.
            # But A* usually generates contiguous nodes.
            self.canvas.create_line(points, fill=COLOR_PATH, width=3, arrow=tk.LAST)

        # Draw dots
        for _, r, c in path_on_floor:
            cx, cy = c*CELL_PX + CELL_PX/2, r*CELL_PX + CELL_PX/2
            r_dot = 4
            self.canvas.create_oval(cx-r_dot, cy-r_dot, cx+r_dot, cy+r_dot, fill=COLOR_PATH_MARKER, outline="white")

    # -------------------------
    # Logic: Pathfinding (3D A*)
    # -------------------------
    def update_room_dropdowns(self):
        # Gather all rooms from all floors
        rooms = []
        for i, f in enumerate(self.floors):
            for rname in f.rooms.keys():
                rooms.append(f"{rname} (F{i+1})")
        rooms.sort()
        
        if not rooms: rooms = ["(No Rooms)"]
        
        self.combo_start.configure(values=rooms)
        self.combo_end.configure(values=rooms)
        self.combo_start.set(rooms[0])
        self.combo_end.set(rooms[-1] if len(rooms) > 1 else rooms[0])

    def get_room_centroid(self, room_str):
        # Parse "RoomName (F1)" -> returns (floor_idx, r, c)
        try:
            name_part = room_str.rsplit(" (", 1)[0]
            floor_part = room_str.rsplit(" (", 1)[1].replace("F", "").replace(")", "")
            f_idx = int(floor_part) - 1
            
            floor = self.floors[f_idx]
            cells = list(floor.rooms[name_part]["cells"])
            if not cells: return None
            # Return first cell as target (A* works better with concrete target than centroid integer rounding)
            return (f_idx, cells[0][0], cells[0][1]) 
        except:
            return None

    def calculate_path(self):
        start_str = self.combo_start.get()
        end_str = self.combo_end.get()
        
        start_node = self.get_room_centroid(start_str)
        end_node = self.get_room_centroid(end_str)
        
        if not start_node or not end_node:
            messagebox.showerror("Error", "Invalid rooms selected.")
            return

        path = self.astar_3d(start_node, end_node)
        
        if path:
            self.path_result = path
            self.redraw()
            steps = len(path) - 1
            messagebox.showinfo("Path Found", f"Path found!\nSteps: {steps}\nFollow the gold line.")
            return path
        else:
            self.path_result = []
            self.redraw()
            messagebox.showwarning("No Path", "No route exists between these rooms.\nCheck walls and floor connections (Stairs/Elevators).")
            err = "No Path", "No route exists between these rooms.\nCheck walls and floor connections (Stairs/Elevators)."
            return err

    def astar_3d(self, start, goal):
        # Node: (f, r, c)
        def heuristic(a, b):
            return abs(a[1] - b[1]) + abs(a[2] - b[2]) + abs(a[0] - b[0]) * 5 # Floor change penalty

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                # Reconstruct
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            cf, cr, cc = current
            floor_obj = self.floors[cf]

            neighbors = []
            
            # 1. Planar moves (Up, Down, Left, Right)
            # Move North (cr-1)
            if cr > 0:
                # Check wall below neighbor (cr-1, cc) i.e., floor.h_walls at (cr-1, cc)
                if (cr-1, cc) not in floor_obj.h_walls:
                    neighbors.append((cf, cr-1, cc))
            
            # Move South (cr+1)
            if cr < GRID_N - 1:
                # Check wall below current (cr, cc)
                if (cr, cc) not in floor_obj.h_walls:
                    neighbors.append((cf, cr+1, cc))

            # Move West (cc-1)
            if cc > 0:
                # Check wall right of neighbor (cr, cc-1)
                if (cr, cc-1) not in floor_obj.v_walls:
                    neighbors.append((cf, cr, cc-1))

            # Move East (cc+1)
            if cc < GRID_N - 1:
                # Check wall right of current (cr, cc)
                if (cr, cc) not in floor_obj.v_walls:
                    neighbors.append((cf, cr, cc+1))

            # 2. Vertical Moves (Stairs/Elevators)
            # Stairs connect (f,r,c) <-> (f+1,r,c)
            if (cr, cc) in floor_obj.stairs:
                # Can go up?
                if cf < len(self.floors) - 1:
                    if (cr, cc) in self.floors[cf+1].stairs:
                        neighbors.append((cf+1, cr, cc))
                # Can go down?
                if cf > 0:
                    if (cr, cc) in self.floors[cf-1].stairs:
                        neighbors.append((cf-1, cr, cc))
            
            # Elevators connect (f,r,c) <-> (any_f,r,c)
            if (cr, cc) in floor_obj.elevators:
                for other_f in range(len(self.floors)):
                    if other_f == cf: continue
                    if (cr, cc) in self.floors[other_f].elevators:
                        neighbors.append((other_f, cr, cc))

            for neighbor in neighbors:
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
                    came_from[neighbor] = current

        return None # No path

    # -------------------------
    # Logic: Room Graph (Distance Calculation)
    # -------------------------
    def show_distance_graph(self):
        # Build a list of all room centroids
        nodes = [] # (name_with_floor, (f,r,c))
        for i, floor in enumerate(self.floors):
            for rname in floor.rooms:
                centroid = self.get_room_centroid(f"{rname} (F{i+1})")
                if centroid:
                    nodes.append((f"{rname} (F{i+1})", centroid))
        
        if len(nodes) < 2:
            messagebox.showinfo("Info", "Need at least 2 rooms to calculate distances.")
            return

        # Calculate pairwise distances
        results = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                name_a, pos_a = nodes[i]
                name_b, pos_b = nodes[j]
                
                path = self.astar_3d(pos_a, pos_b)
                dist = len(path) - 1 if path else float('inf')
                
                dist_str = f"{dist} steps" if dist != float('inf') else "No path"
                results.append(f"{name_a} <-> {name_b} : {dist_str}")

        # Show Popup
        top = ctk.CTkToplevel(self)
        top.title("Room Walking Distances")
        top.geometry("400x500")
        
        lbl = ctk.CTkLabel(top, text="Shortest Walking Distances", font=("Arial", 16, "bold"))
        lbl.pack(pady=10)
        
        textbox = ctk.CTkTextbox(top)
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", "\n".join(results))
        textbox.configure(state="disabled")

    # -------------------------
    # Logic: Save/Load
    # -------------------------
    def save_project(self):
        fpath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not fpath: return
        
        data = []
        for f in self.floors:
            floor_dict = {
                "name": f.name,
                "rooms": {k: {"cells": list(v["cells"]), "color": v["color"]} for k,v in f.rooms.items()},
                "h_walls": list(f.h_walls),
                "v_walls": list(f.v_walls),
                "stairs": list(f.stairs),
                "elevators": list(f.elevators)
            }
            data.append(floor_dict)
            
        with open(fpath, "w") as outfile:
            json.dump(data, outfile, indent=4)
        messagebox.showinfo("Saved", "Project saved successfully.")

    def load_project(self):
        fpath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not fpath: return
        
        try:
            with open(fpath, "r") as infile:
                data = json.load(infile)
            
            self.floors = []
            self.floor_tabs._segmented_button.configure(values=[]) # Clear tabs hackily or iterate delete
            # Proper tab clearing is hard in ctk, easier to rebuild or just remove old keys
            # For this script, we just append loaded floors to current or reset
            # Let's reset properly
            
            # Re-init app state essentially
            for old_name in list(self.floor_tabs._tab_dict.keys()):
                 self.floor_tabs.delete(old_name)

            for f_data in data:
                new_f = FloorData(f_data["name"])
                # Rooms
                for rname, rdata in f_data["rooms"].items():
                    new_f.rooms[rname] = {
                        "cells": set(tuple(x) for x in rdata["cells"]), 
                        "color": rdata["color"]
                    }
                # Walls & Conn
                new_f.h_walls = set(tuple(x) for x in f_data["h_walls"])
                new_f.v_walls = set(tuple(x) for x in f_data["v_walls"])
                new_f.stairs = set(tuple(x) for x in f_data["stairs"])
                new_f.elevators = set(tuple(x) for x in f_data["elevators"])
                
                self.floors.append(new_f)
                self.floor_tabs.add(new_f.name)
            
            self.current_floor_index = 0
            if self.floors:
                self.floor_tabs.set(self.floors[0].name)
            
            self.update_room_dropdowns()
            self.redraw()
            messagebox.showinfo("Loaded", "Project loaded successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")

if __name__ == "__main__":
    app = MultiFloorPlanner()
    app.mainloop()