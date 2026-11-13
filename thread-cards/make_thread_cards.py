"""Generate dainty 3D-printable thread cards (STL) with a scalloped bottom edge.

Run:  python3 make_thread_cards.py
Needs: pip install trimesh shapely manifold3d mapbox_earcut matplotlib
All sizes are millimetres; tweak the constants below and re-run.
"""
import os
import numpy as np
import shapely
import shapely.affinity
from shapely.geometry import box, Point
from shapely.ops import unary_union
import trimesh

# ---- design settings -------------------------------------------------------
THICK = 1.2          # card thickness
WIDE = 46.0          # width of header / dividers / footer
NARROW = 36.0        # width where the thread is wound
HEADER_H = 32.0
ZONE_H = 17.0        # height of each thread-winding section
DIVIDER_H = 6.0
FOOTER_H = 10.0
SCALLOPS = 5         # bumps across the bottom edge
SCALLOP_DEPTH = 3.5  # how far the scallops hang below the footer
HOLE_D = 5.5         # carabiner hole in the top tab (0 to remove)
TAB_R = 6.0          # radius of the rounded tab that holds the hole
TAB_Y = 3.5          # how far the hole centre sits above the card top
LABEL = (32.0, 10.0, 0)   # flat name area on the header (depth 0 = no recess)
LOGO_FILE = "sookies_logo.png"
LOGO_W = 40.0        # logo width on the header
LOGO_RAISE = 0.6     # how much the logo stands up from the card
LOGO_MIN = 0.12      # thickens hairlines so they print (mm added per side)
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
    if HOLE_D:  # rounded tab on top for the carabiner
        parts.append(Point(0, TAB_Y).buffer(TAB_R, quad_segs=48))
        parts.append(box(-TAB_R, -1, TAB_R, TAB_Y))
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
        cuts.append(Point(0, TAB_Y).buffer(HOLE_D / 2, quad_segs=48))
    return shape.difference(unary_union(cuts))


def logo_shape():
    """Trace the logo artwork (anything not background colour) into 2D shapes."""
    import cv2
    im = cv2.imread(os.path.join(HERE, LOGO_FILE))
    bg = im[5, 5].astype(int)
    mask = (np.abs(im.astype(int) - bg).sum(2) > 90).astype(np.uint8) * 255
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for i, c in enumerate(cnts):
        if hier[0][i][3] != -1 or len(c) < 3:
            continue
        holes = []
        j = hier[0][i][2]
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
    g = shapely.affinity.scale(g, k, -k, origin=(0, 0))      # flip y (image is top-down)
    x0, y0, x1, y1 = g.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    g = shapely.affinity.translate(g, -cx, -(HEADER_H - 4.0) / 2 - 1.0 - cy)
    return g.buffer(LOGO_MIN, quad_segs=8).simplify(0.02)


def extrude(poly, h, z0=0.0):
    ms = [trimesh.creation.extrude_polygon(g, h) for g in getattr(poly, "geoms", [poly])]
    m = ms[0] if len(ms) == 1 else trimesh.boolean.union(ms, engine="manifold")
    m.apply_translation([0, 0, z0])
    return m


def card(n):
    poly = outline(n)
    body = extrude(poly, THICK)
    lw, lh, ld = LABEL
    if ld:
        lab = box(-lw / 2, -HEADER_H + 5.0, lw / 2, -HEADER_H + 5.0 + lh)
        lab = lab.buffer(-1.5).buffer(1.5, quad_segs=16)
        body = body.difference(extrude(lab, ld + 0.1, THICK - ld), engine="manifold")
    logo = extrude(LOGO, LOGO_RAISE, THICK)
    return poly, body, logo


def main():
    global LOGO
    LOGO = logo_shape()
    os.makedirs(OUT, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    counts = [2, 3, 4]
    fig, axes = plt.subplots(1, len(counts), figsize=(12, 7))
    for ax, n in zip(axes, counts):
        poly, card_only, logo = card(n)
        mesh = trimesh.boolean.union([card_only, logo], engine="manifold")
        assert mesh.is_watertight, f"{n}-thread mesh not watertight"
        path = os.path.join(OUT, f"thread_card_{n}_threads.stl")
        mesh.export(path)
        ext = mesh.extents
        print(f"{n} threads: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm -> {path}")
        for geom in getattr(poly, "geoms", [poly]):
            ax.fill(*geom.exterior.xy, color="#f6efe6", ec="#8a6f5a", lw=1.2)
            for hole in geom.interiors:
                ax.fill(*hole.xy, color="white", ec="#8a6f5a", lw=1)
        for geom in getattr(LOGO, "geoms", [LOGO]):
            ax.fill(*geom.exterior.xy, color="#e3d3c3", ec="#b39a85", lw=0.4)
            for hole in geom.interiors:
                ax.fill(*hole.xy, color="#f6efe6", lw=0)
        ax.set_title(f"{n} threads\n{ext[0]:.0f} x {ext[1]:.0f} mm")
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_ylim(-130, 12); ax.set_xlim(-26, 26)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "preview.png"), dpi=130, facecolor="white")


if __name__ == "__main__":
    main()
