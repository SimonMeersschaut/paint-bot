import matplotlib.pyplot as plt
from enum import Enum
import numpy as np


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

        self.Z_VALUE = 0 # sigma;  1.28sigma = 10%

        # --- Kalman Filter Parameters ---
        self.mu = 50.0       # Initial estimated mean color error
        self.P = 100.0       # Initial estimation uncertainty (variance)
        self.Q = 0.5         # Process noise (allows the mean to drift over time)
        self.R = 25.0        # Measurement noise 
        self.sigma = 15.0    # Initial estimated standard deviation of the population
        self.alpha = 0.05    # Learning rate for the moving standard deviation

        self.history_errors = []
        self.history_mu = []
        self.history_sigma = []
        self.history_accepted = []

        self.error_threshold_history = []

        self.brush_size = 15
    
    def register_event(self, event: Events):
        if event == Events.stroke_accepted:
            pass
        else:
            if event not in self.events:
                self.events[event] = 0
            self.events[event] += 1
    
    def is_accepted(self, stroke_color_error: float, update_kalman=True) -> bool:
        # Guard it so it doesn't exceed the absolute hard limit or drop below 0
        current_threshold = max(0.0, self.mu - self.Z_VALUE * self.sigma)
        accepted = stroke_color_error <= current_threshold

        if update_kalman:
            # 1. Predict Step (Constant state model)
            self.P = self.P + self.Q

            # 2. Update Step (Kalman Gain and Measurement Correction)
            kalman_gain = self.P / (self.P + self.R)
            residual = stroke_color_error - self.mu
            self.mu = self.mu + kalman_gain * residual
            self.P = (1 - kalman_gain) * self.P

            # 3. Dynamic Population Variance Tracking (Exponential Moving Variance)
            # Tracks how spread out the incoming stroke errors are around the current mean
            self.sigma = np.sqrt((1 - self.alpha) * (self.sigma ** 2) + self.alpha * (residual ** 2))

            # 4. Determine Dynamic Threshold (Z = -1.28 targets the lowest 10%)

            # 5. Save Data for Plotting
            self.history_errors.append(stroke_color_error)
            self.history_mu.append(self.mu)
            self.history_sigma.append(self.sigma)
            self.history_accepted.append(accepted)

            if accepted:
                self.register_event(Events.stroke_accepted)
            else:
                self.register_event(Events.too_much_color_error)

        return accepted

    def plot_color_error_history(self):
        """Plots the Kalman filter tracking parameters, threshold, and raw stroke errors."""
        if not self.history_errors:
            print("No history data to plot.")
            return

        steps = np.arange(len(self.history_errors))
        errors = np.array(self.history_errors)
        accepted = np.array(self.history_accepted)

        # Convert history arrays to numpy arrays for vector math operations
        mu_arr = np.array(self.history_mu)
        sigma_arr = np.array(self.history_sigma)

        # Vectorized equivalent of: max(0.0, self.mu - self.Z_VALUE * self.sigma)
        thresholds = np.maximum(0.0, mu_arr - self.Z_VALUE * sigma_arr)

        plt.figure(figsize=(12, 6))

        # Scatter plot for strokes (Green = Accepted, Red = Rejected)
        plt.scatter(steps[accepted], errors[accepted], color='g', alpha=0.6, label='Accepted Strokes (Best 10%)', zorder=3)
        plt.scatter(steps[~accepted], errors[~accepted], color='r', alpha=0.15, label='Rejected Strokes', zorder=2)

        # Line plots for Kalman parameters
        plt.plot(steps, self.history_mu, color='blue', linewidth=2, label='Estimated Mean ($\mu$)')
        
        label_text = f'Acceptance Threshold ($\mu - {self.Z_VALUE}\sigma$)'
        plt.plot(steps, thresholds, color='black', linestyle='--', linewidth=2, label=label_text, zorder=4)
        
        # Shade the standard deviation band around the mean
        plt.fill_between(steps, mu_arr - sigma_arr, mu_arr + sigma_arr, color='blue', alpha=0.1, label='Population Spread ($\pm 1\sigma$)')

        plt.title("Adaptive Kalman Filter Stroke Error", fontsize=14, weight='bold')
        plt.xlabel("Stroke Sequence / Time", fontsize=11)
        plt.ylabel("Color Error", fontsize=11)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='upper right')
        
        plt.tight_layout()
        plt.show()

    def plot_decline_reasons(self):
        """Generates a circular donut chart of the counted events."""
        if not self.events:
            print("No events to plot.")
            return

        labels = [event.value for event in self.events.keys()]
        sizes = list(self.events.values())
        
        fig, ax = plt.subplots(figsize=(6, 6))
        cmap = plt.colormaps['Set3']
        colors = cmap(range(len(labels)))

        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct=lambda p: f'{int(round(p * sum(sizes) / 100))}', 
            startangle=90, 
            colors=colors,
            textprops=dict(color="black"),
            wedgeprops=dict(width=0.4, edgecolor='white') 
        )

        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_weight('bold')

        ax.set_title("Stroke Generation Events", fontsize=14, weight='bold', pad=20)
        ax.axis('equal')  
        plt.tight_layout()
        plt.show()

    @property
    def max_attempts(self) -> int:
        """Attempts to create a stroke, per segment"""
        return 1000
        
    @property
    def supercell_target_coverage(self) -> float:
        """If we have more coverage than this, we wont try fitting."""
        return .95

    @property
    def max_stroke_list_length(self) -> int:
        """The maximum length a list can have."""
        return 30

    @property
    def min_stroke_length_pixels(self) -> float:
        """The maximum length a stroke can have, algebraically."""
        return 10
    
    @property
    def max_error_threshold(self) -> float:
        """The maximum error a stroke can have with the original image."""
        return self._max_error_threshold
        

    @property
    def min_stroke_coverage_score(self) -> float:
        """The minimum stroke score a stroke must have."""
        return .25

    @property
    def gradient_step_size(self) -> float:
        """The step size for iterative stroke generation."""
        return 1
    