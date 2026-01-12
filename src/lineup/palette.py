from __future__ import annotations

from dataclasses import dataclass

PaletteRGB = tuple[int, int, int]

PALETTE: dict[str, PaletteRGB] = {
    "Red": (255, 0, 0),
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
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
    "Turquoise": (0, 180, 170),
    "Mint": (60, 200, 120),
    "Seafoam": (70, 160, 130),
    "Forest": (20, 110, 40),
    "Emerald": (0, 150, 80),
    "Chartreuse": (150, 200, 0),
    "Amber": (230, 150, 20),
    "Coral": (235, 100, 80),
    "Salmon": (210, 90, 70),
    "Peach": (220, 130, 90),
    "Sand": (190, 160, 90),
    "Khaki": (150, 140, 80),
    "Tan": (170, 120, 70),
    "Bronze": (140, 95, 45),
    "Crimson": (180, 30, 45),
    "Violet": (140, 70, 210),
    "Lavender": (150, 110, 210),
    "Plum": (90, 40, 120),
    "Steel": (80, 110, 140),
    "Charcoal": (50, 55, 70),
}

def darken(rgb: PaletteRGB, factor: float = 0.66) -> PaletteRGB:
    """Return a darker shade of `rgb` by multiplying channels by `factor`."""
    r, g, b = rgb
    return (max(0, min(255, int(r * factor))),
            max(0, min(255, int(g * factor))),
            max(0, min(255, int(b * factor))))
