import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiments import conduct_experiment


def fit_attraction_weight(num_samples, plot_path="experiment1_attraction_weight.png"):
    """Fit ATTRACTION_WEIGHT on a bounded grid in [0, 1] and plot results and durations."""
    attraction_weights = []
    scores = []
    durations = []  # Track experiment durations
    best_weight = 0.0
    best_score = float("inf")

    for z_value in np.linspace(-30, -5, num_samples):
        try:
            # Time the individual experiment execution
            start_time = time.time()
            try:
                score = conduct_experiment(KALMAN_Z_VALUE=float(z_value))
            except ValueError:
                # no strokes to visualize
                score = 0
            duration = time.time() - start_time

            print(f"ATTRACTION_WEIGHT={z_value:.3f} -> score={score:.6f} ({duration:.2f}s)")

            attraction_weights.append(float(z_value))
            scores.append(float(score))
            durations.append(duration)

            if score < best_score:
                best_score = score
                best_weight = float(z_value)
        except Exception as e:
            print("error", e)
            attraction_weights.append(float(0))
            scores.append(float(0))
            durations.append(0)
            


    # Create a figure with 2 subplots side-by-side (1 row, 2 columns)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Scores
    ax1.scatter(attraction_weights, scores, marker="o", linewidth=2, color="tab:blue")
    ax1.set_xlabel("ATTRACTION_WEIGHT")
    ax1.set_ylabel("Evaluation score")
    ax1.set_title("Evaluation Score vs Weight")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Durations
    ax2.scatter(attraction_weights, durations, marker="s", linewidth=2, color="tab:orange")
    ax2.set_xlabel("ATTRACTION_WEIGHT")
    ax2.set_ylabel("Duration (seconds)")
    ax2.set_title("Experiment Duration vs Weight")
    ax2.grid(True, alpha=0.3)

    # Global adjustments
    fig.suptitle("Experiment 1: attraction_weight sweep", fontsize=14)
    fig.tight_layout()
    
    # Save the plot if a path is desired
    # plt.savefig(plot_path)
    plt.show()

    return best_weight, best_score, plot_path


if __name__ == "__main__":
    fit_attraction_weight(20)