"""Generate dainty 3D-printable thread cards (STL) with a scalloped bottom edge.

Run:  python3 make_thread_cards.py
Needs: pip install trimesh shapely manifold3d mapbox_earcut matplotlib
All sizes are millimetres; tweak the constants below and re-run.
"""
import os
import numpy as np
import shapely
from shapely.geometry import box, Point
from shapely.ops import unary_union
import trimesh

# ---- design settings -------------------------------------------------------
THICK = 1.6          # card thickness
WIDE = 46.0          # width of header / dividers / footer
NARROW = 36.0        # width where the thread is wound
HEADER_H = 18.0
ZONE_H = 17.0        # height of each thread-winding section
DIVIDER_H = 6.0
FOOTER_H = 10.0
SCALLOPS = 5         # bumps across the bottom edge
SCALLOP_DEPTH = 3.5  # how far the scallops hang below the footer
HOLE_D = 4.0         # hanging hole (0 to remove)
LABEL = (32.0, 7.0, 0.4)   # recessed label panel w, h, depth (sticker spot)
SLIT_W, SLIT_L = 0.9, 4.0  # thread-catch slits cut into the ears
OUTER_R, INNER_R = 2.0, 1.2
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")


def outline(n):
    """2D outline for an n-thread card. y=0 at top, going down (negative)."""
    parts, slit_y = [], []
    y = 0.0
    parts.append(box(-WIDE / 2, y - HEADER_H, WIDE / 2, y))
    slit_y.append(y - HEADER_H + 4.0)
    y -= HEADER_H
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
    # scalloped bottom: row of circles hanging off the footer
    r = WIDE / SCALLOPS / 2
    cy = y + r - SCALLOP_DEPTH
    for k in range(SCALLOPS):
        cx = -WIDE / 2 + r + 2 * r * k
        parts.append(Point(cx, cy).buffer(r, quad_segs=48))
    shape = unary_union(parts)
    # soften: round convex corners, fillet inside corners
    shape = shape.buffer(-OUTER_R, quad_segs=24).buffer(OUTER_R, quad_segs=24)
    shape = shape.buffer(INNER_R, quad_segs=24).buffer(-INNER_R, quad_segs=24)

    cuts = []
    for sy in slit_y:  # thread-catch slits from both side edges, round relief at end
        for s in (-1, 1):
            x0 = s * (WIDE / 2 + 1)
            x1 = s * (WIDE / 2 - SLIT_L)
            cuts.append(box(min(x0, x1), sy - SLIT_W / 2, max(x0, x1), sy + SLIT_W / 2))
            cuts.append(Point(x1, sy).buffer(SLIT_W * 0.75, quad_segs=16))
            # little V lead-in so the thread finds the slit
            cuts.append(shapely.Polygon([(s * (WIDE / 2 + 0.5), sy + 1.0),
                                         (s * (WIDE / 2 - 1.0), sy),
                                         (s * (WIDE / 2 + 0.5), sy - 1.0)]))
    if HOLE_D:
        cuts.append(Point(0, -4.5).buffer(HOLE_D / 2, quad_segs=32))
    return shape.difference(unary_union(cuts))


def extrude(poly, h, z0=0.0):
    m = trimesh.creation.extrude_polygon(poly, h)
    m.apply_translation([0, 0, z0])
    return m


def card(n):
    poly = outline(n)
    body = extrude(poly, THICK)
    lw, lh, ld = LABEL
    if ld:
        lab = box(-lw / 2, -HEADER_H + 3.0, lw / 2, -HEADER_H + 3.0 + lh)
        lab = lab.buffer(-1.5).buffer(1.5, quad_segs=16)
        body = body.difference(extrude(lab, ld + 0.1, THICK - ld), engine="manifold")
    return poly, body


def main():
    os.makedirs(OUT, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    counts = [2, 3, 4, 5]
    fig, axes = plt.subplots(1, len(counts), figsize=(12, 7))
    for ax, n in zip(axes, counts):
        poly, mesh = card(n)
        assert mesh.is_watertight, f"{n}-thread mesh not watertight"
        path = os.path.join(OUT, f"thread_card_{n}_threads.stl")
        mesh.export(path)
        ext = mesh.extents
        print(f"{n} threads: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm -> {path}")
        for geom in getattr(poly, "geoms", [poly]):
            ax.fill(*geom.exterior.xy, color="#f6efe6", ec="#8a6f5a", lw=1.2)
            for hole in geom.interiors:
                ax.fill(*hole.xy, color="white", ec="#8a6f5a", lw=1)
        lw, lh, _ = LABEL
        ax.add_patch(plt.Rectangle((-lw / 2, -HEADER_H + 3), lw, lh, fill=False,
                                   ls="--", ec="#b9a08c"))
        ax.set_title(f"{n} threads\n{ext[0]:.0f} x {ext[1]:.0f} mm")
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_ylim(-150, 3); ax.set_xlim(-26, 26)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "preview.png"), dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
