#!/usr/bin/env python3
"""Proof-of-concept: Render the Mova 600 Plus garden map as PNG.
Uses the saved mova_full_mapdata.json from test_mova_mapdata.py."""

import json, io
from PIL import Image, ImageDraw

# ============================================================
# Step 1: Load and reassemble chunked data
# ============================================================

def parse_chunked_data(data: dict, prefix: str) -> str:
    """Reassemble chunked data (PREFIX.0, PREFIX.1, ...) using PREFIX.info as length."""
    total_len = int(data.get(f"{prefix}.info", 0))
    if total_len == 0:
        return None
    chunks = {}
    for key, val in data.items():
        if key.startswith(f"{prefix}.") and key != f"{prefix}.info":
            idx = int(key.split(".")[1])
            chunks[idx] = str(val)
    full_str = "".join(chunks[i] for i in sorted(chunks.keys()))
    return full_str[:total_len]


with open("mova_full_mapdata.json") as f:
    raw_data = json.load(f)

map_str = parse_chunked_data(raw_data, "MAP")
path_str = parse_chunked_data(raw_data, "M_PATH")

print(f"MAP data: {len(map_str)} chars")
print(f"M_PATH data: {len(path_str)} chars" if path_str else "M_PATH: None")

# ============================================================
# Step 2: Parse map JSON
# ============================================================

maps_raw = json.loads(map_str)
# Each element may be a JSON string that needs a second parse
maps = []
for m in maps_raw:
    if isinstance(m, str):
        maps.append(json.loads(m))
    else:
        maps.append(m)
active_map = maps[0]  # Map1 is the active map
print(f"\nMap: {active_map['name']}, area={active_map['totalArea']}m²")
print(f"Boundary: {active_map['boundary']}")
print(f"Mowing areas: {len(active_map['mowingAreas']['value'])}")
print(f"Forbidden areas: {len(active_map['forbiddenAreas']['value'])}")
print(f"Contours: {len(active_map['contours']['value'])}")

# ============================================================
# Step 3: Parse mowing paths
# ============================================================

path_segments = []
if path_str:
    # M_PATH is a JSON array of [x,y] pairs with [32767,-32768] as pen-up separator
    path_data = json.loads(f"[{path_str}]")
    current_segment = []
    i = 0
    while i < len(path_data):
        val = path_data[i]
        if val is None:
            i += 1
            continue
        if isinstance(val, list):
            if len(val) < 2:
                i += 1
                continue
            x, y = val[0], val[1]
            if x == 32767 and y == -32768:
                if current_segment:
                    path_segments.append(current_segment)
                current_segment = []
            else:
                current_segment.append((x, y))
            i += 1
        else:
            # Flat pairs: x, y, x, y, ...
            if i + 1 < len(path_data) and isinstance(path_data[i+1], (int, float)):
                x, y = int(val), int(path_data[i+1])
                if x == 32767 and y == -32768:
                    if current_segment:
                        path_segments.append(current_segment)
                    current_segment = []
                else:
                    current_segment.append((x, y))
                i += 2
            else:
                i += 1
    if current_segment:
        path_segments.append(current_segment)
    print(f"Path segments: {len(path_segments)}")

# ============================================================
# Step 4: Render PNG
# ============================================================

WIDTH, HEIGHT = 800, 800
PADDING = 40

boundary = active_map["boundary"]
x_min, y_min = boundary["x1"], boundary["y1"]
x_max, y_max = boundary["x2"], boundary["y2"]
x_range = x_max - x_min
y_range = y_max - y_min

# Scale to fit image with padding
scale = min((WIDTH - 2*PADDING) / x_range, (HEIGHT - 2*PADDING) / y_range)

def to_screen(x, y):
    """Convert map coordinates (mm) to screen coordinates (pixels)."""
    sx = int((x - x_min) * scale + PADDING)
    sy = HEIGHT - int((y - y_min) * scale + PADDING)  # Y-flip
    return (sx, sy)

# Create image
img = Image.new("RGBA", (WIDTH, HEIGHT), (40, 40, 40, 255))  # Dark background
draw = ImageDraw.Draw(img)

# Draw contours (garden outline)
for contour_entry in active_map["contours"]["value"]:
    if isinstance(contour_entry, list) and len(contour_entry) >= 2:
        contour_id, contour_data = contour_entry[0], contour_entry[1]
        if isinstance(contour_data, dict) and "path" in contour_data:
            points = [to_screen(p["x"], p["y"]) for p in contour_data["path"]]
            if len(points) >= 3:
                draw.polygon(points, fill=(60, 120, 60, 255), outline=(80, 160, 80, 255))

# Draw mowing areas (lawn)
for area_entry in active_map["mowingAreas"]["value"]:
    if isinstance(area_entry, list) and len(area_entry) >= 2:
        area_id, area_data = area_entry[0], area_entry[1]
        if isinstance(area_data, dict) and "path" in area_data:
            points = [to_screen(p["x"], p["y"]) for p in area_data["path"]]
            if len(points) >= 3:
                draw.polygon(points, fill=(100, 180, 100, 255), outline=(120, 200, 120, 255))

# Draw forbidden areas (no-go zones) in red
for area_entry in active_map["forbiddenAreas"]["value"]:
    if isinstance(area_entry, list) and len(area_entry) >= 2:
        area_id, area_data = area_entry[0], area_entry[1]
        if isinstance(area_data, dict) and "path" in area_data:
            points = [to_screen(p["x"], p["y"]) for p in area_data["path"]]
            if len(points) >= 3:
                draw.polygon(points, fill=(200, 60, 60, 180), outline=(255, 80, 80, 255))

# Draw mowing paths
for segment in path_segments:
    if len(segment) >= 2:
        screen_points = [to_screen(x, y) for x, y in segment]
        draw.line(screen_points, fill=(255, 255, 100, 120), width=1)

# Draw charging station (origin point 0,0)
station = to_screen(0, 0)
draw.ellipse([station[0]-6, station[1]-6, station[0]+6, station[1]+6],
             fill=(0, 150, 255, 255), outline=(255, 255, 255, 255))

# Save
img.save("mova_map_rendered.png")
print(f"\n✓ Map rendered to mova_map_rendered.png ({WIDTH}x{HEIGHT})")

# Also save to raw bytes for camera entity test
buf = io.BytesIO()
img.save(buf, format="PNG")
print(f"  PNG size: {len(buf.getvalue())} bytes")
