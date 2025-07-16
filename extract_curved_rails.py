from lxml import etree
from svgpathtools import parse_path, Path, Line, CubicBezier, QuadraticBezier
import numpy as np

INPUT_SVG = 'SMRT-Map.svg'
OUTPUT_SVG = 'SMRT-Map-curved-rails.svg'
STROKE_WIDTH = 3
OFFSET = 2

# Helper: sample points and normals along a segment
def sample_points_and_normals(seg, n=50):
    ts = np.linspace(0, 1, n)
    points = np.array([seg.point(t) for t in ts])
    # Derivative for tangent
    tangents = np.array([seg.derivative(t) for t in ts])
    # Normal: rotate tangent by 90deg (complex)
    normals = np.array([-1j * t / abs(t) if abs(t) > 0 else 0 for t in tangents])
    return points, normals

# Helper: offset a segment (line or curve) by offset (approximate for curves)
def offset_segment(seg, offset, n=50):
    points, normals = sample_points_and_normals(seg, n)
    offset_points = points + normals * offset
    # For lines, just return a new Line
    if isinstance(seg, Line):
        return Line(offset_points[0], offset_points[-1])
    # For curves, fit a new CubicBezier through sampled points (approximate)
    # Use first, 1/3, 2/3, last as control points
    if len(offset_points) >= 4:
        return CubicBezier(offset_points[0], offset_points[len(offset_points)//3], offset_points[2*len(offset_points)//3], offset_points[-1])
    else:
        return Line(offset_points[0], offset_points[-1])

# Parse SVG
tree = etree.parse(INPUT_SVG)
root = tree.getroot()
SVG_NS = root.nsmap.get(None, '')
ns = {'svg': SVG_NS} if SVG_NS else {}

for g in root.xpath('.//svg:g[starts-with(@id, "Track")]', namespaces=ns):
    for path_elem in g.xpath('./svg:path', namespaces=ns):
        d = path_elem.get('d')
        if not d:
            continue
        path = parse_path(d)
        if not (abs(path.start - path.end) < 1e-6):
            continue  # Only process closed paths
        # Identify the two longest, most parallel segments
        segs = list(path)
        if len(segs) != 4:
            continue  # Only handle 4-segment shapes
        # Compute lengths and directions
        lengths = [seg.length() for seg in segs]
        directions = [np.angle(seg.end - seg.start) if isinstance(seg, Line) else np.angle(seg.point(1) - seg.point(0)) for seg in segs]
        # Find two longest, most parallel
        pairs = [(i, j) for i in range(4) for j in range(i+1, 4)]
        best = None
        best_score = -np.inf
        for i, j in pairs:
            # Score: sum of lengths + parallelism
            parallel = np.cos(directions[i] - directions[j])
            score = lengths[i] + lengths[j] + 10 * abs(parallel)
            if score > best_score:
                best = (i, j)
                best_score = score
        if not best:
            continue
        i, j = best
        # Offset both rails inward
        new_paths = []
        for idx in [i, j]:
            seg = segs[idx]
            new_seg = offset_segment(seg, OFFSET)
            new_paths.append(Path(new_seg))
        # Style
        attribs = {k: v for k, v in path_elem.attrib.items() if k != 'd'}
        stroke = attribs.get('stroke')
        fill = attribs.get('fill')
        if not stroke:
            if fill and fill.lower() != 'none':
                attribs['stroke'] = fill
            else:
                attribs['stroke'] = '#000'
        attribs['stroke-width'] = str(STROKE_WIDTH)
        attribs['fill'] = 'none'
        # Remove old path, add new rails
        parent = path_elem.getparent()
        parent.remove(path_elem)
        for rail_path in new_paths:
            new_elem = etree.Element('path', d=rail_path.d(), **attribs)
            parent.append(new_elem)

with open(OUTPUT_SVG, 'wb') as f:
    tree.write(f, pretty_print=True, xml_declaration=True, encoding='utf-8')

print(f"Done. Output written to {OUTPUT_SVG}") 