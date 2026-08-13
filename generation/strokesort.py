from random import *
from PIL import Image, ImageDraw, ImageOps
from util import *
from lines import Line


def _as_line(stroke):
    if isinstance(stroke, Line):
        return stroke
    return Line.from_points(stroke)


def sortlines(lines):
    print("optimizing stroke sequence...")
    strokes = [_as_line(line) for line in lines]
    clines = strokes[:]
    slines = [clines.pop(0)]
    while clines != []:
        x, s, r = None, 1000000, False
        for stroke in clines:
            d = distsum(stroke.positions[0], slines[-1].positions[-1])
            dr = distsum(stroke.positions[-1], slines[-1].positions[-1])
            if d < s:
                x, s, r = stroke.copy_with_points(stroke.positions[:]), d, False
            if dr < s:
                x, s, r = stroke.copy_with_points(stroke.positions[:]), s, True

        clines.remove(next(stroke for stroke in clines if stroke.positions == x.positions))
        if r is True:
            x = x.copy_with_points(x.positions[::-1])
        slines.append(x)
    return slines

def visualize(lines):
    import turtle
    wn = turtle.Screen()
    t = turtle.Turtle()
    t.speed(0)
    t.pencolor('red')
    t.pd()
    for i in range(0,len(lines)):
        stroke = _as_line(lines[i])
        for p in stroke.positions:
            t.goto(p[0]*640/1024-320,-(p[1]*640/1024-320))
            t.pencolor('black')
        t.pencolor('red')
    turtle.mainloop()

if __name__=="__main__":
    import linedraw
    #linedraw.draw_hatch = False
    lines = linedraw.sketch("Lenna")
    #lines = sortlines(lines)
    visualize(lines)