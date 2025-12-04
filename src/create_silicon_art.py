#!/usr/bin/env python3
"""
TinyTapeout Silicon Art Generator

Creates a complete GDS and LEF file for TinyTapeout custom_gds submission.
The design includes "Hello World" text visible on silicon.

This generates all required files for the custom_gds workflow:
- GDS file with text art and proper pin definitions  
- LEF file for the macro
- Verilog stub

Usage:
    python create_silicon_art.py

Output files are created in the gds/ directory.
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

# Die dimensions in micrometers
DIE_WIDTH_UM = 161.0
DIE_HEIGHT_UM = 111.52

# Pin layer (met4)
PIN_LAYER = 71
PIN_DATATYPE = 20

# Text layer (met1 - most visible under microscope)
TEXT_LAYER = 68  
TEXT_DATATYPE = 20

# Boundary/PR boundary layers
BOUND_LAYER = 235
BOUND_DATATYPE = 4

# Label layer for pin names
LABEL_LAYER = 71
LABEL_DATATYPE = 5

# Top module name
TOP_MODULE = "tt_um_silicon_art"

# =============================================================================
# Pin Definitions (from TinyTapeout DEF file)
# All coordinates in micrometers, pins on met4 at top edge
# =============================================================================

PINS = [
    # Control signals
    ("clk", "INPUT", 143.98),
    ("ena", "INPUT", 146.74),
    ("rst_n", "INPUT", 141.22),
    
    # Input bus ui_in[7:0]
    ("ui_in[0]", "INPUT", 138.46),
    ("ui_in[1]", "INPUT", 135.70),
    ("ui_in[2]", "INPUT", 132.94),
    ("ui_in[3]", "INPUT", 130.18),
    ("ui_in[4]", "INPUT", 127.42),
    ("ui_in[5]", "INPUT", 124.66),
    ("ui_in[6]", "INPUT", 121.90),
    ("ui_in[7]", "INPUT", 119.14),
    
    # Bidirectional input bus uio_in[7:0]
    ("uio_in[0]", "INPUT", 116.38),
    ("uio_in[1]", "INPUT", 113.62),
    ("uio_in[2]", "INPUT", 110.86),
    ("uio_in[3]", "INPUT", 108.10),
    ("uio_in[4]", "INPUT", 105.34),
    ("uio_in[5]", "INPUT", 102.58),
    ("uio_in[6]", "INPUT", 99.82),
    ("uio_in[7]", "INPUT", 97.06),
    
    # Output enable bus uio_oe[7:0]
    ("uio_oe[0]", "OUTPUT", 50.14),
    ("uio_oe[1]", "OUTPUT", 47.38),
    ("uio_oe[2]", "OUTPUT", 44.62),
    ("uio_oe[3]", "OUTPUT", 41.86),
    ("uio_oe[4]", "OUTPUT", 39.10),
    ("uio_oe[5]", "OUTPUT", 36.34),
    ("uio_oe[6]", "OUTPUT", 33.58),
    ("uio_oe[7]", "OUTPUT", 30.82),
    
    # Bidirectional output bus uio_out[7:0]
    ("uio_out[0]", "OUTPUT", 72.22),
    ("uio_out[1]", "OUTPUT", 69.46),
    ("uio_out[2]", "OUTPUT", 66.70),
    ("uio_out[3]", "OUTPUT", 63.94),
    ("uio_out[4]", "OUTPUT", 61.18),
    ("uio_out[5]", "OUTPUT", 58.42),
    ("uio_out[6]", "OUTPUT", 55.66),
    ("uio_out[7]", "OUTPUT", 52.90),
    
    # Output bus uo_out[7:0]
    ("uo_out[0]", "OUTPUT", 94.30),
    ("uo_out[1]", "OUTPUT", 91.54),
    ("uo_out[2]", "OUTPUT", 88.78),
    ("uo_out[3]", "OUTPUT", 86.02),
    ("uo_out[4]", "OUTPUT", 83.26),
    ("uo_out[5]", "OUTPUT", 80.50),
    ("uo_out[6]", "OUTPUT", 77.74),
    ("uo_out[7]", "OUTPUT", 74.98),
]

# Pin Y position (at top edge) and dimensions
PIN_Y = 111.02  # um from bottom
PIN_WIDTH = 0.3  # um
PIN_HEIGHT = 1.0  # um


def create_silicon_art_gds(text="HELLO\nWORLD", output_dir="gds", font_size=None, min_feature_size=0.14):
    """
    Create a complete TinyTapeout-compatible GDS with text art.
    
    Args:
        text: Text to render on the chip
        output_dir: Directory for output files
        font_size: Font size in µm (None = auto-calculate to fit)
        min_feature_size: Minimum feature size in µm (Sky130 met1 = 0.14 µm)
    
    Sky130 Design Rules (for reference):
        - met1 min width: 0.14 µm
        - met1 min spacing: 0.14 µm
        - Recommended for visibility: ≥1 µm features (optical microscope)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create GDS library
    lib = gdstk.Library()
    
    # Create main cell
    cell = lib.new_cell(TOP_MODULE)
    
    # -------------------------------------------------------------------------
    # 1. Add boundary rectangle (PR boundary)
    # -------------------------------------------------------------------------
    boundary = gdstk.rectangle(
        (0, 0), 
        (DIE_WIDTH_UM, DIE_HEIGHT_UM),
        layer=BOUND_LAYER,
        datatype=BOUND_DATATYPE
    )
    cell.add(boundary)
    
    # -------------------------------------------------------------------------
    # 2. Add pin shapes on met4
    # -------------------------------------------------------------------------
    for pin_name, direction, x_pos in PINS:
        # Pin rectangle
        pin_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, PIN_Y - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, PIN_Y + PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(pin_rect)
        
        # Pin label
        label = gdstk.Label(
            pin_name,
            (x_pos, PIN_Y),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 3. Add text art on met1 (most visible layer)
    # -------------------------------------------------------------------------
    
    # Calculate text area (leave margins from edges and pins)
    margin = 8.0  # um from edges
    text_area_width = DIE_WIDTH_UM - 2 * margin
    text_area_height = DIE_HEIGHT_UM - 2 * margin - 10  # Extra margin from top for pins
    
    # Calculate optimal font size if not specified
    lines = text.split('\n')
    max_line_len = max(len(line) for line in lines)
    num_lines = len(lines)
    
    # gdstk text aspect ratio
    char_width_ratio = 9/16
    line_height_ratio = 5/4
    
    if font_size is None:
        # Auto-calculate font size to fit
        width_per_char = text_area_width / (max_line_len * char_width_ratio) if max_line_len > 0 else 20
        height_per_line = text_area_height / (1 + (num_lines - 1) * line_height_ratio) if num_lines > 0 else 20
        
        font_size = min(width_per_char, height_per_line) * 0.85
        font_size = max(font_size, 0.5)   # Absolute minimum (DRC limit ~0.4 µm)
        font_size = min(font_size, 25.0)  # Maximum 25um
    
    # Calculate stroke width (gdstk text stroke is ~font_size * 9/32)
    stroke_width = font_size * 9 / 32
    
    print(f"Using font size: {font_size:.2f} µm")
    print(f"Estimated stroke width: {stroke_width:.2f} µm")
    
    # Warn about DRC and visibility
    if stroke_width < min_feature_size:
        print(f"⚠ WARNING: Stroke width ({stroke_width:.2f} µm) is below Sky130 minimum ({min_feature_size} µm)!")
        print(f"           This may cause DRC errors or fabrication issues.")
    elif stroke_width < 1.0:
        print(f"ℹ NOTE: Features are very small. Will need high magnification (500x+) or SEM to view.")
    elif stroke_width < 3.0:
        print(f"ℹ NOTE: Features will need ~200x magnification to read clearly.")
    
    # Generate text polygons
    text_polys = gdstk.text(
        text, 
        font_size, 
        (0, 0),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    if not text_polys:
        print("Warning: No text polygons generated!")
        return None
    
    # Calculate text bounding box
    all_points = []
    for poly in text_polys:
        all_points.extend(poly.points)
    
    if all_points:
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        text_width = max(xs) - min(xs)
        text_height = max(ys) - min(ys)
        text_min_x = min(xs)
        text_min_y = min(ys)
    else:
        print("Warning: No points in text polygons!")
        return None
    
    # Center text in the available area (lower part of die, away from pins)
    center_x = DIE_WIDTH_UM / 2
    center_y = (DIE_HEIGHT_UM - 15) / 2  # Shift down to avoid pin area
    
    offset_x = center_x - text_width / 2 - text_min_x
    offset_y = center_y - text_height / 2 - text_min_y
    
    # Add translated text polygons
    for poly in text_polys:
        translated = poly.translate(offset_x, offset_y)
        cell.add(translated)
    
    print(f"Text dimensions: {text_width:.2f} x {text_height:.2f} um")
    print(f"Text position: ({offset_x:.2f}, {offset_y:.2f})")
    
    # -------------------------------------------------------------------------
    # 4. Add decorative border on met1
    # -------------------------------------------------------------------------
    border_width = 2.0
    border_margin = 5.0
    
    # Outer border
    outer = gdstk.rectangle(
        (border_margin, border_margin),
        (DIE_WIDTH_UM - border_margin, DIE_HEIGHT_UM - border_margin - 8),  # Stay away from pins
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    # Inner cutout
    inner = gdstk.rectangle(
        (border_margin + border_width, border_margin + border_width),
        (DIE_WIDTH_UM - border_margin - border_width, DIE_HEIGHT_UM - border_margin - 8 - border_width)
    )
    
    # Create border by boolean difference
    border_polys = gdstk.boolean(outer, inner, "not",
                                  layer=TEXT_LAYER, datatype=TEXT_DATATYPE)
    for poly in border_polys:
        cell.add(poly)
    
    # -------------------------------------------------------------------------
    # 5. Save GDS file
    # -------------------------------------------------------------------------
    gds_path = output_path / f"{TOP_MODULE}.gds"
    lib.write_gds(gds_path)
    print(f"GDS saved to: {gds_path}")
    
    # -------------------------------------------------------------------------
    # 6. Create LEF file
    # -------------------------------------------------------------------------
    lef_content = generate_lef()
    lef_path = output_path / f"{TOP_MODULE}.lef"
    with open(lef_path, 'w') as f:
        f.write(lef_content)
    print(f"LEF saved to: {lef_path}")
    
    # -------------------------------------------------------------------------
    # 7. Create Verilog stub
    # -------------------------------------------------------------------------
    verilog_content = generate_verilog_stub()
    verilog_path = output_path / f"{TOP_MODULE}.v"
    with open(verilog_path, 'w') as f:
        f.write(verilog_content)
    print(f"Verilog saved to: {verilog_path}")
    
    # -------------------------------------------------------------------------
    # 8. Create SVG preview
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
    
    # Add pin definitions
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
// This is a silicon art project - minimal functional logic

`default_nettype none

module {TOP_MODULE} (
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
    """Create an SVG preview of the GDS."""
    
    cell = lib.cells[0]
    bbox = cell.bounding_box()
    
    if bbox is None:
        print("Warning: Cannot create SVG - no bounding box")
        return
    
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[1]
    cell_width = max_x - min_x
    cell_height = max_y - min_y
    
    padding = 20
    scale = min((width - 2*padding) / cell_width,
                (height - 2*padding) / cell_height)
    
    # Layer colors
    colors = {
        68: '#4169E1',   # met1 - Royal Blue
        71: '#FF6347',   # met4 - Tomato (pins)
        235: '#CCCCCC',  # boundary - Gray
    }
    
    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'  <rect width="100%" height="100%" fill="#1a1a2e"/>',
        f'  <g transform="translate({padding},{height - padding}) scale({scale},-{scale}) translate({-min_x},{-min_y})">',
    ]
    
    # Add polygons
    for poly in cell.polygons:
        layer = poly.layer
        color = colors.get(layer, '#888888')
        opacity = 0.3 if layer == 235 else 0.9
        
        points_str = ' '.join(f'{p[0]},{p[1]}' for p in poly.points)
        svg_parts.append(
            f'    <polygon points="{points_str}" fill="{color}" '
            f'fill-opacity="{opacity}" stroke="{color}" stroke-width="{0.3/scale}"/>'
        )
    
    svg_parts.extend([
        '  </g>',
        f'  <text x="{width/2}" y="30" text-anchor="middle" fill="white" font-size="16">',
        f'    TinyTapeout Silicon Art - {TOP_MODULE}',
        f'  </text>',
        '</svg>'
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_parts))
    
    print(f"SVG preview saved to: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create TinyTapeout silicon art GDS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Font Size Guide:
  25 µm  - Large text, ~10 chars, easy to read at 50x
  10 µm  - Medium text, ~60 chars, readable at 50x  
   5 µm  - Small text, ~250 chars, needs 100x microscope
   3 µm  - Tiny text, ~680 chars, needs 200x microscope
   2 µm  - Very tiny, ~1500 chars, needs 500x microscope
   1 µm  - Microscopic, ~6000 chars, needs SEM or 1000x
 0.5 µm  - Near DRC limit, ~24000 chars, SEM only

Sky130 minimum feature size: 0.14 µm (met1)
        """
    )
    parser.add_argument('--text', '-t', default='HELLO\nWORLD',
                       help='Text to render (use \\n for newlines)')
    parser.add_argument('--output', '-o', default='gds',
                       help='Output directory')
    parser.add_argument('--font-size', '-s', type=float, default=None,
                       help='Font size in µm (default: auto-fit to tile)')
    
    args = parser.parse_args()
    
    # Handle escaped newlines
    text = args.text.replace('\\n', '\n')
    
    print(f"Creating silicon art with text: {repr(text)}")
    print(f"Die size: {DIE_WIDTH_UM} x {DIE_HEIGHT_UM} µm")
    print(f"Output directory: {args.output}")
    print()
    
    gds_path = create_silicon_art_gds(text, args.output, font_size=args.font_size)
    
    if gds_path:
        print()
        print("=" * 60)
        print("SUCCESS! Files created:")
        print(f"  - {args.output}/{TOP_MODULE}.gds")
        print(f"  - {args.output}/{TOP_MODULE}.lef")
        print(f"  - {args.output}/{TOP_MODULE}.v")
        print(f"  - {args.output}/preview.svg")
        print("=" * 60)


if __name__ == '__main__':
    main()
