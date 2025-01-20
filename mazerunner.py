import tkinter as tk
from tkinter import messagebox
import numpy as np
import time


class MicromouseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MazeRunner")
        self.tile_size = 40
        self.rows = 10
        self.cols = 10
        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.start = None
        self.end = None
        self.mode = None
        self.distances = np.full((self.rows, self.cols), -1)
        self.randomness = 30  # Default randomness percentage

        # UI Frames
        self.canvas = tk.Canvas(root, width=self.cols * self.tile_size, height=self.rows * self.tile_size)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.control_frame = tk.Frame(root)
        self.control_frame.pack()

        self.create_controls()

        self.draw_grid()

    def create_controls(self):
        """Create buttons and input fields for the GUI."""
        tk.Label(self.control_frame, text="Rows:").grid(row=0, column=0)
        self.row_input = tk.Entry(self.control_frame, width=5)
        self.row_input.insert(0, "10")
        self.row_input.grid(row=0, column=1)

        tk.Label(self.control_frame, text="Cols:").grid(row=0, column=2)
        self.col_input = tk.Entry(self.control_frame, width=5)
        self.col_input.insert(0, "10")
        self.col_input.grid(row=0, column=3)

        tk.Button(self.control_frame, text="Set Grid Size", command=self.set_grid_size).grid(row=0, column=4)

        tk.Label(self.control_frame, text="Randomness:").grid(row=1, column=0)
        self.randomness_slider = tk.Scale(self.control_frame, from_=10, to=90, orient=tk.HORIZONTAL)
        self.randomness_slider.set(self.randomness)
        self.randomness_slider.grid(row=1, column=1, columnspan=3)

        tk.Button(self.control_frame, text="Generate Random Maze", command=self.generate_random_maze).grid(row=1, column=4)
        tk.Button(self.control_frame, text="Set Start Point", command=lambda: self.set_mode("start")).grid(row=1, column=5)
        tk.Button(self.control_frame, text="Set End Point", command=lambda: self.set_mode("end")).grid(row=1, column=6)
        tk.Button(self.control_frame, text="Toggle Obstacle", command=lambda: self.set_mode("toggle_obstacle")).grid(row=1, column=7)
        tk.Button(self.control_frame, text="Solve Maze", command=self.solve_maze).grid(row=1, column=8)
        tk.Button(self.control_frame, text="Reset", command=self.reset_grid).grid(row=1, column=9)

    def set_mode(self, mode):
        """Set the current mode for clicking."""
        self.mode = mode
        messagebox.showinfo("Mode Set", f"Mode set to: {mode}")

    def on_canvas_click(self, event):
        """Handle clicks on the canvas to set obstacles, start, or end points."""
        x, y = event.x // self.tile_size, event.y // self.tile_size

        if self.mode == "toggle_obstacle":
            self.grid[y][x] = 0 if self.grid[y][x] == 1 else 1
        elif self.mode == "start":
            if self.start:
                self.grid[self.start[1]][self.start[0]] = 0
            self.start = (x, y)
            self.grid[y][x] = 2
        elif self.mode == "end":
            if self.end:
                self.grid[self.end[1]][self.end[0]] = 0
            self.end = (x, y)
            self.grid[y][x] = 3

        self.draw_grid()

    def draw_grid(self):
        """Draw the maze grid with obstacles, start, end points, and distances."""
        self.canvas.delete("all")
        for y in range(self.rows):
            for x in range(self.cols):
                color = "white"
                if self.grid[y][x] == 1:
                    color = "black"  # Obstacle
                elif self.grid[y][x] == 2:
                    color = "green"  # Start
                elif self.grid[y][x] == 3:
                    color = "red"  # End
                elif self.grid[y][x] == 4:
                    color = "blue"  # Path
                self.canvas.create_rectangle(
                    x * self.tile_size, y * self.tile_size,
                    (x + 1) * self.tile_size, (y + 1) * self.tile_size,
                    fill=color, outline="gray"
                )
                # Draw distance numbers
                if self.grid[y][x] == 0 or self.grid[y][x] == 4:
                    dist = self.distances[y][x]
                    if dist >= 0:
                        self.canvas.create_text(
                            (x + 0.5) * self.tile_size,
                            (y + 0.5) * self.tile_size,
                            text=str(dist),
                            fill="black"
                        )

    def generate_random_maze(self):
        """Generate a random maze based on the specified dimensions."""
        self.randomness = self.randomness_slider.get()
        obstacle_probability = self.randomness / 100
        self.grid = np.random.choice([0, 1], size=(self.rows, self.cols), p=[1 - obstacle_probability, obstacle_probability])
        self.start = self.end = None
        self.distances.fill(-1)
        self.draw_grid()

    def set_grid_size(self):
        """Set the grid size based on user input."""
        try:
            self.rows = int(self.row_input.get())
            self.cols = int(self.col_input.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid dimensions!")
            return

        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.distances = np.full((self.rows, self.cols), -1)
        self.canvas.config(width=self.cols * self.tile_size, height=self.rows * self.tile_size)
        self.start = self.end = None
        self.draw_grid()

    def solve_maze(self):
        """Solve the maze and calculate distances."""
        if not self.start or not self.end:
            messagebox.showerror("Error", "Start or End point not set!")
            return

        self.calculate_distances()
        path = self.find_path()
        if path:
            self.animate_path(path)
        else:
            messagebox.showinfo("Maze Unsolvable", "No path to the end point!")

    def calculate_distances(self):
        """Calculate the distances of each cell from the end point using BFS."""
        self.distances.fill(-1)
        if not self.end:
            return
        queue = [self.end]
        self.distances[self.end[1]][self.end[0]] = 0
        while queue:
            x, y = queue.pop(0)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] != 1:
                    if self.distances[ny][nx] == -1:
                        self.distances[ny][nx] = self.distances[y][x] + 1
                        queue.append((nx, ny))

    def find_path(self):
        """Find the path from start to end using distances."""
        if not self.start or not self.end:
            return None

        path = []
        current = self.start
        while current != self.end:
            path.append(current)
            x, y = current
            neighbors = [(x + dx, y + dy) for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]]
            neighbors = [(nx, ny) for nx, ny in neighbors if 0 <= nx < self.cols and 0 <= ny < self.rows]
            current = min(neighbors, key=lambda p: self.distances[p[1]][p[0]] if self.distances[p[1]][p[0]] >= 0 else float('inf'), default=None)
            if current is None or self.distances[current[1]][current[0]] == -1:
                return None
        path.append(self.end)
        return path

    def animate_path(self, path):
        """Animate the path on the canvas."""
        for x, y in path:
            if self.grid[y][x] == 0:  # Avoid overwriting start or end points
                self.grid[y][x] = 4  # Mark path
                self.draw_grid()
                time.sleep(0.1)  # Delay for animation
                self.root.update()

    def reset_grid(self):
        """Reset the grid to an empty state."""
        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.start = self.end = None
        self.distances.fill(-1)
        self.draw_grid()


if __name__ == "__main__":
    root = tk.Tk()
    app = MicromouseApp(root)
    root.mainloop()
