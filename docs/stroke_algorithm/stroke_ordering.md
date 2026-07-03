# Stroke Ordering

!!! failure "The Crux of the Problem: Stroke Ordering"
    How do we optimally order strokes so that the execution happens naturally and efficient?

    As a human painter, we will naturallly draw strokes that are further away fist, and gradually move closer to a subject. For this, we will use a model that does monocular distance estimation.

    On top of that, we also deal with problems in our physical world. 
    When we want to change the paint color on our brush, we first have to clean 
    our brush. This takes quite some time.
    Thus, changing color should be kept to a minimum.
