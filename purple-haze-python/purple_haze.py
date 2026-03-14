"""
Purple Haze — Color Interpolation Demo (Python / matplotlib)

Demonstrates the purple hue shift that occurs when interpolating blue
into black or white in CIE L*a*b*, and how OKLab corrects it.

Usage:
    python purple_haze.py                   # default #0044ff
    python purple_haze.py "#0000ff"         # pure blue
    python purple_haze.py "#0088ff"         # sky blue
    python purple_haze.py "#0044ff" --save  # save to PNG instead of displaying
"""

import sys
import numpy as np
import colour
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_hex

# Suppress scipy warning — we don't need it
import warnings
warnings.filterwarnings("ignore", message=".*SciPy.*")

STEPS = 13


# ---------------------------------------------------------------------------
# Color space conversion helpers
# ---------------------------------------------------------------------------

def hex_to_srgb(hex_str: str) -> np.ndarray:
    """Convert '#RRGGBB' to linear-domain sRGB [0,1] array."""
    h = hex_str.lstrip("#")
    return np.array([int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)])


def srgb_to_hex(srgb: np.ndarray) -> str:
    """Convert [0,1] sRGB array to '#rrggbb'."""
    clipped = np.clip(srgb, 0, 1)
    return "#{:02x}{:02x}{:02x}".format(*(clipped * 255).astype(int))


def srgb_to_xyz(srgb: np.ndarray) -> np.ndarray:
    return colour.sRGB_to_XYZ(srgb)


def xyz_to_srgb(xyz: np.ndarray) -> np.ndarray:
    return colour.XYZ_to_sRGB(xyz)


# ---------------------------------------------------------------------------
# Interpolation in each color space
# ---------------------------------------------------------------------------

def interpolate_srgb(c1: np.ndarray, c2: np.ndarray, steps: int) -> list:
    """Direct linear interpolation in sRGB — the naive approach."""
    return [c1 * (1 - t) + c2 * t for t in np.linspace(0, 1, steps)]


def interpolate_hsl(c1: np.ndarray, c2: np.ndarray, steps: int) -> list:
    """Interpolation in HSL (cylindrical sRGB)."""
    from colorsys import rgb_to_hls, hls_to_rgb

    h1, l1, s1 = rgb_to_hls(*c1)
    h2, l2, s2 = rgb_to_hls(*c2)

    results = []
    for t in np.linspace(0, 1, steps):
        # Shortest hue path
        dh = h2 - h1
        if abs(dh) > 0.5:
            dh = dh - 1.0 if dh > 0 else dh + 1.0
        h = (h1 + t * dh) % 1.0
        l = l1 * (1 - t) + l2 * t
        s = s1 * (1 - t) + s2 * t
        r, g, b = hls_to_rgb(h, l, s)
        results.append(np.array([r, g, b]))
    return results


def interpolate_lab(c1: np.ndarray, c2: np.ndarray, steps: int) -> list:
    """Interpolation in CIE L*a*b* — where the purple shift lives."""
    lab1 = colour.XYZ_to_Lab(srgb_to_xyz(c1))
    lab2 = colour.XYZ_to_Lab(srgb_to_xyz(c2))

    results = []
    for t in np.linspace(0, 1, steps):
        lab = lab1 * (1 - t) + lab2 * t
        srgb = xyz_to_srgb(colour.Lab_to_XYZ(lab))
        results.append(srgb)
    return results


def interpolate_lch(c1: np.ndarray, c2: np.ndarray, steps: int) -> list:
    """Interpolation in CIE LCH (cylindrical Lab) with shortest hue path."""
    lab1 = colour.XYZ_to_Lab(srgb_to_xyz(c1))
    lab2 = colour.XYZ_to_Lab(srgb_to_xyz(c2))
    lch1 = _lab_to_lch(lab1)
    lch2 = _lab_to_lch(lab2)

    results = []
    for t in np.linspace(0, 1, steps):
        L = lch1[0] * (1 - t) + lch2[0] * t
        C = lch1[1] * (1 - t) + lch2[1] * t
        # Shortest hue path
        dh = lch2[2] - lch1[2]
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        h = (lch1[2] + t * dh) % 360
        lab = _lch_to_lab(np.array([L, C, h]))
        srgb = xyz_to_srgb(colour.Lab_to_XYZ(lab))
        results.append(srgb)
    return results


def interpolate_oklab(c1: np.ndarray, c2: np.ndarray, steps: int) -> list:
    """Interpolation in OKLab — the fix for the purple shift."""
    ok1 = colour.XYZ_to_Oklab(srgb_to_xyz(c1))
    ok2 = colour.XYZ_to_Oklab(srgb_to_xyz(c2))

    results = []
    for t in np.linspace(0, 1, steps):
        ok = ok1 * (1 - t) + ok2 * t
        srgb = xyz_to_srgb(colour.Oklab_to_XYZ(ok))
        results.append(srgb)
    return results


def interpolate_oklch(c1: np.ndarray, c2: np.ndarray, steps: int) -> list:
    """Interpolation in OKLch (cylindrical OKLab) with shortest hue path."""
    ok1 = colour.XYZ_to_Oklab(srgb_to_xyz(c1))
    ok2 = colour.XYZ_to_Oklab(srgb_to_xyz(c2))
    lch1 = _lab_to_lch(ok1)
    lch2 = _lab_to_lch(ok2)

    results = []
    for t in np.linspace(0, 1, steps):
        L = lch1[0] * (1 - t) + lch2[0] * t
        C = lch1[1] * (1 - t) + lch2[1] * t
        dh = lch2[2] - lch1[2]
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        h = (lch1[2] + t * dh) % 360
        ok = _lch_to_lab(np.array([L, C, h]))
        srgb = xyz_to_srgb(colour.Oklab_to_XYZ(ok))
        results.append(srgb)
    return results


# ---------------------------------------------------------------------------
# LCH <-> Lab helpers (works for both CIE Lab and OKLab)
# ---------------------------------------------------------------------------

def _lab_to_lch(lab: np.ndarray) -> np.ndarray:
    L, a, b = lab
    C = np.sqrt(a**2 + b**2)
    h = np.degrees(np.arctan2(b, a)) % 360
    return np.array([L, C, h])


def _lch_to_lab(lch: np.ndarray) -> np.ndarray:
    L, C, h = lch
    a = C * np.cos(np.radians(h))
    b = C * np.sin(np.radians(h))
    return np.array([L, a, b])


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

SPACES = [
    ("sRGB",      "Naive linear — the default most tools use",             interpolate_srgb),
    ("HSL",       "Cylindrical sRGB — hue preserved, perceptually uneven", interpolate_hsl),
    ("CIE L*a*b*", "Perceptually uniform (1976) — purple hue shift on blues", interpolate_lab),
    ("CIE LCH",  "Cylindrical Lab — hue angle preserved, uneven chroma",  interpolate_lch),
    ("OKLab",     "Improved uniformity (Ottosson 2020) — fixes purple shift", interpolate_oklab),
    ("OKLch",     "Cylindrical OKLab — uniform + hue stable",             interpolate_oklch),
]


def render(input_hex: str, save: bool = False):
    """Generate the full comparison figure."""
    input_srgb = hex_to_srgb(input_hex)
    white = np.array([1.0, 1.0, 1.0])
    black = np.array([0.0, 0.0, 0.0])

    n_spaces = len(SPACES)
    fig, axes = plt.subplots(
        n_spaces, 2,
        figsize=(16, n_spaces * 1.2 + 2),
        gridspec_kw={"wspace": 0.08, "hspace": 0.35},
    )

    fig.patch.set_facecolor("#1a1a2e")

    fig.suptitle(
        f"Purple Haze — Interpolation of {input_hex}",
        fontsize=20,
        fontweight="bold",
        color="white",
        y=0.97,
    )

    col_titles = [f"{input_hex}  →  white", f"{input_hex}  →  black"]
    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title, fontsize=12, color="#aaa", pad=12)

    for row, (label, desc, interp_fn) in enumerate(SPACES):
        # To white
        to_white = interp_fn(input_srgb, white, STEPS)
        _draw_swatches(axes[row, 0], to_white, label, desc, show_label=True)

        # To black
        to_black = interp_fn(input_srgb, black, STEPS)
        _draw_swatches(axes[row, 1], to_black, label, desc, show_label=False)

    if save:
        out_path = f"purple_haze_{input_hex.lstrip('#')}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"Saved to {out_path}")
    else:
        plt.show()


def _draw_swatches(ax, colors: list, label: str, desc: str, show_label: bool):
    """Draw a row of color swatches on the given axes."""
    ax.set_xlim(0, STEPS)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("#1a1a2e")

    for i, srgb in enumerate(colors):
        clipped = np.clip(srgb, 0, 1)
        rect = mpatches.FancyBboxPatch(
            (i + 0.05, 0.05), 0.9, 0.9,
            boxstyle="round,pad=0.02",
            facecolor=clipped,
            edgecolor="none",
        )
        ax.add_patch(rect)

    if show_label:
        ax.text(
            -0.3, 0.5, label,
            transform=ax.transData,
            fontsize=11, fontweight="bold", color="white",
            ha="right", va="center",
        )
        ax.text(
            -0.3, 0.05, desc,
            transform=ax.transData,
            fontsize=7, color="#777",
            ha="right", va="bottom",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    input_hex = "#0044ff"
    save = False

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = [a for a in sys.argv[1:] if a.startswith("-")]

    if args:
        input_hex = args[0].strip('"').strip("'")
        if not input_hex.startswith("#"):
            input_hex = "#" + input_hex

    if "--save" in flags:
        save = True

    print(f"Purple Haze — interpolating {input_hex}")
    print(f"Spaces: {', '.join(s[0] for s in SPACES)}")
    print()

    render(input_hex, save=save)
