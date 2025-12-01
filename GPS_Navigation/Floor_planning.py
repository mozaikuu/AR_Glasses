"""
floorplanner_walls.py

Features:
 - CustomTkinter UI
 - Rooms occupy multiple contiguous cells
 - Painting a room auto-adds wall segments around its perimeter (enclosed room)
 - Wall segments are stored as horizontal and vertical edges (not full cell blocks)
 - Click near a grid line to toggle that wall segment explicitly
 - A* pathfinding respects wall segments (cannot cross a wall)
 - Save/Load plan (JSON)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import random
from queue import PriorityQueue

# -------------------- Config --------------------
GRID_N = 28          # cells per dimension
CELL_PX = 24         # pixels per cell
CANVAS_W = GRID_N * CELL_PX
CANVAS_H = GRID_N * CELL_PX
WALL_LINE_WIDTH = 4  # visual width of wall lines
CLICK_EDGE_TOL = 8   # pixels tolerance to detect edge click
# ------------------------------------------------

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar_with_walled_edges(grid_rows, grid_cols, horizontal_walls, vertical_walls, start, goal):
    """
    A*: neighbors exist only if no wall segment between cells.
    horizontal_walls contains (r, c) meaning a horizontal wall between (r,c) and (r+1,c).
    vertical_walls contains (r, c) meaning a vertical wall between (r,c) and (r,c+1).
    start/goal are (r,c)
    """
    openq = PriorityQueue()
    openq.put((heuristic(start, goal), 0, start))
    came_from = {start: None}
    gscore = {start: 0}
    visited = set()

    while not openq.empty():
        _, g, cur = openq.get()
        if cur == goal:
            # reconstruct
            path = []
            node = cur
            while node:
                path.append(node)
                node = came_from[node]
            return list(reversed(path))

        if cur in visited:
            continue
        visited.add(cur)

        r, c = cur
        neighbors = []
        # Up: to (r-1, c) — check horizontal wall between (r-1,c) and (r,c) which is horizontal_walls[(r-1,c)]
        if r - 1 >= 0:
            if (r - 1, c) not in horizontal_walls:
                neighbors.append((r - 1, c))
        # Down: to (r+1, c) — check horizontal wall between (r,c) and (r+1,c)
        if r + 1 < grid_rows:
            if (r, c) not in horizontal_walls:
                neighbors.append((r + 1, c))
        # Left: to (r, c-1) — check vertical wall between (r,c-1) and (r,c)
        if c - 1 >= 0:
            if (r, c - 1) not in vertical_walls:
                neighbors.append((r, c - 1))
        # Right: to (r, c+1) — check vertical wall between (r,c) and (r,c+1)
        if c + 1 < grid_cols:
            if (r, c) not in vertical_walls:
                neighbors.append((r, c + 1))

        for nb in neighbors:
            tentative = g + 1
            if tentative < gscore.get(nb, float("inf")):
                gscore[nb] = tentative
                f = tentative + heuristic(nb, goal)
                came_from[nb] = cur
                openq.put((f, tentative, nb))

    return None


class FloorPlanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Floor Planner — Walls on edges")
        self.geometry(f"{1100}x{800}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Model
        self.grid_n = GRID_N
        self.cell_px = CELL_PX

        # rooms: name -> {"cells": set((r,c),...), "color":"#rrggbb"}
        self.rooms = {}

        # walls as segments on edges:
        # horizontal_walls: set of (r,c) meaning wall between (r,c) and (r+1,c)  (0 <= r < grid_n-1)
        # vertical_walls: set of (r,c) meaning wall between (r,c) and (r,c+1)    (0 <= c < grid_n-1)
        self.horizontal_walls = set()
        self.vertical_walls = set()

        # UI state
        self.painting_room = False
        self.room_to_paint = None
        self.wall_edit_mode = False  # if True, clicking near edge toggles wall segment
        self.current_path = None

        self._build_ui()
        self.update_room_menus()
        self.redraw()

    # -------------- UI --------------
    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=260)
        sidebar.pack(side="left", fill="y", padx=8, pady=8)

        ctk.CTkLabel(sidebar, text="Indoor Nav Editor", font=("Arial", 18, "bold")).pack(pady=(6,10))

        ctk.CTkLabel(sidebar, text="Room name:").pack(anchor="w", padx=8)
        self.room_entry = ctk.CTkEntry(sidebar, width=200)
        self.room_entry.pack(padx=8, pady=(2,8))

        ctk.CTkButton(sidebar, text="Paint Room (click/drag)", command=self.enable_room_paint).pack(padx=8, pady=4)
        ctk.CTkButton(sidebar, text="Stop Painting", command=self.stop_painting).pack(padx=8, pady=4)
        ctk.CTkButton(sidebar, text="Delete Room", command=self.delete_room_prompt).pack(padx=8, pady=4)

        ctk.CTkButton(sidebar, text="Toggle Wall Edit Mode", command=self.toggle_wall_edit).pack(padx=8, pady=(10,6))

        ctk.CTkLabel(sidebar, text="Pathfinding", font=("Arial", 12, "bold")).pack(padx=8, pady=(12,4))
        ctk.CTkLabel(sidebar, text="Start room:").pack(anchor="w", padx=8)
        self.start_var = tk.StringVar(value="")
        self.start_menu = ctk.CTkOptionMenu(sidebar, variable=self.start_var, values=[])
        self.start_menu.pack(padx=8, pady=2, fill="x")

        ctk.CTkLabel(sidebar, text="End room:").pack(anchor="w", padx=8)
        self.end_var = tk.StringVar(value="")
        self.end_menu = ctk.CTkOptionMenu(sidebar, variable=self.end_var, values=[])
        self.end_menu.pack(padx=8, pady=2, fill="x")

        ctk.CTkButton(sidebar, text="Find Path (A*)", command=self.find_path).pack(padx=8, pady=(8,4))
        ctk.CTkButton(sidebar, text="Clear Path", command=self.clear_path).pack(padx=8, pady=4)

        ctk.CTkLabel(sidebar, text="Plan", font=("Arial", 12, "bold")).pack(padx=8, pady=(12,2))
        ctk.CTkButton(sidebar, text="Save Plan", command=self.save_plan).pack(padx=8, pady=4)
        ctk.CTkButton(sidebar, text="Load Plan", command=self.load_plan).pack(padx=8, pady=4)

        # legend / help
        helpf = ctk.CTkFrame(sidebar)
        helpf.pack(fill="x", padx=8, pady=(12,4))
        ctk.CTkLabel(helpf, text="Legend / Tips:", anchor="w").pack(fill="x")
        ctk.CTkLabel(helpf, text="• Paint Room: fills contiguous cells; auto-adds perimeter walls").pack(anchor="w")
        ctk.CTkLabel(helpf, text="• Edge-click (wall edit) toggles that wall segment").pack(anchor="w")
        ctk.CTkLabel(helpf, text="• A* respects walls — cannot cross wall segments").pack(anchor="w")

        # Canvas
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(side="right", padx=8, pady=8)
        self.canvas = tk.Canvas(canvas_frame, width=CANVAS_W, height=CANVAS_H, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

    # -------------- Room painting --------------
    def enable_room_paint(self):
        name = self.room_entry.get().strip()
        if not name:
            messagebox.showwarning("Room name", "Enter a room name first.")
            return
        self.room_to_paint = name
        self.painting_room = True
        self.wall_edit_mode = False
        if name not in self.rooms:
            self.rooms[name] = {"cells": set(), "color": self._random_color()}
        self.update_room_menus()

    def stop_painting(self):
        self.painting_room = False
        self.room_to_paint = None

    def delete_room_prompt(self):
        name = self.room_entry.get().strip()
        if not name:
            messagebox.showwarning("Delete room", "Enter the room name to delete.")
            return
        if name not in self.rooms:
            messagebox.showinfo("Delete room", "Room not found.")
            return
        if not messagebox.askyesno("Delete room", f"Delete room '{name}' and free its cells?"):
            return
        # remove room cells and remove now-exposed perimeter walls? leave walls as-is
        del self.rooms[name]
        # after deletion, it's reasonable to remove internal walls that separated this room from others
        # but we'll keep walls as the user can edit them manually
        self.update_room_menus()
        self.redraw()

    # -------------- Wall edit --------------
    def toggle_wall_edit(self):
        self.wall_edit_mode = not self.wall_edit_mode
        self.painting_room = False
        self.room_to_paint = None
        # simple feedback
        if self.wall_edit_mode:
            self.title("Floor Planner — Wall Edit Mode (click edges to toggle)")
        else:
            self.title("Floor Planner — Walls on edges")

    # -------------- Canvas actions --------------
    def on_canvas_click(self, ev):
        x, y = ev.x, ev.y
        if self.wall_edit_mode:
            toggled = self._toggle_nearest_edge(x, y)
            if toggled:
                self.current_path = None
                self.redraw()
            return

        if self.painting_room and self.room_to_paint:
            self._paint_cell_from_coords(x, y)
            return

    def on_canvas_drag(self, ev):
        x, y = ev.x, ev.y
        if self.wall_edit_mode:
            toggled = self._toggle_nearest_edge(x, y)
            if toggled:
                self.current_path = None
                self.redraw()
            return
        if self.painting_room and self.room_to_paint:
            self._paint_cell_from_coords(x, y)

    def _paint_cell_from_coords(self, x, y):
        r = y // self.cell_px
        c = x // self.cell_px
        if not (0 <= r < self.grid_n and 0 <= c < self.grid_n): 
            return
        room = self.room_to_paint
        cell = (r, c)
        if cell in self.rooms[room]["cells"]:
            return  # nothing to do
        # connectivity rule: if room empty, allow cell; else only add if adjacent to existing
        if not self.rooms[room]["cells"]:
            self.rooms[room]["cells"].add(cell)
            # set perimeter walls around this newly added cell
            self._add_perimeter_walls_for_cell(room, cell)
            self.current_path = None
            self.update_room_menus()
            self.redraw()
            return

        # require adjacency to existing cell
        adj = False
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            if (r+dr, c+dc) in self.rooms[room]["cells"]:
                adj = True
                break
        if not adj:
            # disallow creating disconnected island
            return

        # if cell belongs to another room, remove it from that room
        other = self._room_at_cell(r, c)
        if other and other != room:
            self.rooms[other]["cells"].discard((r, c))
            if not self.rooms[other]["cells"]:
                del self.rooms[other]

        # add cell to this room
        self.rooms[room]["cells"].add(cell)
        # auto-add perimeter walls around the new cell, and remove interior walls to same-room neighbors
        self._add_perimeter_walls_for_cell(room, cell)
        self.current_path = None
        self.update_room_menus()
        self.redraw()

    # -------------- Wall operations --------------
    def _add_perimeter_walls_for_cell(self, room_name, cell):
        """
        For a newly added cell, ensure there are walls on edges where neighbor is not same room.
        Also remove walls where neighbor IS same room (internal edges).
        """
        r, c = cell
        # Up edge: horizontal wall between (r-1,c) and (r,c) is represented at (r-1,c)
        # If neighbor above is same room -> remove that horizontal wall
        if r - 1 >= 0:
            if (r - 1, c) in self.rooms[room_name]["cells"]:
                # remove horizontal wall at (r-1,c)
                self.horizontal_walls.discard((r-1, c))
            else:
                # add horizontal wall at (r-1,c)
                self.horizontal_walls.add((r-1, c))
        else:
            # outer boundary: add wall at top edge (we represent by horizontal at -1,c? better to add at ( -1,c ) but our astar checks within valid ranges only.
            # We'll represent top boundary by horizontal wall at (-1,c). Keep consistent.
            self.horizontal_walls.add((-1, c))

        # Down edge: horizontal wall between (r,c) and (r+1,c) -> at (r,c)
        if r + 1 < self.grid_n:
            if (r + 1, c) in self.rooms[room_name]["cells"]:
                self.horizontal_walls.discard((r, c))
            else:
                self.horizontal_walls.add((r, c))
        else:
            self.horizontal_walls.add((r, c))  # bottom outer boundary

        # Left edge: vertical wall between (r,c-1) and (r,c) -> at (r,c-1)
        if c - 1 >= 0:
            if (r, c - 1) in self.rooms[room_name]["cells"]:
                self.vertical_walls.discard((r, c - 1))
            else:
                self.vertical_walls.add((r, c - 1))
        else:
            self.vertical_walls.add((r, -1))

        # Right edge: vertical wall between (r,c) and (r,c+1) -> at (r,c)
        if c + 1 < self.grid_n:
            if (r, c + 1) in self.rooms[room_name]["cells"]:
                self.vertical_walls.discard((r, c))
            else:
                self.vertical_walls.add((r, c))
        else:
            self.vertical_walls.add((r, c))

        # Additionally, neighbors that now become adjacent to this new cell and belong to THIS room should have their perimeter walls updated (remove internal walls)
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.grid_n and 0 <= nc < self.grid_n:
                if (nr, nc) in self.rooms[room_name]["cells"]:
                    # ensure no wall between (r,c) <-> (nr,nc)
                    # horizontal neighbor
                    if dr != 0:
                        top = min(r, nr)
                        self.horizontal_walls.discard((top, c))
                    else:
                        left = min(c, nc)
                        self.vertical_walls.discard((r, left))

    def _toggle_nearest_edge(self, x_px, y_px):
        """
        Toggle the nearest grid edge (horizontal or vertical) if the click is close enough to an edge line.
        Returns True if toggled.
        """
        # find nearest vertical grid line and horizontal grid line
        # vertical lines are at x = c*cell_px for c in 0..grid_n
        # horizontal lines at y = r*cell_px for r in 0..grid_n
        # We must inspect closeness to these lines; if close to vertical line within tolerance and also close to horizontal line, decide which is closer.

        # compute fractional cell coordinates
        fx = x_px / self.cell_px
        fy = y_px / self.cell_px

        # nearest vertical line index (0..grid_n)
        v_idx = round(fx)
        h_idx = round(fy)

        # distance to vertical line in pixels
        dx = abs(x_px - v_idx * self.cell_px)
        dy = abs(y_px - h_idx * self.cell_px)

        # if both distances exceed tolerance -> not an edge click
        if dx > CLICK_EDGE_TOL and dy > CLICK_EDGE_TOL:
            return False

        # choose orientation by smaller distance
        if dx <= dy:
            # toggle vertical line v_idx at column v_idx between cells column v_idx-1 and v_idx
            col = v_idx - 1  # vertical wall between (r, col) and (r, col+1) is stored as (r, col)
            # iterate through row which is chosen by nearest integer row fy
            row = int(fy)
            if not (0 <= row < self.grid_n):
                return False
            key = (row, col)
            # special handling: if col == -1 or col == grid_n-1 etc allowed to represent outer boundary
            if key in self.vertical_walls:
                self.vertical_walls.remove(key)
            else:
                self.vertical_walls.add(key)
            # when toggling vertical wall, if that edge is between cells belonging to same room, keep it removed (but user explicit toggles override)
            # leave as explicit toggle
            return True
        else:
            # toggle horizontal line at h_idx
            row = h_idx - 1  # horizontal wall between (row, c) and (row+1, c) stored as (row, c)
            col = int(fx)
            if not (0 <= col < self.grid_n):
                return False
            key = (row, col)
            if key in self.horizontal_walls:
                self.horizontal_walls.remove(key)
            else:
                self.horizontal_walls.add(key)
            return True

    # -------------- Drawing --------------
    def redraw(self):
        self.canvas.delete("all")
        # draw cells
        for r in range(self.grid_n):
            for c in range(self.grid_n):
                x1 = c * self.cell_px
                y1 = r * self.cell_px
                x2 = x1 + self.cell_px
                y2 = y1 + self.cell_px
                room = self._room_at_cell(r, c)
                fill = self.rooms[room]["color"] if room else "white"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#cccccc", width=1)

        # draw vertical wall segments (lines between columns)
        for r in range(self.grid_n):
            for c in range(-1, self.grid_n):  # allow -1 and grid_n as outer boundary markers
                if (r, c) in self.vertical_walls:
                    # line x at c+1? vertical wall between (r,c) and (r,c+1) drawn at x = (c+1)*cell_px if c >=0 else x=0
                    x = (c + 1) * self.cell_px
                    y1 = r * self.cell_px
                    y2 = y1 + self.cell_px
                    self.canvas.create_line(x, y1, x, y2, fill="#222222", width=WALL_LINE_WIDTH)

        # draw horizontal wall segments (lines between rows)
        for r in range(-1, self.grid_n):
            for c in range(self.grid_n):
                if (r, c) in self.horizontal_walls:
                    # horizontal wall between (r,c) and (r+1,c) drawn at y = (r+1)*cell_px
                    y = (r + 1) * self.cell_px
                    x1 = c * self.cell_px
                    x2 = x1 + self.cell_px
                    self.canvas.create_line(x1, y, x2, y, fill="#222222", width=WALL_LINE_WIDTH)

        # draw room labels at centroids
        for name, data in self.rooms.items():
            if not data["cells"]:
                continue
            cx, cy = self._room_centroid_pixel(name)
            self.canvas.create_text(cx, cy, text=name, fill="black", font=("Arial", 10, "bold"))

        # draw path if exists
        if self.current_path:
            pts = []
            for (r, c) in self.current_path:
                cx = c * self.cell_px + self.cell_px / 2
                cy = r * self.cell_px + self.cell_px / 2
                pts.append((cx, cy))
                # highlight cell
                x1 = c * self.cell_px + 4
                y1 = r * self.cell_px + 4
                x2 = x1 + self.cell_px - 8
                y2 = y1 + self.cell_px - 8
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ffea5c", outline="#e67e22")
            # lines connecting centers
            for i in range(len(pts) - 1):
                self.canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill="#e74c3c", width=3)

    # -------------- Utilities --------------
    def _room_at_cell(self, r, c):
        for name, data in self.rooms.items():
            if (r, c) in data["cells"]:
                return name
        return None

    def _room_centroid_cell(self, name):
        cells = list(self.rooms[name]["cells"])
        if not cells:
            return None
        avg_r = sum(rc[0] for rc in cells) / len(cells)
        avg_c = sum(rc[1] for rc in cells) / len(cells)
        best = min(cells, key=lambda rc: abs(rc[0] - avg_r) + abs(rc[1] - avg_c))
        return best

    def _room_centroid_pixel(self, name):
        cell = self._room_centroid_cell(name)
        if not cell:
            return (0, 0)
        r, c = cell
        cx = c * self.cell_px + self.cell_px / 2
        cy = r * self.cell_px + self.cell_px / 2
        return (cx, cy)

    def _random_color(self):
        def pastel():
            return random.randint(150, 255)
        return f"#{pastel():02x}{pastel():02x}{pastel():02x}"

    # -------------- Pathfinding --------------
    def find_path(self):
        start_name = self.start_var.get()
        end_name = self.end_var.get()
        if not start_name or not end_name:
            messagebox.showwarning("Missing", "Select both start and end rooms.")
            return
        if start_name not in self.rooms or end_name not in self.rooms:
            messagebox.showwarning("Missing", "Start or end room missing.")
            return

        start_cell = self._room_centroid_cell(start_name)
        end_cell = self._room_centroid_cell(end_name)
        if not start_cell or not end_cell:
            messagebox.showerror("Invalid", "Could not determine start or end cell.")
            return

        # run A* using wall segments
        path = astar_with_walled_edges(self.grid_n, self.grid_n, self.horizontal_walls, self.vertical_walls, start_cell, end_cell)
        if path is None:
            messagebox.showinfo("No path", "No path found (blocked by walls).")
            self.current_path = None
        else:
            self.current_path = path
        self.redraw()

    def clear_path(self):
        self.current_path = None
        self.redraw()

    # -------------- Save/Load --------------
    def save_plan(self):
        fname = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not fname:
            return
        # serialize sets as lists
        rooms_serial = {}
        for name, data in self.rooms.items():
            rooms_serial[name] = {"cells": list(data["cells"]), "color": data["color"]}
        payload = {
            "rooms": rooms_serial,
            "horizontal_walls": list(self.horizontal_walls),
            "vertical_walls": list(self.vertical_walls),
            "grid_n": self.grid_n,
            "cell_px": self.cell_px
        }
        with open(fname, "w") as f:
            json.dump(payload, f, indent=2)
        messagebox.showinfo("Saved", f"Plan saved to {fname}")

    def load_plan(self):
        fname = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not fname:
            return
        with open(fname, "r") as f:
            payload = json.load(f)
        rooms_serial = payload.get("rooms", {})
        self.rooms = {}
        for name, rd in rooms_serial.items():
            self.rooms[name] = {"cells": set(tuple(x) for x in rd.get("cells", [])), "color": rd.get("color", self._random_color())}
        self.horizontal_walls = set(tuple(x) for x in payload.get("horizontal_walls", []))
        self.vertical_walls = set(tuple(x) for x in payload.get("vertical_walls", []))
        self.update_room_menus()
        self.current_path = None
        self.redraw()
        messagebox.showinfo("Loaded", f"Plan loaded from {fname}")

    def update_room_menus(self):
        names = sorted(self.rooms.keys())
        if not names:
            names = [""]
        self.start_menu.configure(values=names)
        self.end_menu.configure(values=names)
        if names and names[0] != "":
            self.start_var.set(names[0])
            self.end_var.set(names[-1])

    # -------------- Run --------------
    def run(self):
        self.update_room_menus()
        self.mainloop()


if __name__ == "__main__":
    app = FloorPlanner()
    app.run()
