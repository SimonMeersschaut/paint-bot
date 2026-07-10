import time
# from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiments import conduct_experiment
# from stroke_generation import Hyperparameters
from stroke_generation import ColorMethod, PaletteColorsOnly, KNearest


LITE = True

def make_experiment_plot():
    """Fit ATTRACTION_WEIGHT on a bounded grid in [0, 1] and plot results and durations."""

    fig, ax1  = plt.subplots(1, 1, figsize=(14, 5))
    
    score = conduct_experiment(LITE, COLOR_METHOD=PaletteColorsOnly())
    print("Color palette", score)

    ax1.axhline(y=score, color='r', linestyle='--', label='Palette colors only')

    ks = []
    scores = []

    try:
        for k in range(1, 20):
            score = conduct_experiment(LITE, COLOR_METHOD=KNearest(k))
            print(k, "nearest", score)
            ks.append(k)
            scores.append(score)
    except Exception as e:
        print(e)

    # Plot 1: Scores
    ax1.scatter(ks, scores, marker="o", linewidth=2, color="tab:blue")
    ax1.set_xlabel("K-nearest k")
    ax1.set_ylabel("Evaluation score")
    ax1.set_title("Evaluation Score")
    ax1.grid(True, alpha=0.3)

    # Global adjustments
    fig.suptitle("Experiment 3: K-nearest", fontsize=14)
    fig.tight_layout()
    
    # Save the plot if a path is desired
    plt.show()

if __name__ == "__main__":
    make_experiment_plot()