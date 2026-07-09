# Experiments

## Evaluation

All experiments were conducted with the following metric.
The pixels were converted to `HSV` values.
The pixel differences were weighted as follows:

$$ dif_{hue}^2 * weigth_0 + \\ dif_{saturation}^2 * weight_1 + \\ dif_{value}^2 * weight_2 $$.

At last, the mean is taken over these weighted squares.

## Experiments

| File | Description |
| :--- | :--- |
| [Experiment 1](experiment1.md) | Attraction weight |
| [Experiment 2](experiment2.md) | Kalman filter z-value |