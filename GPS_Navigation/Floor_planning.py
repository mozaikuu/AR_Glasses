"""
floorplanner_final.py

Features:
 - CustomTkinter UI
 - Rooms occupy contiguous cells; painting auto-adds perimeter walls
 - Walls are stored as horizontal and vertical edge segments (not full cells)
 - Click near a grid line to toggle that wall segment (wall edit mode)
 - Delete Room via dropdown — removes only walls exclusive to that room
 - Shows current painting room in the UI
 - A* pathfinding respects wall segments
 - Save / Load plan (JSON)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import random
from queue import PriorityQueue

# ---------- Config ----------
GRID_N = 28
CELL_PX = 24
CANVAS_W = GRID_N * CELL_PX
CANVAS_H = GRID_N * CELL_PX
WALL_LINE_WIDTH = 4
CLICK_EDGE_TOL = 8
# ----------------------------

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar_with_walled_edges(grid_n, horizontal_walls, vertical_walls, start, goal):
    """
    A*: neighbors exist only if no wall segment between cells.
    horizontal_walls: set((r,c)) meaning a horizontal wall between (r,c) and (r+1,c).
    vertical_walls: set((r,c)) meaning a vertical wall between (r,c) and (r,c+1).
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
            # reconstruct path
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
        # Up: to (r-1, c) — check horizontal wall between (r-1,c) and (r,c) stored as (r-1,c)
        if r - 1 >= 0:
            if (r - 1, c) not in horizontal_walls:
                nb = (r - 1, c)
                tentative = g + 1
                if tentative < gscore.get(nb, float("inf")):
                    gscore[nb] = tentative
                    came_from[nb] = cur
                    f = tentative + heuristic(nb, goal)
                    openq.put((f, tentative, nb))
        # Down: to (r+1, c) — check horizontal wall between (r,c) and (r+1,c) stored as (r,c)
        if r + 1 < grid_n:
            if (r, c) not in horizontal_walls:
                nb = (r + 1, c)
                tentative = g + 1
                if tentative < gscore.get(nb, float("inf")):
                    gscore[nb] = tentative
                    came_from[nb] = cur
                    f = tentative + heuristic(nb, goal)
                    openq.put((f, tentative, nb))
        # Left: to (r, c-1) — check vertical wall between (r,c-1) and (r,c) stored as (r, c-1)
        if c - 1 >= 0:
            if (r, c - 1) not in vertical_walls:
                nb = (r, c - 1)
                tentative = g + 1
                if tentative < gscore.get(nb, float("inf")):
                    gscore[nb] = tentative
                    came_from[nb] = cur
                    f = tentative + heuristic(nb, goal)
                    openq.put((f, tentative, nb))
        # Right: to (r, c+1) — check vertical wall between (r,c) and (r,c+1) stored as (r,c)
        if c + 1 < grid_n:
            if (r, c) not in vertical_walls:
                nb = (r, c + 1)
                tentative = g + 1
                if tentative < gscore.get(nb, float("inf")):
                    gscore[nb] = tentative
                    came_from[nb] = cur
                    f = tentative + heuristic(nb, goal)
                    openq.put((f, tentative, nb))

    return None

class FloorPlanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Floor Planner — Final")
        self.geometry(f"1200x820")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Model
        self.grid_n = GRID_N
        self.cell_px = CELL_PX
        self.rooms = {}  # name -> {"cells": set((r,c)), "color": "#rrggbb"}
        self.horizontal_walls = set()  # (r,c) -> between (r,c) and (r+1,c)
        self.vertical_walls = set()    # (r,c) -> between (r,c) and (r,c+1)

        # UI / state
        self.painting_room = False
        self.room_to_paint = None
        self.wall_edit_mode = False
        self.current_path = None

        self._build_ui()
        self.update_room_menus()
        self.redraw()

    # ------- UI -------
    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=300)
        sidebar.pack(side="left", fill="y", padx=8, pady=8)

        ctk.CTkLabel(sidebar, text="Indoor Nav Editor", font=("Arial", 18, "bold")).pack(pady=(6,12))

        # Room controls
        ctk.CTkLabel(sidebar, text="Room name:").pack(anchor="w", padx=8)
        self.room_entry = ctk.CTkEntry(sidebar, width=220)
        self.room_entry.pack(padx=8, pady=(2,8))

        btn_frame = ctk.CTkFrame(sidebar)
        btn_frame.pack(fill="x", padx=8)
        ctk.CTkButton(btn_frame, text="Paint Room", command=self.enable_room_paint).grid(row=0, column=0, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Stop Paint", command=self.stop_painting).grid(row=0, column=1, padx=4, pady=4)

        # Show current painting room label
        self.current_room_label = ctk.CTkLabel(sidebar, text="Current Room: —", anchor="w")
        self.current_room_label.pack(fill="x", padx=8, pady=(6,8))

        ctk.CTkButton(sidebar, text="Delete Room...", command=self.delete_room_dialog).pack(padx=8, pady=6)

        # wall edit
        ctk.CTkButton(sidebar, text="Toggle Wall Edit Mode", command=self.toggle_wall_edit).pack(padx=8, pady=(8,12))

        # Pathfinding
        ctk.CTkLabel(sidebar, text="Pathfinding", font=("Arial", 12, "bold")).pack(padx=8, pady=(8,4))
        ctk.CTkLabel(sidebar, text="Start room:").pack(anchor="w", padx=8)
        self.start_var = tk.StringVar(value="")
        self.start_menu = ctk.CTkOptionMenu(sidebar, variable=self.start_var, values=[])
        self.start_menu.pack(padx=8, pady=4, fill="x")

        ctk.CTkLabel(sidebar, text="End room:").pack(anchor="w", padx=8)
        self.end_var = tk.StringVar(value="")
        self.end_menu = ctk.CTkOptionMenu(sidebar, variable=self.end_var, values=[])
        self.end_menu.pack(padx=8, pady=4, fill="x")

        ctk.CTkButton(sidebar, text="Find Path (A*)", command=self.find_path).pack(padx=8, pady=(6,4))
        ctk.CTkButton(sidebar, text="Clear Path", command=self.clear_path).pack(padx=8, pady=4)

        # Save / Load
        ctk.CTkLabel(sidebar, text="Plan", font=("Arial", 12, "bold")).pack(padx=8, pady=(12,4))
        ctk.CTkButton(sidebar, text="Save Plan", command=self.save_plan).pack(padx=8, pady=4)
        ctk.CTkButton(sidebar, text="Load Plan", command=self.load_plan).pack(padx=8, pady=4)

        # Legend
        legend = ctk.CTkFrame(sidebar)
        legend.pack(fill="x", padx=8, pady=(12,8))
        ctk.CTkLabel(legend, text="Tips:", anchor="w").pack(fill="x")
        ctk.CTkLabel(legend, text="• Paint Room: click/drag contiguous cells (auto-add perimeter walls)").pack(anchor="w")
        ctk.CTkLabel(legend, text="• Wall Edit: click near grid line to toggle single wall segment").pack(anchor="w")
        ctk.CTkLabel(legend, text="• Delete Room: removes room cells and only walls exclusive to that room").pack(anchor="w")

        # Canvas
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(side="right", padx=8, pady=8)
        self.canvas = tk.Canvas(canvas_frame, width=CANVAS_W, height=CANVAS_H, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

    # ------- Paint / Wall modes -------
    def enable_room_paint(self):
        name = self.room_entry.get().strip()
        if not name:
            messagebox.showwarning("Room name", "Please enter a room name.")
            return
        self.room_to_paint = name
        self.painting_room = True
        self.wall_edit_mode = False
        if name not in self.rooms:
            self.rooms[name] = {"cells": set(), "color": self._random_color()}
        self._update_current_room_label()
        self.update_room_menus()

    def stop_painting(self):
        self.painting_room = False
        self.room_to_paint = None
        self._update_current_room_label()

    def toggle_wall_edit(self):
        self.wall_edit_mode = not self.wall_edit_mode
        self.painting_room = False
        self.room_to_paint = None
        self._update_current_room_label()
        if self.wall_edit_mode:
            self.title("Floor Planner — Wall Edit Mode (click edges to toggle)")
        else:
            self.title("Floor Planner — Final")

    def _update_current_room_label(self):
        if self.painting_room and self.room_to_paint:
            self.current_room_label.configure(text=f"Current Room: {self.room_to_paint}")
        else:
            self.current_room_label.configure(text="Current Room: —")

    # ------- Canvas events -------
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
            return
        # connectivity: if room empty, allow first cell; else only adjacent
        if not self.rooms[room]["cells"]:
            self.rooms[room]["cells"].add(cell)
            self._add_perimeter_walls_for_cell(room, cell)
            self.current_path = None
            self._update_current_room_label()
            self.update_room_menus()
            self.redraw()
            return
        # require adjacency
        adj = False
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            if (r+dr, c+dc) in self.rooms[room]["cells"]:
                adj = True
                break
        if not adj:
            return
        # if cell belongs to other room, remove from other room
        other = self._room_at_cell(r, c)
        if other and other != room:
            self.rooms[other]["cells"].discard((r, c))
            if not self.rooms[other]["cells"]:
                del self.rooms[other]
        # add cell
        self.rooms[room]["cells"].add(cell)
        self._add_perimeter_walls_for_cell(room, cell)
        self.current_path = None
        self._update_current_room_label()
        self.update_room_menus()
        self.redraw()

    # ------- Perimeter wall bookkeeping -------
    def _add_perimeter_walls_for_cell(self, room_name, cell):
        """
        For newly added cell:
         - add wall segments on edges where neighbor is not same room
         - remove internal walls between this cell and same-room neighbors
        """
        r, c = cell
        # Up: horizontal wall at (r-1, c)
        if r - 1 >= 0:
            if (r - 1, c) in self.rooms[room_name]["cells"]:
                # internal: remove horizontal wall between them
                self.horizontal_walls.discard((r - 1, c))
            else:
                self.horizontal_walls.add((r - 1, c))
        else:
            # top outer boundary
            self.horizontal_walls.add((-1, c))
        # Down: horizontal at (r, c)
        if r + 1 < self.grid_n:
            if (r + 1, c) in self.rooms[room_name]["cells"]:
                self.horizontal_walls.discard((r, c))
            else:
                self.horizontal_walls.add((r, c))
        else:
            self.horizontal_walls.add((r, c))
        # Left: vertical at (r, c-1)
        if c - 1 >= 0:
            if (r, c - 1) in self.rooms[room_name]["cells"]:
                self.vertical_walls.discard((r, c - 1))
            else:
                self.vertical_walls.add((r, c - 1))
        else:
            self.vertical_walls.add((r, -1))
        # Right: vertical at (r, c)
        if c + 1 < self.grid_n:
            if (r, c + 1) in self.rooms[room_name]["cells"]:
                self.vertical_walls.discard((r, c))
            else:
                self.vertical_walls.add((r, c))
        else:
            self.vertical_walls.add((r, c))

        # For same-room neighbors, ensure internal walls removed
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.grid_n and 0 <= nc < self.grid_n:
                if (nr, nc) in self.rooms[room_name]["cells"]:
                    if dr != 0:
                        top = min(r, nr)
                        self.horizontal_walls.discard((top, c))
                    else:
                        left = min(c, nc)
                        self.vertical_walls.discard((r, left))

    # ------- Toggle nearest edge -------
    def _toggle_nearest_edge(self, x_px, y_px):
        fx = x_px / self.cell_px
        fy = y_px / self.cell_px
        v_idx = round(fx)
        h_idx = round(fy)
        dx = abs(x_px - v_idx * self.cell_px)
        dy = abs(y_px - h_idx * self.cell_px)
        if dx > CLICK_EDGE_TOL and dy > CLICK_EDGE_TOL:
            return False
        if dx <= dy:
            # vertical
            col = v_idx - 1
            row = int(fy)
            if not (0 <= row < self.grid_n):
                return False
            key = (row, col)
            if key in self.vertical_walls:
                self.vertical_walls.remove(key)
            else:
                self.vertical_walls.add(key)
            return True
        else:
            # horizontal
            row = h_idx - 1
            col = int(fx)
            if not (0 <= col < self.grid_n):
                return False
            key = (row, col)
            if key in self.horizontal_walls:
                self.horizontal_walls.remove(key)
            else:
                self.horizontal_walls.add(key)
            return True

    # ------- Drawing -------
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
        # vertical walls
        for r in range(self.grid_n):
            for c in range(-1, self.grid_n):
                if (r, c) in self.vertical_walls:
                    x = (c + 1) * self.cell_px
                    y1 = r * self.cell_px
                    y2 = y1 + self.cell_px
                    self.canvas.create_line(x, y1, x, y2, fill="#222222", width=WALL_LINE_WIDTH)
        # horizontal walls
        for r in range(-1, self.grid_n):
            for c in range(self.grid_n):
                if (r, c) in self.horizontal_walls:
                    y = (r + 1) * self.cell_px
                    x1 = c * self.cell_px
                    x2 = x1 + self.cell_px
                    self.canvas.create_line(x1, y, x2, y, fill="#222222", width=WALL_LINE_WIDTH)
        # room labels
        for name, data in self.rooms.items():
            if not data["cells"]:
                continue
            cx, cy = self._room_centroid_pixel(name)
            self.canvas.create_text(cx, cy, text=name, fill="black", font=("Arial", 10, "bold"))
        # draw path
        if self.current_path:
            pts = []
            for (r, c) in self.current_path:
                cx = c * self.cell_px + self.cell_px / 2
                cy = r * self.cell_px + self.cell_px / 2
                pts.append((cx, cy))
                x1 = c * self.cell_px + 4
                y1 = r * self.cell_px + 4
                x2 = x1 + self.cell_px - 8
                y2 = y1 + self.cell_px - 8
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ffea5c", outline="#e67e22")
            for i in range(len(pts) - 1):
                self.canvas.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill="#e74c3c", width=3)

    # ------- Room utilities -------
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
            return (0,0)
        r,c = cell
        return (c * self.cell_px + self.cell_px/2, r * self.cell_px + self.cell_px/2)

    def _random_color(self):
        def pastel(): return random.randint(150,255)
        return f"#{pastel():02x}{pastel():02x}{pastel():02x}"

    # ------- Delete room dialog & logic -------
    def delete_room_dialog(self):
        if not self.rooms:
            messagebox.showinfo("Delete Room", "No rooms to delete.")
            return
        dlg = tk.Toplevel(self)
        dlg.title("Delete Room")
        dlg.geometry("300x140")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Select room to delete:", font=("Arial", 10)).pack(pady=(12,6))
        sel = tk.StringVar(value=sorted(self.rooms.keys())[0])
        om = tk.OptionMenu(dlg, sel, *sorted(self.rooms.keys()))
        om.pack(pady=6)
        def confirm():
            name = sel.get()
            dlg.destroy()
            self._delete_room(name)
        tk.Button(dlg, text="Delete", command=confirm).pack(pady=(6,8))

    def _delete_room(self, name):
        if name not in self.rooms:
            messagebox.showinfo("Delete Room", "Room not found.")
            return
        cells = list(self.rooms[name]["cells"])
        # For each cell and each of its four edges: if that wall segment exists and the adjacent cell on other side is NOT in any other room, remove that wall.
        for (r,c) in cells:
            # Up edge: horizontal at (r-1, c) between (r-1,c) and (r,c)
            key_up = (r-1, c)
            if key_up in self.horizontal_walls:
                neighbor = (r-1, c)
                if not self._cell_belongs_to_any_room_except(neighbor, name):
                    self.horizontal_walls.discard(key_up)
            # Down edge: horizontal at (r,c) between (r,c) and (r+1,c)
            key_down = (r, c)
            if key_down in self.horizontal_walls:
                neighbor = (r+1, c)
                if not self._cell_belongs_to_any_room_except(neighbor, name):
                    self.horizontal_walls.discard(key_down)
            # Left edge: vertical at (r, c-1) between (r,c-1) and (r,c)
            key_left = (r, c-1)
            if key_left in self.vertical_walls:
                neighbor = (r, c-1)
                if not self._cell_belongs_to_any_room_except(neighbor, name):
                    self.vertical_walls.discard(key_left)
            # Right edge: vertical at (r, c) between (r,c) and (r,c+1)
            key_right = (r, c)
            if key_right in self.vertical_walls:
                neighbor = (r, c+1)
                if not self._cell_belongs_to_any_room_except(neighbor, name):
                    self.vertical_walls.discard(key_right)
        # finally remove the room and its cells
        del self.rooms[name]
        # After removing, some internal walls that were between this room and another remain (as they are shared). That's intended.
        self.current_path = None
        self.update_room_menus()
        self.redraw()

    def _cell_belongs_to_any_room_except(self, cell, exclude_room):
        r,c = cell
        if not (0 <= r < self.grid_n and 0 <= c < self.grid_n):
            # out-of-bounds considered "no room"
            return False
        for name, data in self.rooms.items():
            if name == exclude_room:
                continue
            if (r,c) in data["cells"]:
                return True
        return False

    # ------- Pathfinding glue -------
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
        path = astar_with_walled_edges(self.grid_n, self.horizontal_walls, self.vertical_walls, start_cell, end_cell)
        if path is None:
            messagebox.showinfo("No path", "No path found (blocked by walls).")
            self.current_path = None
        else:
            self.current_path = path
        self.redraw()

    def clear_path(self):
        self.current_path = None
        self.redraw()

    # ------- Save / Load -------
    def save_plan(self):
        fname = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not fname:
            return
        rooms_serial = {name: {"cells": list(data["cells"]), "color": data["color"]} for name,data in self.rooms.items()}
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
        fname = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not fname:
            return
        with open(fname, "r") as f:
            payload = json.load(f)
        rooms_serial = payload.get("rooms", {})
        self.rooms = {name: {"cells": set(tuple(x) for x in rd.get("cells", [])), "color": rd.get("color", self._random_color())} for name,rd in rooms_serial.items()}
        self.horizontal_walls = set(tuple(x) for x in payload.get("horizontal_walls", []))
        self.vertical_walls = set(tuple(x) for x in payload.get("vertical_walls", []))
        self.update_room_menus()
        self.current_path = None
        self.redraw()
        messagebox.showinfo("Loaded", f"Plan loaded from {fname}")

    # ------- Menus / helpers -------
    def update_room_menus(self):
        names = sorted(self.rooms.keys())
        if not names:
            names = [""]
        self.start_menu.configure(values=names)
        self.end_menu.configure(values=names)
        if names and names[0] != "":
            self.start_var.set(names[0])
            self.end_var.set(names[-1])
        self._update_current_room_label()

    # ------- Run -------
    def run(self):
        self.update_room_menus()
        self.mainloop()

if __name__ == "__main__":
    app = FloorPlanner()
    app.run()
