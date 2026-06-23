# Stroke Expanding

This document details the mathematical framework used to dynamically expand a robotic painting toolpath stroke from a given starting position $(x_0, y_0)$, as implemented in `generate_strokes_for_layer`.

---

## 1. Core Vector Expansion Framework

Once a stroke seed position is established, the path expands iteratively. At each step $k$, the next position is determined using the current position and a unified, normalized direction vector $\mathbf{d}_k = (dx, dy)$:

$$\begin{aligned}
x_{k+1} &= x_k + dx \cdot \Delta s \\
y_{k+1} &= y_k + dy \cdot \Delta s
\end{aligned}$$

Where:
* $(x_k, y_k)$ represents the current continuous coordinate.
* $\Delta s$ is the step size constant (`stroke_generation_supervisor.gradient_step_size`).
* $\mathbf{d}_k$ is a unit vector ($||\mathbf{d}_k|| = 1$) computed by blending **gradient-orthogonal guidance** and an **unpainted area attraction force**.

---

## 2. Gradient-Orthogonal Guidance (Flow Tracking)

To ensure the stroke mimics artistic behavior by flowing *along* image contours rather than cutting across them, the algorithm computes a vector orthogonal to the image gradient $\nabla I = (g_x, g_y)$.

### Vector Orthogonality
The image gradient points in the direction of the sharpest intensity change. The vector perpendicular to this gradient is obtained via a 90-degree rotation:

$$\mathbf{v}_{\text{grad}} = (-g_y, g_x)$$

### Direction Normalization and Consistency
If the vector magnitude $M = \sqrt{(-g_y)^2 + g_x^2}$ is non-zero, it is converted to a unit vector:

$$\mathbf{\hat{v}}_{\text{grad}} = \left( \frac{-g_y}{M}, \frac{g_x}{M} \right)$$

To prevent the path from making abrupt 180-degree U-turns between steps, the dot product between the new vector and the previous step's direction vector $\mathbf{d}_{k-1}$ is evaluated. If it opposes the current momentum, the direction is flipped:

$$\mathbf{\hat{v}}_{\text{grad}} = 
\begin{cases} 
-\mathbf{\hat{v}}_{\text{grad}}, & \text{if } \mathbf{\hat{v}}_{\text{grad}} \cdot \mathbf{d}_{k-1} < 0 \\ 
\mathbf{\hat{v}}_{\text{grad}}, & \text{otherwise} 
\end{cases}$$

---

## 3. Unpainted Region Attraction Force

To maximize superpixel area coverage and fill bare spots efficiently, an expansion "pull" vector towards local unpainted regions is calculated within a local neighborhood defined by an attraction radius $R$ (`ATTRACTION_RADIUS`).

### Center of Mass via Inverse Distance Weighting (IDW)
Let $U$ be the set of relative offsets $(\Delta x_i, \Delta y_i)$ corresponding to unpainted pixels within the bounding box $[x_k - R, x_k + R] \times [y_k - R, y_k + R]$. 

For each unpainted pixel $i \in U$, its squared Euclidean distance to the brush tip is:

$$d_i^2 = (\Delta x_i)^2 + (\Delta y_i)^2$$

To give closer pixels a stronger pull over distant ones, the algorithm maps an inverse distance weight (safeguarding the brush tip center to avoid division-by-zero):

$$w_i = \frac{1}{\max(1.0, d_i^2)}$$

The total attraction pull vector $\mathbf{v}_{\text{pull}} = (P_x, P_y)$ acts as a localized center of mass:

$$P_x = \sum_{i \in U} \Delta x_i \cdot w_i, \quad P_y = \sum_{i \in U} \Delta y_i \cdot w_i$$

If $||\mathbf{v}_{\text{pull}}|| > 0$, it is normalized into a unit vector $\mathbf{\hat{v}}_{\text{pull}}$.

---

## 4. Vector Blending and Final Normalization

The final direction vector $\mathbf{d}_k$ is a linear combination of the structural stroke path vector and the unpainted coverage attraction vector, modulated by the attraction weight $w_a$ (`ATTRACTION_WEIGHT`):

$$\mathbf{v}_{\text{final}} = \mathbf{\hat{v}}_{\text{grad}} + w_a \cdot \mathbf{\hat{v}}_{\text{pull}}$$

Because the addition of two unit vectors does not scale to unity, the blended vector is normalized a final time to produce the directional step components:

$$\mathbf{d}_k = \frac{\mathbf{v}_{\text{final}}}{||\mathbf{v}_{\text{final}}||} = (dx, dy)$$

---

## 5. Early Termination Conditions

The loop stops expanding the stroke sequence if any of the following boundaries are crossed:

1. **Length Limit:** Loop iterations hit `max_stroke_list_length`.

2. **Flat Gradient Fallback Failure:** If $M = 0$ and there is no prior historical direction, expansion falls back to a random coordinate shift. If it still fails to exit the current pixel matrix, a flat gradient event is triggered and expansion halts.

3. **Color Deviation Threshold:** If the continuous Euclidean color distance between the initial seed color $C_{\text{seed}}$ and the current canvas pixel canvas color $C_{k+1}$ surpasses an acceptable threshold while satisfying minimum length rules:

$$\|C_{k+1} - C_{\text{seed}}\|_2 > 120$$