"""
gui/overlay.py - Small always-on-top status overlay for Aria.
Runs in the main thread; the voice/agent loop runs in a background thread
and pushes status updates through a thread-safe queue.
"""
import queue
import tkinter as tk

STATUS_COLORS = {
    "idle": "#3b3b3b",
    "listening": "#2ecc71",
    "thinking": "#f1c40f",
    "speaking": "#3498db",
    "error": "#e74c3c",
}

status_queue = queue.Queue()


def set_status(text: str, state: str = "idle"):
    """Called from the worker thread to update the overlay."""
    status_queue.put((text, state))


class AriaOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Aria")
        self.root.geometry("220x70+40+40")
        self.root.overrideredirect(True)  # no title bar
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1e1e")

        self.canvas = tk.Canvas(self.root, width=220, height=70, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack()

        self.dot = self.canvas.create_oval(15, 25, 35, 45, fill=STATUS_COLORS["idle"], outline="")
        self.label = self.canvas.create_text(
            50, 35, anchor="w", text="Aria - idle", fill="white", font=("Segoe UI", 11)
        )

        # allow dragging the window since it has no title bar
        self.canvas.bind("<ButtonPress-1>", self._start_move)
        self.canvas.bind("<B1-Motion>", self._do_move)

        self._poll_queue()

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _poll_queue(self):
        try:
            while True:
                text, state = status_queue.get_nowait()
                color = STATUS_COLORS.get(state, STATUS_COLORS["idle"])
                self.canvas.itemconfig(self.dot, fill=color)
                self.canvas.itemconfig(self.label, text=f"Aria - {text}")
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def run(self):
        self.root.mainloop()


def start_overlay_blocking():
    """Call this from the MAIN thread. Blocks forever running the tkinter loop."""
    overlay = AriaOverlay()
    overlay.run()