"""Generate dainty 3D-printable "collectible animal" thread cards (STL).

Each card: an animal head on top (with a carabiner hole), a collar band carrying the
raised "Sookie's" logo, thread-winding sections with slit dividers, and a scalloped bottom.

Run:  python3 make_thread_cards.py
Needs: pip install trimesh shapely manifold3d mapbox_earcut matplotlib opencv-python-headless
All sizes are millimetres. Single-colour print: details are raised, not coloured.
"""
import os
import numpy as np
import shapely
import shapely.affinity as aff
from shapely.geometry import box, Point
from shapely.ops import unary_union
import trimesh

# ---- design settings -------------------------------------------------------
THICK = 1.2          # card thickness
RAISE = 0.6          # height of raised details (logo, face, ears)
WIDE = 46.0          # width of collar / dividers / footer
NARROW = 36.0        # width where the thread is wound
COLLAR_H = 25.0      # top panel that carries the logo
ZONE_H = 17.0        # height of each thread-winding section
DIVIDER_H = 6.0
FOOTER_H = 10.0
SCALLOPS = 5
SCALLOP_DEPTH = 3.5
HOLE_D = 5.5         # carabiner hole
LOGO_FILE = "sookies_logo.png"
LOGO_CROP_ROWS = 800  # keep only artwork above this pixel row (drops "NEEDLEPOINT")
LOGO_W = 34.0
LOGO_TOP_GAP = 2.5   # logo sits this far below the top edge (keeps it clear of the slits)
LOGO_MIN = 0.12      # thickens hairlines so they print
SLIT_W, SLIT_L = 0.9, 4.0
OUTER_R, INNER_R = 1.2, 1.2
COUNTS = [2, 3, 4]
ANIMALS = ["plain"]
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")


def ellipse(cx, cy, rx, ry, rot=0.0):
    e = aff.scale(Point(0, 0).buffer(1, quad_segs=64), rx, ry)
    e = aff.rotate(e, rot, origin=(0, 0))
    return aff.translate(e, cx, cy)


# ---- animals: each returns (silhouette, raised details, hole centre) -------
# y = 0 is the top edge of the collar; the head sits above it.
def dog():
    head = ellipse(0, 16, 14.5, 13.5)
    neck = box(-9, -1, 9, 6)
    ears = [ellipse(s * 14.5, 15, 5.8, 11.5, s * 18) for s in (-1, 1)]
    sil = unary_union([head, neck] + ears)
    ear_raise = unary_union([e.buffer(-0.6) for e in ears])           # floppy ears stand proud
    muzzle = ellipse(0, 10.5, 7.0, 5.2).difference(ellipse(0, 10.5, 7.0, 5.2).buffer(-0.7))
    eyes = [Point(s * 5.8, 17.5).buffer(1.7, quad_segs=24) for s in (-1, 1)]
    nose = ellipse(0, 12.3, 2.8, 2.0)
    mouth = shapely.LineString([(-2.6, 8.6), (-1.3, 8.0), (0, 8.7), (1.3, 8.0), (2.6, 8.6)]).buffer(0.35)
    philtrum = shapely.LineString([(0, 10.5), (0, 8.7)]).buffer(0.35)
    details = unary_union([ear_raise, muzzle, nose, mouth, philtrum] + eyes)
    hole = (0, 24.5)
    return sil, details, hole


def plain():
    """Simple rounded tab on top for a carabiner."""
    sil = unary_union([Point(0, 3.5).buffer(6.0, quad_segs=48), box(-6, -1, 6, 3.5)])
    return sil, shapely.Polygon(), (0, 3.5)


ANIMAL_FUNCS = {"dog": dog, "plain": plain}
# ---------------------------------------------------------------------------


def logo_shape():
    import cv2
    im = cv2.imread(os.path.join(HERE, LOGO_FILE))
    bg = im[5, 5].astype(int)
    mask = (np.abs(im.astype(int) - bg).sum(2) > 90).astype(np.uint8) * 255
    mask[LOGO_CROP_ROWS:] = 0
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for i, c in enumerate(cnts):
        if hier[0][i][3] != -1 or len(c) < 3:
            continue
        holes, j = [], hier[0][i][2]
        while j != -1:
            if len(cnts[j]) >= 3:
                holes.append(cnts[j][:, 0, :])
            j = hier[0][j][0]
        pg = shapely.Polygon(c[:, 0, :], holes).buffer(0)
        if pg.area > 4:
            polys.append(pg)
    g = unary_union(polys)
    x0, y0, x1, y1 = g.bounds
    k = LOGO_W / (x1 - x0)
    g = aff.scale(g, k, -k, origin=(0, 0))
    x0, y0, x1, y1 = g.bounds
    g = aff.translate(g, -(x0 + x1) / 2, -LOGO_TOP_GAP - y1)
    return g.buffer(LOGO_MIN, quad_segs=8).simplify(0.02)


def outline(n, animal):
    sil, details, hole = ANIMAL_FUNCS[animal]()
    parts, slit_y = [sil], []
    y = 0.0
    parts.append(box(-WIDE / 2, y - COLLAR_H, WIDE / 2, y))
    slit_y.append(y - COLLAR_H + 3.5)
    y -= COLLAR_H
    for i in range(n):
        parts.append(box(-NARROW / 2, y - ZONE_H, NARROW / 2, y + 0.01))
        y -= ZONE_H
        if i < n - 1:
            parts.append(box(-WIDE / 2, y - DIVIDER_H, WIDE / 2, y + 0.01))
            slit_y.append(y - DIVIDER_H / 2)
            y -= DIVIDER_H
    parts.append(box(-WIDE / 2, y - FOOTER_H, WIDE / 2, y + 0.01))
    slit_y.append(y - 4.0)
    y -= FOOTER_H
    r = WIDE / SCALLOPS / 2
    for k in range(SCALLOPS):
        parts.append(Point(-WIDE / 2 + r + 2 * r * k, y + r - SCALLOP_DEPTH).buffer(r, quad_segs=48))
    shape = unary_union(parts)
    shape = shape.buffer(-OUTER_R, quad_segs=24).buffer(OUTER_R, quad_segs=24)
    shape = shape.buffer(INNER_R, quad_segs=24).buffer(-INNER_R, quad_segs=24)

    cuts = [Point(*hole).buffer(HOLE_D / 2, quad_segs=48)]
    for sy in slit_y:
        for s in (-1, 1):
            x0, x1 = s * (WIDE / 2 + 1), s * (WIDE / 2 - SLIT_L)
            cuts.append(box(min(x0, x1), sy - SLIT_W / 2, max(x0, x1), sy + SLIT_W / 2))
            cuts.append(Point(x1, sy).buffer(SLIT_W * 0.75, quad_segs=16))
            cuts.append(shapely.Polygon([(s * (WIDE / 2 + 0.5), sy + 1.0),
                                         (s * (WIDE / 2 - 1.0), sy),
                                         (s * (WIDE / 2 + 0.5), sy - 1.0)]))
    cutu = unary_union(cuts)
    details = details.intersection(shape).difference(cutu.buffer(0.8))
    return shape.difference(cutu), details


def extrude(poly, h, z0=0.0):
    geoms = [g for g in getattr(poly, "geoms", [poly]) if g.area > 0.01]
    ms = [trimesh.creation.extrude_polygon(g, h) for g in geoms]
    m = ms[0] if len(ms) == 1 else trimesh.boolean.union(ms, engine="manifold")
    m.apply_translation([0, 0, z0])
    return m


def draw(ax, shape, raised):
    for g in getattr(shape, "geoms", [shape]):
        ax.fill(*g.exterior.xy, color="#f6efe6", ec="#8a6f5a", lw=1)
        for h in g.interiors:
            ax.fill(*h.xy, color="white", ec="#8a6f5a", lw=0.8)
    for g in getattr(raised, "geoms", [raised]):
        ax.fill(*g.exterior.xy, color="#e3d3c3", ec="#b39a85", lw=0.4)
        for h in g.interiors:
            ax.fill(*h.xy, color="#f6efe6", lw=0)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    logo = logo_shape()
    os.makedirs(OUT, exist_ok=True)
    for animal in ANIMALS:
        fig, axes = plt.subplots(1, len(COUNTS), figsize=(12, 8))
        for ax, n in zip(axes, COUNTS):
            shape, details = outline(n, animal)
            raised = unary_union([details, logo])
            mesh = trimesh.boolean.union([extrude(shape, THICK), extrude(raised, RAISE, THICK)],
                                         engine="manifold")
            assert mesh.is_watertight
            path = os.path.join(OUT, (f"{animal}_" if animal != "plain" else "") + f"thread_card_{n}_threads.stl")
            mesh.export(path)
            e = mesh.extents
            print(f"{animal} {n} threads: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm -> {path}")
            draw(ax, shape, raised)
            ax.set_title(f"{n} threads\n{e[0]:.0f} x {e[1]:.0f} mm")
            ax.set_aspect("equal"); ax.axis("off")
            ax.set_ylim(-130, 12); ax.set_xlim(-26, 26)
        plt.tight_layout()
        plt.savefig(os.path.join(HERE, f"preview_{animal}.png"), dpi=130, facecolor="white")
        # close-up of the head
        fig, ax = plt.subplots(figsize=(7, 7))
        shape, details = outline(2, animal)
        draw(ax, shape, unary_union([details, logo]))
        ax.set_xlim(-25, 25); ax.set_ylim(-34, 12); ax.set_aspect("equal"); ax.axis("off")
        plt.savefig(os.path.join(HERE, f"closeup_{animal}.png"), dpi=150, facecolor="white")


if __name__ == "__main__":
    main()
