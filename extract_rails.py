from lxml import etree
from svgpathtools import parse_path, Path, Line, CubicBezier, QuadraticBezier
import numpy as np

INPUT_SVG = 'SMRT-Map.svg'
OUTPUT_SVG = 'SMRT-Map-rails.svg'
STROKE_WIDTH = 2
OFFSET = 1  # Move rails inward by 1 unit

# Helper: sample points along a path
def sample_points(path, n=200):
    return np.array([path.point(t) for t in np.linspace(0, 1, n)])

# Helper: find corners by maximizing distance between points
# For 4-corner shapes, this will approximate the corners
# Returns indices of corners in the sampled points array
def find_corners(points):
    # Use Ramer-Douglas-Peucker to find corners
    from scipy.spatial.distance import cdist
    n = len(points)
    dists = cdist(points, points)
    # Find the two most distant points (long axis)
    i1, i2 = np.unravel_index(np.argmax(dists), dists.shape)
    # Find the two points most distant from the line (i1, i2)
    def point_line_dist(pt, a, b):
        return np.abs(np.cross(b-a, a-pt)) / np.linalg.norm(b-a)
    d_to_line = np.array([point_line_dist(p, points[i1], points[i2]) for p in points])
    i3 = np.argmax(d_to_line)
    # The fourth corner is opposite i3
    i4 = (i3 + n//2) % n
    # Sort corners in order
    idxs = np.array([i1, i3, i2, i4])
    idxs = np.sort(idxs)
    return idxs

# Helper: offset a line inward by OFFSET
# For curves, this is an approximation

def offset_segment(p0, p1, offset):
    # Offset a straight line segment inward by offset
    v = p1 - p0
    n = np.array([-v.imag, v.real])
    n = n / np.linalg.norm(n) * offset
    return p0 + n[0] + 1j*n[1], p1 + n[0] + 1j*n[1]

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
        # Sample points
        points = sample_points(path, n=400)
        # Find corners
        try:
            corner_idxs = find_corners(points)
        except Exception:
            continue  # Skip if can't find corners
        corners = points[corner_idxs]
        # Identify rails: the two longest sides
        rails = []
        for i in range(4):
            p0, p1 = corners[i], corners[(i+1)%4]
            rails.append((np.abs(p1-p0), i, p0, p1))
        rails = sorted(rails, reverse=True)[:2]  # Two longest
        # Offset rails inward
        new_paths = []
        for _, i, p0, p1 in rails:
            p0_off, p1_off = offset_segment(p0, p1, OFFSET)
            new_paths.append(Path(Line(p0_off, p1_off)))
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