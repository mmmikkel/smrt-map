from lxml import etree
from svgpathtools import parse_path, Path
import numpy as np
import re

SVG_FILE = 'sg-mrt-map.svg'

# Helper: get the first geometric child position from a <g id="Group-XXX">
def get_station_pos(group_elem):
    for child in group_elem:
        if child.tag.endswith(('circle', 'ellipse', 'rect')):
            if child.tag.endswith('circle'):
                cx = child.get('cx')
                cy = child.get('cy')
                if cx is not None and cy is not None:
                    return float(cx), float(cy)
            elif child.tag.endswith('ellipse'):
                cx = child.get('cx')
                cy = child.get('cy')
                if cx is not None and cy is not None:
                    return float(cx), float(cy)
            elif child.tag.endswith('rect'):
                x = child.get('x')
                y = child.get('y')
                w = float(child.get('width', 0))
                h = float(child.get('height', 0))
                if x is not None and y is not None:
                    return float(x) + w/2, float(y) + h/2
                # Try transform attribute
                if 'transform' in child.attrib:
                    m = re.search(r'translate\(([^)]+)\)', child.attrib['transform'])
                    if m:
                        tx, ty = map(float, m.group(1).replace(',', ' ').split())
                        return tx + w/2, ty + h/2
    # If not found, try transform attribute on group
    if 'transform' in group_elem.attrib:
        m = re.search(r'translate\\(([^)]+)\\)', group_elem.attrib['transform'])
        if m:
            x, y = map(float, m.group(1).split())
            return x, y
    print(f"Warning: No geometric child or transform found in {group_elem.get('id')}")
    return None

# Parse SVG
tree = etree.parse(SVG_FILE)
root = tree.getroot()
SVG_NS = root.nsmap.get(None, '')
ns = {'svg': SVG_NS} if SVG_NS else {}

def find_station_group(station):
    return root.xpath(f'.//svg:g[@id="Station-{station}"]', namespaces=ns)

# Find Track_18 group
g_track = root.xpath('.//svg:g[@id="Track_18"]', namespaces=ns)[0]

for path_elem in g_track.xpath('./svg:path', namespaces=ns):
    path_id = path_elem.get('id')
    if not path_id or '-' not in path_id:
        continue
    from_station, to_station = path_id.split('-', 1)
    # Only debug for EW32-EW33 and EW33-EW32
    debug = path_id in ('EW32-EW33', 'EW33-EW32')
    # Get station positions
    from_groups = find_station_group(from_station)
    to_groups = find_station_group(to_station)
    if not from_groups or not to_groups:
        if debug:
            print(f"Could not find group for {from_station} or {to_station}")
        continue  # skip if station group not found
    from_pos = get_station_pos(from_groups[0])
    to_pos = get_station_pos(to_groups[0])
    if from_pos is None or to_pos is None:
        if debug:
            print(f"Could not extract position for {from_station} or {to_station}")
        continue
    # Parse path
    d = path_elem.get('d')
    path = parse_path(d)
    start = path.point(0)
    end = path.point(1)
    # Compare distances
    dist_start_from = np.linalg.norm([start.real - from_pos[0], start.imag - from_pos[1]])
    dist_end_from = np.linalg.norm([end.real - from_pos[0], end.imag - from_pos[1]])
    if debug:
        print(f"Path {path_id}:")
        print(f"  {from_station} pos: {from_pos}")
        print(f"  {to_station} pos: {to_pos}")
        print(f"  start: ({start.real}, {start.imag})")
        print(f"  end:   ({end.real}, {end.imag})")
        print(f"  dist_start_from: {dist_start_from}")
        print(f"  dist_end_from:   {dist_end_from}")
    if dist_start_from > dist_end_from:
        # Reverse path
        path = path.reversed()
        path_elem.set('d', path.d())
        if debug:
            print(f"  Path {path_id} reversed!")

# Write back
with open(SVG_FILE, 'wb') as f:
    tree.write(f, pretty_print=True, xml_declaration=True, encoding='utf-8')

print('Done: Track_18 paths checked and reversed if needed.') 