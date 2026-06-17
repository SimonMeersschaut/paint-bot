import matplotlib.pyplot as plt
from enum import Enum


class Events(Enum):
    superpixel_too_small = "Superpixel too small."
    coverage_reached = "Coverage reached."
    all_indices_painted = "All indices painted."
    magnitude_zero = "Magnitude zero."
    flat_gradient = "Flat gradient."
    too_much_color_error = "Too much color error."
    no_painted_area = "No painted area."
    coverage_score_too_low = "Coverage score too low."
    stroke_too_short = "Stroke too short."
    max_attempts_reached = "Max attempts reached."
    stroke_accepted = "Stroke accepted"

class StrokeGenerationSupervisor:
    def __init__(self):
        self.events = {}
        self._max_error_threshold = 100
        self._min_stroke_length_pixels = 20

        self.error_threshold_history = [self._max_error_threshold]
        self.stroke_length_history = [self._min_stroke_length_pixels]
    
    def register_event(self, event: Events):
        TARGET_ACCEPTANCE_RATE = .02
        D_ERROR = .1
        D_STROKE_LENGTH = .1
        if event == Events.stroke_accepted:
            self._max_error_threshold -= D_ERROR / TARGET_ACCEPTANCE_RATE
            self._min_stroke_length_pixels += D_STROKE_LENGTH / TARGET_ACCEPTANCE_RATE

        else:
            if event not in self.events:
                self.events[event] = 0
            self.events[event] += 1

            if event == Events.too_much_color_error:
                self._max_error_threshold += D_ERROR
            elif event == Events.stroke_too_short:
                self._min_stroke_length_pixels -= D_STROKE_LENGTH

        self.error_threshold_history.append(self._max_error_threshold)
        self.stroke_length_history.append(self._min_stroke_length_pixels)
    
    def plot_settings_history(self):
        """Plots the evaluation history of max color error and min stroke length over time."""
        if len(self.error_threshold_history) <= 1:
            print("Not enough history events to plot yet.")
            return

        # Setup dual-axis figure for differing scale scopes
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Primary Axis (Left) - Color Error Threshold
        color1 = '#e74c3c' # Modern crimson/red
        line1 = ax1.plot(self.error_threshold_history, color=color1, linewidth=2, label="Max Color Error Threshold")
        ax1.set_xlabel("Event Sequence (Time)", fontsize=11, fontweight='bold', labelpad=10)
        ax1.set_ylabel("Max Color Error Threshold", color=color1, fontsize=11, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, linestyle='--', alpha=0.5)

        # Secondary Axis (Right) - Minimum Stroke Length
        ax2 = ax1.twinx()
        color2 = '#2980b9' # Modern slate/blue
        line2 = ax2.plot(self.stroke_length_history, color=color2, linewidth=2, linestyle='--', label="Min Stroke Length (px)")
        ax2.set_ylabel("Min Stroke Length (pixels)", color=color2, fontsize=11, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=color2)

        # Unified Legend configuration
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', frameon=True, facecolor='white', edgecolor='none')

        plt.title("Parameter Evolution History Across Tuning Events", fontsize=13, fontweight='bold', pad=15)
        plt.tight_layout()
        plt.show()

    def plot_decline_reasons(self):
        """Generates a circular donut chart of the counted events."""
        if not self.events:
            print("No events to plot.")
            return

        # Extract clean string values from the Enum for readable labels
        labels = [event.value for event in self.events.keys()]
        sizes = list(self.events.values())
        
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # FIX: Use the modern Matplotlib 3.8+ colormap syntax
        cmap = plt.colormaps['Set3']
        colors = cmap(range(len(labels)))

        # Plot the pie chart
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct=lambda p: f'{int(round(p * sum(sizes) / 100))}', # Added round() to prevent float truncation errors
            startangle=90, 
            colors=colors,
            textprops=dict(color="black"),
            wedgeprops=dict(width=0.4, edgecolor='white') # 'width' creates the donut hole
        )

        # Style the text inside the slices
        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_weight('bold')

        ax.set_title("Stroke Generation Events", fontsize=14, weight='bold', pad=20)
        
        # Ensure the chart is a perfect circle
        ax.axis('equal')  
        plt.tight_layout()
        plt.show()

    @property
    def max_attempts(self) -> int:
        return 1000
        
    @property
    def target_coverage(self) -> float:
        return .90

    @property
    def max_stroke_list_length(self) -> int:
        return 300

    @property
    def max_error_threshold(self) -> float:
        return self._max_error_threshold
        
    @property
    def min_stroke_length_pixels(self) -> float:
        return self._min_stroke_length_pixels

    @property
    def brush_size(self) -> float:
        return 15
 
    @property
    def min_coverage_percentage(self) -> float:
        return .9

    @property
    def gradient_step_size(self) -> float:
        return 5
    