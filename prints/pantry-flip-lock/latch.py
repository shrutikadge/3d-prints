"""Pantry flip-bar lock: ties the two pantry doors together across the gap.

Coordinates: X along the door face toward the other door, Y up, Z out of the door.
Parts (all print flat, no supports, no print-in-place):
  base    - plate on door A with the pivot boss (screws ABOVE the pivot)
  bar     - flips down onto the keeper; hooked slot drops over the post
  keeper  - plate on door B with the post sleeve (screws BELOW the post)
  washer  - x2, clamp under the pivot / post screw heads, keep the bar on
  shim    - 1.5 mm and 3 mm, same footprint as base/keeper, for doors that
            don't sit flush with each other

Screws: #8 (4.2 mm) or #6 flat-head wood screws.
  2 x 5/8"  through the plates (11.9 mm into the door)
  2 x 1"    through washer + boss/sleeve + plate (pivot and post)

Usage: python latch.py ['{"D": 68}']
"""
import json
import sys

import manifold3d as m3
import numpy as np
import trimesh

P = dict(
    D=68.0,          # pivot-to-post distance (keeper is placed in situ anyway)
    PLATE_W=26.0,
    PLATE_T=4.0,
    SCREW_PITCH=22.0,  # pivot/post -> plate screw spacing
    N_SCREWS=1,      # plate screws besides the pivot/post screw
    HOLE_D=4.6,      # clearance for #8 / #6
    CSK_D=8.8,       # 90 deg countersink top diameter
    BOSS_D=11.0,
    BAR_T=7.0,
    BAR_W=24.0,
    PIVOT_HOLE=12.0,
    SLOT_W=12.0,
    SLOT_CY=-3.0,    # post centre relative to bar centreline when locked
    NOSE=10.0,
    TAIL=10.0,
    BOSS_CLEAR=0.4,  # bar rotates freely on the base boss
    SLEEVE_CLEAR=1.4,  # extra z play on the keeper for door misalignment
    WASHER_D=22.0,
    WASHER_T=2.5,
    CHAMFER=0.6,
    SEG=96,
)
if len(sys.argv) > 1:
    P.update(json.loads(sys.argv[1]))
m3.set_circular_segments(P["SEG"])


def cyl(d, h, z0=0.0, x=0.0, y=0.0):
    return m3.Manifold.cylinder(h, d / 2, d / 2).translate((x, y, z0))


def cone(d0, d1, h, z0=0.0, x=0.0, y=0.0):
    return m3.Manifold.cylinder(h, d0 / 2, d1 / 2).translate((x, y, z0))


def box(x0, y0, x1, y1, z0, z1):
    return m3.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def stadium(y0, y1, w, t):
    """Vertical rounded plate from y0 to y1 (centres of the end arcs), width w."""
    r = w / 2
    return (box(-r, y0, r, y1, 0, t) + cyl(w, t, y=y0) + cyl(w, t, y=y1))


def csk_hole(x, y, t):
    """Through hole with a 90 deg countersink at the top face z=t."""
    h_csk = (P["CSK_D"] - P["HOLE_D"]) / 2
    return (cyl(P["HOLE_D"], t + 2, -1, x, y)
            + cone(P["HOLE_D"], P["CSK_D"], h_csk, t - h_csk, x, y)
            + cyl(P["CSK_D"], 1, t, x, y))


def plate(boss_h):
    """Plate with a boss at (0,0) and N_SCREWS screws above it. Keeper = this rotated 180."""
    t = P["PLATE_T"]
    s = P["SCREW_PITCH"]
    n = P["N_SCREWS"]
    body = stadium(0, n * s, P["PLATE_W"], t)
    body += cyl(P["BOSS_D"], t + boss_h)
    body -= cyl(P["HOLE_D"], t + boss_h + 2, -1)
    for k in range(1, n + 1):
        body -= csk_hole(0, k * s, t)
    # chamfer the top edge of the boss so the bar drops on easily
    c = P["CHAMFER"]
    top = t + boss_h
    ring = (cyl(P["BOSS_D"] + 2, c + 0.01, top - c)
            - cone(P["BOSS_D"], P["BOSS_D"] - 2 * c, c + 0.01, top - c))
    return body - ring


def bar():
    t, w = P["BAR_T"], P["BAR_W"]
    r = w / 2
    D = P["D"]
    x_end = D + P["SLOT_W"] / 2 + P["NOSE"] + P["TAIL"]
    body = box(0, -r, x_end - r, r, 0, t) + cyl(w, t) + cyl(w, t, x=x_end - r)
    body -= cyl(P["PIVOT_HOLE"], t + 2, -1)
    # hook slot: open downward, post sits at (D, SLOT_CY)
    sw = P["SLOT_W"]
    body -= box(D - sw / 2, -r - 1, D + sw / 2, P["SLOT_CY"], -1, t + 1)
    body -= cyl(sw, t + 2, -1, D, P["SLOT_CY"])
    # flare the slot mouth so the hook finds the post
    flare = m3.Manifold.extrude(
        m3.CrossSection([[(D - sw / 2, -r + 4), (D - sw / 2 - 3, -r - 0.01),
                          (D + sw / 2 + 3, -r - 0.01), (D + sw / 2, -r + 4)]]),
        t + 2).translate((0, 0, -1))
    body -= flare
    # bottom-edge chamfers on the holes (elephant foot)
    c = P["CHAMFER"]
    body -= cone(P["PIVOT_HOLE"] + 2 * c, P["PIVOT_HOLE"], c, 0)
    return body


def washer():
    t = P["WASHER_T"]
    w = cyl(P["WASHER_D"], t) - cyl(P["HOLE_D"], t + 2, -1)
    h_csk = min((P["CSK_D"] - P["HOLE_D"]) / 2, t - 0.6)
    w -= cone(P["CSK_D"] - 2 * ((P["CSK_D"] - P["HOLE_D"]) / 2 - h_csk), P["CSK_D"], h_csk, t - h_csk)
    w -= cyl(P["CSK_D"], 1, t)
    return w


def shim(t):
    s = P["SCREW_PITCH"]
    n = P["N_SCREWS"]
    body = stadium(0, n * s, P["PLATE_W"], t)
    for k in range(n + 1):
        body -= cyl(P["HOLE_D"] + 0.4, t + 2, -1, 0, k * s)
    return body


def to_tm(man):
    mesh = man.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                           faces=np.asarray(mesh.tri_verts), process=True)


def build():
    base_h = P["BAR_T"] + P["BOSS_CLEAR"]
    sleeve_h = P["BAR_T"] + P["SLEEVE_CLEAR"]
    parts = {
        "base": plate(base_h),
        "keeper": plate(sleeve_h),
        "bar": bar(),
        "washer": washer(),
        "shim_1p5": shim(1.5),
        "shim_3": shim(3.0),
    }
    return {k: to_tm(v) for k, v in parts.items()}, base_h, sleeve_h


if __name__ == "__main__":
    import os
    os.makedirs("stl", exist_ok=True)
    parts, base_h, sleeve_h = build()
    for k, tm in parts.items():
        assert tm.is_watertight, k
        tm.export(f"stl/{k}.stl")
        ext = tm.bounds[1] - tm.bounds[0]
        print(f"{k:9s} {ext[0]:6.1f} x {ext[1]:6.1f} x {ext[2]:5.1f} mm  vol {tm.volume/1000:5.2f} cm3")
    stack = P["WASHER_T"] + base_h + P["PLATE_T"]
    print(f"pivot stack {stack:.1f} mm -> 1in screw bites {25.4-stack:.1f} mm; "
          f"post stack {P['WASHER_T']+sleeve_h+P['PLATE_T']:.1f} -> {25.4-(P['WASHER_T']+sleeve_h+P['PLATE_T']):.1f} mm; "
          f"5/8in plate screws bite {15.9-P['PLATE_T']:.1f} mm")
