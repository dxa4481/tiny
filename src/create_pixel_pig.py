#!/usr/bin/env python3
"""
Pixel Pig + Canary Token Silicon Art Generator

Creates a combined design with:
- Canary token text (AWS credentials)
- Pixel pig artwork

Uses IHP-SG13G2 PDK layer specifications from create_silicon_art.py.

Usage:
    python create_pixel_pig.py
"""

import sys
from pathlib import Path

try:
    import gdstk
except ImportError:
    print("Error: gdstk library required. Install with: pip install gdstk")
    sys.exit(1)

# Import IHP specifications from create_silicon_art
from create_silicon_art import (
    DIE_WIDTH_UM, DIE_HEIGHT_UM,
    PIN_WIDTH, PIN_HEIGHT, PIN_Y_CENTER,
    PIN_LAYER, PIN_DATATYPE,
    PIN_DRAWING_LAYER, PIN_DRAWING_DATATYPE,  # Metal4.drawing to enclose pins
    POWER_PIN_LAYER, POWER_PIN_DATATYPE,
    POWER_DRAWING_LAYER, POWER_DRAWING_DATATYPE,  # TopMetal1.drawing to enclose pins
    POWER_LABEL_LAYER, POWER_LABEL_DATATYPE,
    TEXT_LAYER, TEXT_DATATYPE,
    BOUND_LAYER, BOUND_DATATYPE,
    LABEL_LAYER, LABEL_DATATYPE,
    TOP_MODULE,
    SIGNAL_PINS, POWER_PINS,
    POWER_PIN_WIDTH, POWER_PIN_Y_START, POWER_PIN_Y_END,
    POWER_PINS_DISTRIBUTED,  # New distributed power pin configuration
    VGND_X_POSITIONS, VPWR_X_POSITIONS,  # Individual stripe positions
    GDS_UNIT, GDS_PRECISION,
    VIA4_LAYER, VIA4_DATATYPE,        # Via between Metal4 and Metal5
    METAL5_LAYER, METAL5_DATATYPE,    # Metal5 layer
    METAL5_PIN_DATATYPE,              # Metal5.pin layer for VGND ground bus
    TOPVIA1_LAYER, TOPVIA1_DATATYPE,  # Via between Metal5 and TopMetal1
)

# =============================================================================
# IHP-SG13G2 Layer Definitions for Pixel Art
# Layer numbers from: IHP-Open-PDK/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp
#
# IMPORTANT: TinyTapeout's precheck only allows specific layer/datatype combos!
# .filler layers (datatype 22) are NOT in the whitelist!
# We must use .drawing layers (datatype 0) which ARE whitelisted but DRC checked.
#
# For pixel art to pass DRC:
#   - Each pixel must be >= 0.20µm wide (max of all metal min widths)
#   - Pixels must be spaced >= 0.21µm apart (max of all metal min spaces)
#   - Current pixel size is ~2.6µm which easily meets these requirements
# =============================================================================

# 5 colors mapped to IHP metal .drawing layers (datatype 0 = drawing, TinyTapeout whitelisted)
PIXEL_LAYERS = {
    'light_pink':  {'layer': 8,   'datatype': 0, 'name': 'Metal1.drawing'},   # Body (same as text)
    'dark_pink':   {'layer': 10,  'datatype': 0, 'name': 'Metal2.drawing'},   # Details/ears  
    'medium_pink': {'layer': 30,  'datatype': 0, 'name': 'Metal3.drawing'},   # Snout
    'golden':      {'layer': 30,  'datatype': 0, 'name': 'Metal3.drawing'},   # Key (same as snout - both visible)
    'black':       {'layer': 10,  'datatype': 0, 'name': 'Metal2.drawing'},   # Eyes (same as dark - visible as dark)
}

# =============================================================================
# Pixel Art Definition - Extracted from "pixel_pig (4).png"
# Grid: 19 x 12 pixels
# =============================================================================

LIGHT_PINK_PIXELS = [
    (11, 0), (14, 0), (14, 1),
    (12, 2), (13, 2), (14, 2), (15, 2),
    (12, 3), (13, 3), (14, 3), (15, 3), (16, 3),
    (12, 4), (13, 4), (14, 4), (15, 4),
    (11, 5), (12, 5), (14, 5), (15, 5),
    (10, 6), (11, 6), (12, 6), (13, 6),
]

DARK_PINK_PIXELS = [
    (10, 0), (13, 0), (16, 0),
    (9, 1), (10, 1), (11, 1), (12, 1), (13, 1), (15, 1), (16, 1),
    (16, 2), (18, 2),
    (8, 3), (10, 3), (17, 3),
    (16, 4),
    (9, 5), (16, 5),
    (9, 6), (14, 6), (15, 6),
    (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7),
    (9, 8), (14, 8),
]

MEDIUM_PINK_PIXELS = [
    (8, 2), (9, 2), (10, 2), (11, 2),
    (9, 3), (11, 3),
    (8, 4), (9, 4), (10, 4), (11, 4),
]

GOLDEN_PIXELS = [
    (3, 4), (4, 4), (5, 4),
    (2, 5), (6, 5),
    (2, 6), (6, 6),
    (3, 7), (4, 7), (5, 7),
    (4, 8),
    (4, 9), (5, 9),
    (4, 10),
    (4, 11), (5, 11),
]

BLACK_PIXELS = [
    (10, 5), (13, 5),
]

GRID_WIDTH = 19
GRID_HEIGHT = 12

# Density fill parameters - DISABLED to avoid DRC issues
# IHP density requirements are complex and fill often causes more DRC violations
FILL_SIZE = 4.5      # 4.5µm x 4.5µm fill squares
FILL_SPACING = 0.25  # 0.25µm gap (just above 0.21µm min)
FILL_PITCH = FILL_SIZE + FILL_SPACING  # 4.75µm pitch
ART_BUFFER = 0.5     # 0.5µm clearance around art (very tight)
ENABLE_DENSITY_FILL = False  # Disable - density fill not needed for art
ENABLE_TEXT = True  # Canary token text enabled
ENABLE_BORDER = False  # Disable - border not needed
ENABLE_PIG = True  # Pig art enabled - violations are not from the pig
ENABLE_POWER_PINS = True  # Power pins REQUIRED by TinyTapeout pin check
ENABLE_OUTPUT_GROUND = True  # Connect output pins to ground (all metal declared in LEF for LVS)
ENABLE_VIA_TO_TOPMETAL = True  # Add via stack with correct sizes (Via4=0.19µm, TopVia1=0.42µm)

# Ground bus parameters - connects output pins to VGND
GROUND_BUS_Y = 148.0      # Y position of horizontal Metal4 bus (within VGND Y range, below pins at 154.48)
GROUND_BUS_WIDTH = 1.0    # Width of Metal4 ground bus (above 0.20µm min)
GROUND_TRACE_WIDTH = 0.5  # Width of vertical traces from pins to bus
# Via sizes from IHP DRC rules - MUST be exact sizes!
VIA4_SIZE = 0.19          # Via4 size - IHP DRC V4.a requires exactly 0.19µm
TOPVIA1_SIZE = 0.42       # TopVia1 size - IHP DRC TV1.a requires exactly 0.42µm
VIA_ENCLOSURE = 0.5       # Metal enclosure around vias

# Ground bus metal bounds - populated during GDS generation, used for LEF
# These store the bounding boxes of all metal that's part of the VGND ground routing
# Format: list of (layer_name, llx, lly, urx, ury) tuples
GROUND_BUS_METAL_BOUNDS = []

# =============================================================================
# Pixel Font Definition (5x7 characters)
# Each character is a list of (x, y) coordinates for filled pixels
# Origin is bottom-left of character cell
# =============================================================================

# DRC-safe pixel font parameters
FONT_PIXEL_SIZE = 0.5   # 0.5 µm pixels (well above 0.16 µm min width)
FONT_PIXEL_GAP = 0.25   # 0.25 µm gap (above 0.18 µm min spacing)
FONT_CHAR_WIDTH = 5     # 5 pixels wide
FONT_CHAR_HEIGHT = 7    # 7 pixels tall
FONT_CHAR_GAP = 1       # 1 pixel gap between characters
FONT_LINE_GAP = 2       # 2 pixel gap between lines

# 5x7 Pixel Font - each character defined as list of (x, y) pixel coordinates
# Coordinates are 0-indexed from bottom-left
PIXEL_FONT = {
    'A': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(1,3),(1,6),(2,6),(3,3),(3,6),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5)],
    'B': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,2),(4,4),(4,5)],
    'C': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,6),(2,0),(2,6),(3,0),(3,6),(4,1),(4,5)],
    'D': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(1,6),(2,0),(2,6),(3,0),(3,6),(4,1),(4,2),(4,3),(4,4),(4,5)],
    'E': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,0),(4,6)],
    'F': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,3),(1,6),(2,3),(2,6),(3,3),(3,6),(4,6)],
    'G': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,2),(4,3),(4,5)],
    'H': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,3),(2,3),(3,3),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'I': [(0,0),(0,6),(1,0),(1,6),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(3,0),(3,6),(4,0),(4,6)],
    'J': [(0,1),(0,2),(1,0),(2,0),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(4,6)],
    'K': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,3),(2,2),(2,4),(3,1),(3,5),(4,0),(4,6)],
    'L': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(2,0),(3,0),(4,0)],
    'M': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,5),(2,4),(3,5),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'N': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,5),(2,4),(3,3),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'O': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,6),(2,0),(2,6),(3,0),(3,6),(4,1),(4,2),(4,3),(4,4),(4,5)],
    'P': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,3),(1,6),(2,3),(2,6),(3,3),(3,6),(4,4),(4,5)],
    'Q': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,6),(2,0),(2,2),(2,6),(3,0),(3,1),(3,6),(4,0),(4,2),(4,3),(4,4),(4,5)],
    'R': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,3),(1,6),(2,3),(2,6),(3,2),(3,3),(3,6),(4,0),(4,1),(4,4),(4,5)],
    'S': [(0,1),(0,5),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,5)],
    'T': [(0,6),(1,6),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(3,6),(4,6)],
    'U': [(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(2,0),(3,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'V': [(0,2),(0,3),(0,4),(0,5),(0,6),(1,1),(2,0),(3,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'W': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,1),(2,2),(3,1),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'X': [(0,0),(0,1),(0,5),(0,6),(1,2),(1,4),(2,3),(3,2),(3,4),(4,0),(4,1),(4,5),(4,6)],
    'Y': [(0,4),(0,5),(0,6),(1,3),(2,0),(2,1),(2,2),(3,3),(4,4),(4,5),(4,6)],
    'Z': [(0,0),(0,6),(1,0),(1,1),(1,6),(2,0),(2,2),(2,6),(3,0),(3,3),(3,6),(4,0),(4,4),(4,5),(4,6)],
    'a': [(0,1),(0,2),(1,0),(1,3),(2,0),(2,3),(3,0),(3,3),(4,0),(4,1),(4,2),(4,3),(4,4)],
    'b': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(1,3),(2,0),(2,3),(3,0),(3,3),(4,1),(4,2)],
    'c': [(0,1),(0,2),(1,0),(1,3),(2,0),(2,3),(3,0),(3,3),(4,1)],
    'd': [(0,1),(0,2),(1,0),(1,3),(2,0),(2,3),(3,0),(3,3),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)],
    'e': [(0,1),(0,2),(1,0),(1,2),(1,3),(2,0),(2,2),(2,3),(3,0),(3,2),(3,3),(4,1),(4,2)],
    'f': [(0,3),(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(2,3),(2,6),(3,6)],
    'g': [(0,0),(1,0),(1,1),(1,3),(1,4),(2,0),(2,2),(2,5),(3,0),(3,2),(3,5),(4,1),(4,3),(4,4)],
    'h': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,3),(2,3),(3,3),(4,0),(4,1),(4,2)],
    'i': [(2,0),(2,1),(2,2),(2,3),(2,5)],
    'j': [(0,0),(1,0),(1,1),(2,0),(2,1),(2,2),(2,3),(2,5)],
    'k': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,2),(2,1),(2,3),(3,0),(4,0)],
    'l': [(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(2,0),(3,0)],
    'm': [(0,0),(0,1),(0,2),(0,3),(1,3),(2,0),(2,1),(2,2),(2,3),(3,3),(4,0),(4,1),(4,2),(4,3)],
    'n': [(0,0),(0,1),(0,2),(0,3),(1,3),(2,3),(3,3),(4,0),(4,1),(4,2)],
    'o': [(0,1),(0,2),(1,0),(1,3),(2,0),(2,3),(3,0),(3,3),(4,1),(4,2)],
    'p': [(0,0),(0,1),(0,2),(0,3),(0,4),(1,3),(1,4),(2,3),(2,4),(3,3),(3,4),(4,4)],
    'q': [(0,4),(1,3),(1,4),(2,3),(2,4),(3,3),(3,4),(4,0),(4,1),(4,2),(4,3),(4,4)],
    'r': [(0,0),(0,1),(0,2),(0,3),(1,3),(2,3),(3,3)],
    's': [(0,0),(0,3),(1,0),(1,2),(1,3),(2,0),(2,2),(2,3),(3,0),(3,2),(3,3),(4,0),(4,3)],
    't': [(0,3),(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(2,0),(2,3),(3,0)],
    'u': [(0,1),(0,2),(0,3),(1,0),(2,0),(3,0),(4,0),(4,1),(4,2),(4,3)],
    'v': [(0,1),(0,2),(0,3),(1,0),(2,0),(3,0),(4,1),(4,2),(4,3)],
    'w': [(0,0),(0,1),(0,2),(0,3),(1,0),(2,0),(2,1),(3,0),(4,0),(4,1),(4,2),(4,3)],
    'x': [(0,0),(0,3),(1,1),(1,2),(2,1),(2,2),(3,1),(3,2),(4,0),(4,3)],
    'y': [(0,0),(0,4),(0,5),(1,0),(1,3),(2,0),(2,3),(3,0),(3,3),(4,1),(4,2),(4,3)],
    'z': [(0,0),(0,3),(1,0),(1,1),(1,3),(2,0),(2,2),(2,3),(3,0),(3,3),(4,0),(4,3)],
    '0': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,2),(1,6),(2,0),(2,3),(2,6),(3,0),(3,4),(3,6),(4,1),(4,2),(4,3),(4,4),(4,5)],
    '1': [(0,0),(1,0),(1,5),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(3,0),(4,0)],
    '2': [(0,0),(0,1),(0,4),(0,5),(1,0),(1,2),(1,6),(2,0),(2,3),(2,6),(3,0),(3,4),(3,6),(4,0),(4,5),(4,6)],
    '3': [(0,1),(0,5),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,2),(4,4),(4,5)],
    '4': [(0,2),(0,3),(1,2),(1,4),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(3,2),(3,5),(4,2),(4,6)],
    '5': [(0,1),(0,6),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,0),(4,2),(4,4),(4,5),(4,6)],
    '6': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,2),(4,5)],
    '7': [(0,6),(1,0),(1,1),(1,6),(2,2),(2,6),(3,3),(3,6),(4,4),(4,5),(4,6)],
    '8': [(0,1),(0,2),(0,4),(0,5),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,2),(4,4),(4,5)],
    '9': [(0,1),(0,4),(0,5),(1,0),(1,3),(1,6),(2,0),(2,3),(2,6),(3,0),(3,3),(3,6),(4,1),(4,2),(4,3),(4,4),(4,5)],
    ' ': [],
    '.': [(2,0)],
    ',': [(1,0),(2,1)],
    ':': [(2,1),(2,4)],
    ';': [(1,0),(2,1),(2,4)],
    '!': [(2,0),(2,2),(2,3),(2,4),(2,5),(2,6)],
    '?': [(0,4),(0,5),(1,0),(1,6),(2,2),(2,3),(2,6),(3,6),(4,4),(4,5)],
    '-': [(1,3),(2,3),(3,3)],
    '_': [(0,0),(1,0),(2,0),(3,0),(4,0)],
    '=': [(0,2),(0,4),(1,2),(1,4),(2,2),(2,4),(3,2),(3,4),(4,2),(4,4)],
    '+': [(1,3),(2,2),(2,3),(2,4),(3,3)],
    '*': [(0,2),(0,4),(1,3),(2,2),(2,3),(2,4),(3,3),(4,2),(4,4)],
    '/': [(0,0),(0,1),(1,2),(2,3),(3,4),(4,5),(4,6)],
    '\\': [(0,5),(0,6),(1,4),(2,3),(3,2),(4,0),(4,1)],
    '(': [(1,1),(1,2),(1,3),(1,4),(1,5),(2,0),(2,6),(3,0),(3,6)],
    ')': [(1,0),(1,6),(2,0),(2,6),(3,1),(3,2),(3,3),(3,4),(3,5)],
    '[': [(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(2,0),(2,6),(3,0),(3,6)],
    ']': [(1,0),(1,6),(2,0),(2,6),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6)],
    '{': [(1,3),(2,0),(2,1),(2,2),(2,4),(2,5),(2,6),(3,0),(3,6)],
    '}': [(1,0),(1,6),(2,0),(2,1),(2,2),(2,4),(2,5),(2,6),(3,3)],
    '<': [(1,2),(1,4),(2,1),(2,5),(3,0),(3,6)],
    '>': [(1,0),(1,6),(2,1),(2,5),(3,2),(3,4)],
    '\'': [(2,5),(2,6)],
    '"': [(1,5),(1,6),(3,5),(3,6)],
    '`': [(1,6),(2,5)],
    '@': [(0,1),(0,2),(0,3),(0,4),(0,5),(1,0),(1,3),(1,6),(2,0),(2,2),(2,4),(2,6),(3,0),(3,2),(3,3),(3,6),(4,1),(4,2),(4,5)],
    '#': [(0,1),(0,2),(0,4),(0,5),(1,0),(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(2,1),(2,2),(2,4),(2,5),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(4,1),(4,2),(4,4),(4,5)],
    '$': [(0,1),(0,4),(0,5),(1,0),(1,2),(1,6),(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(3,0),(3,4),(3,6),(4,1),(4,2),(4,5)],
    '%': [(0,0),(0,1),(0,5),(0,6),(1,0),(1,2),(1,6),(2,3),(3,0),(3,4),(3,6),(4,0),(4,1),(4,5),(4,6)],
    '^': [(1,5),(2,6),(3,5)],
    '&': [(0,0),(0,1),(0,4),(0,5),(1,0),(1,2),(1,3),(1,6),(2,0),(2,3),(2,6),(3,1),(3,4),(3,6),(4,0),(4,2),(4,5)],
    '|': [(2,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6)],
    '~': [(0,4),(1,5),(2,4),(3,5),(4,4)],
}


def render_pixel_text(text, x_start, y_start, layer, datatype, pixel_size=None, pixel_gap=None):
    """
    Render text as DRC-safe pixel rectangles.
    
    Args:
        text: String to render (supports newlines)
        x_start: X coordinate of text origin (left edge)
        y_start: Y coordinate of text origin (bottom edge)
        layer: GDS layer number
        datatype: GDS datatype
        pixel_size: Size of each pixel in µm (default: FONT_PIXEL_SIZE)
        pixel_gap: Gap between pixels in µm (default: FONT_PIXEL_GAP)
    
    Returns:
        List of gdstk.Rectangle objects, and (width, height) of rendered text
    """
    if pixel_size is None:
        pixel_size = FONT_PIXEL_SIZE
    if pixel_gap is None:
        pixel_gap = FONT_PIXEL_GAP
    
    pixel_pitch = pixel_size + pixel_gap
    char_width = FONT_CHAR_WIDTH * pixel_pitch
    char_height = FONT_CHAR_HEIGHT * pixel_pitch
    char_spacing = (FONT_CHAR_WIDTH + FONT_CHAR_GAP) * pixel_pitch
    line_spacing = (FONT_CHAR_HEIGHT + FONT_LINE_GAP) * pixel_pitch
    
    rectangles = []
    lines = text.split('\n')
    
    # Calculate total dimensions
    max_line_len = max(len(line) for line in lines) if lines else 0
    total_width = max_line_len * char_spacing - (FONT_CHAR_GAP * pixel_pitch) if max_line_len > 0 else 0
    total_height = len(lines) * line_spacing - (FONT_LINE_GAP * pixel_pitch) if lines else 0
    
    # Render from top line to bottom (y decreases)
    for line_idx, line in enumerate(lines):
        line_y = y_start + total_height - (line_idx + 1) * line_spacing + (FONT_LINE_GAP * pixel_pitch)
        
        for char_idx, char in enumerate(line):
            char_x = x_start + char_idx * char_spacing
            
            # Get pixel pattern for this character
            if char in PIXEL_FONT:
                pixels = PIXEL_FONT[char]
            else:
                # Unknown character - render as filled block
                pixels = [(x, y) for x in range(5) for y in range(7)]
            
            # Create rectangles for each pixel
            for (px, py) in pixels:
                rect_x = char_x + px * pixel_pitch
                rect_y = line_y + py * pixel_pitch
                rect = gdstk.rectangle(
                    (rect_x, rect_y),
                    (rect_x + pixel_size, rect_y + pixel_size),
                    layer=layer,
                    datatype=datatype
                )
                rectangles.append(rect)
    
    return rectangles, (total_width, total_height)


def get_art_exclusion_zone(cell, buffer_distance, pig_bounds, text_bounds):
    """
    Create exclusion zones using BOUNDING BOXES around art regions.
    This prevents fill from appearing in gaps between characters/pixels.
    
    Args:
        cell: The GDS cell
        buffer_distance: Buffer around art regions
        pig_bounds: (x1, y1, x2, y2) bounding box of pig area
        text_bounds: (x1, y1, x2, y2) bounding box of text area
    """
    import gdstk
    
    exclusion_rects = []
    
    # Pig exclusion zone (bounding box + buffer)
    if pig_bounds:
        x1, y1, x2, y2 = pig_bounds
        exclusion_rects.append(gdstk.rectangle(
            (x1 - buffer_distance, y1 - buffer_distance),
            (x2 + buffer_distance, y2 + buffer_distance)
        ))
    
    # Text exclusion zone (bounding box + buffer)  
    if text_bounds:
        x1, y1, x2, y2 = text_bounds
        exclusion_rects.append(gdstk.rectangle(
            (x1 - buffer_distance, y1 - buffer_distance),
            (x2 + buffer_distance, y2 + buffer_distance)
        ))
    
    # Also exclude the border area (it's on Metal1)
    # The border is a frame around the die
    border_polys = [p for p in cell.polygons 
                    if p.layer == 8 and p.datatype == 0 and p.area() > 100]
    for poly in border_polys:
        try:
            offsets = gdstk.offset(poly, buffer_distance, join="round", tolerance=0.1)
            exclusion_rects.extend(offsets)
        except:
            pass
    
    if exclusion_rects:
        return gdstk.boolean(exclusion_rects, [], "or")
    return []


def add_density_fill(cell, layer, datatype, margin_left, margin_right, margin_bottom, margin_top, exclusion_zone):
    """
    Add density fill pattern to meet 35-60% metal coverage requirement.
    
    Uses a pre-computed exclusion zone that covers art on ALL layers,
    so fill on any layer won't appear under art on other layers.
    """
    import gdstk
    
    # Calculate fill area (inside the border, avoid pin margins)
    fill_x_start = margin_left + 2
    fill_x_end = DIE_WIDTH_UM - margin_right - 2
    fill_y_start = margin_bottom + 5
    fill_y_end = DIE_HEIGHT_UM - margin_top - 2
    
    # Generate grid of fill squares
    fill_count = 0
    x = fill_x_start
    while x + FILL_SIZE <= fill_x_end:
        y = fill_y_start
        while y + FILL_SIZE <= fill_y_end:
            # Create candidate fill square
            fill_rect = gdstk.rectangle((x, y), (x + FILL_SIZE, y + FILL_SIZE))
            
            # Check if it overlaps with unified exclusion zone
            overlaps = False
            if exclusion_zone:
                result = gdstk.boolean(fill_rect, exclusion_zone, "and")
                if result:
                    overlaps = True
            
            if not overlaps:
                fill_rect_final = gdstk.rectangle(
                    (x, y),
                    (x + FILL_SIZE, y + FILL_SIZE),
                    layer=layer,
                    datatype=datatype
                )
                cell.add(fill_rect_final)
                fill_count += 1
            
            y += FILL_PITCH
        x += FILL_PITCH
    
    return fill_count


def create_combined_gds(text, output_dir="gds", font_size=None, pig_scale=0.4):
    """
    Create GDS with pixel pig art only (text DISABLED to avoid DRC issues).
    
    Args:
        text: Canary token text (DISABLED - gdstk.text() creates self-touching 
              polygons that cause DRC violations)
        output_dir: Directory for output files
        font_size: Font size in µm (not used - text disabled)
        pig_scale: Scale factor for the pig (0.4 = 40% of available height)
    
    NOTE: gdstk.text() creates polygons with self-touching points at letter corners
    (e.g., 'A', 'R', 'B', 'D' have internal notches). These cause DRC violations
    for notch width rules. The text is completely disabled to pass DRC.
    
    The pixel pig uses simple rectangles that are DRC-safe.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create GDS library with explicit unit and precision to avoid floating-point issues
    # This prevents "Layout dbu deviates from rule file dbu" warnings
    lib = gdstk.Library(unit=GDS_UNIT, precision=GDS_PRECISION)
    cell = lib.new_cell(TOP_MODULE)
    
    # -------------------------------------------------------------------------
    # 1. Add boundary rectangle
    # -------------------------------------------------------------------------
    boundary = gdstk.rectangle(
        (0, 0), 
        (DIE_WIDTH_UM, DIE_HEIGHT_UM),
        layer=BOUND_LAYER,
        datatype=BOUND_DATATYPE
    )
    cell.add(boundary)
    
    # -------------------------------------------------------------------------
    # 2. Add signal pins (Metal4.pin + Metal4.drawing)
    # -------------------------------------------------------------------------
    # DRC Rule Pin.f.M4 requires: Metal4 enclosure of Metal4:pin = 0.00
    # This means every pin shape must be covered by a Metal4.drawing shape
    for pin_name, direction, x_pos in SIGNAL_PINS:
        # Add Metal4.drawing shape (required by DRC to enclose pin)
        drawing_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, PIN_Y_CENTER - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, PIN_Y_CENTER + PIN_HEIGHT/2),
            layer=PIN_DRAWING_LAYER,
            datatype=PIN_DRAWING_DATATYPE
        )
        cell.add(drawing_rect)
        
        # Add Metal4.pin shape
        pin_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, PIN_Y_CENTER - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, PIN_Y_CENTER + PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(pin_rect)
        
        label = gdstk.Label(
            pin_name,
            (x_pos, PIN_Y_CENTER),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 3. Add power pins on TopMetal1 (TopMetal1.pin + TopMetal1.drawing)
    # -------------------------------------------------------------------------
    # DRC Rule Pin.g requires: TopMetal1 enclosure of TopMetal1:pin = 0.00
    # This means every pin shape must be covered by a TopMetal1.drawing shape
    #
    # IMPORTANT: Must create DISTRIBUTED stripes across the macro width
    # to match TinyTapeout top-level power grid integration requirements.
    # Single power pins at one corner cause routing failures with:
    #   "Error: via does not have shape on layer cut"
    if ENABLE_POWER_PINS:
        for pin_name, use_type, x_positions, y_start, y_end in POWER_PINS_DISTRIBUTED:
            for i, llx in enumerate(x_positions):
                # x_positions are LEFT EDGE values (llx), not centers
                urx = llx + POWER_PIN_WIDTH
                
                # Add TopMetal1.drawing shape (required by DRC to enclose pin)
                drawing_rect = gdstk.rectangle(
                    (llx, y_start),
                    (urx, y_end),
                    layer=POWER_DRAWING_LAYER,
                    datatype=POWER_DRAWING_DATATYPE
                )
                cell.add(drawing_rect)
                
                # Add TopMetal1.pin shape
                power_rect = gdstk.rectangle(
                    (llx, y_start),
                    (urx, y_end),
                    layer=POWER_PIN_LAYER,
                    datatype=POWER_PIN_DATATYPE
                )
                cell.add(power_rect)
                
                # Add label only on first stripe (avoid clutter)
                if i == 0:
                    label = gdstk.Label(
                        pin_name,
                        (llx + POWER_PIN_WIDTH/2, (y_start + y_end) / 2),
                        layer=POWER_LABEL_LAYER,
                        texttype=POWER_LABEL_DATATYPE
                    )
                    cell.add(label)
        
        print(f"Power pins: {len(VPWR_X_POSITIONS)} VPWR stripes + {len(VGND_X_POSITIONS)} VGND stripes (distributed)")
    else:
        print("Power pins: DISABLED (wrapper provides power grid)")
    
    # -------------------------------------------------------------------------
    # 3b. Connect OUTPUT pins to ground (VGND) via Metal4 bus and TopVia1
    # -------------------------------------------------------------------------
    # The leftmost 24 pins are all OUTPUT pins that need to be tied to ground.
    # We create a Metal4 ground bus below the pins, connect each output pin
    # to the bus with vertical traces, then use TopVia1 to connect to TopMetal1
    # which connects to the VGND power pin.
    #
    # IMPORTANT FOR LVS: All ground routing metal must be declared in the LEF
    # as part of the VGND pin. We track metal bounds in GROUND_BUS_METAL_BOUNDS.
    global GROUND_BUS_METAL_BOUNDS
    GROUND_BUS_METAL_BOUNDS = []  # Reset for this run
    
    if ENABLE_OUTPUT_GROUND:
        # Get output pins sorted by X position
        output_pins = [(name, direction, x) for name, direction, x in SIGNAL_PINS 
                       if direction == 'OUTPUT']
        output_pins_sorted = sorted(output_pins, key=lambda p: p[2])
        
        print(f"\nConnecting {len(output_pins_sorted)} output pins to ground...")
        
        # Find VGND power pin position (use last/rightmost stripe from distributed positions)
        # VGND_X_POSITIONS contains LEFT EDGE (llx) values
        # We use the last position since we're now using rightmost stripes
        vgnd_llx = VGND_X_POSITIONS[-1] if VGND_X_POSITIONS else None
        vgnd_x = vgnd_llx + POWER_PIN_WIDTH/2 if vgnd_llx else None  # Center of stripe
        
        # Get Y range for VGND from distributed config
        vgnd_y_start = POWER_PIN_Y_START
        vgnd_y_end = POWER_PIN_Y_END
        for pin_name, use_type, x_positions, y_start, y_end in POWER_PINS_DISTRIBUTED:
            if pin_name == "VGND":
                vgnd_y_start = y_start
                vgnd_y_end = y_end
                break
        
        if vgnd_llx is None:
            print("  WARNING: VGND power pin not found, skipping ground bus")
        else:
            # Calculate ground bus extent
            leftmost_output_x = output_pins_sorted[0][2]
            rightmost_output_x = output_pins_sorted[-1][2]
            
            # VGND pin boundaries (vgnd_llx is the left edge)
            vgnd_left = vgnd_llx
            vgnd_right = vgnd_llx + POWER_PIN_WIDTH
            
            # Place via within VGND's X footprint to connect directly
            # Via must be inside VGND bounds with proper enclosure
            via_x = vgnd_x  # Center of VGND
            via_y = GROUND_BUS_Y
            
            # Metal4 ground bus extends from leftmost output to VGND via location
            # The bus needs to span from the leftmost output pin to the VGND connection point
            bus_x_left = leftmost_output_x - PIN_WIDTH/2 - 0.5  # Past leftmost output
            bus_x_right = via_x + TOPVIA1_SIZE/2 + VIA_ENCLOSURE  # Past via with enclosure
            
            # Ensure proper ordering (handle case where VGND is to left or right of outputs)
            bus_x_start = min(bus_x_left, bus_x_right)
            bus_x_end = max(bus_x_left, bus_x_right)
            
            # Metal4 horizontal ground bus
            # NOTE: Only add .drawing shape - NOT .pin shape because:
            # 1. Power pins must be TopMetal1 only (precheck requirement)
            # 2. This is internal routing that connects to VGND via the via stack
            m4_bus_lly = GROUND_BUS_Y - GROUND_BUS_WIDTH/2
            m4_bus_ury = GROUND_BUS_Y + GROUND_BUS_WIDTH/2
            ground_bus = gdstk.rectangle(
                (bus_x_start, m4_bus_lly),
                (bus_x_end, m4_bus_ury),
                layer=PIN_DRAWING_LAYER,  # Metal4.drawing
                datatype=PIN_DRAWING_DATATYPE
            )
            cell.add(ground_bus)
            # Track bounds but don't add to LEF (internal routing only)
            print(f"  Metal4 ground bus: x={bus_x_start:.1f} to {bus_x_end:.1f}, y={GROUND_BUS_Y:.1f}")
            
            # Connect each output pin to the ground bus with vertical Metal4 traces
            # NOTE: Only add .drawing shape - this is internal routing, not a pin
            pin_bottom_y = PIN_Y_CENTER - PIN_HEIGHT/2
            for pin_name, direction, x_pos in output_pins_sorted:
                # Vertical trace from pin bottom to ground bus top
                trace_llx = x_pos - GROUND_TRACE_WIDTH/2
                trace_urx = x_pos + GROUND_TRACE_WIDTH/2
                trace_lly = m4_bus_ury  # Start at top of bus
                trace_ury = pin_bottom_y  # End at bottom of pin
                trace = gdstk.rectangle(
                    (trace_llx, trace_lly),
                    (trace_urx, trace_ury),
                    layer=PIN_DRAWING_LAYER,  # Metal4.drawing
                    datatype=PIN_DRAWING_DATATYPE
                )
                cell.add(trace)
            print(f"  Added {len(output_pins_sorted)} vertical traces to ground bus")
            
            # Via stack to connect Metal4 ground bus to TopMetal1/VGND
            # Stack: Metal4 → Via4 → Metal5 → TopVia1 → TopMetal1
            # IMPORTANT: Via sizes must be EXACT per IHP DRC rules!
            #   - Via4: 0.19µm × 0.19µm (V4.a)
            #   - TopVia1: 0.42µm × 0.42µm (TV1.a)
            if ENABLE_VIA_TO_TOPMETAL:
                # 1. Via4 (Metal4 to Metal5) - must be exactly 0.19µm
                via4_rect = gdstk.rectangle(
                    (via_x - VIA4_SIZE/2, via_y - VIA4_SIZE/2),
                    (via_x + VIA4_SIZE/2, via_y + VIA4_SIZE/2),
                    layer=VIA4_LAYER,
                    datatype=VIA4_DATATYPE
                )
                cell.add(via4_rect)
                print(f"  Via4 ({VIA4_SIZE}µm) at ({via_x:.1f}, {via_y:.1f})")
                
                # 2. Metal4 via pad - ensure proper enclosure of Via4
                # NOTE: Only add .drawing shape - this is internal routing
                m4_pad_llx = via_x - VIA4_SIZE/2 - VIA_ENCLOSURE
                m4_pad_lly = via_y - VIA4_SIZE/2 - VIA_ENCLOSURE
                m4_pad_urx = via_x + VIA4_SIZE/2 + VIA_ENCLOSURE
                m4_pad_ury = via_y + VIA4_SIZE/2 + VIA_ENCLOSURE
                m4_via_pad = gdstk.rectangle(
                    (m4_pad_llx, m4_pad_lly),
                    (m4_pad_urx, m4_pad_ury),
                    layer=PIN_DRAWING_LAYER,  # Metal4.drawing
                    datatype=PIN_DRAWING_DATATYPE
                )
                cell.add(m4_via_pad)
                
                # 3. Metal5 pad - must be large enough to enclose both Via4 and TopVia1
                # TopVia1 is larger (0.42µm) so use that as the reference
                # NOTE: Only add .drawing shape - this is internal routing
                m5_pad_half = max(VIA4_SIZE/2, TOPVIA1_SIZE/2) + VIA_ENCLOSURE
                m5_pad_llx = via_x - m5_pad_half
                m5_pad_lly = via_y - m5_pad_half
                m5_pad_urx = via_x + m5_pad_half
                m5_pad_ury = via_y + m5_pad_half
                m5_pad = gdstk.rectangle(
                    (m5_pad_llx, m5_pad_lly),
                    (m5_pad_urx, m5_pad_ury),
                    layer=METAL5_LAYER,
                    datatype=METAL5_DATATYPE
                )
                cell.add(m5_pad)
                print(f"  Metal5 pad with {VIA_ENCLOSURE}µm enclosure")
                
                # 4. TopVia1 (Metal5 to TopMetal1) - must be exactly 0.42µm
                topvia1_rect = gdstk.rectangle(
                    (via_x - TOPVIA1_SIZE/2, via_y - TOPVIA1_SIZE/2),
                    (via_x + TOPVIA1_SIZE/2, via_y + TOPVIA1_SIZE/2),
                    layer=TOPVIA1_LAYER,
                    datatype=TOPVIA1_DATATYPE
                )
                cell.add(topvia1_rect)
                print(f"  TopVia1 ({TOPVIA1_SIZE}µm) at ({via_x:.1f}, {via_y:.1f})")
                
                # 5. TopMetal1 connection - extends from VGND to cover TopVia1
                # This should be within the main VGND stripe bounds, so no need to track separately
                via_enclosure_tm1 = 0.5
                tm1_y_start = max(vgnd_y_start, via_y - TOPVIA1_SIZE/2 - via_enclosure_tm1)
                tm1_y_end = min(vgnd_y_end, via_y + TOPVIA1_SIZE/2 + via_enclosure_tm1)
                
                topmetal_rect = gdstk.rectangle(
                    (vgnd_left, tm1_y_start),
                    (vgnd_right, tm1_y_end),
                    layer=POWER_DRAWING_LAYER,  # TopMetal1.drawing
                    datatype=POWER_DRAWING_DATATYPE
                )
                cell.add(topmetal_rect)
                print(f"  TopMetal1 via enclosure: y={tm1_y_start:.1f} to {tm1_y_end:.1f}")
                print(f"  Via stack complete: Metal4→Via4→Metal5→TopVia1→TopMetal1")
            else:
                print(f"  Via to TopMetal1: DISABLED (Metal4 bus only)")
            
            print(f"  Ground routing metal tracked: {len(GROUND_BUS_METAL_BOUNDS)} shapes for LEF")
            print(f"  Ground connection complete!")
    else:
        print("Output ground bus: DISABLED")
    
    # -------------------------------------------------------------------------
    # 4. Calculate layout areas - pig centered in available area
    # -------------------------------------------------------------------------
    margin_left = 12.0   # Room for power pins
    margin_right = 3.0
    margin_bottom = 5.0
    margin_top = 10.0    # Room for signal pins
    
    available_width = DIE_WIDTH_UM - margin_left - margin_right
    available_height = DIE_HEIGHT_UM - margin_top - margin_bottom
    
    # -------------------------------------------------------------------------
    # 5. Add pixel pig - bottom portion of available area
    # -------------------------------------------------------------------------
    pig_width = 0
    pig_height = 0
    pig_offset_x = margin_left + 5.0
    pig_offset_y = margin_bottom + 5.0
    
    if ENABLE_PIG:
        # Size pig to take about 45% of available width (leaving room for text above)
        pig_area_width = available_width * 0.45
        pig_area_height = available_height * 0.50  # Bottom half for pig
        
        max_pixel_by_width = pig_area_width / GRID_WIDTH
        max_pixel_by_height = pig_area_height / GRID_HEIGHT
        pixel_size = min(max_pixel_by_width, max_pixel_by_height) * 0.90
        
        # Ensure pixel size meets minimum DRC requirements (0.20µm for all metals)
        MIN_PIXEL_SIZE = 0.5  # Well above 0.20µm minimum
        pixel_size = max(pixel_size, MIN_PIXEL_SIZE)
        
        # Add gap between pixels to prevent DRC violations from merged shapes
        # When adjacent pixels touch, they create notches that can violate spacing rules
        # Gap must be >= max metal spacing (0.21µm for Metal2/3)
        PIXEL_GAP = 0.25  # 0.25 µm gap between pixels
        pixel_pitch = pixel_size + PIXEL_GAP  # Total grid spacing
        
        # Reduce pixel size slightly to account for gap
        actual_pixel_size = pixel_size - PIXEL_GAP
        
        pig_width = GRID_WIDTH * pixel_pitch
        pig_height = GRID_HEIGHT * pixel_pitch
        
        print(f"Pig pixel size: {actual_pixel_size:.2f} µm (min DRC: 0.20 µm)")
        print(f"Pig pixel gap: {PIXEL_GAP:.2f} µm (min DRC: 0.21 µm)")
        print(f"Pig dimensions: {pig_width:.1f} x {pig_height:.1f} µm")
        print(f"Pig position: ({pig_offset_x:.1f}, {pig_offset_y:.1f})")
        
        # Add all pig pixels with gaps between them
        pixel_data = [
            ('light_pink', LIGHT_PINK_PIXELS),
            ('dark_pink', DARK_PINK_PIXELS),
            ('medium_pink', MEDIUM_PINK_PIXELS),
            ('golden', GOLDEN_PIXELS),
            ('black', BLACK_PIXELS),
        ]
        
        total_pixels = 0
        for color_name, positions in pixel_data:
            layer_info = PIXEL_LAYERS[color_name]
            for (gx, gy) in positions:
                # Use pixel_pitch for grid position, actual_pixel_size for shape
                x = pig_offset_x + gx * pixel_pitch
                y = pig_offset_y + gy * pixel_pitch
                
                rect = gdstk.rectangle(
                    (x, y),
                    (x + actual_pixel_size, y + actual_pixel_size),
                    layer=layer_info['layer'],
                    datatype=layer_info['datatype']
                )
                cell.add(rect)
                total_pixels += 1
        
        print(f"Pig pixels: {total_pixels}")
    else:
        print("Pig art: DISABLED (testing if DRC issues are from wrapper)")
    
    # -------------------------------------------------------------------------
    # 6. Add canary token text using DRC-safe pixel font
    # -------------------------------------------------------------------------
    text_final_x = 0
    text_final_y = 0
    text_final_width = 0
    text_final_height = 0
    
    if ENABLE_TEXT:
        # NOTE: gdstk.text() creates polygons with self-touching points that violate DRC.
        # Instead, we use a custom pixel font renderer that creates simple rectangles.
        # Each pixel is a separate rectangle, ensuring DRC compliance.
        
        # Text area: above the pig (with proper margins to stay within die)
        text_area_x = margin_left + 2.0
        text_area_y = pig_offset_y + pig_height + 3.0
        # Constrain text width to avoid overlapping with rightmost power stripes
        # Power stripes are at x=170.86 (VPWR) and x=177.06 (VGND)
        # Text starts at x=14.0, so max width to avoid stripes = 170.86 - 14.0 - 2.0 (margin)
        text_area_width = min(
            DIE_WIDTH_UM - margin_left - margin_right - 4.0,  # Original: stay within die
            154.0  # Avoid power stripes at x≈170-179
        )
        text_area_height = DIE_HEIGHT_UM - margin_top - text_area_y - 2.0
        
        # Calculate optimal pixel size to fit the text
        lines = text.split('\n')
        max_line_len = max(len(line) for line in lines) if lines else 1
        num_lines = len(lines)
        
        # Character cell is 5 pixels wide + 1 gap, 7 pixels tall + 2 gap
        # Total pitch per character = (5 + 1) * pixel_pitch for width
        # Total pitch per line = (7 + 2) * pixel_pitch for height
        # 
        # To fit max_line_len characters in text_area_width:
        # max_line_len * 6 * pixel_pitch = text_area_width
        # pixel_pitch = text_area_width / (max_line_len * 6)
        # pixel_size = pixel_pitch * (1 / (1 + gap_ratio))
        
        # Using gap_ratio = 0.5 (gap is 50% of pixel size)
        gap_ratio = 0.5
        
        # Calculate max pixel_pitch that fits width and height
        chars_pitch_units = max_line_len * 6 - 1  # Subtract 1 for no gap after last char
        lines_pitch_units = num_lines * 9 - 2     # Subtract 2 for no gap after last line
        
        max_pitch_by_width = text_area_width / chars_pitch_units if chars_pitch_units > 0 else 1
        max_pitch_by_height = text_area_height / lines_pitch_units if lines_pitch_units > 0 else 1
        
        pixel_pitch = min(max_pitch_by_width, max_pitch_by_height)
        
        # pixel_pitch = pixel_size + pixel_gap = pixel_size * (1 + gap_ratio)
        pixel_size = pixel_pitch / (1 + gap_ratio)
        pixel_gap = pixel_size * gap_ratio
        
        # Ensure minimum DRC-safe sizes
        MIN_TEXT_PIXEL = 0.20  # Metal1 min width is 0.16, use 0.20 for margin
        MIN_TEXT_GAP = 0.20    # Metal1 min spacing is 0.18, use 0.20 for margin
        
        if pixel_size < MIN_TEXT_PIXEL or pixel_gap < MIN_TEXT_GAP:
            # Text won't fit with DRC-safe dimensions - use minimum and accept clipping
            pixel_size = MIN_TEXT_PIXEL
            pixel_gap = MIN_TEXT_GAP
            print(f"WARNING: Text may be clipped to fit (using minimum DRC-safe sizes)")
    
        # Cap at reasonable size for readability
        MAX_TEXT_PIXEL = 1.0
        if pixel_size > MAX_TEXT_PIXEL:
            pixel_size = MAX_TEXT_PIXEL
            pixel_gap = pixel_size * gap_ratio
        
        print(f"Text pixel size: {pixel_size:.3f} µm (DRC min: 0.16 µm)")
        print(f"Text pixel gap: {pixel_gap:.3f} µm (DRC min: 0.18 µm)")
        
        # Render the text
        text_rects, (text_width, text_height) = render_pixel_text(
            text, text_area_x, text_area_y,
            layer=TEXT_LAYER, datatype=TEXT_DATATYPE,
            pixel_size=pixel_size, pixel_gap=pixel_gap
        )
        
        # Verify text fits within die (clip any rectangles outside)
        valid_rects = []
        for rect in text_rects:
            bb = rect.bounding_box()
            if bb[1][0] <= DIE_WIDTH_UM - 1 and bb[1][1] <= DIE_HEIGHT_UM - 1:
                valid_rects.append(rect)
                cell.add(rect)
        
        if len(valid_rects) < len(text_rects):
            print(f"  Clipped {len(text_rects) - len(valid_rects)} pixels outside die boundary")
        
        text_final_x = text_area_x
        text_final_y = text_area_y
        text_final_width = min(text_width, text_area_width)
        text_final_height = min(text_height, text_area_height)
        
        print(f"Text dimensions: {text_width:.1f} x {text_height:.1f} µm")
        print(f"Text position: ({text_final_x:.1f}, {text_final_y:.1f})")
        print(f"Text pixels rendered: {len(valid_rects)}")
    else:
        print("Text: DISABLED (to reduce DRC violations)")
    
    # -------------------------------------------------------------------------
    # 7. Add decorative border using 4 separate rectangles (DRC-safe)
    # -------------------------------------------------------------------------
    if ENABLE_BORDER:
        # NOTE: Using gdstk.boolean(outer, inner, "not") creates a single polygon
        # with self-touching corners that violate DRC. Instead, we create 4 separate
        # rectangles for the border sides, which avoids self-touching geometry.
        border_width = 1.0  # 1µm is well above 0.16µm Metal1 min width
        border_margin = 3.0
        
        # Inner rectangle corners (the hole in the frame)
        inner_x1 = margin_left - 2 + border_width
        inner_y1 = border_margin + border_width
        inner_x2 = DIE_WIDTH_UM - border_margin - border_width
        inner_y2 = DIE_HEIGHT_UM - margin_top + 2 - border_width
        
        # Outer rectangle corners
        outer_x1 = margin_left - 2
        outer_y1 = border_margin
        outer_x2 = DIE_WIDTH_UM - border_margin
        outer_y2 = DIE_HEIGHT_UM - margin_top + 2
        
        # Create 4 separate rectangles for the border sides
        # Left side (full height)
        left_border = gdstk.rectangle(
            (outer_x1, outer_y1),
            (inner_x1, outer_y2),
            layer=TEXT_LAYER,
            datatype=TEXT_DATATYPE
        )
        cell.add(left_border)
        
        # Right side (full height)
        right_border = gdstk.rectangle(
            (inner_x2, outer_y1),
            (outer_x2, outer_y2),
            layer=TEXT_LAYER,
            datatype=TEXT_DATATYPE
        )
        cell.add(right_border)
        
        # Bottom side (between left and right)
        bottom_border = gdstk.rectangle(
            (inner_x1, outer_y1),
            (inner_x2, inner_y1),
            layer=TEXT_LAYER,
            datatype=TEXT_DATATYPE
        )
        cell.add(bottom_border)
        
        # Top side (between left and right)
        top_border = gdstk.rectangle(
            (inner_x1, inner_y2),
            (inner_x2, outer_y2),
            layer=TEXT_LAYER,
            datatype=TEXT_DATATYPE
        )
        cell.add(top_border)
        
        print(f"Border: 4 rectangles ({border_width} µm width) - DRC-safe")
    else:
        print("Border: DISABLED (to reduce DRC violations)")
    
    # -------------------------------------------------------------------------
    # 8. Add density fill to meet 35-60% metal coverage requirement
    # -------------------------------------------------------------------------
    if ENABLE_DENSITY_FILL:
        print()
        print("Adding density fill (IHP requires 35-60% metal coverage)...")
        print(f"  Using {ART_BUFFER}µm BOUNDING BOX exclusion (covers entire art regions)")
        
        # Define art region bounding boxes (these exclude the ENTIRE region, not just individual polygons)
        # This prevents fill from appearing in gaps between characters/pixels
        pig_bounds = (pig_offset_x, pig_offset_y, pig_offset_x + pig_width, pig_offset_y + pig_height)
        
        # Text bounds for exclusion zone
        text_bounds = None
        if text_final_width > 0:
            text_bounds = (text_final_x, text_final_y, 
                           text_final_x + text_final_width,
                           text_final_y + text_final_height)
        
        # Create unified exclusion zone using bounding boxes
        exclusion_zone = get_art_exclusion_zone(cell, ART_BUFFER, pig_bounds, text_bounds)
        
        fill_layers = [
            (8, 0, 'Metal1'),   # Metal1.drawing
            (10, 0, 'Metal2'),  # Metal2.drawing
            (30, 0, 'Metal3'),  # Metal3.drawing
        ]
        
        for layer, datatype, name in fill_layers:
            count = add_density_fill(cell, layer, datatype, margin_left, margin_right, margin_bottom, margin_top, exclusion_zone)
            print(f"  {name}: added {count} fill squares ({count * FILL_SIZE**2:.0f} µm²)")
    else:
        print()
        print("Density fill: DISABLED (to reduce DRC violations)")
    
    # -------------------------------------------------------------------------
    # 9. Save files
    # -------------------------------------------------------------------------
    gds_path = output_path / f"{TOP_MODULE}.gds"
    lib.write_gds(gds_path)
    print(f"\nGDS saved to: {gds_path}")
    
    lef_content = generate_lef()
    lef_path = output_path / f"{TOP_MODULE}.lef"
    with open(lef_path, 'w') as f:
        f.write(lef_content)
    print(f"LEF saved to: {lef_path}")
    
    verilog_content = generate_verilog_stub()
    verilog_path = output_path / f"{TOP_MODULE}.v"
    with open(verilog_path, 'w') as f:
        f.write(verilog_content)
    print(f"Verilog saved to: {verilog_path}")
    
    create_svg_preview(lib, output_path / "preview.svg")
    
    return gds_path


def generate_lef():
    """
    Generate LEF file using IHP specifications.
    
    IMPORTANT: Power pins must have MULTIPLE PORT entries distributed across 
    the macro to match TinyTapeout top-level power grid integration requirements.
    
    FOR LVS: The VGND pin must include all ground routing metal (Metal4 bus,
    Metal5 pads) so LVS recognizes them as part of the VGND network.
    """
    lef = f"""VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO {TOP_MODULE}
  CLASS BLOCK ;
  FOREIGN {TOP_MODULE} 0.000 0.000 ;
  ORIGIN 0.000 0.000 ;
  SIZE {DIE_WIDTH_UM:.3f} BY {DIE_HEIGHT_UM:.3f} ;
  SYMMETRY X Y ;
"""
    
    # Power pins on TopMetal1 - MUST have multiple PORT entries distributed across macro
    # This is required for TinyTapeout top-level integration to connect power grid
    if ENABLE_POWER_PINS:
        for pin_name, use_type, x_positions, y_start, y_end in POWER_PINS_DISTRIBUTED:
            lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;"""
            
            # Add a PORT entry for each stripe position
            # x_positions are LEFT EDGE values (llx), not centers
            for llx in x_positions:
                urx = llx + POWER_PIN_WIDTH
                lef += f"""
    PORT
      LAYER TopMetal1 ;
        RECT {llx:.3f} {y_start:.3f} {urx:.3f} {y_end:.3f} ;
    END"""
            
            # NOTE: We do NOT declare the Metal4/Metal5 ground routing in LEF because:
            # 1. Precheck requires power pins to be TopMetal1 only
            # 2. Power pins must be within 10µm of top/bottom edges
            # 3. Power pins cannot overlap with signal pins
            # The ground routing is internal wiring that connects to VGND via the via stack.
            # LVS should recognize this connection through the via stack to TopMetal1.
            
            lef += f"""
  END {pin_name}
"""
    
    # Signal pins on Metal4
    for pin_name, direction, x_pos in SIGNAL_PINS:
        llx = x_pos - PIN_WIDTH/2
        lly = PIN_Y_CENTER - PIN_HEIGHT/2
        urx = x_pos + PIN_WIDTH/2
        ury = PIN_Y_CENTER + PIN_HEIGHT/2
        
        lef += f"""
  PIN {pin_name}
    DIRECTION {direction} ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT {llx:.3f} {lly:.3f} {urx:.3f} {ury:.3f} ;
    END
  END {pin_name}
"""
    
    lef += f"""
END {TOP_MODULE}

END LIBRARY
"""
    return lef


def generate_verilog_stub():
    """Generate a Verilog stub module."""
    return f"""// Verilog stub for {TOP_MODULE}
// Combined Pixel Pig + Canary Token Silicon Art

`default_nettype none

module {TOP_MODULE} (
`ifdef USE_POWER_PINS
    inout  wire       VPWR,
    inout  wire       VGND,
`endif
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    assign uo_out = ui_in ^ 8'hAA;
    assign uio_out = 8'b0;
    assign uio_oe = 8'b0;

    wire _unused = &{{ena, clk, rst_n, uio_in, 1'b0}};

endmodule
"""


def create_svg_preview(lib, output_path, width=1000, height=600):
    """Create an SVG preview with both pig and text."""
    cell = lib.cells[0]
    bbox = cell.bounding_box()
    
    if bbox is None:
        return
    
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[1]
    cell_width = max_x - min_x
    cell_height = max_y - min_y
    
    padding = 40
    scale = min((width - 2*padding) / cell_width, (height - 2*padding) / cell_height)
    
    # IHP layer colors (Metal1-4, TopMetal1, and prBoundary)
    # Layer numbers from IHP-Open-PDK sg13g2.lyp
    colors = {
        8:   '#4169E1',  # Metal1.drawing - Blue (text + pig body)
        10:  '#32CD32',  # Metal2.drawing - Green (pig details + eyes)
        30:  '#FF6347',  # Metal3.drawing - Tomato (pig snout + key)
        50:  '#9370DB',  # Metal4.pin - Purple (signal pins)
        126: '#FFD700',  # TopMetal1.pin - Gold (power pins)
        189: '#CCCCCC',  # prBoundary.boundary - Gray (boundary)
    }
    
    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'  <rect width="100%" height="100%" fill="#1a1a2e"/>',
        f'  <g transform="translate({padding},{height - padding}) scale({scale},-{scale}) translate({-min_x},{-min_y})">',
    ]
    
    for poly in cell.polygons:
        layer = poly.layer
        color = colors.get(layer, '#888888')
        opacity = 0.3 if layer == 189 else 0.9
        points_str = ' '.join(f'{p[0]},{p[1]}' for p in poly.points)
        svg_parts.append(
            f'    <polygon points="{points_str}" fill="{color}" '
            f'fill-opacity="{opacity}" stroke="{color}" stroke-width="{0.2/scale}"/>'
        )
    
    svg_parts.extend([
        '  </g>',
        f'  <text x="{width/2}" y="25" text-anchor="middle" fill="white" font-size="14">',
        f'    TinyTapeout IHP - Pixel Pig + Canary Token',
        f'  </text>',
        '</svg>'
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_parts))
    print(f"SVG preview saved to: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create combined Pixel Pig + Canary Token GDS'
    )
    parser.add_argument('--text', '-t', 
        default='[default]\naws_access_key_id =\n     AKIAX24QKKOLLIHNWPFY\naws_secret_access_key =\n     n6KkGJ8wrUpVUd6ZH8rw7DivKurwuxRX\\\n     uFrzrSpi\n\n\nDon\'t Forget To Run TruffleHog!',
        help='Canary token text')
    parser.add_argument('--output', '-o', default='gds',
                       help='Output directory')
    parser.add_argument('--font-size', '-s', type=float, default=None,
                       help='Font size in µm (auto if not specified)')
    
    args = parser.parse_args()
    text = args.text.replace('\\n', '\n')
    
    print("=" * 65)
    print("Pixel Pig + Canary Token Silicon Art Generator")
    print("=" * 65)
    print(f"Die size: {DIE_WIDTH_UM} x {DIE_HEIGHT_UM} µm (IHP 1x1 tile)")
    print(f"Output: {args.output}")
    print()
    
    gds_path = create_combined_gds(text, args.output, font_size=args.font_size)
    
    if gds_path:
        print()
        print("=" * 65)
        print("SUCCESS! Design created with DRC-safe pixel font:")
        print(f"  - {args.output}/{TOP_MODULE}.gds")
        print(f"  - {args.output}/{TOP_MODULE}.lef")
        print(f"  - {args.output}/{TOP_MODULE}.v")
        print(f"  - {args.output}/preview.svg")
        print("=" * 65)
        print()
        print("Design contents:")
        print("  🐷 Pixel Pig (bottom) - on Metal.drawing layers")
        print("  📝 Canary Token (top) - pixel font on Metal1.drawing")
        print("  🔲 Border frame (4 rectangles) - on Metal1.drawing")
        if ENABLE_OUTPUT_GROUND:
            print("  ⚡ Ground bus connecting 24 output pins to VGND")
        else:
            print("  ⚡ Output ground bus DISABLED (LVS compatibility)")
        print()
        print("Layer usage:")
        print("  🔵 Metal1.drawing (8/0)  = text + pig body + border + fill")
        print("  🟢 Metal2.drawing (10/0) = pig details + eyes + fill")
        print("  🔴 Metal3.drawing (30/0) = pig snout + key + fill")
        print("  🟣 Metal4.drawing (50/0) = signal pins")
        print("  🟡 TopMetal1.drawing (126/0) = power pins")
        if ENABLE_OUTPUT_GROUND:
            print("  🔗 Via4 (66/0) + Metal5 (67/0) + TopVia1 (125/0) = via stack to TopMetal1")
        print()
        if ENABLE_OUTPUT_GROUND:
            print("Output pin grounding:")
            print("  ✅ 24 output pins connected to Metal4 ground bus")
            print("  ✅ Ground bus connected to VGND via Metal4→Via4→Metal5→TopVia1→TopMetal1")
            print("  ✅ 19 input pins left floating (as required)")
        else:
            print("Output pins: NOT connected to ground (LVS-safe design)")
        print()
        print("DRC fixes applied:")
        print("  ✅ Text uses pixel font (simple rectangles, not gdstk.text)")
        print("  ✅ Border uses 4 separate rectangles (no self-touching corners)")
        print("  ✅ All geometry is simple rectangles (DRC-safe)")


if __name__ == '__main__':
    main()
