"""Thin marking template: centre window over the door gap, 4 pencil holes for the screws.

Hole positions come from latch.py (pivot/post spacing D, post drop SLOT_CY, SCREW_PITCH),
centred on the gap: pivot on the left door, post on the right door.
"""
import numpy as np, manifold3d as m3, trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import latch

P = latch.P
T, RAISE = 0.6, 0.4                     # sheet thickness, raised marks
HOLE = 2.0                              # pencil / awl hole
X = P["D"] / 2                          # pivot at -X, post at +X (gap centre = 0)
s = P["SCREW_PITCH"]
holes = {1: (-X, s), 2: (-X, 0.0), 3: (X, P["SLOT_CY"] - s), 4: (X, P["SLOT_CY"])}
W, Y0, Y1 = 2 * (X + 18), -42.0, 38.0   # sheet extents

def rrect(x0, y0, x1, y1, r):
    cs = m3.CrossSection.square((x1 - x0 - 2 * r, y1 - y0 - 2 * r)).translate((x0 + r, y0 + r))
    return cs.offset(r, m3.JoinType.Round, circular_segments=48)

def circle(x, y, d):
    return m3.CrossSection.circle(d / 2, 48).translate((x, y))

def stadium_outline(x, ya, yb, w, line=0.8):
    outer = m3.CrossSection.square((0.001, abs(yb - ya))).translate((x, min(ya, yb))).offset(w / 2, m3.JoinType.Round, circular_segments=48)
    return outer - outer.offset(-line, m3.JoinType.Round, circular_segments=48)

def text(st, x, y, size, center=True):
    tp = TextPath((0, 0), st, size=size, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polys = [p for p in tp.to_polygons() if len(p) > 2]
    cs = m3.CrossSection([[tuple(v) for v in p] for p in polys], m3.FillRule.EvenOdd)
    (bx0, by0), (bx1, by1) = cs.bounds()[:2], cs.bounds()[2:]
    dx = -(bx0 + bx1) / 2 if center else 0
    return cs.translate((x + dx, y - (by0 + by1) / 2))

def stadium(x, ya, yb, w):
    return m3.CrossSection.square((0.001, abs(yb - ya))).translate((x, min(ya, yb))).offset(w / 2, m3.JoinType.Round, circular_segments=48)

PW = P["PLATE_W"]
yk = P["SLOT_CY"]                                   # keeper post height
foot_l = stadium(-X, 0, s, PW)                     # base plate footprint (left door)
foot_r = stadium(X, yk, yk - s, PW)                # keeper footprint (right door)
BAR_W = 6.0
bars = (m3.CrossSection.square((2 * X, BAR_W)).translate((-X, 5 - BAR_W / 2))
        + m3.CrossSection.square((2 * X, BAR_W)).translate((-X, -9 - BAR_W / 2)))
sheet = foot_l + foot_r + bars
for yy, sgn in ((5 + BAR_W / 2, 1), (-9 - BAR_W / 2, -1)):     # gap pointers: V notches at x=0
    sheet -= m3.CrossSection([[(-2.2, yy + sgn * 0.01), (2.2, yy + sgn * 0.01), (0, yy - sgn * 3.2)]], m3.FillRule.EvenOdd)
for k, (x, y) in holes.items():
    sheet -= circle(x, y, HOLE)
body = m3.Manifold.extrude(sheet, T)

marks = m3.CrossSection()
for k, (x, y) in holes.items():
    marks += circle(x, y, HOLE + 3.2) - circle(x, y, HOLE + 1.4)           # ring round each hole
    marks += text(str(k), x + (-7.5 if x < 0 else 7.5), y, 5.0)
marks += m3.CrossSection([[(-X - 6, s + 6), (-X - 2, s + 6), (-X - 4, s + 11)]], m3.FillRule.EvenOdd).offset(0.5, m3.JoinType.Miter)
marks += text("L", -X + 6, s + 7.5, 4.5)
marks += text("R", X, yk - s - 9.5, 4.5)
assert (marks - sheet).area() < 0.05, "raised marks hang off the sheet: %.2f mm2" % (marks - sheet).area()
body += m3.Manifold.extrude(marks, RAISE).translate((0, 0, T))
for k, (x, y) in holes.items():
    body -= m3.Manifold.cylinder(5, HOLE / 2, HOLE / 2, 48).translate((x, y, -1))
W, Y0, Y1 = 2 * X + PW + 6, yk - s - PW / 2 - 3, s + PW / 2 + 3
mesh = body.to_mesh()
tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
assert tm.is_watertight
tm.export("stl/template.stl")
print("template", (tm.bounds[1] - tm.bounds[0]).round(1), "holes", {k: (round(x, 1), round(y, 1)) for k, (x, y) in holes.items()},
      "pivot-post", round(np.hypot(2 * X, P["SLOT_CY"]), 2), "D", P["D"])

# preview from the actual mesh: sheet layer and raised-mark layer
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.path import Path; from matplotlib.patches import PathPatch
fig, ax = plt.subplots(figsize=(8, 6.4), dpi=110)
from shapely.geometry import Polygon as SPoly
for z, col in ((0.3, "#e9e2d0"), (T + 0.2, "#4a6fa5")):
    shape = None
    for e in tm.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).discrete:
        p = SPoly(e[:, :2]).buffer(0)
        shape = p if shape is None else shape.symmetric_difference(p)   # even-odd
    for poly in getattr(shape, "geoms", [shape]):
        verts, codes = [], []
        for ring in [poly.exterior] + list(poly.interiors):
            c = np.asarray(ring.coords)[:, :2]
            verts += list(c); codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=col, ec="#888" if z < 0.5 else "none", lw=0.5))
ax.set_xlim(-W / 2 - 3, W / 2 + 3); ax.set_ylim(Y0 - 3, Y1 + 3)
ax.set_aspect("equal"); ax.axis("off"); ax.set_title("Marking template, front view (1-4 = screw dots)")
fig.tight_layout(); fig.savefig("docs/template.png")
