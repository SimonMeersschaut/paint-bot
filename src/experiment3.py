import time
# from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiments import conduct_experiment
from stroke_generation import Hyperparameters
from stroke_generation import ColorMethod, PaletteColorsOnly, KNearest


def fit_attraction_weight(num_samples, plot_path="experiment1_attraction_weight.png"):
    """Fit ATTRACTION_WEIGHT on a bounded grid in [0, 1] and plot results and durations."""
    
    # score = conduct_experiment(COLOR_METHOD=None)
    # print("WITHOUT dynamic colors", score)

    ks = []
    scores = []

    for k in range(1, 20):
        score = conduct_experiment(COLOR_METHOD=KNearest(k))
        print("K-nearest", score)
        ks.append(k)
        scores.append(score)

    fig, ax1  = plt.subplots(1, 1, figsize=(14, 5))

    # Plot 1: Scores
    ax1.scatter(ks, scores, marker="o", linewidth=2, color="tab:blue")
    ax1.set_xlabel("K-nearest k")
    ax1.set_ylabel("Evaluation score")
    ax1.set_title("Evaluation Score")
    ax1.grid(True, alpha=0.3)

    # Global adjustments
    fig.suptitle("Experiment 1: K-nearest", fontsize=14)
    fig.tight_layout()
    
    # Save the plot if a path is desired
    # plt.savefig(plot_path)
    plt.show()

if __name__ == "__main__":
    fit_attraction_weight(20)