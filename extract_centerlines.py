import sys
from lxml import etree
from svgpathtools import parse_path, Path, Line
import numpy as np

INPUT_SVG = 'SMRT-Map.svg'
OUTPUT_SVG = 'SMRT-Map-centerlines.svg'

# Helper: sample points along a path
def sample_points(path, n=100):
    return np.array([path.point(t) for t in np.linspace(0, 1, n)])

# Helper: principal axis (PCA)
def principal_axis(points):
    mean = np.mean(points, axis=0)
    centered = points - mean
    u, s, vh = np.linalg.svd(centered, full_matrices=False)
    direction = vh[0]
    projections = centered @ direction
    min_proj, max_proj = projections.min(), projections.max()
    p1 = mean + min_proj * direction
    p2 = mean + max_proj * direction
    return p1, p2

# Parse SVG
tree = etree.parse(INPUT_SVG)
root = tree.getroot()
SVG_NS = root.nsmap.get(None, '')
ns = {'svg': SVG_NS} if SVG_NS else {}

def is_closed_path(path):
    # Only check if start and end points are nearly equal
    return abs(path.start - path.end) < 1e-6

for g in root.xpath('.//svg:g[starts-with(@id, "Track")]', namespaces=ns):
    for path_elem in g.xpath('./svg:path', namespaces=ns):
        d = path_elem.get('d')
        if not d:
            raise ValueError(f"Path element missing 'd' attribute in group {g.get('id')}")
        path = parse_path(d)
        if not is_closed_path(path):
            continue  # Only process closed paths
        # Sample points
        points = sample_points(path, n=200)
        points_2d = np.column_stack((points.real, points.imag))
        # Find principal axis
        try:
            p1, p2 = principal_axis(points_2d)
        except Exception as e:
            raise RuntimeError(f"Failed PCA for path in group {g.get('id')}: {e}")
        # Create new open path (straight line)
        new_path = Path(Line(complex(*p1), complex(*p2)))
        new_d = new_path.d()
        # Copy style, but ensure stroke and stroke-width are set
        attribs = {k: v for k, v in path_elem.attrib.items() if k != 'd'}
        stroke = attribs.get('stroke')
        fill = attribs.get('fill')
        if not stroke:
            if fill and fill.lower() != 'none':
                attribs['stroke'] = fill
            else:
                attribs['stroke'] = '#000'
        if 'stroke-width' not in attribs:
            attribs['stroke-width'] = '4'
        # Remove old path, add new one
        parent = path_elem.getparent()
        parent.remove(path_elem)
        new_elem = etree.Element('path', d=new_d, **attribs)
        parent.append(new_elem)

# Write output
with open(OUTPUT_SVG, 'wb') as f:
    tree.write(f, pretty_print=True, xml_declaration=True, encoding='utf-8')

print(f"Done. Output written to {OUTPUT_SVG}") 