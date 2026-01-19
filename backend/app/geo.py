import numpy as np
from shapely.geometry import Polygon, Point

def bd_bbox_polygon():
    return Polygon([(88.0, 20.5), (92.8, 20.5), (92.8, 26.8), (88.0, 26.8)])

def grid_points_within(poly: Polygon, step_deg: float = 0.12):
    minx, miny, maxx, maxy = poly.bounds
    xs = np.arange(minx, maxx + step_deg, step_deg)
    ys = np.arange(miny, maxy + step_deg, step_deg)
    pts = []
    for y in ys:
        for x in xs:
            p = Point(float(x), float(y))
            if poly.contains(p):
                pts.append((float(x), float(y)))
    return pts

def make_heat_values(points, year_value, seed=7):
    rng = np.random.default_rng(seed)
    cx, cy = 90.35, 23.8
    vals = []
    for lon, lat in points:
        d = ((lon - cx) ** 2 + (lat - cy) ** 2) ** 0.5
        spatial = np.exp(-(d ** 2) / 1.2)
        noise = rng.normal(0, 0.03)
        v = float(np.clip(year_value + 0.25 * (spatial - 0.4) + noise, -0.5, 0.5))
        vals.append(v)
    return vals
