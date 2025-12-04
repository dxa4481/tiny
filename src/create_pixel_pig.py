#!/usr/bin/env python3
"""
Pixel Pig Silicon Art Generator

Creates a pixel art pig using multiple silicon layers for different colors.
Each color maps to a different metal layer, creating a multi-layer artwork
visible under different conditions/illumination.

Layer Mapping (for visualization and microscopy):
    - Light pink (body)    → met1 (layer 68) 
    - Dark pink (details)  → met2 (layer 69)
    - Black (eyes)         → li1  (layer 67)
    - Golden (key)         → met3 (layer 70)

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

LAYERS = {
    'light_pink': {'layer': 68, 'datatype': 20, 'name': 'met1'},   # Body
    'dark_pink':  {'layer': 69, 'datatype': 20, 'name': 'met2'},   # Details/ears
    'black':      {'layer': 67, 'datatype': 20, 'name': 'li1'},    # Eyes
    'golden':     {'layer': 70, 'datatype': 20, 'name': 'met3'},   # Key
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
# Pixel Art Definition
# =============================================================================

# Pixel art is defined as a grid where each cell contains a color code:
# '.' = empty (no pixel)
# 'L' = light pink (body)
# 'D' = dark pink (details, ears, hooves)
# 'B' = black (eyes)
# 'G' = golden (key)

# The pig sprite - carefully recreated from the reference image
# Origin is bottom-left, positive Y goes up  
# The pig faces left with snout on left, ears at top, tail on right
PIG_PIXELS = [
    # Row 0 (bottom) - hooves
    "......DD........DD........",
    # Row 1 - lower legs
    "......DD........DD........",
    # Row 2 - legs
    "......LL........LL........",
    # Row 3 - legs
    "......LL........LL........",
    # Row 4 - legs/lower body
    "......LL........LL........",
    # Row 5 - lower body connection
    "....LLLLLLLLLLLLLLLL......",
    # Row 6 - body start
    "....LLLLLLLLLLLLLLLLLL....",
    # Row 7 - body
    "..LLLLLLLLLLLLLLLLLLLLLL..",
    # Row 8 - body with tail curling
    "..LLLLLLLLLLLLLLLLLLLLLLDD",
    # Row 9 - main body with tail
    "LLLLLLLLLLLLLLLLLLLLLL..DD",
    # Row 10 - body with cheek shade
    "LLLLLLLLLLLLLLLLLLLLLLDD..",
    # Row 11 - snout with nostrils
    "LLLLDDDDLLLLLLLLLLLLLLLL..",
    # Row 12 - snout detail
    "LLDDLLLLDDLLLLLLLLLLLLLL..",
    # Row 13 - face with eyes
    "LLLLLLLLLLLLBBLLLLBBLLDD..",
    # Row 14 - upper face
    "..LLLLLLLLLLLLLLLLLLLLDD..",
    # Row 15 - head top
    "....LLLLLLLLLLLLLLLLLL....",
    # Row 16 - below ears
    "......LLLLLLLLLLLLLL......",
    # Row 17 - ear connection
    "....DDLLLLLLLLLLLLLLDD....",
    # Row 18 - ears
    "..DDDDLL..LLLLLLLL..LLDDDD",
    # Row 19 (top) - ear tips
    "..DD......LLLLLLLL......DD",
]

# Key sprite (to the left of pig) - old-fashioned key design
# Bow (loop) at top, shaft with teeth
KEY_PIXELS = [
    # Row 0 (bottom) - bottom of shaft
    "..GG..",
    # Row 1
    "..GG..",
    # Row 2 - tooth
    ".GGG..",
    # Row 3
    "..GG..",
    # Row 4 - tooth
    ".GGG..",
    # Row 5
    "..GG..",
    # Row 6
    "..GG..",
    # Row 7 - start of bow
    ".GGGG.",
    # Row 8
    "GG..GG",
    # Row 9
    "GG..GG",
    # Row 10
    "GG..GG",
    # Row 11
    ".GGGG.",
    # Row 12 - bow inner
    ".G..G.",
    # Row 13 (top)
    ".GGGG.",
]


def create_pixel_art_gds(output_dir="gds", pixel_size=5.0):
    """
    Create the pixel pig GDS file using multiple layers.
    
    Args:
        output_dir: Directory for output files
        pixel_size: Size of each pixel in micrometers
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
    # 3. Calculate pixel art placement
    # -------------------------------------------------------------------------
    
    # Calculate pig dimensions
    pig_height = len(PIG_PIXELS)
    pig_width = max(len(row) for row in PIG_PIXELS)
    
    # Calculate key dimensions  
    key_height = len(KEY_PIXELS)
    key_width = max(len(row) for row in KEY_PIXELS)
    
    # Total art width (key + gap + pig)
    gap_pixels = 3
    total_width_pixels = key_width + gap_pixels + pig_width
    total_height_pixels = max(pig_height, key_height)
    
    # Calculate pixel size to fit in available area
    # Leave margins: 8um from edges, 12um from top (for pins)
    margin_x = 8.0
    margin_bottom = 8.0
    margin_top = 15.0  # Extra margin from pins
    
    available_width = DIE_WIDTH_UM - 2 * margin_x
    available_height = DIE_HEIGHT_UM - margin_bottom - margin_top
    
    # Calculate pixel size if not specified to fit
    max_pixel_by_width = available_width / total_width_pixels
    max_pixel_by_height = available_height / total_height_pixels
    
    auto_pixel_size = min(max_pixel_by_width, max_pixel_by_height) * 0.9
    
    if pixel_size is None or pixel_size > auto_pixel_size:
        pixel_size = auto_pixel_size
    
    print(f"Pixel size: {pixel_size:.2f} µm")
    print(f"Pig dimensions: {pig_width}x{pig_height} pixels = {pig_width*pixel_size:.1f}x{pig_height*pixel_size:.1f} µm")
    print(f"Key dimensions: {key_width}x{key_height} pixels = {key_width*pixel_size:.1f}x{key_height*pixel_size:.1f} µm")
    
    # Calculate offsets to center the art
    art_width = total_width_pixels * pixel_size
    art_height = total_height_pixels * pixel_size
    
    offset_x = (DIE_WIDTH_UM - art_width) / 2
    offset_y = margin_bottom + (available_height - art_height) / 2
    
    # Color to layer mapping
    color_map = {
        'L': LAYERS['light_pink'],
        'D': LAYERS['dark_pink'],
        'B': LAYERS['black'],
        'G': LAYERS['golden'],
    }
    
    pixel_count = {k: 0 for k in color_map}
    
    # -------------------------------------------------------------------------
    # 4. Add key pixels
    # -------------------------------------------------------------------------
    key_offset_x = offset_x
    # Center key vertically relative to pig
    key_offset_y = offset_y + (pig_height - key_height) * pixel_size / 2
    
    for row_idx, row in enumerate(KEY_PIXELS):
        for col_idx, pixel in enumerate(row):
            if pixel in color_map:
                layer_info = color_map[pixel]
                
                # Calculate pixel position (row 0 is bottom)
                x = key_offset_x + col_idx * pixel_size
                y = key_offset_y + row_idx * pixel_size
                
                # Create pixel rectangle
                rect = gdstk.rectangle(
                    (x, y),
                    (x + pixel_size, y + pixel_size),
                    layer=layer_info['layer'],
                    datatype=layer_info['datatype']
                )
                cell.add(rect)
                pixel_count[pixel] += 1
    
    # -------------------------------------------------------------------------
    # 5. Add pig pixels
    # -------------------------------------------------------------------------
    pig_offset_x = offset_x + (key_width + gap_pixels) * pixel_size
    pig_offset_y = offset_y
    
    for row_idx, row in enumerate(PIG_PIXELS):
        for col_idx, pixel in enumerate(row):
            if pixel in color_map:
                layer_info = color_map[pixel]
                
                x = pig_offset_x + col_idx * pixel_size
                y = pig_offset_y + row_idx * pixel_size
                
                rect = gdstk.rectangle(
                    (x, y),
                    (x + pixel_size, y + pixel_size),
                    layer=layer_info['layer'],
                    datatype=layer_info['datatype']
                )
                cell.add(rect)
                pixel_count[pixel] += 1
    
    print(f"\nPixel counts:")
    for color, count in pixel_count.items():
        if count > 0:
            layer_info = color_map[color]
            print(f"  {color} ({layer_info['name']}): {count} pixels")
    
    # -------------------------------------------------------------------------
    # 6. Save GDS file
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
    """Create an SVG preview of the GDS with accurate pixel art colors."""
    
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
    
    # Layer colors matching the original pixel art colors
    colors = {
        68: '#E8A89E',  # met1 - Light pink (body)
        69: '#A65B5B',  # met2 - Dark pink (details)
        70: '#A68B4C',  # met3 - Golden (key)
        67: '#1A1A1A',  # li1 - Black (eyes)
        71: '#666666',  # met4 - Gray (pins)
        235: '#DDDDDD', # boundary - Light gray
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
        f'    met1: body | met2: details | met3: key | li1: eyes',
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
        print("Layer Legend:")
        print("  🟠 met1 (layer 68) - Light pink body")
        print("  🟤 met2 (layer 69) - Dark pink details")
        print("  🟡 met3 (layer 70) - Golden key")
        print("  ⚫ li1  (layer 67) - Black eyes")


if __name__ == '__main__':
    main()
