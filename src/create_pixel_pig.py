#!/usr/bin/env python3
"""
Pixel Pig Silicon Art Generator

Creates a pixel art pig using multiple silicon layers for different colors.
Each color maps to a different metal layer, creating a multi-layer artwork
visible under different conditions/illumination.

Pixel data extracted from "pixel_pig (4).png" image.

Layer Mapping (for visualization and microscopy):
    - Light pink (body)    → met1 (layer 68)  - RGB(221, 142, 136)
    - Dark pink (details)  → met2 (layer 69)  - RGB(153, 90, 86)
    - Medium pink (snout)  → poly (layer 66)  - RGB(200, 109, 102)
    - Golden (key)         → met3 (layer 70)  - RGB(174, 140, 87)
    - Black (eyes)         → li1  (layer 67)  - RGB(30, 30, 30)

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

# =============================================================================
# TinyTapeout 1x1 Tile Specifications
# =============================================================================

DIE_WIDTH_UM = 202.08
DIE_HEIGHT_UM = 154.98

# Module name
TOP_MODULE = "tt_um_silicon_art"

# =============================================================================
# Layer Definitions (Sky130 PDK)
# =============================================================================

# 5 colors from the image mapped to different silicon layers
# Using layers that are clearly visible in the TinyTapeout GDS viewer:
# - met1, met2, met3 = Metal layers (most visible, different colors)
# - li1 = Local interconnect (visible, distinct color)
# - poly = Polysilicon (visible, good for dark features)
LAYERS = {
    'light_pink':  {'layer': 68, 'datatype': 20, 'name': 'met1', 'rgb': (221, 142, 136)},   # Body - blue in viewer
    'dark_pink':   {'layer': 69, 'datatype': 20, 'name': 'met2', 'rgb': (153, 90, 86)},    # Details - cyan in viewer
    'medium_pink': {'layer': 70, 'datatype': 20, 'name': 'met3', 'rgb': (200, 109, 102)},  # Snout - pink in viewer
    'golden':      {'layer': 67, 'datatype': 20, 'name': 'li1',  'rgb': (174, 140, 87)},   # Key - tan in viewer
    'black':       {'layer': 66, 'datatype': 20, 'name': 'poly', 'rgb': (30, 30, 30)},     # Eyes - red in viewer
}

# Pin layer (met4)
PIN_LAYER = 71
PIN_DATATYPE = 20

# Boundary/PR boundary layers
BOUND_LAYER = 235
BOUND_DATATYPE = 4

# Label layer for pin names
LABEL_LAYER = 71
LABEL_DATATYPE = 5

# =============================================================================
# Pin Definitions (from TinyTapeout DEF file)
# =============================================================================

PINS = [
    ("clk", "INPUT", 143.98),
    ("ena", "INPUT", 146.74),
    ("rst_n", "INPUT", 141.22),
    ("ui_in[0]", "INPUT", 138.46),
    ("ui_in[1]", "INPUT", 135.70),
    ("ui_in[2]", "INPUT", 132.94),
    ("ui_in[3]", "INPUT", 130.18),
    ("ui_in[4]", "INPUT", 127.42),
    ("ui_in[5]", "INPUT", 124.66),
    ("ui_in[6]", "INPUT", 121.90),
    ("ui_in[7]", "INPUT", 119.14),
    ("uio_in[0]", "INPUT", 116.38),
    ("uio_in[1]", "INPUT", 113.62),
    ("uio_in[2]", "INPUT", 110.86),
    ("uio_in[3]", "INPUT", 108.10),
    ("uio_in[4]", "INPUT", 105.34),
    ("uio_in[5]", "INPUT", 102.58),
    ("uio_in[6]", "INPUT", 99.82),
    ("uio_in[7]", "INPUT", 97.06),
    ("uio_oe[0]", "OUTPUT", 50.14),
    ("uio_oe[1]", "OUTPUT", 47.38),
    ("uio_oe[2]", "OUTPUT", 44.62),
    ("uio_oe[3]", "OUTPUT", 41.86),
    ("uio_oe[4]", "OUTPUT", 39.10),
    ("uio_oe[5]", "OUTPUT", 36.34),
    ("uio_oe[6]", "OUTPUT", 33.58),
    ("uio_oe[7]", "OUTPUT", 30.82),
    ("uio_out[0]", "OUTPUT", 72.22),
    ("uio_out[1]", "OUTPUT", 69.46),
    ("uio_out[2]", "OUTPUT", 66.70),
    ("uio_out[3]", "OUTPUT", 63.94),
    ("uio_out[4]", "OUTPUT", 61.18),
    ("uio_out[5]", "OUTPUT", 58.42),
    ("uio_out[6]", "OUTPUT", 55.66),
    ("uio_out[7]", "OUTPUT", 52.90),
    ("uo_out[0]", "OUTPUT", 94.30),
    ("uo_out[1]", "OUTPUT", 91.54),
    ("uo_out[2]", "OUTPUT", 88.78),
    ("uo_out[3]", "OUTPUT", 86.02),
    ("uo_out[4]", "OUTPUT", 83.26),
    ("uo_out[5]", "OUTPUT", 80.50),
    ("uo_out[6]", "OUTPUT", 77.74),
    ("uo_out[7]", "OUTPUT", 74.98),
]

PIN_Y = 154.48
PIN_WIDTH = 0.3
PIN_HEIGHT = 1.0

POWER_PINS = [
    ("VGND", "GROUND", 1.0),
    ("VPWR", "POWER", 3.0),
]
POWER_PIN_WIDTH = 1.0
POWER_PIN_HEIGHT = DIE_HEIGHT_UM - 2.0
POWER_PIN_Y_CENTER = DIE_HEIGHT_UM / 2


# =============================================================================
# Pixel Art Definition - Extracted from "pixel_pig (4).png"
# =============================================================================

# Grid size: 19 x 12 art pixels
# Pixel positions (x, y) with origin at bottom-left

# DARK_PINK - RGB(153, 90, 86) - Ears and body details
# Layer: met2 (69:20)
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

# LIGHT_PINK - RGB(221, 142, 136) - Main body
# Layer: met1 (68:20)
LIGHT_PINK_PIXELS = [
    (11, 0), (14, 0),
    (14, 1),
    (12, 2), (13, 2), (14, 2), (15, 2),
    (12, 3), (13, 3), (14, 3), (15, 3), (16, 3),
    (12, 4), (13, 4), (14, 4), (15, 4),
    (11, 5), (12, 5), (14, 5), (15, 5),
    (10, 6), (11, 6), (12, 6), (13, 6),
]

# MEDIUM_PINK - RGB(200, 109, 102) - Snout/nose details
# Layer: poly (66:20)
MEDIUM_PINK_PIXELS = [
    (8, 2), (9, 2), (10, 2), (11, 2),
    (9, 3), (11, 3),
    (8, 4), (9, 4), (10, 4), (11, 4),
]

# GOLDEN - RGB(174, 140, 87) - Key
# Layer: met3 (70:20)
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

# BLACK - RGB(30, 30, 30) - Eyes
# Layer: li1 (67:20)
BLACK_PIXELS = [
    (10, 5), (13, 5),
]

# Grid dimensions from image analysis
GRID_WIDTH = 19
GRID_HEIGHT = 12


def create_pixel_art_gds(output_dir="gds", pixel_size=None):
    """
    Create the pixel pig GDS file using multiple layers.
    
    Args:
        output_dir: Directory for output files
        pixel_size: Size of each pixel in micrometers (auto-calculated if None)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create GDS library
    lib = gdstk.Library()
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
    # 2. Add signal pins
    # -------------------------------------------------------------------------
    for pin_name, direction, x_pos in PINS:
        pin_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, PIN_Y - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, PIN_Y + PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(pin_rect)
        
        label = gdstk.Label(
            pin_name,
            (x_pos, PIN_Y),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 2b. Add power pins
    # -------------------------------------------------------------------------
    for pin_name, use_type, x_pos in POWER_PINS:
        power_rect = gdstk.rectangle(
            (x_pos - POWER_PIN_WIDTH/2, POWER_PIN_Y_CENTER - POWER_PIN_HEIGHT/2),
            (x_pos + POWER_PIN_WIDTH/2, POWER_PIN_Y_CENTER + POWER_PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(power_rect)
        
        label = gdstk.Label(
            pin_name,
            (x_pos, POWER_PIN_Y_CENTER),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 3. Calculate pixel art placement using extracted grid dimensions
    # -------------------------------------------------------------------------
    
    # Calculate pixel size to fit in available area
    # Leave margins: 8um from edges, 15um from top (for pins)
    margin_x = 8.0
    margin_bottom = 8.0
    margin_top = 15.0  # Extra margin from pins
    
    available_width = DIE_WIDTH_UM - 2 * margin_x
    available_height = DIE_HEIGHT_UM - margin_bottom - margin_top
    
    # Calculate pixel size to fit the grid
    max_pixel_by_width = available_width / GRID_WIDTH
    max_pixel_by_height = available_height / GRID_HEIGHT
    
    auto_pixel_size = min(max_pixel_by_width, max_pixel_by_height) * 0.95
    
    if pixel_size is None or pixel_size > auto_pixel_size:
        pixel_size = auto_pixel_size
    
    print(f"Pixel size: {pixel_size:.2f} µm")
    print(f"Grid dimensions: {GRID_WIDTH}x{GRID_HEIGHT} pixels = {GRID_WIDTH*pixel_size:.1f}x{GRID_HEIGHT*pixel_size:.1f} µm")
    
    # Calculate offsets to center the art
    art_width = GRID_WIDTH * pixel_size
    art_height = GRID_HEIGHT * pixel_size
    
    offset_x = (DIE_WIDTH_UM - art_width) / 2
    offset_y = margin_bottom + (available_height - art_height) / 2
    
    # -------------------------------------------------------------------------
    # 4. Add all pixels from extracted data
    # -------------------------------------------------------------------------
    
    # Map pixel arrays to their layer info
    pixel_data = [
        ('light_pink', LIGHT_PINK_PIXELS, LAYERS['light_pink']),
        ('dark_pink', DARK_PINK_PIXELS, LAYERS['dark_pink']),
        ('medium_pink', MEDIUM_PINK_PIXELS, LAYERS['medium_pink']),
        ('golden', GOLDEN_PIXELS, LAYERS['golden']),
        ('black', BLACK_PIXELS, LAYERS['black']),
    ]
    
    pixel_count = {}
    
    for color_name, positions, layer_info in pixel_data:
        pixel_count[color_name] = len(positions)
        
        for (gx, gy) in positions:
            # Calculate pixel position
            x = offset_x + gx * pixel_size
            y = offset_y + gy * pixel_size
            
            # Create pixel rectangle
            rect = gdstk.rectangle(
                (x, y),
                (x + pixel_size, y + pixel_size),
                layer=layer_info['layer'],
                datatype=layer_info['datatype']
            )
            cell.add(rect)
    
    print(f"\nPixel counts by color:")
    total = 0
    for color_name, positions, layer_info in pixel_data:
        count = len(positions)
        total += count
        rgb = layer_info.get('rgb', (0, 0, 0))
        print(f"  {color_name:12} ({layer_info['name']:4}): {count:3} pixels - RGB{rgb}")
    print(f"  {'TOTAL':12}       : {total:3} pixels")
    
    # -------------------------------------------------------------------------
    # 5. Save GDS file
    # -------------------------------------------------------------------------
    gds_path = output_path / f"{TOP_MODULE}.gds"
    lib.write_gds(gds_path)
    print(f"\nGDS saved to: {gds_path}")
    
    # -------------------------------------------------------------------------
    # 7. Create LEF file
    # -------------------------------------------------------------------------
    lef_content = generate_lef()
    lef_path = output_path / f"{TOP_MODULE}.lef"
    with open(lef_path, 'w') as f:
        f.write(lef_content)
    print(f"LEF saved to: {lef_path}")
    
    # -------------------------------------------------------------------------
    # 8. Create Verilog stub
    # -------------------------------------------------------------------------
    verilog_content = generate_verilog_stub()
    verilog_path = output_path / f"{TOP_MODULE}.v"
    with open(verilog_path, 'w') as f:
        f.write(verilog_content)
    print(f"Verilog saved to: {verilog_path}")
    
    # -------------------------------------------------------------------------
    # 9. Create SVG preview
    # -------------------------------------------------------------------------
    create_svg_preview(lib, output_path / "preview.svg")
    
    return gds_path


def generate_lef():
    """Generate LEF file for the macro."""
    
    lef = f"""VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO {TOP_MODULE}
  CLASS BLOCK ;
  FOREIGN {TOP_MODULE} 0 0 ;
  ORIGIN 0 0 ;
  SIZE {DIE_WIDTH_UM:.3f} BY {DIE_HEIGHT_UM:.3f} ;
  SYMMETRY X Y ;
"""
    
    # Add power pins
    for pin_name, use_type, x_pos in POWER_PINS:
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER met4 ;
        RECT {x_pos - POWER_PIN_WIDTH/2:.3f} {POWER_PIN_Y_CENTER - POWER_PIN_HEIGHT/2:.3f} {x_pos + POWER_PIN_WIDTH/2:.3f} {POWER_PIN_Y_CENTER + POWER_PIN_HEIGHT/2:.3f} ;
    END
  END {pin_name}
"""
    
    # Add signal pins
    for pin_name, direction, x_pos in PINS:
        lef += f"""
  PIN {pin_name}
    DIRECTION {direction} ;
    USE SIGNAL ;
    PORT
      LAYER met4 ;
        RECT {x_pos - PIN_WIDTH/2:.3f} {PIN_Y - PIN_HEIGHT/2:.3f} {x_pos + PIN_WIDTH/2:.3f} {PIN_Y + PIN_HEIGHT/2:.3f} ;
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
// Pixel Pig Silicon Art Project

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

    // Simple pass-through (art project - minimal logic)
    assign uo_out = ui_in ^ 8'hAA;
    assign uio_out = 8'b0;
    assign uio_oe = 8'b0;

    // Unused inputs
    wire _unused = &{{ena, clk, rst_n, uio_in, 1'b0}};

endmodule
"""


def create_svg_preview(lib, output_path, width=800, height=600):
    """Create an SVG preview of the GDS with accurate pixel art colors from the image."""
    
    cell = lib.cells[0]
    bbox = cell.bounding_box()
    
    if bbox is None:
        print("Warning: Cannot create SVG - no bounding box")
        return
    
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[1]
    cell_width = max_x - min_x
    cell_height = max_y - min_y
    
    padding = 40
    scale = min((width - 2*padding) / cell_width,
                (height - 2*padding) / cell_height)
    
    # Layer colors matching the EXACT RGB values from "pixel_pig (4).png"
    colors = {
        68: '#DD8E88',  # met1 - Light pink body - RGB(221, 142, 136)
        69: '#995A56',  # met2 - Dark pink details - RGB(153, 90, 86)
        70: '#C86D66',  # met3 - Medium pink NOSE - RGB(200, 109, 102)
        67: '#AE8C57',  # li1 - Golden key - RGB(174, 140, 87)
        66: '#1E1E1E',  # poly - Black eyes - RGB(30, 30, 30)
        71: '#666666',  # met4 - Gray (pins)
        235: '#EEEEEE', # boundary - Light gray
    }
    
    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'  <defs>',
        f'    <style>',
        f'      .title {{ font-family: Arial, sans-serif; font-size: 16px; fill: #333; }}',
        f'      .subtitle {{ font-family: Arial, sans-serif; font-size: 12px; fill: #666; }}',
        f'    </style>',
        f'  </defs>',
        f'  <rect width="100%" height="100%" fill="#FAFAFA"/>',
        f'  <g transform="translate({padding},{height - padding}) scale({scale},-{scale}) translate({-min_x},{-min_y})">',
    ]
    
    # Group polygons by layer for z-ordering
    layer_order = [235, 68, 69, 70, 67, 71]  # Draw boundary first, pins last
    
    polys_by_layer = {}
    for poly in cell.polygons:
        layer = poly.layer
        if layer not in polys_by_layer:
            polys_by_layer[layer] = []
        polys_by_layer[layer].append(poly)
    
    # Add polygons in layer order
    for layer in layer_order:
        if layer in polys_by_layer:
            color = colors.get(layer, '#888888')
            opacity = 0.2 if layer == 235 else 1.0
            stroke_width = 0.3 / scale if layer == 235 else 0
            stroke = '#999' if layer == 235 else 'none'
            
            for poly in polys_by_layer[layer]:
                points_str = ' '.join(f'{p[0]},{p[1]}' for p in poly.points)
                svg_parts.append(
                    f'    <polygon points="{points_str}" fill="{color}" '
                    f'fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
                )
    
    svg_parts.extend([
        '  </g>',
        f'  <text x="{width/2}" y="25" text-anchor="middle" class="title">',
        f'    TinyTapeout Pixel Pig - Multi-Layer Silicon Art',
        f'  </text>',
        f'  <text x="{width/2}" y="45" text-anchor="middle" class="subtitle">',
        f'    met1: body | met2: details | met3: snout | li1: key | poly: eyes',
        f'  </text>',
        '</svg>'
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_parts))
    
    print(f"SVG preview saved to: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create TinyTapeout Pixel Pig silicon art GDS'
    )
    parser.add_argument('--output', '-o', default='gds',
                       help='Output directory')
    parser.add_argument('--pixel-size', '-p', type=float, default=None,
                       help='Pixel size in µm (auto-calculated if not specified)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Pixel Pig Silicon Art Generator")
    print("Extracted from: pixel_pig (4).png")
    print("=" * 60)
    print(f"Die size: {DIE_WIDTH_UM} x {DIE_HEIGHT_UM} µm")
    print(f"Output directory: {args.output}")
    print()
    
    gds_path = create_pixel_art_gds(args.output, pixel_size=args.pixel_size)
    
    if gds_path:
        print()
        print("=" * 60)
        print("SUCCESS! Files created:")
        print(f"  - {args.output}/{TOP_MODULE}.gds")
        print(f"  - {args.output}/{TOP_MODULE}.lef")
        print(f"  - {args.output}/{TOP_MODULE}.v")
        print(f"  - {args.output}/preview.svg")
        print("=" * 60)
        print()
        print("Layer Legend (5 colors from image):")
        print("  🟠 met1 (layer 68) - Light pink body     RGB(221, 142, 136)")
        print("  🟤 met2 (layer 69) - Dark pink details   RGB(153, 90, 86)")
        print("  🔴 met3 (layer 70) - Medium pink snout   RGB(200, 109, 102)")
        print("  🟡 li1  (layer 67) - Golden key          RGB(174, 140, 87)")
        print("  ⚫ poly (layer 66) - Black eyes          RGB(30, 30, 30)")


if __name__ == '__main__':
    main()
