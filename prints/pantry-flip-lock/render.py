"""Preview renders: 3D assembly (locked) + front view (locked / stored)."""
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import latch

parts, base_h, sleeve_h = latch.build()
P = latch.P
GAP, PIV = 4.0, -32.0                    # gap x 0..4; pivot 32 mm from door A's edge
post = np.array([PIV + P["D"], P["SLOT_CY"]])

def place(tm, rotz=0, t=(0, 0, 0)):
    m = tm.copy()
    if rotz: m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rotz), [0, 0, 1]))
    m.apply_translation(t); return m

def assembly(bar_angle=0):
    T = P["PLATE_T"]
    a = [("base", place(parts["base"], 0, (PIV, 0, 0)), "#4a90d9"),
         ("keeper", place(parts["keeper"], 180, (post[0], post[1], 0)), "#4a90d9"),
         ("bar", place(parts["bar"], bar_angle, (PIV, 0, T)), "#e8a33d"),
         ("w1", place(parts["washer"], 0, (PIV, 0, T + base_h)), "#888"),
         ("w2", place(parts["washer"], 0, (post[0], post[1], T + sleeve_h)), "#888")]
    return a

fig = plt.figure(figsize=(11, 7), dpi=110)
ax2 = fig.add_subplot(1, 2, 1)
ax3 = fig.add_subplot(1, 2, 2)
ax2.add_patch(plt.Rectangle((-80, -130), 80, 220, color="#f2efe8"))
ax2.add_patch(plt.Rectangle((GAP, -130), 76, 220, color="#ebe7de"))
ax2.axvspan(0, GAP, color="#333")
for x in (-76, 80):
    ax2.axvline(x, color="#bbb", ls="--", lw=1)
def outline(m, col, lw=1.5, alpha=1):
    sec = m.section(plane_origin=[0, 0, m.bounds[0][2] + 0.3], plane_normal=[0, 0, 1])
    if sec is None: return
    for e in sec.discrete:
        ax2.plot(e[:, 0], e[:, 1], color=col, lw=lw, alpha=alpha)
for name, m, col in assembly(0):
    outline(m, col)
for name, m, col in assembly(-90):
    if name == "bar": outline(m, "#e8a33d", 1.2, 0.45)
ax2.annotate("door A", (-70, 80), fontsize=10); ax2.annotate("door B", (12, 80), fontsize=10)
ax2.annotate("gap", (0.5, -125), fontsize=8, color="#333")
ax2.annotate("unlocked: bar\nhangs down", (PIV + 18, -108), fontsize=9, color="#b07a20")
ax2.annotate("pivot", (PIV - 26, -6), fontsize=9); ax2.annotate("post", (post[0] + 14, post[1] - 6), fontsize=9)
ax2.annotate("~76 mm flat border\n(each door)", (-74, 60), fontsize=8, color="#888")
ax2.set_xlim(-85, 85); ax2.set_ylim(-135, 95); ax2.set_aspect("equal")
ax2.set_title("Front view, mm (screw above pivot, screw below post)", fontsize=11)
for name, m, col in assembly(0):
    for x in (PIV, post[0]):
        sec = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
        if sec is None: continue
        for e in sec.discrete:
            off = 0 if x == PIV else 80
            ax3.fill(e[:, 2] + off, e[:, 1], color=col, alpha=0.9, lw=0)
for off, lab, h in ((0, "pivot (door A)", 13.9), (80, "post (door B)", 14.9)):
    ax3.add_patch(plt.Rectangle((off - 19, -70), 19, 140, color="#e9e5dc"))
    ax3.plot([off - 9, off + h], [0 if off == 0 else post[1]] * 2, color="k", lw=2.2)
    ax3.annotate(lab, (off - 18, 62), fontsize=9)
    ax3.annotate("1 in screw", (off + h + 1, 1.5), fontsize=8)
ax3.annotate("door", (-18, -66), fontsize=8, color="#777")
ax3.annotate("bar", (6, 20), fontsize=8, color="#b07a20")
ax3.set_xlim(-22, 112); ax3.set_ylim(-72, 72); ax3.set_aspect("equal")
ax3.set_title("Side cut through pivot and post", fontsize=11); ax3.set_xticks([]); ax3.set_yticks([])
fig.tight_layout(); fig.savefig("docs/assembly.png"); print("ok")
