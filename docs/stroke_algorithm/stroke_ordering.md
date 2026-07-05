# Stroke Ordering

!!! failure "The Crux of the Problem: Stroke Ordering"
    How do we optimally order strokes so that the execution happens naturally and efficient?

    As a human painter, we will naturallly draw strokes that are further away fist, and gradually move closer to a subject. For this, we will use a model that does monocular distance estimation.

    On top of that, we also deal with problems in our physical world. 
    When we want to change the paint color on our brush, we first have to clean 
    our brush. This takes quite some time.
    Thus, changing color should be kept to a minimum.

    Moreover, travel distance between two subsequent strokes should also be minimized for a faster execution time.

    Lastly, one should note that while drawing strokes the amount  of pigment on the brush decreases.
    Indeed, that is the reason why we refill the brush every, say, 20 strokes.
    Thus, brighter strokes should be placed later after a refill.


## Our Approach

Let's first note that there are many different ways to order the strokes, and that our approach is *not* the best solution.

![Overview](reordering_overview.png)

![Bucket Partitioning](bucket_partitioning.png)

![Bucket Ordering](bucket_ordering.png)



In conclusion, these are the metrics we optimized:

| Metric | Status |
| :--- | :--- |
| Minimal color change | ✅  |
| Dark to bright |  ✅ |
| Far to near | ❌ |
| Minimal travel distance |  ❌ |