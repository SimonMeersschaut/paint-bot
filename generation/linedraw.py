from random import *
import math
import argparse

from pigment import calculate_pigment
from PIL import Image, ImageDraw, ImageOps
from visualisation import rotate_if_vertical

from filters import *
from stroke_ordering import sort_strokes
from strokesort import *
import perlin
from util import *
from datatypes import LoadBrush, StrokePath
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


def resolve_line_settings(density=1.0, hatch_size=hatch_size, contour_simplify=contour_simplify):
    if density is None or density <= 0:
        density = 1.0

    adjusted_hatch = max(4, int(round(hatch_size / density)))
    adjusted_contour = max(1, int(round(contour_simplify / density)))

    return {
        'density': density,
        'hatch_size': adjusted_hatch,
        'contour_simplify': adjusted_contour,
    }


def _stroke_length(points):
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def filter_short_lines(strokes, min_length_pixels=0):
    if min_length_pixels is None or min_length_pixels <= 0:
        return list(strokes)

    filtered = []
    for stroke in strokes:
        if stroke is None:
            continue
        if isinstance(stroke, LoadBrush):
            filtered.append(stroke)
            continue
        if isinstance(stroke, Line):
            if _stroke_length(stroke.positions) >= min_length_pixels:
                filtered.append(stroke)
        else:
            line = _as_line(stroke)
            if line is not None and _stroke_length(line.positions) >= min_length_pixels:
                filtered.append(line)
    return filtered


def _as_line(stroke):
    if isinstance(stroke, LoadBrush):
        return None
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


def _resize_preserve_short_edge(img, target_short_edge):
    w, h = img.size
    target = max(1, int(target_short_edge))

    # Keep sampling density consistent across portrait/landscape orientations.
    if w <= h:
        new_w = target
        new_h = max(1, int(round((h / w) * target)))
    else:
        new_h = target
        new_w = max(1, int(round((w / h) * target)))

    return img.resize((new_w, new_h))


def _normalize_depth(values):
    if not values:
        return []
    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return [0.0 for _ in values]
    return [(value - minimum) / (maximum - minimum) for value in values]


def estimate_depth_map(image):
    """Build a cheap mono-depth map from local contrast and edge structure.

    Nearer objects have stronger local contrast and sharper edges, so their
    estimated depth is higher. Smooth low-contrast regions are treated as more
    distant background.
    """
    gray = image.convert('L') if image.mode != 'L' else image
    width, height = gray.size

    if no_cv:
        pixels = gray.load()
        depth_values = []
        for y in range(height):
            for x in range(width):
                center = pixels[x, y]
                neighbors = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx = max(0, min(width - 1, x + dx))
                        ny = max(0, min(height - 1, y + dy))
                        if nx == x and ny == y:
                            continue
                        neighbors.append(pixels[nx, ny])
                if not neighbors:
                    contrast = 0.0
                else:
                    contrast = sum(abs(center - n) for n in neighbors) / len(neighbors)
                edge = contrast / 255.0
                depth_values.append(edge)
        min_value = min(depth_values) if depth_values else 0.0
        max_value = max(depth_values) if depth_values else 0.0
        if max_value == min_value:
            normalized = [0.0 for _ in depth_values]
        else:
            normalized = [(value - min_value) / (max_value - min_value) for value in depth_values]

        depth_image = Image.new('L', (width, height))
        depth_image.putdata([int(round(value * 255.0)) for value in normalized])
        return depth_image

    arr = np.asarray(gray, dtype=np.float32)
    blur = cv2.GaussianBlur(arr, (9, 9), 0)
    grad_x = cv2.Sobel(blur, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(blur, cv2.CV_32F, 0, 1, ksize=3)
    edge_energy = cv2.magnitude(grad_x, grad_y)
    local_contrast = np.abs(arr - blur)
    depth_map = (edge_energy * 0.7 + local_contrast * 0.3)
    depth_map = depth_map.astype(np.float32)
    min_depth = float(np.min(depth_map))
    max_depth = float(np.max(depth_map))
    if max_depth == min_depth:
        depth_map = np.zeros_like(depth_map, dtype=np.float32)
    else:
        depth_map = (depth_map - min_depth) / (max_depth - min_depth)
    return Image.fromarray(np.uint8(np.clip(depth_map, 0.0, 1.0) * 255.0)).convert('L')


def _detect_background_stroke(depth_map, stroke, depth_threshold=0.40):
    if stroke is None or not getattr(stroke, 'positions', None):
        return False

    threshold = max(0.0, min(1.0, float(depth_threshold)))

    values = []
    sample_count = min(len(stroke.positions), 16)
    for x, y in stroke.positions[:sample_count]:
        px = max(0, min(depth_map.size[0] - 1, int(round(x))))
        py = max(0, min(depth_map.size[1] - 1, int(round(y))))
        values.append(depth_map.getpixel((px, py)) / 255.0)

    if not values:
        return False

    avg_depth = sum(values) / len(values)
    return avg_depth < threshold


def _rotate_strokes_90cw(strokes):
    drawable = [stroke for stroke in strokes if stroke is not None and not isinstance(stroke, LoadBrush) and stroke.positions]
    if not drawable:
        return strokes

    all_points = [p for stroke in drawable for p in stroke.positions]
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_x = max(p[0] for p in all_points)
    max_y = max(p[1] for p in all_points)

    rotated = []
    x_span = max_x - min_x
    y_span = max_y - min_y
    for stroke in strokes:
        if stroke is None or isinstance(stroke, LoadBrush):
            rotated.append(stroke)
            continue

        new_points = []
        for x, y in stroke.positions:
            x_rel = x - min_x
            y_rel = y - min_y
            new_x = (y_span - y_rel) + min_x
            new_y = x_rel + min_y
            new_points.append((new_x, new_y))
        rotated.append(stroke.copy_with_points(new_points))

    return rotated


def sketch(path, density=1.0, min_line_length=0, depth_threshold=0.40):
    img = None
    possible = [path,"images/"+path,"images/"+path+".jpg","images/"+path+".png","images/"+path+".tif"]
    for p in possible:
        try:
            img = Image.open(p)
            break
        except FileNotFoundError:
            continue

    if img is None:
        print("The Input File wasn't found. Check Path")
        exit(0)

    settings = resolve_line_settings(density=density, hatch_size=hatch_size, contour_simplify=contour_simplify)
    effective_hatch_size = settings['hatch_size']
    effective_contour_simplify = settings['contour_simplify']

    # Respect EXIF orientation before any portrait/landscape logic.
    # img = ImageOps.exif_transpose(img)
    # should_rotate_output = img.height > img.width
    # w, h = img.size

    img = img.convert("L")
    img=ImageOps.autocontrast(img,10)
    depth_map = estimate_depth_map(img)

    raw_lines = []
    if draw_contours:
        contour_img = _resize_preserve_short_edge(img, resolution // effective_contour_simplify)
        raw_lines += getcontours(contour_img, effective_contour_simplify)
    if draw_hatch:
        hatch_img = _resize_preserve_short_edge(img, resolution // effective_hatch_size)
        raw_lines += hatch(hatch_img, effective_hatch_size)

    lines = [_as_line(stroke) for stroke in raw_lines]
    lines = [line for line in lines if line is not None]
    lines = filter_short_lines(lines, min_line_length)
    for stroke in lines:
        avg_darkness = sum(img.getpixel((int(p[0] / max(1, len(stroke.positions))), int(p[1]))) for p in stroke.positions[:min(10, len(stroke.positions))]) / max(1, min(10, len(stroke.positions))) / 255.0
        contour_strength = measure_stroke_contour_strength(img, stroke)
        calculate_pigment(stroke, avg_darkness, contour_strength, image=img)
        stroke.background = _detect_background_stroke(depth_map, stroke, depth_threshold=depth_threshold)
        stroke.brushDiameter = 12 if stroke.background else 4

    lines = sort_strokes(lines)
    # if should_rotate_output:
    #     lines = _rotate_strokes_90cw(lines)

    if show_bitmap:
        disp_size = _resize_preserve_short_edge(img, resolution).size
        disp = Image.new("RGB", disp_size, (255,255,255))
        draw = ImageDraw.Draw(disp)
        for stroke in lines:
            if isinstance(stroke, LoadBrush):
                continue
            draw.line(stroke.positions,(0,0,0),5)
        disp.show()

    strokes = [line for line in (_as_line(line) for line in lines) if line is not None]
    all_points = [p for stroke in strokes for p in stroke.positions]
    
    min_x = min(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_x = max(p[0] for p in all_points)
    max_y = max(p[1] for p in all_points)

    width = max_x - min_x
    height = max_y - min_y

    f = open(export_path,'w')
    f.write(makesvg(strokes, width, height, min_x=min_x, min_y=min_y))
    f.close()
    print(len(lines),"strokes.")
    print("done.")

    return lines, max_x, max_y

def makesvg(strokes, width=None, height=None, min_x=None, min_y=None):
    STROKE_WIDTH = 10
    print("generating svg file...")
    if not strokes:
        return '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="0" height="0" viewBox="0 0 0 0"></svg>'

    if min_x is None or min_y is None or width is None or height is None:
        all_points = [point for stroke in strokes for point in getattr(stroke, 'positions', [])]
        if not all_points:
            return '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="0" height="0" viewBox="0 0 0 0"></svg>'
        if min_x is None:
            min_x = min(point[0] for point in all_points)
        if min_y is None:
            min_y = min(point[1] for point in all_points)
        if width is None:
            width = max(point[0] for point in all_points) - min_x
        if height is None:
            height = max(point[1] for point in all_points) - min_y

    pad = 20
    svg_width = max(1, (width + pad * 2) * 0.5)
    svg_height = max(1, (height + pad * 2) * 0.5)

    out = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{0}" height="{1}" viewBox="0 0 {0} {1}">'.format(
        int(svg_width),
        int(svg_height),
    )

    for stroke in strokes:
        if isinstance(stroke, LoadBrush):
            continue

        stroke_width = getattr(stroke, 'brushDiameter', STROKE_WIDTH)
        if hasattr(stroke, 'background') and stroke.background:
            stroke_width = max(stroke_width, 12)

        if hasattr(stroke, 'to_string'):
            points = stroke.to_string(min_x, min_y, pad)
            color = f"rgba(0, 0, 0, {getattr(stroke, 'pigment', 0.0)})"
            out += '<polyline points="'+points+'" stroke="'+color+f'" stroke-width="{stroke_width}" fill="none" />\n'
        else:
            points = stroke
            out += '<polyline points="'+','.join(f"{x},{y}" for x, y in points)+f'" stroke="rgba(0, 0, 0, 1)" stroke-width="{stroke_width}" fill="none" />\n'
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
    parser.add_argument('--density',dest='density',
        default=1.0,action='store',nargs='?',type=float,
        help='Line density multiplier. Values above 1.0 create more lines; values below 1.0 reduce them.')
    parser.add_argument('--min_line_length',dest='min_line_length',
        default=0,action='store',nargs='?',type=float,
        help='Remove any stroke shorter than this many pixels.')
    parser.add_argument('--depth_threshold',dest='depth_threshold',
        default=0.40,action='store',nargs='?',type=float,
        help='Depth cutoff used to classify background strokes. Lower values make more of the image background; higher values make it stricter.')

    args = parser.parse_args()
    
    export_path = args.output_path
    draw_hatch = not args.no_hatch
    draw_contours = not args.no_contour
    hatch_size = args.hatch_size
    contour_simplify = args.contour_simplify
    show_bitmap = args.show_bitmap
    no_cv = args.no_cv
    lines, max_x, max_y = sketch(
        args.input_path,
        density=args.density,
        min_line_length=args.min_line_length,
        depth_threshold=args.depth_threshold,
    )

    import json
    filename = 'output'
    with open("output.json", 'w') as f:
        f.write('{\n\t"stage": 0,\n')
        f.write(f'\t"name": "{filename}",\n')
        f.write(f'\t"image_size": [{max_x}, {max_y}],\n')
        f.write('\t"strokes": [\n')
        for i, line in enumerate(lines):
            if isinstance(line, LoadBrush):
                payload = {
                    "type": "LoadBrush",
                    "color": list(line.color),
                    "pigment": round(float(line.pigment), 4),
                    "deep_clean": line.deep_clean,
                }
            else:
                payload = _as_line(line).to_dict()
            line_str = json.dumps(payload)
            f.write("\t\t" + line_str)
            if i == len(lines) -1:
                f.write("\n")
            else:
                f.write(", \n")
        f.write("\t]\n")
        f.write("}")
