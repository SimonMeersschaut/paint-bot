from random import *
import math
import argparse

from pigment import calculate_pigment, normalize_stroke_distribution
from PIL import Image, ImageDraw, ImageOps

from filters import *
from strokesort import *
import perlin
from util import *
from lines import Line

no_cv = False
export_path = "output/out.svg"
draw_contours = True
draw_hatch = True
show_bitmap = False
resolution = 1024
hatch_size = 16
contour_simplify = 2

try:
    import numpy as np
    import cv2
except:
    print("Cannot import numpy/openCV. Switching to NO_CV mode.")
    no_cv = True

def find_edges(IM):
    print("finding edges...")
    if no_cv:
        #appmask(IM,[F_Blur])
        appmask(IM,[F_SobelX,F_SobelY])
    else:
        im = np.array(IM) 
        im = cv2.GaussianBlur(im,(3,3),0)
        im = cv2.Canny(im,100,200)
        IM = Image.fromarray(im)
    return IM.point(lambda p: p > 128 and 255)  


def getdots(IM):
    print("getting contour points...")
    PX = IM.load()
    dots = []
    w,h = IM.size
    for y in range(h-1):
        row = []
        for x in range(1,w):
            if PX[x,y] == 255:
                if len(row) > 0:
                    if x-row[-1][0] == row[-1][-1]+1:
                        row[-1] = (row[-1][0],row[-1][-1]+1)
                    else:
                        row.append((x,0))
                else:
                    row.append((x,0))
        dots.append(row)
    return dots
    
def connectdots(dots):
    print("connecting contour points...")
    contours = []
    for y in range(len(dots)):
        for x,v in dots[y]:
            if v > -1:
                if y == 0:
                    contours.append([(x,y)])
                else:
                    closest = -1
                    cdist = 100
                    for x0,v0 in dots[y-1]:
                        if abs(x0-x) < cdist:
                            cdist = abs(x0-x)
                            closest = x0

                    if cdist > 3:
                        contours.append([(x,y)])
                    else:
                        found = 0
                        for i in range(len(contours)):
                            if contours[i][-1] == (closest,y-1):
                                contours[i].append((x,y,))
                                found = 1
                                break
                        if found == 0:
                            contours.append([(x,y)])
        for c in contours:
            if c[-1][1] < y-1 and len(c)<4:
                contours.remove(c)
    return contours


def getcontours(IM,sc=2):
    print("generating contours...")
    IM = find_edges(IM)
    IM1 = IM.copy()
    IM2 = IM.rotate(-90,expand=True).transpose(Image.FLIP_LEFT_RIGHT)
    dots1 = getdots(IM1)
    contours1 = connectdots(dots1)
    dots2 = getdots(IM2)
    contours2 = connectdots(dots2)

    for i in range(len(contours2)):
        contours2[i] = [(c[1],c[0]) for c in contours2[i]]    
    contours = contours1+contours2

    for i in range(len(contours)):
        for j in range(len(contours)):
            if len(contours[i]) > 0 and len(contours[j])>0:
                if distsum(contours[j][0],contours[i][-1]) < 8:
                    contours[i] = contours[i]+contours[j]
                    contours[j] = []

    for i in range(len(contours)):
        contours[i] = [contours[i][j] for j in range(0,len(contours[i]),8)]


    contours = [c for c in contours if len(c) > 1]

    for i in range(0,len(contours)):
        contours[i] = [(v[0]*sc,v[1]*sc) for v in contours[i]]

    for i in range(0,len(contours)):
        for j in range(0,len(contours[i])):
            contours[i][j] = int(contours[i][j][0]+10*perlin.noise(i*0.5,j*0.1,1)),int(contours[i][j][1]+10*perlin.noise(i*0.5,j*0.1,2))

    return contours


def hatch(IM,sc=16):
    print("hatching...")
    PX = IM.load()
    w,h = IM.size
    lg1 = []
    lg2 = []
    for x0 in range(w):
        for y0 in range(h):
            x = x0*sc
            y = y0*sc
            if PX[x0,y0] > 144:
                pass
                
            elif PX[x0,y0] > 64:
                lg1.append([(x,y+sc/4),(x+sc,y+sc/4)])
            elif PX[x0,y0] > 16:
                lg1.append([(x,y+sc/4),(x+sc,y+sc/4)])
                lg2.append([(x+sc,y),(x,y+sc)])

            else:
                lg1.append([(x,y+sc/4),(x+sc,y+sc/4)])
                lg1.append([(x,y+sc/2+sc/4),(x+sc,y+sc/2+sc/4)])
                lg2.append([(x+sc,y),(x,y+sc)])

    lines = [lg1,lg2]
    for k in range(0,len(lines)):
        for i in range(0,len(lines[k])):
            for j in range(0,len(lines[k])):
                if lines[k][i] != [] and lines[k][j] != []:
                    if lines[k][i][-1] == lines[k][j][0]:
                        lines[k][i] = lines[k][i]+lines[k][j][1:]
                        lines[k][j] = []
        lines[k] = [l for l in lines[k] if len(l) > 0]
    lines = lines[0]+lines[1]

    for i in range(0,len(lines)):
        for j in range(0,len(lines[i])):
            lines[i][j] = int(lines[i][j][0]+sc*perlin.noise(i*0.5,j*0.1,1)),int(lines[i][j][1]+sc*perlin.noise(i*0.5,j*0.1,2))-j
    return lines



def _as_line(stroke):
    if isinstance(stroke, Line):
        return stroke
    return Line.from_points(stroke)


def measure_stroke_contour_strength(image, stroke):
    if not stroke.positions or len(stroke.positions) < 2:
        return 0.0

    gray = image.convert('L') if image.mode != 'L' else image
    width, height = gray.size
    pixels = gray.load()

    samples = []
    for i in range(1, len(stroke.positions)):
        x0, y0 = map(int, stroke.positions[i - 1])
        x1, y1 = map(int, stroke.positions[i])
        dx = x1 - x0
        dy = y1 - y0
        if dx == 0 and dy == 0:
            continue

        length = max(1.0, math.hypot(dx, dy))
        stroke_dir = (dx / length, dy / length)

        local_strengths = []
        for offset_x in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                sample_x = max(1, min(width - 2, int(round((x0 + x1) / 2.0)) + offset_x))
                sample_y = max(1, min(height - 2, int(round((y0 + y1) / 2.0)) + offset_y))

                sx = (
                    -pixels[sample_x - 1, sample_y - 1] - 2 * pixels[sample_x - 1, sample_y] - pixels[sample_x - 1, sample_y + 1]
                    + pixels[sample_x + 1, sample_y - 1] + 2 * pixels[sample_x + 1, sample_y] + pixels[sample_x + 1, sample_y + 1]
                )
                sy = (
                    -pixels[sample_x - 1, sample_y - 1] - 2 * pixels[sample_x, sample_y - 1] - pixels[sample_x + 1, sample_y - 1]
                    + pixels[sample_x - 1, sample_y + 1] + 2 * pixels[sample_x, sample_y + 1] + pixels[sample_x + 1, sample_y + 1]
                )
                grad_mag = math.hypot(sx, sy)
                if grad_mag == 0:
                    continue

                edge_tangent = (-sy / grad_mag, sx / grad_mag)
                alignment = abs(stroke_dir[0] * edge_tangent[0] + stroke_dir[1] * edge_tangent[1])
                local_strengths.append(min(1.0, (grad_mag / 1020.0) * alignment))

        if local_strengths:
            samples.append(max(local_strengths))

    if not samples:
        return 0.0
    return max(0.0, min(1.0, sum(samples) / len(samples)))


def sketch(path):
    IM = None
    possible = [path,"images/"+path,"images/"+path+".jpg","images/"+path+".png","images/"+path+".tif"]
    for p in possible:
        try:
            IM = Image.open(p)
            break
        except FileNotFoundError:
            print("The Input File wasn't found. Check Path")
            exit(0)
            pass
    w,h = IM.size

    IM = IM.convert("L")
    IM=ImageOps.autocontrast(IM,10)

    raw_lines = []
    if draw_contours:
        raw_lines += getcontours(IM.resize((resolution//contour_simplify,resolution//contour_simplify*h//w)),contour_simplify)
    if draw_hatch:
        raw_lines += hatch(IM.resize((resolution//hatch_size,resolution//hatch_size*h//w)),hatch_size)

    lines = [_as_line(stroke) for stroke in raw_lines]
    for stroke in lines:
        avg_darkness = sum(IM.getpixel((int(p[0] / max(1, len(stroke.positions))), int(p[1]))) for p in stroke.positions[:min(10, len(stroke.positions))]) / max(1, min(10, len(stroke.positions))) / 255.0
        contour_strength = measure_stroke_contour_strength(IM, stroke)
        calculate_pigment(stroke, avg_darkness, contour_strength, image=IM)

    lines = sortlines(lines)
    normalize_stroke_distribution(lines)
    if show_bitmap:
        disp = Image.new("RGB",(resolution,resolution*h//w),(255,255,255))
        draw = ImageDraw.Draw(disp)
        for stroke in lines:
            draw.line(stroke.positions,(0,0,0),5)
        disp.show()

    f = open(export_path,'w')
    f.write(makesvg(lines))
    f.close()
    print(len(lines),"strokes.")
    print("done.")
    return lines


def makesvg(lines):
    print("generating svg file...")
    if not lines:
        return '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="0" height="0" viewBox="0 0 0 0"></svg>'

    strokes = [_as_line(line) for line in lines]
    all_points = [p for stroke in strokes for p in stroke.positions]
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_x = max(p[0] for p in all_points)
    max_y = max(p[1] for p in all_points)

    pad = 20
    width = max_x - min_x
    height = max_y - min_y
    svg_width = max(1, (width + pad * 2) * 0.5)
    svg_height = max(1, (height + pad * 2) * 0.5)

    out = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{0}" height="{1}" viewBox="0 0 {0} {1}">'.format(
        int(svg_width),
        int(svg_height),
    )

    for stroke in strokes:
        points = stroke.to_string(min_x, min_y, pad)
        color = f"rgba(0, 0, 0, {stroke.pigment})"
        out += '<polyline points="'+points+'" stroke="'+color+'" stroke-width="2" fill="none" />\n'
    out += '</svg>'
    return out



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert image to vectorized line drawing for plotters.')
    parser.add_argument('-i','--input',dest='input_path',
        default='lenna',action='store',nargs='?',type=str,
        help='Input path')

    parser.add_argument('-o','--output',dest='output_path',
        default=export_path,action='store',nargs='?',type=str,
        help='Output path.')

    parser.add_argument('-b','--show_bitmap',dest='show_bitmap',
        const = not show_bitmap,default= show_bitmap,action='store_const',
        help="Display bitmap preview.")

    parser.add_argument('-nc','--no_contour',dest='no_contour',
        const = draw_contours,default= not draw_contours,action='store_const',
        help="Don't draw contours.")
       
    parser.add_argument('-nh','--no_hatch',dest='no_hatch',
        const = draw_hatch,default= not draw_hatch,action='store_const',
        help='Disable hatching.')

    parser.add_argument('--no_cv',dest='no_cv',
        const = not no_cv,default= no_cv,action='store_const',
        help="Don't use openCV.")


    parser.add_argument('--hatch_size',dest='hatch_size',
        default=hatch_size,action='store',nargs='?',type=int,
        help='Patch size of hatches. eg. 8, 16, 32')
    parser.add_argument('--contour_simplify',dest='contour_simplify',
        default=contour_simplify,action='store',nargs='?',type=int,
        help='Level of contour simplification. eg. 1, 2, 3')

    args = parser.parse_args()
    
    export_path = args.output_path
    draw_hatch = not args.no_hatch
    draw_contours = not args.no_contour
    hatch_size = args.hatch_size
    contour_simplify = args.contour_simplify
    show_bitmap = args.show_bitmap
    no_cv = args.no_cv
    lines = sketch(args.input_path)

    import json
    filename = 'output'
    with open("output.json", 'w') as f:
        f.write('{\n\t"stage": 0,\n')
        f.write(f'\t"name": "{filename}",\n')
        f.write('\t"lines": [\n')
        for i, line in enumerate(lines):
            payload = _as_line(line).to_dict()
            line_str = json.dumps(payload)
            f.write("\t\t" + line_str)
            if i == len(lines) -1:
                f.write("\n")
            else:
                f.write(", \n")
        f.write("\t]\n")
        f.write("}")
