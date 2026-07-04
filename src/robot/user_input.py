import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser

from .printer import Printer


class RobotCalibrator:
    def __init__(self, printer: Printer, initial_position: tuple[float, float, float] = (0.0, 0.0, 0.0)):
        self.printer = printer
        self.current_position = {
            "X": float(initial_position[0]),
            "Y": float(initial_position[1]),
            "Z": float(initial_position[2]),
        }

    def _set_current_position(self, position: dict[str, float]) -> None:
        self.current_position = position.copy()

    def input_position(self, query: str, color=False, ask_z=True, initial_color: str = "#FFFFFF", master=None):
        """
        Opens an intuitive Tkinter window with sliders and a clickable 2D grid
        to control the printer coordinates live.

        The next session starts from the most recent known printer position.

        Returns:
            tuple: ((x, y, z), color_hex) if color=True
                   ((x, y, z), None) if color=False
                   (where z is None if ask_z=False)
        """
        X_MAX, Y_MAX, Z_MAX = 300, 300, 40
        FEED_RATE = 2000

        target_pos = self.current_position.copy()
        last_sent_pos = self.current_position.copy()

        chosen_color = {"HEX": initial_color}

        root = tk.Toplevel(master) if master is not None else tk.Tk()
        root.title("Live Printer Controller")

        window_height = "580" if color else "520"
        root.geometry(f"640x{window_height}")

        x_label_var = tk.StringVar(value=f"{target_pos['X']:.1f}")
        y_label_var = tk.StringVar(value=f"{target_pos['Y']:.1f}")
        if ask_z:
            z_label_var = tk.StringVar(value=f"{target_pos['Z']:.1f}")

        x_scale = None
        y_scale = None
        z_scale = None

        def update_from_sliders(*args):
            if x_scale is not None:
                target_pos["X"] = round(x_scale.get(), 1)
            if y_scale is not None:
                target_pos["Y"] = round(y_scale.get(), 1)
            if ask_z and z_scale is not None:
                target_pos["Z"] = round(z_scale.get(), 1)

            x_label_var.set(f"{target_pos['X']:.1f}")
            y_label_var.set(f"{target_pos['Y']:.1f}")
            if ask_z:
                z_label_var.set(f"{target_pos['Z']:.1f}")

            update_canvas_crosshair()

        def update_from_canvas(event):
            x_mm = (event.x / 250) * X_MAX
            y_mm = ((250 - event.y) / 250) * Y_MAX

            x_mm = max(0.0, min(float(X_MAX), x_mm))
            y_mm = max(0.0, min(float(Y_MAX), y_mm))

            x_scale.set(x_mm)
            y_scale.set(y_mm)

            update_from_sliders()

        def update_canvas_crosshair():
            canvas.delete("crosshair")
            cx = (target_pos["X"] / X_MAX) * 250
            cy = 250 - ((target_pos["Y"] / Y_MAX) * 250)

            canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="red", tags="crosshair")
            canvas.create_line(cx - 15, cy, cx + 15, cy, fill="red", tags="crosshair")
            canvas.create_line(cx, cy - 15, cx, cy + 15, fill="red", tags="crosshair")

        def choose_color_action():
            color_code = colorchooser.askcolor(color=chosen_color["HEX"], title="Select Filament/LED Color")
            if color_code[1]:
                chosen_color["HEX"] = color_code[1]
                color_preview.config(background=color_code[1])

        def live_stream_loop():
            nonlocal last_sent_pos
            commanded_pos = target_pos.copy()
            if not ask_z:
                commanded_pos["Z"] = last_sent_pos["Z"]

            if commanded_pos != last_sent_pos:
                try:
                    self.printer.move_to(
                        x=commanded_pos["X"],
                        y=commanded_pos["Y"],
                        z=commanded_pos["Z"],
                        feed_rate=FEED_RATE,
                    )
                    last_sent_pos = commanded_pos.copy()
                    self._set_current_position(commanded_pos)
                except Exception as e:
                    print(f"Serial communication error: {e}")

            if root.winfo_exists():
                root.after(100, live_stream_loop)

        def home_printer():
            self.printer.home()
            target_pos.update({"X": 0.0, "Y": 0.0, "Z": 0.0})
            last_sent_pos.update({"X": 0.0, "Y": 0.0, "Z": 0.0})
            self._set_current_position(target_pos)
            x_scale.set(0.0)
            y_scale.set(0.0)
            if ask_z:
                z_scale.set(0.0)
            update_canvas_crosshair()

        query_label = ttk.Label(
            root,
            text=query,
            font=('Helvetica', 12, 'bold'),
            anchor=tk.CENTER,
            justify=tk.CENTER,
            background="#e1e1e1",
            padding=10,
        )
        query_label.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(15, 0))

        canvas_frame = ttk.LabelFrame(root, text=" 2D Position Pad (Click to Move X/Y) ", padding=10)
        canvas_frame.pack(side=tk.LEFT, padx=15, pady=15, fill=tk.BOTH)

        canvas = tk.Canvas(canvas_frame, width=250, height=250, bg="#f0f0f0", relief="sunken", bd=2)
        canvas.pack()
        for i in range(1, 4):
            canvas.create_line(i * 62.5, 0, i * 62.5, 250, fill="#e0e0e0")
            canvas.create_line(0, i * 62.5, 250, i * 62.5, fill="#e0e0e0")

        canvas.bind("<Button-1>", update_from_canvas)
        canvas.bind("<B1-Motion>", update_from_canvas)

        slider_frame = ttk.LabelFrame(root, text=" Precision Controls ", padding=15)
        slider_frame.pack(side=tk.RIGHT, padx=15, pady=15, fill=tk.BOTH, expand=True)

        ttk.Label(slider_frame, text="X Position (mm):").pack(anchor=tk.W)
        x_scale = ttk.Scale(slider_frame, from_=0, to=X_MAX, orient=tk.HORIZONTAL, command=update_from_sliders)
        x_scale.set(target_pos["X"])
        x_scale.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(slider_frame, textvariable=x_label_var, font=('Courier', 10, 'bold')).pack(anchor=tk.E)

        ttk.Label(slider_frame, text="Y Position (mm):").pack(anchor=tk.W)
        y_scale = ttk.Scale(slider_frame, from_=0, to=Y_MAX, orient=tk.HORIZONTAL, command=update_from_sliders)
        y_scale.set(target_pos["Y"])
        y_scale.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(slider_frame, textvariable=y_label_var, font=('Courier', 10, 'bold')).pack(anchor=tk.E)

        if ask_z:
            ttk.Label(slider_frame, text="Z Height (mm):").pack(anchor=tk.W)
            z_scale = ttk.Scale(slider_frame, from_=0, to=Z_MAX, orient=tk.HORIZONTAL, command=update_from_sliders)
            z_scale.set(target_pos["Z"])
            z_scale.pack(fill=tk.X, pady=(0, 10))
            ttk.Label(slider_frame, textvariable=z_label_var, font=('Courier', 10, 'bold')).pack(anchor=tk.E)

        if color:
            color_frame = ttk.Frame(slider_frame)
            color_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))

            color_preview = tk.Frame(color_frame, width=24, height=24, relief="raised", bd=2, background=chosen_color["HEX"])
            color_preview.pack_propagate(False)
            color_preview.pack(side=tk.LEFT, padx=(0, 10))

            color_btn = ttk.Button(color_frame, text="Select Color", command=choose_color_action)
            color_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_frame = ttk.Frame(slider_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Home Printer", command=home_printer).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="Submit", command=root.destroy).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        update_canvas_crosshair()
        root.after(100, live_stream_loop)
        if master is not None:
            root.transient(master)
            root.grab_set()
            root.wait_window()
        else:
            root.mainloop()

        final_z = target_pos["Z"] if ask_z else self.current_position["Z"]
        final_coordinates = (target_pos["X"], target_pos["Y"], final_z)
        self._set_current_position({"X": final_coordinates[0], "Y": final_coordinates[1], "Z": final_coordinates[2]})
        final_color = chosen_color["HEX"] if color else None

        return final_coordinates, final_color