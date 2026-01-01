from __future__ import annotations

from dataclasses import dataclass

PaletteRGB = tuple[int, int, int]

PALETTE: dict[str, PaletteRGB] = {
    "Red": (255, 40, 40),
    "Green": (40, 200, 40),
    "Blue": (40, 80, 255),
    "Cyan": (0, 200, 200),
    "Magenta": (200, 0, 200),
    "Yellow": (220, 200, 40),
    "Orange": (255, 140, 0),
    "Teal": (0, 150, 150),
    "Gray": (150, 150, 150),
    "Purple": (120, 60, 200),
    "Pink": (255, 105, 180),
    "Lime": (140, 220, 60),
    "Navy": (20, 40, 120),
    "Sky": (90, 170, 255),
    "Olive": (120, 130, 40),
    "Maroon": (140, 20, 20),
    "Brown": (140, 90, 50),
    "Gold": (220, 170, 20),
    "Indigo": (75, 0, 130),
    "Slate": (110, 120, 140),
}

def darken(rgb: PaletteRGB, factor: float = 0.75) -> PaletteRGB:
    """Return a darker shade of `rgb` by multiplying channels by `factor`."""
    r, g, b = rgb
    return (max(0, min(255, int(r * factor))),
            max(0, min(255, int(g * factor))),
            max(0, min(255, int(b * factor))))
