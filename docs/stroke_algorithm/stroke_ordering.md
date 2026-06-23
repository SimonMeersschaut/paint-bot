# Stroke Ordering

!!! failure "The Crux of the Problem: Stroke Ordering"
    How do we optimally order strokes so that the execution happens naturally and efficiency?

    As a human painter, we will naturallly draw strokes that are further away fist, and gradually move closer to a subject. 

    Meanwhile our robot can only hold one brush at a time so if we want more detailed segments to be painted with a thinner brush we will have to switch. This switching mechanism will require human interaction. Thus, we need to avoid switching brushes as much as possible; ideally we only switch to each brush once.
