#!/usr/bin/env python3
"""Build floorplan.svg from a list of measured segments. Scale: 4 px = 1 inch, north up."""
from pathlib import Path

SCALE = 4  # px per inch
START = ("A", 0, 0)  # label, x inches (east +), y inches (south +)
DIRS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}

# (direction, length in inches, kind, end label[, start label])
# Start label defaults to the previous segment's end point.
SEGMENTS = [
    # East wall, A to H (north to south), room to the west
    ("S", 3.5, "wall", "B"),
    ("S", 36, "window", "C"),
    ("S", 9, "wall", "D"),
    ("S", 36, "wall:stovetop", "E"),
    ("S", 8.5, "wall", "F"),
    ("S", 36, "window", "G"),
    ("S", 48, "wall", "H"),
    # South wall, H to K (east to west); 32" window centred over the 36" sink I-J
    ("W", 45, "wall", "I"),
    ("W", 2, "wall", "_w1"),
    ("W", 32, "window", "_w2"),
    ("W", 2, "wall", "J"),
    ("W", 42.5, "wall", "K"),
    # West wall, K to S (south to north), with a 40.5" jog west at N-O
    ("N", 28.5, "wall", "L"),
    ("N", 29, "opening:opening", "M"),
    ("N", 8, "wall", "N"),
    ("W", 40.5, "wall", "O"),
    ("N", 41, "wall:fridge space", "P"),
    ("N", 48, "wall:appliance garage", "Q"),
    ("N", 30, "wall:oven + microwave", "R"),
    # Pantry K-K1-O-N (walk-in, entered through the L-M opening)
    ("W", 40.5, "wall", "K1", "K"),
    ("N", 65.5, "wall", "O", "K1"),
]

# Room labels: (title, subtitle, points whose centre the label sits at)
ROOMS = [("PANTRY", "3′ × 5′ (walk-in)", ["K", "K1", "O", "N"], -6)]  # last: x shift in inches

# Force dimension side for walls whose outside is cluttered, keyed by segment end label
# (1 = east/south of the wall, -1 = west/north). Totals use "A-B" keys.
DIM_SIDE = {"L": -1, "M": -1, "N": -1}  # K-N dims sit inside the pantry, clear of the south-wall cabinets

# Dimensions for runs whose segments use hidden "_" points: (from, to, text)
SPANS = [("I", "J", '36" sink base · 32" window centred')]

LABELS = {"opening": "walkway opening"}
MARGIN = 80
# Overall run dimensions drawn outside the segment dimensions: (from label, to label)
TOTALS = [("A", "H"), ("H", "K"), ("O", "R")]

# Countertops along walls: (points along the wall, depth in inches)
# Points may be a label or an (x, y) position in inches.
MM = 1 / 25.4
# Tall corner pantry (2100 mm tall): corner, side along the N-S wall, side along the E-W wall, depth
CORNER_PANTRY = None
# Base corner cabinet under the counter (lazy Susan): corner, size along each wall, cabinet depth
CORNER_BASE = None
COUNTERS = [(["A", "H", "K"], 25.625)]  # IKEA countertop depth 25 5/8"

# Appliances against a wall: (label, from point, to point, width, depth[, note]).
# Centred on the wall segment between the two points, projecting into the room.
APPLIANCES = [
    ("FRIDGE", "P", "O", 36, 30, "French door", '41" space'),
    ("APPLIANCE", "Q", "P", 48, 24, "GARAGE", "2 × 24\" tall cab.", "on 9\" box"),
    ("OVEN+MW", "R", "Q", 30, 24, "coffee gap", "on 9\" box"),
]

# Raised floor boxes against a wall: (from, to, depth, step depth, label). Drawn as a dashed outline.
PLATFORMS = [("P", "R", 24.75, 11, '9" box · flush 24¾" · 3 toe-kick drawers')]

# Wall (upper) cabinets, 15" deep, drawn dotted on the plan: (label, from, to, offset, width)
UPPERS = [
    ("U1", "A", "H", 133, 18),   # east, between window F-G and the corner unit
    ("U3", "A", "H", 48.5, 36),  # east, above the hood (D-E)
    ("U4", "H", "K", 26, 18),    # south, corner unit to the sink window
    ("U5", "H", "K", 81, 24),    # south, right of the sink window
    ("U6", "H", "K", 105, 18),
]
UPPER_DEPTH = 15
# L-shaped corner wall cabinet: (label, corner, size along each wall)
UPPER_CORNER = ("U2", "H", 26)

# Design constraints: segments (by end points) that must never be a window.
NO_WINDOW = []

# Fixtures placed along a wall run, measured in inches from the first point:
# (kind, label, from, to, offset, width, depth). kind: range | hood | sink | under
FIXTURES = [
    # East wall base cabinets (IKEA SEKTION, 24" deep), measured south from A
    ("under", "1 DRAWERS", "A", "H", 0.5, 24, 24),  # 0.5" filler / cover panel at A
    ("under", "2 DRAWERS", "A", "H", 24.5, 24, 24),
    ("under", "3 COOKTOP BASE", "A", "H", 48.5, 36, 24),  # 36" drawer base under the stovetop, D-E
    ("range", "STOVETOP|3 · 36\" drawer base below", "D", "E", 0, 36, 22),
    ("under", "4 PULL-OUT", "A", "H", 84.5, 15, 24),  # next to the stovetop: oils, ladles
    ("under", "5 DRAWERS", "A", "H", 99.5, 30, 24),  # 0.5" filler to the corner cabinet
    ("under", "6 CORNER", "A", "H", 130, 47, 24),  # 47" blind corner base, blind end at H
    # South wall, measured west from H (0-24" is the corner cabinet's blind end)
    ("under", "7 DRAWERS", "H", "K", 27, 18, 24),  # after a 3" filler off the corner cabinet
    ("under", "8 SINK BASE", "H", "K", 45, 36, 24),  # IKEA 36" sink base
    ("sink", "SINK", "H", "K", 46.5, 33, 22),  # 33" sink centred on the base (and under the 32" window)
    ("under", "9 TRASH", "H", "K", 81, 18, 24),  # 18" cabinet, double 35 qt pull-out
    ("under", "DW", "H", "K", 99, 24, 24),  # dishwasher against wall K, 0.5" filler
]

DIM_OFFSET = 40  # px, dimension line offset to the left/top of the segment


def build():
    pts = [START]
    by_label = {START[0]: START}
    starts = []
    for seg in SEGMENTS:
        d, length, _, label = seg[:4]
        start = by_label[seg[4]] if len(seg) > 4 else pts[-1]
        starts.append(start)
        dx, dy = DIRS[d]
        pt = (label, start[1] + dx * length, start[2] + dy * length)
        pts.append(pt)
        by_label[label] = pt

    xs = [p[1] for p in pts]
    ys = [p[2] for p in pts]
    ox = MARGIN + 80 - min(xs) * SCALE
    oy = MARGIN - min(ys) * SCALE
    width = int((max(xs) - min(xs)) * SCALE + 2 * MARGIN + 240)
    height = int((max(ys) - min(ys)) * SCALE + 2 * MARGIN + 60)

    def P(px, py):
        return ox + px * SCALE, oy + py * SCALE

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- Generated by build_floorplan.py. Scale: 4 px = 1 inch. North is up. -->",
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="Helvetica, Arial, sans-serif">',
        f'  <rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'  <g id="north" transform="translate({width - 40},40)"><circle r="14" fill="none" stroke="#555"/>'
        '<path d="M 0 -11 L 5 7 L 0 3 L -5 7 Z" fill="#333"/><text y="-18" font-size="10" fill="#555" text-anchor="middle">N</text></g>',
    ]

    cx_in, cy_in = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    for labels, depth in COUNTERS:
        wall = [by_label[l] if isinstance(l, str) else ("", *l) for l in labels]
        normals = []
        for a, b in zip(wall, wall[1:]):
            if a[1] == b[1]:  # vertical run: offset toward room centre in x
                normals.append((1 if cx_in > a[1] else -1, 0))
            else:
                normals.append((0, 1 if cy_in > a[2] else -1))
        inner = []
        for i, p in enumerate(wall):
            nx = sum(n[0] for n in normals[max(0, i - 1):i + 1])
            ny = sum(n[1] for n in normals[max(0, i - 1):i + 1])
            inner.append((p[1] + nx * depth, p[2] + ny * depth))
        poly = [(p[1], p[2]) for p in wall] + inner[::-1]
        d_attr = " ".join(f"{'M' if i == 0 else 'L'} {P(x, y)[0]} {P(x, y)[1]}" for i, (x, y) in enumerate(poly)) + " Z"
        out.append(f'  <path id="counter-{"".join(l if isinstance(l, str) else "p" for l in labels)}" d="{d_attr}" fill="#efe6d6" stroke="#8a6a3d" stroke-width="1.5"/>')
        for i, (a, b) in enumerate(zip(wall, wall[1:])):
            # label at the middle of the longest stretch of this run not covered by a fixture
            vertical = a[1] == b[1]
            lo, hi = sorted((a[2], b[2]) if vertical else (a[1], b[1]))
            taken = []
            for f in FIXTURES:
                fa, fb = by_label[f[2]], by_label[f[3]]
                if (fa[1] == fb[1] == a[1]) if vertical else (fa[2] == fb[2] == a[2]):
                    k = 2 if vertical else 1
                    sgn = 1 if fb[k] > fa[k] else -1
                    taken.append(tuple(sorted((fa[k] + sgn * f[4], fa[k] + sgn * (f[4] + f[5])))))
            if CORNER_BASE:  # the corner cabinet also occupies the run near its corner
                cc = by_label[CORNER_BASE[0]]
                k = 2 if vertical else 1
                if (cc[1] == a[1]) if vertical else (cc[2] == a[2]):
                    sgn = 1 if (lo + hi) / 2 > cc[k] else -1
                    taken.append(tuple(sorted((cc[k], cc[k] + sgn * CORNER_BASE[1]))))
            gaps, cur = [], lo
            for t0, t1 in sorted(taken):
                if t0 > cur:
                    gaps.append((cur, min(t0, hi)))
                cur = max(cur, t1)
            if cur < hi:
                gaps.append((cur, hi))
            if not gaps:  # run fully covered by fixtures
                continue
            g0, g1 = max(gaps, key=lambda g: g[1] - g[0])
            if g1 - g0 < 30:  # not enough clear counter to fit the label
                continue
            pos = (g0 + g1) / 2
            start = a[2] if vertical else a[1]
            t = (pos - start) / ((b[2] if vertical else b[1]) - start)
            mx = a[1] + (b[1] - a[1]) * t + normals[i][0] * depth / 2
            my = a[2] + (b[2] - a[2]) * t + normals[i][1] * depth / 2
            tx, ty = P(mx, my)
            rot = f' transform="rotate(-90 {tx} {ty})"' if a[1] == b[1] else ""
            out.append(f'  <text x="{tx}" y="{ty + 4}" font-size="12" fill="#6b4f2a" text-anchor="middle"{rot}>{depth}" countertop</text>')

    for name, a_lbl, b_lbl, w, dep, *note in APPLIANCES:
        a, b = by_label[a_lbl], by_label[b_lbl]
        if a[1] == b[1]:  # vertical wall
            nx = 1 if cx_in > a[1] else -1
            sy = 1 if a[2] > b[2] else -1  # from b back toward a
            off = (abs(a[2] - b[2]) - w) / 2  # centred on the wall segment
            rx = (a[1], a[1] + nx * dep)
            ry = (b[2] + sy * off, b[2] + sy * (off + w))
        else:
            ny = 1 if cy_in > a[2] else -1
            sx = 1 if a[1] > b[1] else -1
            off = (abs(a[1] - b[1]) - w) / 2
            rx = (b[1] + sx * off, b[1] + sx * (off + w))
            ry = (a[2], a[2] + ny * dep)
        (x1, y1), (x2, y2) = P(min(rx), min(ry)), P(max(rx), max(ry))
        out.append(f'  <g id="appliance-{name.lower()}"><rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="#eef1f3" stroke="#333" stroke-width="1.5"/>'
                   + "".join(f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 + 14 * (i - len(note) / 2)}" font-size="{12 if i == 0 else 10}"'
                             f' font-weight="{700 if i == 0 else 400}" fill="#333" text-anchor="middle">{t}</text>'
                             for i, t in enumerate([name, *note, f'{w}" × {dep}"']))
                   + '</g>')

    if CORNER_PANTRY:
        c_lbl, side_v, side_h, dep = CORNER_PANTRY
        c = by_label[c_lbl]
        ix = 1 if cx_in > c[1] else -1
        iy = 1 if cy_in > c[2] else -1
        cp_pts = [(c[1], c[2]), (c[1], c[2] + iy * side_v), (c[1] + ix * dep, c[2] + iy * side_v),
                  (c[1] + ix * side_h, c[2] + iy * dep), (c[1] + ix * side_h, c[2])]
        d_attr = " ".join(f"{'M' if i == 0 else 'L'} {P(x, y)[0]} {P(x, y)[1]}" for i, (x, y) in enumerate(cp_pts)) + " Z"
        out.append(f'  <path id="corner-pantry" d="{d_attr}" fill="#dfe6ee" stroke="#333" stroke-width="1.5"/>')
        # diagonal door
        (dx1, dy1), (dx2, dy2) = P(*cp_pts[2]), P(*cp_pts[3])
        out.append(f'  <line x1="{dx1}" y1="{dy1}" x2="{dx2}" y2="{dy2}" stroke="#8a6a3d" stroke-width="3"/>')
        tx, ty = P(c[1] + ix * side_h * 0.45, c[2] + iy * side_v * 0.42)
        out.append(f'  <text x="{tx}" y="{ty - 4}" font-size="10" font-weight="700" fill="#333" text-anchor="middle">CORNER</text>'
                   f'<text x="{tx}" y="{ty + 8}" font-size="10" font-weight="700" fill="#333" text-anchor="middle">PANTRY</text>'
                   f'<text x="{tx}" y="{ty + 20}" font-size="9" fill="#555" text-anchor="middle">900/800 · 2100 H</text>')

    if CORNER_BASE:
        c_lbl, size, dep = CORNER_BASE
        c = by_label[c_lbl]
        ix = 1 if cx_in > c[1] else -1
        iy = 1 if cy_in > c[2] else -1
        cb = [(c[1], c[2]), (c[1], c[2] + iy * size), (c[1] + ix * dep, c[2] + iy * size),
              (c[1] + ix * dep, c[2] + iy * dep), (c[1] + ix * size, c[2] + iy * dep), (c[1] + ix * size, c[2])]
        d_attr = " ".join(f"{'M' if i == 0 else 'L'} {P(x, y)[0]} {P(x, y)[1]}" for i, (x, y) in enumerate(cb)) + " Z"
        out.append(f'  <path id="corner-base" d="{d_attr}" fill="none" stroke="#333" stroke-width="1.25" stroke-dasharray="5 3"/>')
        tx, ty = P(c[1] + ix * dep * 0.55, c[2] + iy * dep * 0.55)
        out.append(f'  <text x="{tx}" y="{ty - 2}" font-size="10" font-weight="700" fill="#333" text-anchor="middle">CORNER {size}"</text>'
                   f'<text x="{tx}" y="{ty + 10}" font-size="9" fill="#555" text-anchor="middle">lazy Susan</text>')

    for a_lbl, b_lbl in NO_WINDOW:
        for i, seg in enumerate(SEGMENTS):
            if {starts[i][0], seg[3]} == {a_lbl, b_lbl}:
                assert not seg[2].startswith("window"), f"{a_lbl}-{b_lbl} must not be a window"
        a, b = by_label[a_lbl], by_label[b_lbl]
        tx, ty = P((a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
        out.append(f'  <text x="{tx}" y="{ty + 14}" font-size="10" font-style="italic" fill="#c0392b" text-anchor="middle">no window</text>')

    for a_lbl, b_lbl, dep, step, txt in PLATFORMS:
        a, b = by_label[a_lbl], by_label[b_lbl]
        if a[1] == b[1]:
            nx = 1 if cx_in > a[1] else -1
            (x1, y1), (x2, y2) = P(min(a[1], a[1] + nx * dep), min(a[2], b[2])), P(max(a[1], a[1] + nx * dep), max(a[2], b[2]))
            sx = P(a[1] + nx * step, 0)[0]
            out.append(f'  <line x1="{sx}" y1="{y1}" x2="{sx}" y2="{y2}" stroke="#8a6a3d" stroke-width="1" stroke-dasharray="2 3"/>')
            tx = P(a[1] + nx * (dep + 3), 0)[0]
            out.append(f'  <text x="{tx}" y="{(y1 + y2) / 2}" font-size="10" fill="#6b4f2a" text-anchor="middle" transform="rotate(-90 {tx} {(y1 + y2) / 2})">{txt}</text>')
        else:
            ny = 1 if cy_in > a[2] else -1
            (x1, y1), (x2, y2) = P(min(a[1], b[1]), min(a[2], a[2] + ny * dep)), P(max(a[1], b[1]), max(a[2], a[2] + ny * dep))
        out.append(f'  <rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="none" stroke="#8a6a3d" stroke-width="1.5" stroke-dasharray="6 3"/>')

    def upper_rect(lbl_a, lbl_b, off, w, dep):
        a, b = by_label[lbl_a], by_label[lbl_b]
        if a[1] == b[1]:
            nx = 1 if cx_in > a[1] else -1
            sy = 1 if b[2] > a[2] else -1
            return (a[1], a[1] + nx * dep), (a[2] + sy * off, a[2] + sy * (off + w))
        ny = 1 if cy_in > a[2] else -1
        sx = 1 if b[1] > a[1] else -1
        return (a[1] + sx * off, a[1] + sx * (off + w)), (a[2], a[2] + ny * dep)

    def emit_upper(points, lbl, tx, ty):
        d_attr = " ".join(f"{'M' if i == 0 else 'L'} {P(x, y)[0]} {P(x, y)[1]}" for i, (x, y) in enumerate(points)) + " Z"
        out.append(f'  <path d="{d_attr}" fill="none" stroke="#2e6f9e" stroke-width="1.25" stroke-dasharray="2 2"/>')
        cx_, cy_ = P(tx, ty)
        out.append(f'  <text x="{cx_}" y="{cy_ + 4}" font-size="10" font-weight="700" fill="#2e6f9e" text-anchor="middle">{lbl}</text>')

    upper_labels = []
    for lbl, a_lbl, b_lbl, off, w in UPPERS:
        rx, ry = upper_rect(a_lbl, b_lbl, off, w, UPPER_DEPTH)
        pts4 = [(rx[0], ry[0]), (rx[1], ry[0]), (rx[1], ry[1]), (rx[0], ry[1])]
        upper_labels.append((pts4, lbl, (rx[0] + rx[1]) / 2, (ry[0] + ry[1]) / 2))
    if UPPER_CORNER:
        lbl, c_lbl, size = UPPER_CORNER
        c = by_label[c_lbl]
        ix = 1 if cx_in > c[1] else -1
        iy = 1 if cy_in > c[2] else -1
        dp = UPPER_DEPTH
        pts6 = [(c[1], c[2]), (c[1], c[2] + iy * size), (c[1] + ix * dp, c[2] + iy * size),
                (c[1] + ix * dp, c[2] + iy * dp), (c[1] + ix * size, c[2] + iy * dp), (c[1] + ix * size, c[2])]
        upper_labels.append((pts6, lbl, c[1] + ix * dp * 0.5, c[2] + iy * dp * 0.5))

    for kind, name, a_lbl, b_lbl, off, w, dep in FIXTURES:
        a, b = by_label[a_lbl], by_label[b_lbl]
        if a[1] == b[1]:
            nx = 1 if cx_in > a[1] else -1
            sy = 1 if b[2] > a[2] else -1
            rx, ry = (a[1], a[1] + nx * dep), (a[2] + sy * off, a[2] + sy * (off + w))
        else:
            ny = 1 if cy_in > a[2] else -1
            sx = 1 if b[1] > a[1] else -1
            rx, ry = (a[1] + sx * off, a[1] + sx * (off + w)), (a[2], a[2] + ny * dep)
        (x1, y1), (x2, y2) = P(min(rx), min(ry)), P(max(rx), max(ry))
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        g = [f'  <g id="{kind}-{(name.split() or ["base"])[0].split("|")[0].lower()}">']
        if kind == "range":
            g.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="#e9e9e9" stroke="#333" stroke-width="1.5"/>')
            bw, bh = (x2 - x1) / 4, (y2 - y1) / 4
            for fx in (1, 3):
                for fy in (1, 3):
                    g.append(f'<circle cx="{x1 + fx * bw}" cy="{y1 + fy * bh}" r="{min(bw, bh) * 0.45}" fill="none" stroke="#333"/>')
        elif kind == "hood":
            g.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="none" stroke="#c0392b" stroke-width="1.25" stroke-dasharray="6 4"/>')
        elif kind == "onc":  # appliance sitting on the countertop
            g.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="4" fill="#f7f7f7" stroke="#333" stroke-width="1.25"/>')
        elif kind == "rack":
            g.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="none" stroke="#2e6f9e" stroke-width="1.25" stroke-dasharray="6 4"/>')
        elif kind == "sink":
            g.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="10" fill="#fff" stroke="#333" stroke-width="1.5"/>'
                     f'<rect x="{x1 + 8}" y="{y1 + 8}" width="{x2 - x1 - 16}" height="{y2 - y1 - 16}" rx="8" fill="none" stroke="#999"/>')
        else:
            g.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="none" stroke="#333" stroke-width="1.25" stroke-dasharray="5 3"/>')
        if kind not in ("hood", "rack"):
            vertical = a[1] == b[1]
            rot = f' transform="rotate(-90 {cx} {cy})"' if vertical and kind in ("range", "sink", "onc", "under") else ""
            title, _, sub = name.partition("|")
            if kind == "under" and title and not sub:
                # fit the label inside the box: drop the description if it is too long
                room_px = (y2 - y1) if vertical else (x2 - x1)
                if len(f'{title} {w}"') * 6.6 > room_px - 6:
                    title = title.split()[0]
            if title:
                dy = -4 if sub else 4
                tx_, ty_ = (cx + dy, cy) if rot else (cx, cy + dy)
                rot_ = f' transform="rotate(-90 {tx_} {ty_})"' if rot else ""
                g.append(f'<text x="{tx_}" y="{ty_}" font-size="11" font-weight="700" fill="#333" text-anchor="middle"{rot_}>{title}{"" if kind == "onc" else f" {w}\""}</text>')
            if sub:
                tx_, ty_ = (cx + 12, cy) if rot else (cx, cy + 16)
                rot_ = f' transform="rotate(-90 {tx_} {ty_})"' if rot else ""
                g.append(f'<text x="{tx_}" y="{ty_}" font-size="9" fill="#555" text-anchor="middle"{rot_}>{sub}</text>')
        else:
            # overhead items: label just beyond the counter front, in the room
            colour = "#c0392b" if kind == "hood" else "#2e6f9e"
            if a[1] == b[1]:
                tx, ty = P(a[1] + nx * 28, 0)[0], cy + 4
                anchor = "end" if nx < 0 else "start"
            else:
                tx, ty = cx, P(0, a[2] + ny * 29)[1] + (4 if ny > 0 else 0)
                anchor = "middle"
            g.append(f'<text x="{tx}" y="{ty}" font-size="10" fill="{colour}" text-anchor="{anchor}">{name}</text>')
        g.append('</g>')
        out.append("".join(g))

    for pts_, lbl, tx, ty in upper_labels:
        emit_upper(pts_, lbl, tx, ty)

    def seg_dim(x1, y1, x2, y2, vertical, text, force=None):
        if vertical:
            side = force or (1 if (x1 - ox) / SCALE >= (min(xs) + max(xs)) / 2 else -1)  # keep dims outside the room
            dx_ = x1 + side * (30 if force else DIM_OFFSET + 30)  # forced dims hug the wall
            mid = (y1 + y2) / 2
            out.append(f'  <g stroke="#888"><line x1="{dx_}" y1="{y1}" x2="{dx_}" y2="{y2}"/>'
                       f'<line x1="{dx_-6}" y1="{y1}" x2="{dx_+6}" y2="{y1}"/><line x1="{dx_-6}" y1="{y2}" x2="{dx_+6}" y2="{y2}"/></g>')
            out.append(f'  <text x="{dx_+16*side}" y="{mid}" font-size="12" fill="#444" text-anchor="middle" transform="rotate({90*side} {dx_+16*side} {mid})">{text}</text>')
        else:
            vside = force or (1 if (y1 - oy) / SCALE >= (min(ys) + max(ys)) / 2 else -1)
            dy_ = y1 + vside * DIM_OFFSET
            mid = (x1 + x2) / 2
            out.append(f'  <g stroke="#888"><line x1="{x1}" y1="{dy_}" x2="{x2}" y2="{dy_}"/>'
                       f'<line x1="{x1}" y1="{dy_-6}" x2="{x1}" y2="{dy_+6}"/><line x1="{x2}" y1="{dy_-6}" x2="{x2}" y2="{dy_+6}"/></g>')
            out.append(f'  <text x="{mid}" y="{dy_+(16 if vside > 0 else -8)}" font-size="12" fill="#444" text-anchor="middle">{text}</text>')

    for i, seg in enumerate(SEGMENTS):
        d, length, kind, label = seg[:4]
        kind, _, name = kind.partition(":")
        name = name or LABELS.get(kind, kind)
        a, b = starts[i], pts[i + 1]
        x1, y1 = P(a[1], a[2])
        x2, y2 = P(b[1], b[2])
        vertical = d in "NS"
        seg_id = f"{kind}-{a[0]}{b[0]}"
        if kind == "wall":
            out.append(f'  <line id="{seg_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2b2b2b" stroke-width="8"/>')
        elif kind == "door":
            # Door shown as a gap with jambs (no swing drawn).
            jx, jy = (6, 0) if vertical else (0, 6)
            out.append(f'  <g id="{seg_id}" stroke="#2b2b2b"><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#8a6a3d" stroke-width="2"/>'
                       f'<line x1="{x1-jx}" y1="{y1-jy}" x2="{x1+jx}" y2="{y1+jy}" stroke-width="3"/>'
                       f'<line x1="{x2-jx}" y1="{y2-jy}" x2="{x2+jx}" y2="{y2+jy}" stroke-width="3"/></g>')
        elif kind == "opening":
            jx, jy = (6, 0) if vertical else (0, 6)
            out.append(f'  <g id="{seg_id}" stroke="#2b2b2b"><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#999" stroke-dasharray="6 5"/>'
                       f'<line x1="{x1-jx}" y1="{y1-jy}" x2="{x1+jx}" y2="{y1+jy}" stroke-width="3"/>'
                       f'<line x1="{x2-jx}" y1="{y2-jy}" x2="{x2+jx}" y2="{y2+jy}" stroke-width="3"/></g>')
        else:
            rx, ry = min(x1, x2) - (4 if vertical else 0), min(y1, y2) - (0 if vertical else 4)
            rw, rh = (8, abs(y2 - y1)) if vertical else (abs(x2 - x1), 8)
            out.append(f'  <g id="{seg_id}"><rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="#fff" stroke="#2b2b2b"/>'
                       f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4a6b80" stroke-width="2"/></g>')
        # dimension (segments touching a hidden "_" point are dimensioned by SPANS instead)
        if not (a[0].startswith("_") or b[0].startswith("_")):
            text = f'{length}"' if length < 12 else f'{length}" {name}'  # short segments: number only
            seg_dim(x1, y1, x2, y2, vertical, text, DIM_SIDE.get(b[0]))

    for a_lbl, b_lbl, text in SPANS:
        a, b = by_label[a_lbl], by_label[b_lbl]
        (x1, y1), (x2, y2) = P(a[1], a[2]), P(b[1], b[2])
        seg_dim(x1, y1, x2, y2, x1 == x2, text)

    for a_lbl, b_lbl in TOTALS:
        a, b = by_label[a_lbl], by_label[b_lbl]
        x1, y1 = P(a[1], a[2])
        x2, y2 = P(b[1], b[2])
        inches = abs(b[1] - a[1]) + abs(b[2] - a[2])
        ft, rem = divmod(inches, 12)
        text = f"{a_lbl}–{b_lbl}: {f"{inches / 12:.2f}".rstrip("0").rstrip(".")} linear ft ({int(ft)}′-{rem:g}″)"
        if x1 == x2:
            side = DIM_SIDE.get(f"{a_lbl}-{b_lbl}") or (1 if (x1 - ox) / SCALE >= (min(xs) + max(xs)) / 2 else -1)
            dx_ = x1 + side * (DIM_OFFSET + 90)
            mid = (y1 + y2) / 2
            out.append(f'  <g stroke="#c0392b"><line x1="{dx_}" y1="{y1}" x2="{dx_}" y2="{y2}"/>'
                       f'<line x1="{dx_-8}" y1="{y1}" x2="{dx_+8}" y2="{y1}"/><line x1="{dx_-8}" y1="{y2}" x2="{dx_+8}" y2="{y2}"/></g>')
            out.append(f'  <text x="{dx_+18*side}" y="{mid}" font-size="13" font-weight="700" fill="#c0392b" text-anchor="middle" transform="rotate({90*side} {dx_+18*side} {mid})">{text}</text>')
        else:
            vside = 1 if (y1 - oy) / SCALE >= (min(ys) + max(ys)) / 2 else -1
            dy_ = y1 + vside * (DIM_OFFSET + 50)
            mid = (x1 + x2) / 2
            out.append(f'  <g stroke="#c0392b"><line x1="{x1}" y1="{dy_}" x2="{x2}" y2="{dy_}"/>'
                       f'<line x1="{x1}" y1="{dy_-8}" x2="{x1}" y2="{dy_+8}"/><line x1="{x2}" y1="{dy_-8}" x2="{x2}" y2="{dy_+8}"/></g>')
            out.append(f'  <text x="{mid}" y="{dy_+(18 if vside > 0 else -8)}" font-size="13" font-weight="700" fill="#c0392b" text-anchor="middle">{text}</text>')

    for title, sub, lbls, shift in ROOMS:
        cxr = sum(by_label[l][1] for l in lbls) / len(lbls) + shift
        cyr = sum(by_label[l][2] for l in lbls) / len(lbls)
        tx, ty = P(cxr, cyr)
        out.append(f'  <text x="{tx}" y="{ty}" font-size="14" font-weight="700" fill="#555" text-anchor="middle" letter-spacing="2">{title}</text>'
                   f'<text x="{tx}" y="{ty + 16}" font-size="11" fill="#777" text-anchor="middle">{sub}</text>')

    out.append('  <g font-size="14" font-weight="700" fill="#c0392b">')
    drawn = set()
    for label, px, py in pts:
        if label.startswith("_") or label in drawn:  # construction point, or already drawn
            continue
        drawn.add(label)
        cx, cy = P(px, py)
        out.append(f'    <circle cx="{cx}" cy="{cy}" r="5"/><text x="{cx + 10}" y="{cy - 10}">{label}</text>')
    out.append("  </g>")
    out.append("</svg>")
    Path(__file__).with_name("floorplan.svg").write_text("\n".join(out) + "\n")
    return width, height


# Wall elevations (viewed from inside the room). Heights in inches from the floor.
WINDOW_SILL, WINDOW_HEIGHT = 46.5, 36  # default for every window
WINDOW_SIZES = {}  # per window, keyed by the window segment's end label: (sill, height)
COUNTER_HEIGHT = 36
# (file, title, points along the wall in viewing order, ceiling height at first point, at last point)
ELEVATIONS = [
    ("east_elevation.svg", "East wall elevation (A–H), viewed from inside facing east",
     ["A", "B", "C", "D", "E", "F", "G", "H"], 96, 96,
     {"uppers": [  # (from point, offset start, offset end, bottom, top, title, subtitle, glass)
         ("A", 48.5, 84.5, 66, 73, "HOOD 36\"", "under-cabinet, vents out east wall", False),
         ("A", 48.5, 84.5, 74, 94, "U3 · 36\" LIFT-UP", "solid front (grease)", False),
         ("A", 133, 151, 54, 74, "U1", "glass lift-up", True),
         ("A", 133, 151, 74, 94, "U1", "lift-up", False),
         ("A", 151, 177, 54, 94, "U2 CORNER", "glass doors", True)]}),
    ("south_elevation.svg", "South wall elevation (H–K), viewed from inside facing south",
     ["H", "I", "_w1", "_w2", "J", "K"], 96, 100,
     {"uppers": [
         ("H", 0, 26, 54, 94, "U2 CORNER", "glass doors", True),
         ("H", 26, 44, 54, 74, "U4", "glass lift-up", True),
         ("H", 26, 44, 74, 94, "U4", "lift-up", False),
         ("H", 81, 105, 54, 74, "U5", "glass lift-up", True),
         ("H", 81, 105, 74, 94, "U5", "lift-up", False),
         ("H", 105, 123, 54, 74, "U6", "glass lift-up", True),
         ("H", 105, 123, 74, 94, "U6", "lift-up", False)]}),
    ("west_elevation.svg", "West wall elevation (K–R), viewed from inside facing west",
     ["K", "L", "M", "N", "O", "P", "Q", "R"], 100, 100,
     {"project": True,  # N-O is a return wall: O-R sits 40.5" further west
      "platforms": [("P", "R", 9, "")],
      "box_drawers": [("P", 0, 24), ("P", 24, 48), ("Q", 0, 30)],  # toe-kick drawers in the box front
      "openings": {"M": 80},  # opening height assumed
      "zones": [("O", "P", 0, 72, "FRIDGE (French door)", '41" space · 72" tall (assumed)'),
                ("O", "P", 79, 99, "10 · CABINET ABOVE FRIDGE", '36"W × 24"D × 20"H · fillers each side'),
                ("P", "Q", 9, 99, "11 + 12 · APPLIANCE GARAGE", "2 × 24\"W × 24\"D × 90\"H tall cabinets"),
                ("Q", "R", 9, 37, "13 · GE CONV. OVEN", "28\" tall, on the box"),
                ("Q", "R", 37, 38, "", ""),
                ("Q", "R", 38, 56, "COFFEE", "counter at 38\""),
                ("Q", "R", 56, 71, "MICROWAVE", "bottom at 56\""),
                ("Q", "R", 71, 99, "STORAGE DOORS", "from 71\" to 99\"")]}),]


def build_elevation(filename, title, labels, ceil0, ceil1, opts=None):
    opts = opts or {}
    pts = {START[0]: (START[1], START[2])}
    kinds = {}
    for seg in SEGMENTS:
        d, length, kind, label = seg[:4]
        a = pts[seg[4]] if len(seg) > 4 else list(pts.values())[-1]
        dx, dy = DIRS[d]
        pts[label] = (a[0] + dx * length, a[1] + dy * length)
        kinds[label] = kind
    along = [0.0]
    for p, q in zip(labels, labels[1:]):
        if opts.get("project"):  # flat projection onto the wall's main axis; return walls collapse
            along.append(along[-1] + abs(pts[q][1] - pts[p][1]))
        else:
            along.append(along[-1] + abs(pts[q][0] - pts[p][0]) + abs(pts[q][1] - pts[p][1]))
    pos = dict(zip(labels, along))
    total = along[-1]
    hmax = max(ceil0, ceil1)
    ceil = lambda t: ceil0 + (ceil1 - ceil0) * t / total
    m, top = 90, 80
    w = int(total * SCALE + 2 * m + 80)
    h = int(hmax * SCALE + top + 150)
    X = lambda t: m + t * SCALE
    Y = lambda z: top + (hmax - z) * SCALE
    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Helvetica, Arial, sans-serif">',
         f'  <rect width="{w}" height="{h}" fill="#fff"/>',
         f'  <text x="{m}" y="30" font-size="16" font-weight="700" fill="#222">{title}</text>',
         f'  <text x="{m}" y="50" font-size="11" fill="#555">Ceiling {ceil0:g}"{"" if ceil0 == ceil1 else f" rising to {ceil1:g}" + chr(34)} · counter {COUNTER_HEIGHT}" · scale 4 px = 1"</text>',
         f'  <path d="M {X(0)} {Y(0)} L {X(0)} {Y(ceil0)} L {X(total)} {Y(ceil1)} L {X(total)} {Y(0)} Z" fill="#f7f4ee" stroke="#2b2b2b" stroke-width="3"/>']
    sills = set()
    for i, (p, q) in enumerate(zip(labels, labels[1:])):
        kind = kinds[q].partition(":")[0]
        if kind != "window":
            continue
        sill, wh = WINDOW_SIZES.get(q, (WINDOW_SILL, WINDOW_HEIGHT))
        sills.add((sill, wh))
        t0, t1 = along[i], along[i + 1]
        o.append(f'  <rect x="{X(t0)}" y="{Y(sill + wh)}" width="{(t1 - t0) * SCALE}" height="{wh * SCALE}" fill="#dceaf3" stroke="#4a6b80" stroke-width="2"/>')
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(sill + wh / 2)}" font-size="11" fill="#2e4a5c" text-anchor="middle">WINDOW {t1 - t0:g}" × {wh:g}"</text>')
    for i, (p, q) in enumerate(zip(labels, labels[1:])):
        if q in opts.get("openings", {}):
            oh = opts["openings"][q]
            t0, t1 = along[i], along[i + 1]
            o.append(f'  <rect x="{X(t0)}" y="{Y(oh)}" width="{(t1 - t0) * SCALE}" height="{oh * SCALE}" fill="#fff" stroke="#999" stroke-dasharray="6 4"/>')
            o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(oh / 2)}" font-size="11" fill="#555" text-anchor="middle">OPENING {t1 - t0:g}"</text>'
                     f'<text x="{X((t0 + t1) / 2)}" y="{Y(oh / 2) + 14}" font-size="9" fill="#777" text-anchor="middle">no door · {oh}" high (assumed)</text>')
    for a_lbl, b_lbl, ph, txt in opts.get("platforms", []):  # raised floor box
        t0, t1 = sorted((pos[a_lbl], pos[b_lbl]))
        o.append(f'  <rect x="{X(t0)}" y="{Y(ph)}" width="{(t1 - t0) * SCALE}" height="{ph * SCALE}" fill="#d9c3a0" stroke="#8a6a3d" stroke-width="1.5"/>')
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(ph / 2) + 4}" font-size="10" fill="#5a4320" text-anchor="middle">{txt}</text>')
    for lbl, d0, d1, z0, z1, ttl, sub, glass in opts.get("uppers", []):
        sgn = 1 if along[-1] > pos[lbl] else -1
        t0, t1 = sorted((pos[lbl] + sgn * d0, pos[lbl] + sgn * d1))
        fill = "#d6e8f2" if glass else "#efe9df"
        o.append(f'  <rect x="{X(t0) + 1}" y="{Y(z1)}" width="{(t1 - t0) * SCALE - 2}" height="{(z1 - z0) * SCALE}" fill="{fill}" stroke="#2e6f9e" stroke-width="1.25"/>')
        if glass:
            o.append(f'  <rect x="{X(t0) + 7}" y="{Y(z1) + 6}" width="{(t1 - t0) * SCALE - 14}" height="{(z1 - z0) * SCALE - 12}" fill="none" stroke="#7fa7c0"/>')
        zc = (z0 + z1) / 2
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(zc)}" font-size="10" font-weight="700" fill="#1f4e6b" text-anchor="middle">{ttl}</text>')
        if (t1 - t0) * SCALE > len(sub) * 5.2:
            o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(zc) + 12}" font-size="9" fill="#2e4a5c" text-anchor="middle">{sub}</text>')
    for lbl, d0, d1 in opts.get("box_drawers", []):
        ph = opts["platforms"][0][2]
        sgn = 1 if along[-1] > pos[lbl] else -1
        t0, t1 = sorted((pos[lbl] + sgn * d0, pos[lbl] + sgn * d1))
        o.append(f'  <rect x="{X(t0) + 2}" y="{Y(ph) + 3}" width="{(t1 - t0) * SCALE - 4}" height="{ph * SCALE - 6}" fill="#e6d3b3" stroke="#8a6a3d"/>')
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(ph / 2) + 4}" font-size="9" fill="#5a4320" text-anchor="middle">{t1 - t0:g}" drawer</text>')
    for a_lbl, b_lbl, z0, z1, ztitle, zsub in opts.get("zones", []):
        t0, t1 = sorted((pos[a_lbl], pos[b_lbl]))
        o.append(f'  <rect x="{X(t0) + 3}" y="{Y(z1) + 3}" width="{(t1 - t0) * SCALE - 6}" height="{(z1 - z0) * SCALE - 6}" fill="#eef1f3" fill-opacity="0.6" stroke="#333" stroke-width="1.25" stroke-dasharray="6 4"/>')
        zc = (z0 + z1) / 2
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(zc)}" font-size="11" font-weight="700" fill="#333" text-anchor="middle">{ztitle}</text>'
                 f'<text x="{X((t0 + t1) / 2)}" y="{Y(zc) + 14}" font-size="9" fill="#555" text-anchor="middle">{zsub}</text>')
    for kind, name, a_lbl, b_lbl, off, fw, dep in FIXTURES:
        if a_lbl not in pos or b_lbl not in pos or kind not in ("range", "sink", "under"):
            continue
        if kind == "under":
            if not name:
                continue
            sgn = 1 if pos[b_lbl] > pos[a_lbl] else -1
            t0, t1 = sorted((pos[a_lbl] + sgn * off, pos[a_lbl] + sgn * (off + fw)))
            ch = COUNTER_HEIGHT - 1.5  # cabinet top, under a 1.5" countertop
            o.append(f'  <rect x="{X(t0) + 1}" y="{Y(ch)}" width="{(t1 - t0) * SCALE - 2}" height="{(ch - 4.5) * SCALE}" fill="#f1ede6" stroke="#333" stroke-dasharray="5 3"/>')
            label = name if len(name) * 6.6 < (t1 - t0) * SCALE - 6 else name.split()[0]
            o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(ch / 2)}" font-size="11" font-weight="700" fill="#333" text-anchor="middle">{label}</text>'
                     f'<text x="{X((t0 + t1) / 2)}" y="{Y(ch / 2) + 14}" font-size="10" fill="#555" text-anchor="middle">{fw:g}"</text>')
            continue
        sgn = 1 if pos[b_lbl] > pos[a_lbl] else -1
        t0, t1 = sorted((pos[a_lbl] + sgn * off, pos[a_lbl] + sgn * (off + fw)))
        title_ = name.split("|")[0]
        if kind == "range":
            o.append(f'  <rect x="{X(t0)}" y="{Y(COUNTER_HEIGHT) - 6}" width="{(t1 - t0) * SCALE}" height="6" fill="#555"/>')
        else:  # sink bowl below the counter line
            o.append(f'  <path d="M {X(t0)} {Y(COUNTER_HEIGHT)} L {X(t0) + 6} {Y(COUNTER_HEIGHT - 9)} L {X(t1) - 6} {Y(COUNTER_HEIGHT - 9)} L {X(t1)} {Y(COUNTER_HEIGHT)}" fill="#fff" stroke="#555" stroke-width="2"/>')
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(COUNTER_HEIGHT) - 12}" font-size="11" font-weight="700" fill="#333" text-anchor="middle">{title_} {fw:g}" (at {COUNTER_HEIGHT}" counter height)</text>')
    vis = []
    for t, l in zip(along, labels):
        if l.startswith("_"):
            continue
        if vis and abs(vis[-1][0] - t) < 1e-6:  # return wall: both ends project to one spot
            vis[-1] = (t, vis[-1][1] + "/" + l)
        else:
            vis.append((t, l))
    for t, lbl in vis:
        o.append(f'  <line x1="{X(t)}" y1="{Y(0)}" x2="{X(t)}" y2="{Y(0) + 40}" stroke="#aaa" stroke-dasharray="3 3"/>')
        o.append(f'  <text x="{X(t)}" y="{Y(0) + 56}" font-size="14" font-weight="700" fill="#c0392b" text-anchor="middle">{lbl}</text>')
    for (t0, _), (t1, _) in zip(vis, vis[1:]):
        o.append(f'  <line x1="{X(t0)}" y1="{Y(0) + 24}" x2="{X(t1)}" y2="{Y(0) + 24}" stroke="#888"/>')
        o.append(f'  <text x="{X((t0 + t1) / 2)}" y="{Y(0) + 18}" font-size="11" fill="#444" text-anchor="middle">{t1 - t0:g}"</text>')
    o.append(f'  <line x1="{X(0)}" y1="{Y(0) + 80}" x2="{X(total)}" y2="{Y(0) + 80}" stroke="#c0392b"/>')
    o.append(f'  <text x="{X(total / 2)}" y="{Y(0) + 98}" font-size="13" font-weight="700" fill="#c0392b" text-anchor="middle">{labels[0]}–{labels[-1]}: {total:g}" ({int(total // 12)}′-{total % 12:g}″)</text>')
    # ceiling heights at each end
    for t, c, side in ((0, ceil0, -1), (total, ceil1, 1)):
        vx = X(t) + side * 40
        o.append(f'  <line x1="{vx}" y1="{Y(0)}" x2="{vx}" y2="{Y(c)}" stroke="#888"/>'
                 f'<line x1="{vx - 5}" y1="{Y(c)}" x2="{vx + 5}" y2="{Y(c)}" stroke="#888"/>')
        tx = vx + side * 12
        o.append(f'  <text x="{tx}" y="{(Y(0) + Y(c)) / 2}" font-size="11" fill="#444" text-anchor="middle" transform="rotate({90 * side} {tx} {(Y(0) + Y(c)) / 2})">{c:g}" floor to ceiling</text>')
    # window sill / head heights, just inside the first window
    for sill, wh in sorted(sills):
        rx = X(total) + 70
        for z0, z1 in [(0, sill), (sill, sill + wh)]:
            o.append(f'  <line x1="{rx}" y1="{Y(z0)}" x2="{rx}" y2="{Y(z1)}" stroke="#4a6b80"/>'
                     f'<line x1="{rx - 5}" y1="{Y(z1)}" x2="{rx + 5}" y2="{Y(z1)}" stroke="#4a6b80"/>')
            o.append(f'  <text x="{rx + 14}" y="{(Y(z0) + Y(z1)) / 2}" font-size="11" fill="#2e4a5c" text-anchor="middle" transform="rotate(90 {rx + 14} {(Y(z0) + Y(z1)) / 2})">{"sill " if z0 == 0 else "window "}{z1 - z0:g}"</text>')
    o.append(f'  <line x1="{X(0) - 10}" y1="{Y(0)}" x2="{X(total) + 10}" y2="{Y(0)}" stroke="#2b2b2b" stroke-width="4"/>')
    o.append("</svg>")
    Path(__file__).with_name(filename).write_text("\n".join(o) + "\n")
    return w, h


# Pantry layout: plan + back-wall elevation (inside dimensions, walls ~4.5" thick)
PANTRY_CEILING = 100
PANTRY_SHELVES = [6, 24, 36, 48, 60, 72, 84]  # back-wall shelf heights; 6" = slatted bag platform
PANTRY_ZONES = [  # (bottom, top, title, items)
    (0, 6, "BAG PLATFORM", "unopened 20–40 lb rice & atta bags, slatted"),
    (6, 24, "ROLLING BINS", "rice bin · atta bin (25–40 lb) · oil tins · jaggery"),
    (24, 60, "DAILY STAPLES", "dals · spice refills · tea · sugar · rava · poha · besan"),
    (60, 84, "WEEKLY", "namkeen · biscuits · pickles · ghee · papad · dry fruits"),
    (84, 100, "OCCASIONAL", "big pressure cooker · large kadai · festival & puja items"),
]


BIN_Y = (34, 48)  # plan: bins 12" along the back wall, measured from the north inside face


def build_pantry():
    S = 7  # px per inch for this sheet
    wall = 4.5
    W_in, D_in = 36, 61  # inside: east-west, north-south
    back, side_s, side_n = 16, 12, 6  # shelf depths: back (west), south side, north side
    ox, oy = 70, 110
    X = lambda x: ox + x * S   # x: inches from inside face of west (back) wall, eastward
    Yp = lambda y: oy + y * S  # y: inches from inside face of north wall, southward
    o = []
    # --- plan ---
    o.append(f'<text x="{ox - 30}" y="40" font-size="18" font-weight="700" fill="#222">Pantry layout</text>')
    o.append(f'<text x="{ox - 30}" y="62" font-size="11" fill="#555">Walk-in, about 36" × 61" inside · entrance from the kitchen through the 29" L–M opening · ceiling {PANTRY_CEILING}"</text>')
    o.append(f'<text x="{ox - 30}" y="{oy - 22}" font-size="13" font-weight="700" fill="#333">PLAN (north up)</text>')
    t = wall * S
    o.append(f'<rect x="{X(-wall)}" y="{Yp(-wall)}" width="{(W_in + 2 * wall) * S}" height="{(D_in + 2 * wall) * S}" fill="#2b2b2b"/>')
    o.append(f'<rect x="{X(0)}" y="{Yp(0)}" width="{W_in * S}" height="{D_in * S}" fill="#f7f4ee"/>')
    # opening in east wall: 29" wide, starting ~6" south of the inside north face (8" stub minus wall)
    op0, op1 = 8 - wall / 2 - 0.25, 8 - wall / 2 - 0.25 + 29
    o.append(f'<rect x="{X(W_in) - 1}" y="{Yp(op0)}" width="{t + 2}" height="{(op1 - op0) * S}" fill="#fff"/>')
    o.append(f'<text x="{X(W_in) + t + 8}" y="{Yp((op0 + op1) / 2)}" font-size="11" fill="#555" transform="rotate(90 {X(W_in) + t + 8} {Yp((op0 + op1) / 2)})" text-anchor="middle">29" opening from kitchen →</text>')
    # shelves
    def shelf(x0, y0, x1, y1, fill, label, sub=""):
        o.append(f'<rect x="{X(x0)}" y="{Yp(y0)}" width="{(x1 - x0) * S}" height="{(y1 - y0) * S}" fill="{fill}" stroke="#8a6a3d" stroke-width="1.5"/>')
        cx, cy = X((x0 + x1) / 2), Yp((y0 + y1) / 2)
        vert = (y1 - y0) > (x1 - x0) * 1.5
        rot = f' transform="rotate(-90 {cx} {cy})"' if vert else ""
        o.append(f'<text x="{cx}" y="{cy - (2 if sub else -4)}" font-size="11" font-weight="700" fill="#5a4320" text-anchor="middle"{rot}>{label}</text>')
        if sub:
            cx2, cy2 = (cx + 13, cy) if vert else (cx, cy + 12)
            rot2 = f' transform="rotate(-90 {cx2} {cy2})"' if vert else ""
            o.append(f'<text x="{cx2}" y="{cy2}" font-size="9" fill="#6b4f2a" text-anchor="middle"{rot2}>{sub}</text>')
    o.append(f'<rect x="{X(0)}" y="{Yp(0)}" width="{back * S}" height="{D_in * S}" fill="#e9d8b8" stroke="#8a6a3d" stroke-width="1.5"/>')
    lx, ly = X(back / 2), Yp(BIN_Y[0] / 2)
    o.append(f'<text x="{lx - 4}" y="{ly}" font-size="11" font-weight="700" fill="#5a4320" text-anchor="middle" transform="rotate(-90 {lx - 4} {ly})">BACK WALL SHELVES · 16" deep</text>'
             f'<text x="{lx + 12}" y="{ly}" font-size="9" fill="#6b4f2a" text-anchor="middle" transform="rotate(-90 {lx + 12} {ly})">staples at eye level · bins on the floor</text>')
    shelf(back, 0, W_in, side_n, "#f1e6d0", 'SPICES 6"')
    shelf(back, D_in - side_s, W_in, D_in, "#f1e6d0", 'COOKWARE 12"', "grinder · cookers · pegboard")
    # rolling bins (plan, dashed) on the floor zone of the back wall
    for y0 in (BIN_Y[0], BIN_Y[1]):
        o.append(f'<rect x="{X(1)}" y="{Yp(y0)}" width="{14 * S}" height="{12 * S}" fill="#dceaf3" fill-opacity="0.5" stroke="#2e6f9e" stroke-dasharray="4 3"/>')
    o.append(f'<text x="{X(8)}" y="{Yp(BIN_Y[0] + 6) + 3}" font-size="9" fill="#1f4e6b" text-anchor="middle">ATTA bin</text>'
             f'<text x="{X(8)}" y="{Yp(BIN_Y[1] + 6) + 3}" font-size="9" fill="#1f4e6b" text-anchor="middle">RICE bin</text>')
    # aisle + hooks
    o.append(f'<text x="{X((back + W_in) / 2)}" y="{Yp(D_in / 2 - 4)}" font-size="11" fill="#777" text-anchor="middle">standing</text>'
             f'<text x="{X((back + W_in) / 2)}" y="{Yp(D_in / 2 - 2)}" font-size="11" fill="#777" text-anchor="middle">aisle</text>'
             f'<text x="{X((back + W_in) / 2)}" y="{Yp(D_in / 2 + 1)}" font-size="10" fill="#999" text-anchor="middle">{W_in - back}" × {D_in - side_s - side_n}"</text>')
    for y in (op1 + 3, op1 + 7, op1 + 11):
        o.append(f'<circle cx="{X(W_in) - 6}" cy="{Yp(y)}" r="4" fill="#555"/>')
    o.append(f'<text x="{X(W_in) - 14}" y="{Yp(op1 + 7) + 4}" font-size="9" fill="#555" text-anchor="end">hooks: broom · mop · stool</text>')
    # plan dims
    o.append(f'<line x1="{X(0)}" y1="{Yp(D_in + wall) + 18}" x2="{X(W_in)}" y2="{Yp(D_in + wall) + 18}" stroke="#888"/>'
             f'<text x="{X(W_in / 2)}" y="{Yp(D_in + wall) + 34}" font-size="11" fill="#444" text-anchor="middle">{W_in}" inside</text>')
    o.append(f'<line x1="{X(-wall) - 18}" y1="{Yp(0)}" x2="{X(-wall) - 18}" y2="{Yp(D_in)}" stroke="#888"/>'
             f'<text x="{X(-wall) - 26}" y="{Yp(D_in / 2)}" font-size="11" fill="#444" text-anchor="middle" transform="rotate(-90 {X(-wall) - 26} {Yp(D_in / 2)})">{D_in}" inside</text>')
    # --- back-wall elevation ---
    E = 5  # px per inch
    ex, ey = X(W_in + wall) + 120, oy
    EX = lambda t: ex + t * E
    EY = lambda z: ey + (PANTRY_CEILING - z) * E
    o.append(f'<text x="{ex}" y="{oy - 22}" font-size="13" font-weight="700" fill="#333">BACK WALL ELEVATION (facing west, 61" wide)</text>')
    o.append(f'<rect x="{EX(0)}" y="{EY(PANTRY_CEILING)}" width="{D_in * E}" height="{PANTRY_CEILING * E}" fill="#f7f4ee" stroke="#2b2b2b" stroke-width="3"/>')
    bins_t = [D_in - y - 12 for y in BIN_Y]  # viewed facing west, south is on the left
    for z0, z1, ttl, items in PANTRY_ZONES:
        cuts = sorted({z0, z1, *[z for z in PANTRY_SHELVES if z0 < z < z1]})
        g0, g1 = max(zip(cuts, cuts[1:]), key=lambda g: g[1] - g[0])
        zc = (g0 + g1) / 2
        tx = EX(D_in / 2)
        if ttl == "ROLLING BINS":  # text beside the bins
            tx = EX((max(bins_t) + 12 + D_in) / 2)
            items = items.replace("rice bin · atta bin (25–40 lb) · ", "25–40 lb each · ")
        o.append(f'<text x="{tx}" y="{EY(zc) - (2 if g1 - g0 > 8 else -3)}" font-size="11" font-weight="700" fill="#333" text-anchor="middle">{ttl}</text>')
        if g1 - g0 > 8:
            o.append(f'<text x="{tx}" y="{EY(zc) + 12}" font-size="9" fill="#555" text-anchor="middle">{items}</text>')
    for t0, name in zip(bins_t, ("ATTA", "RICE")):
        o.append(f'<rect x="{EX(t0)}" y="{EY(22)}" width="{12 * E}" height="{16 * E}" rx="6" fill="#dceaf3" stroke="#2e6f9e"/>')
        o.append(f'<text x="{EX(t0 + 6)}" y="{EY(13)}" font-size="9" fill="#1f4e6b" text-anchor="middle">{name}</text>')
    for z in PANTRY_SHELVES:
        o.append(f'<rect x="{EX(0)}" y="{EY(z) - 3}" width="{D_in * E}" height="6" fill="#b08a55"/>')
        o.append(f'<text x="{EX(D_in) + 10}" y="{EY(z) + 4}" font-size="10" fill="#444">{z}"</text>')
    o.append(f'<line x1="{EX(0)}" y1="{EY(0)}" x2="{EX(D_in)}" y2="{EY(0)}" stroke="#2b2b2b" stroke-width="4"/>')
    o.append(f'<text x="{EX(D_in) + 10}" y="{EY(PANTRY_CEILING) + 10}" font-size="10" fill="#444">{PANTRY_CEILING}" ceiling</text>')
    o.append(f'<text x="{EX(0)}" y="{EY(0) + 18}" font-size="10" fill="#666">← south (cookware side)</text>'
             f'<text x="{EX(D_in)}" y="{EY(0) + 18}" font-size="10" fill="#666" text-anchor="end">north (spice side) →</text>')
    o.append(f'<text x="{EX(0)}" y="{EY(0) + 36}" font-size="10" fill="#666">Shelves 16" deep, adjustable. Keep heavy bags on the platform or in the bins.</text>')
    w = int(EX(D_in) + 120)
    h = int(max(Yp(D_in + wall) + 60, EY(0) + 60))
    svg = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>', *o, '</svg>']
    Path(__file__).with_name("pantry_layout.svg").write_text("\n".join(svg).replace(" & ", " &amp; ") + "\n")
    return w, h


if __name__ == "__main__":
    for spec in ELEVATIONS:
        print(spec[0], *build_elevation(*spec))
    print("pantry_layout.svg", *build_pantry())
    print(*build())
