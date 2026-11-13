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
ANIMALS = ["plain", "pup", "rose"]
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


def arc(cx, cy, r, a0, a1, w):
    t = np.radians(np.linspace(a0, a1, 40))
    return shapely.LineString(np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]).buffer(w / 2, quad_segs=8)


def pup():
    """Chibi sitting puppy perched on top; its curly tail is the carabiner loop."""
    body = ellipse(-0.5, 6.0, 8.0, 7.0)
    chest = ellipse(4.0, 9.0, 5.0, 6.0)
    head = Point(5.5, 19.0).buffer(6.8, quad_segs=64)
    snout = ellipse(11.3, 16.8, 3.8, 3.0)
    nose = Point(14.4, 17.6).buffer(1.9, quad_segs=24)
    leg = box(4.5, -1.0, 8.6, 8.0)
    paw = ellipse(7.4, 0.9, 3.0, 1.9)
    tail_c = (-11.5, 11.5)
    tail = Point(*tail_c).buffer(5.3, quad_segs=48)
    stem = shapely.LineString([(-5.5, 7.5), (-9.0, 9.5)]).buffer(2.6)
    base = box(-9.0, -1.0, 9.0, 2.0)
    sil = unary_union([body, chest, head, snout, nose, leg, paw, tail, stem, base])
    sil = sil.buffer(1.4, quad_segs=24).buffer(-1.4, quad_segs=24)    # smooth soft curves
    ear = ellipse(2.6, 18.0, 2.9, 5.4, 18)
    eye = ellipse(9.0, 20.3, 1.15, 1.45)
    nose_d = ellipse(14.2, 17.8, 1.4, 1.15)
    collar = shapely.LineString([(-1.0, 13.4), (10.5, 11.2)]).buffer(0.75).intersection(sil.buffer(-0.6))
    tag = Point(6.3, 10.0).buffer(1.3, quad_segs=24)
    thigh = arc(-1.2, 4.6, 4.6, 15, 125, 0.7)
    leg_line = shapely.LineString([(4.6, 1.0), (4.6, 6.0)]).buffer(0.35)
    details = unary_union([ear, eye, nose_d, collar, tag, thigh, leg_line]).intersection(sil.buffer(-0.4))
    k = 1.2   # overall pup size
    sil, details = (aff.scale(g, k, k, origin=(0, 0)) for g in (sil, details))
    return sil, details, (tail_c[0] * k, tail_c[1] * k)


def leaf(cx, cy, length, width, rot):
    """Pointed leaf (vesica) with a raised centre vein."""
    r = (length ** 2 / 4 + width ** 2 / 4) / width
    d = r - width / 2
    shape = Point(0, d).buffer(r, quad_segs=64).intersection(Point(0, -d).buffer(r, quad_segs=64))
    vein = shapely.LineString([(-length / 2 + 1.5, 0), (length / 2 - 1.8, 0)]).buffer(0.35)
    veins = [vein] + [shapely.LineString([(x, 0), (x + 2.0, s * 1.6)]).buffer(0.3)
                      for x in (-3.5, -0.5, 2.5) for s in (-1, 1)]
    out = []
    for g in (shape, unary_union(veins)):
        g = aff.rotate(g, rot, origin=(0, 0))
        out.append(aff.translate(g, cx, cy))
    return out[0], out[1]


def rose():
    """Garden rose bloom on top; the carabiner hole is the heart of the rose."""
    c = (0.0, 14.0)
    PR, PD = 6.0, 7.6          # petal radius, petal distance from centre
    petals = [Point(c[0] + PD * np.sin(np.radians(a)), c[1] + PD * np.cos(np.radians(a))).buffer(PR, quad_segs=48)
              for a in range(0, 360, 72)]
    bloom = unary_union(petals + [Point(*c).buffer(9.5, quad_segs=64)])
    lf_l, vein_l = leaf(-14.0, 3.6, 16.0, 7.0, 162)
    lf_r, vein_r = leaf(14.0, 3.6, 16.0, 7.0, 18)
    filler = box(-9.0, -1.0, 9.0, 5.0)
    sil = unary_union([bloom, lf_l, lf_r, filler]).buffer(0.8, quad_segs=24).buffer(-0.8, quad_segs=24)
    # raised spiral petals swirling out from the hole
    t = np.linspace(0, 1.75 * 2 * np.pi, 400)
    r = 4.1 + 4.6 * t / t[-1]
    spiral = shapely.LineString(np.c_[c[0] + r * np.cos(t + 1.2), c[1] + r * np.sin(t + 1.2)]).buffer(0.38)
    # outer petal edges: a soft arc inside each scallop
    arcs = []
    for a in range(0, 360, 72):
        pc = (c[0] + PD * np.sin(np.radians(a)), c[1] + PD * np.cos(np.radians(a)))
        ang = 90 - a
        arcs.append(arc(pc[0], pc[1], PR - 1.9, ang - 60, ang + 60, 0.7))
    details = unary_union([spiral, vein_l, vein_r] + arcs).intersection(sil.buffer(-0.5))
    return sil, details, c


def plain():
    """Simple rounded tab on top for a carabiner."""
    sil = unary_union([Point(0, 3.5).buffer(6.0, quad_segs=48), box(-6, -1, 6, 3.5)])
    return sil, shapely.Polygon(), (0, 3.5)


ANIMAL_FUNCS = {"dog": dog, "plain": plain, "pup": pup, "rose": rose}
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
            ax.set_ylim(-130, 34); ax.set_xlim(-26, 26)
        plt.tight_layout()
        plt.savefig(os.path.join(HERE, f"preview_{animal}.png"), dpi=130, facecolor="white")
        # close-up of the head
        fig, ax = plt.subplots(figsize=(7, 7))
        shape, details = outline(2, animal)
        draw(ax, shape, unary_union([details, logo]))
        ax.set_xlim(-25, 25); ax.set_ylim(-34, 34); ax.set_aspect("equal"); ax.axis("off")
        plt.savefig(os.path.join(HERE, f"closeup_{animal}.png"), dpi=150, facecolor="white")


if __name__ == "__main__":
    main()
