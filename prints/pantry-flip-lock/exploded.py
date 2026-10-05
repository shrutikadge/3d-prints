"""Exploded isometric render of the printed parts -> docs/exploded.png."""
import sys; sys.path.insert(0, ".")
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import latch

parts, base_h, sleeve_h = latch.build()
P = latch.P
PIV, POST = np.array([-34.0, 0]), np.array([34.0, P["SLOT_CY"]])
def place(name, rotz=0, t=(0, 0, 0)):
    m = parts[name].copy()
    if rotz: m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rotz), [0, 0, 1]))
    m.apply_translation(t); return m
EX = 16
items = [(place("base", 0, (*PIV, 0)), "#dfe6ee"), (place("keeper", 180, (*POST, 0)), "#dfe6ee"),
         (place("bar", 0, (*PIV, P["PLATE_T"] + EX)), "#f0d9a8"),
         (place("washer", 0, (*PIV, P["PLATE_T"] + base_h + 2 * EX)), "#d9d9d9"),
         (place("washer", 0, (*POST, P["PLATE_T"] + sleeve_h + 2 * EX)), "#d9d9d9")]
light = np.array([-0.35, -0.45, 1.0]); light /= np.linalg.norm(light)
fig = plt.figure(figsize=(5.34, 4.62), dpi=220)
ax = fig.add_axes([0, 0, 1, 1], projection="3d")
el, az = np.radians(24), np.radians(-58)
view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
tris, cols = [], []
for m, col in items:
    v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=1.2)
    m = trimesh.Trimesh(v, f, process=False)
    m.update_faces(m.face_normals @ view > 1e-6)      # back-face cull so the painter sort can't misorder
    shade = 0.55 + 0.45 * np.clip(m.face_normals @ light, 0, 1)
    rgb = np.array(matplotlib.colors.to_rgb(col))
    tris += list(m.vertices[m.faces]); cols += list((np.outer(shade, rgb)).clip(0, 1))
ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors=cols, linewidths=0.3))
for (x, y), ztop in ((PIV, P["PLATE_T"] + base_h + 2 * EX + 14), (POST, P["PLATE_T"] + sleeve_h + 2 * EX + 14)):
    ax.plot([x, x], [y, y], [-6, ztop], color="#555", lw=0.9, ls=(0, (4, 3)))
ax.set_xlim(-54, 54); ax.set_ylim(-38, 38); ax.set_zlim(-4, 52)
ax.set_box_aspect((108, 76, 56), zoom=1.25); ax.view_init(elev=24, azim=-58); ax.set_proj_type("ortho")
ax.set_axis_off(); fig.patch.set_facecolor("white")
fig.savefig("docs/exploded.png", facecolor="white"); print("ok")
