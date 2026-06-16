import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser
from .printer import Printer

def input_position(printer: Printer, query: str, color=False):
    """
    Opens an intuitive Tkinter window with sliders and a clickable 2D grid 
    to control the Printer coordinates live.
    
    Returns:
        tuple: ((x, y, z), color_hex) if color=True
               ((x, y, z), None) if color=False
    """
    # ----------------------------------------------------
    # State Configuration
    # ----------------------------------------------------
    X_MAX, Y_MAX, Z_MAX = 220, 220, 250  
    FEED_RATE = 2000
    
    target_pos = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    last_sent_pos = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    
    # Track selected color (HEX format)
    chosen_color = {"HEX": "#FFFFFF"} 
    
    # ----------------------------------------------------
    # GUI Setup
    # ----------------------------------------------------
    root = tk.Tk()
    root.title("Live Printer Controller")
    
    window_height = "580" if color else "520"
    root.geometry(f"640x{window_height}")

    x_label_var = tk.StringVar(value="0.0")
    y_label_var = tk.StringVar(value="0.0")
    z_label_var = tk.StringVar(value="0.0")

    # ----------------------------------------------------
    # Event Handlers & Live Loop
    # ----------------------------------------------------
    def update_from_sliders(*args):
        """Callback whenever a slider moves."""
        target_pos["X"] = round(x_scale.get(), 1)
        target_pos["Y"] = round(y_scale.get(), 1)
        target_pos["Z"] = round(z_scale.get(), 1)

        x_label_var.set(f"{target_pos['X']:.1f}")
        y_label_var.set(f"{target_pos['Y']:.1f}")
        z_label_var.set(f"{target_pos['Z']:.1f}")

        update_canvas_crosshair()

    def update_from_canvas(event):
        """Callback when user clicks/drags on the 2D canvas map."""
        x_mm = (event.x / 250) * X_MAX
        y_mm = ((250 - event.y) / 250) * Y_MAX
        
        x_mm = max(0.0, min(float(X_MAX), x_mm))
        y_mm = max(0.0, min(float(Y_MAX), y_mm))
        
        x_scale.set(x_mm)
        y_scale.set(y_mm)
        
        update_from_sliders()

    def update_canvas_crosshair():
        """Redraws the crosshair on the 2D touchpad."""
        canvas.delete("crosshair")
        cx = (target_pos["X"] / X_MAX) * 250
        cy = 250 - ((target_pos["Y"] / Y_MAX) * 250)
        
        canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill="red", tags="crosshair")
        canvas.create_line(cx-15, cy, cx+15, cy, fill="red", tags="crosshair")
        canvas.create_line(cx, cy-15, cx, cy+15, fill="red", tags="crosshair")

    def choose_color_action():
        """Opens native OS color dialog and updates the UI preview block."""
        color_code = colorchooser.askcolor(title="Select Filament/LED Color")
        if color_code[1]:  # Ensure the user didn't hit cancel
            chosen_color["HEX"] = color_code[1]
            color_preview.config(background=color_code[1])

    def live_stream_loop():
        """Throttled background loop running every 100ms."""
        nonlocal last_sent_pos
        if target_pos != last_sent_pos:
            try:
                printer.move_to(
                    x=target_pos["X"], 
                    y=target_pos["Y"], 
                    z=target_pos["Z"], 
                    feed_rate=FEED_RATE
                )
                last_sent_pos = target_pos.copy()
            except Exception as e:
                print(f"Serial communication error: {e}")
                
        # Only repeat loop if the window element still exists
        if root.winfo_exists():
            root.after(100, live_stream_loop)

    # ----------------------------------------------------
    # UI Layout
    # ----------------------------------------------------
    query_label = ttk.Label(
        root, 
        text=query, 
        font=('Helvetica', 12, 'bold'), 
        anchor=tk.CENTER,
        justify=tk.CENTER,
        background="#e1e1e1",
        padding=10
    )
    query_label.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(15, 0))

    canvas_frame = ttk.LabelFrame(root, text=" 2D Position Pad (Click to Move X/Y) ", padding=10)
    canvas_frame.pack(side=tk.LEFT, padx=15, pady=15, fill=tk.BOTH)
    
    canvas = tk.Canvas(canvas_frame, width=250, height=250, bg="#f0f0f0", relief="sunken", bd=2)
    canvas.pack()
    for i in range(1, 4):
        canvas.create_line(i*62.5, 0, i*62.5, 250, fill="#e0e0e0")
        canvas.create_line(0, i*62.5, 250, i*62.5, fill="#e0e0e0")
        
    canvas.bind("<Button-1>", update_from_canvas)
    canvas.bind("<B1-Motion>", update_from_canvas)

    slider_frame = ttk.LabelFrame(root, text=" Precision Controls ", padding=15)
    slider_frame.pack(side=tk.RIGHT, padx=15, pady=15, fill=tk.BOTH, expand=True)

    ttk.Label(slider_frame, text="X Position (mm):").pack(anchor=tk.W)
    x_scale = ttk.Scale(slider_frame, from_=0, to=X_MAX, orient=tk.HORIZONTAL, command=update_from_sliders)
    x_scale.pack(fill=tk.X, pady=(0, 10))
    ttk.Label(slider_frame, textvariable=x_label_var, font=('Courier', 10, 'bold')).pack(anchor=tk.E)

    ttk.Label(slider_frame, text="Y Position (mm):").pack(anchor=tk.W)
    y_scale = ttk.Scale(slider_frame, from_=0, to=Y_MAX, orient=tk.HORIZONTAL, command=update_from_sliders)
    y_scale.pack(fill=tk.X, pady=(0, 10))
    ttk.Label(slider_frame, textvariable=y_label_var, font=('Courier', 10, 'bold')).pack(anchor=tk.E)

    ttk.Label(slider_frame, text="Z Height (mm):").pack(anchor=tk.W)
    z_scale = ttk.Scale(slider_frame, from_=0, to=Z_MAX, orient=tk.HORIZONTAL, command=update_from_sliders)
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
    
    ttk.Button(btn_frame, text="Home Printer", command=printer.home).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
    ttk.Button(btn_frame, text="Submit", command=root.destroy).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

    update_canvas_crosshair()
    root.after(100, live_stream_loop)
    
    # This blocks execution until `root.destroy()` is invoked by Submit
    root.mainloop()

    # ----------------------------------------------------
    # Return Configurations Post-Closing
    # ----------------------------------------------------
    final_coordinates = (target_pos["X"], target_pos["Y"], target_pos["Z"])
    final_color = chosen_color["HEX"] if color else None
    
    return final_coordinates, final_color