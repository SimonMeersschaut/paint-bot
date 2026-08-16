# Pigment

## Vocabulary

| Name | Explanation |
| --- | --- |
| target_pigment | The intended pigment to be used in the final painting. |
| robot_target_pigment | The pigment value selected or assigned by the robotic system. |
| observed_pigment | The observed amount of pigment, after the stroke was drawn. This value is only used to evaluate the accuracy of our pigment-model. |


## Pigment Model

The pigment model consists of a function that maps `target_pigment` values to `robot_target_pigment` values, and mechanic that turns `robot_target_pigment` values into instructions for our robot. That is, when we want very litle pigment on the brush, we could decide to load the brush very shortly after which we dip the brush back into the water again.

