from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiments import conduct_experiment


def fit_attraction_weight(num_samples=21, plot_path="experiment1_attraction_weight.png"):
	"""Fit ATTRACTION_WEIGHT on a bounded grid in [0, 1] and plot the results."""
	attraction_weights = []
	scores = []
	best_weight = 0.0
	best_score = float("inf")

	for attraction_weight in np.linspace(0.0, 1.0, num_samples):
		score = conduct_experiment(ATTRACTION_WEIGHT=float(attraction_weight))
		print(f"ATTRACTION_WEIGHT={attraction_weight:.3f} -> score={score:.6f}")

		attraction_weights.append(float(attraction_weight))
		scores.append(float(score))

		if score < best_score:
			best_score = score
			best_weight = float(attraction_weight)

	# plot_path = Path(plot_path)
	fig, ax = plt.subplots(figsize=(8, 4.5))
	ax.plot(attraction_weights, scores, marker="o", linewidth=2)
	ax.scatter([best_weight], [best_score], color="crimson", zorder=3, label=f"best = {best_weight:.3f}")
	ax.set_xlabel("ATTRACTION_WEIGHT")
	ax.set_ylabel("Evaluation score")
	ax.set_title("Experiment 1: attraction_weight sweep")
	ax.grid(True, alpha=0.3)
	ax.legend()
	fig.tight_layout()
	# fig.savefig(plot_path, dpi=200, bbox_inches="tight")
	plt.close(fig)

	print()
	print(f"Best ATTRACTION_WEIGHT: {best_weight:.3f}")
	print(f"Best score: {best_score:.6f}")
	print(f"Saved plot to: {plot_path.resolve()}")
	return best_weight, best_score, plot_path


if __name__ == "__main__":
	fit_attraction_weight()