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
# These values must match the expected tile dimensions for TinyTapeout
# =============================================================================

# Die dimensions in micrometers (TinyTapeout 1x1 tile)
# Standard TinyTapeout tile size: 202.08 x 154.98 um
DIE_WIDTH_UM = 202.08
DIE_HEIGHT_UM = 154.98

# GDS Layers for Sky130
# met4.pin layer for signal pins in GDS (must match what precheck expects)
PIN_LAYER = 71
PIN_DATATYPE = 16  # met4.pin datatype

# met4.drawing layer for power pins in GDS
MET4_DRAWING_LAYER = 71
MET4_DRAWING_DATATYPE = 20  # met4.drawing datatype

# Text layer (met1.drawing - most visible under microscope)
TEXT_LAYER = 68  
TEXT_DATATYPE = 20

# Boundary/PR boundary layers
BOUND_LAYER = 235
BOUND_DATATYPE = 4

# Label layer for pin names (met4.label)
LABEL_LAYER = 71
LABEL_DATATYPE = 5

# Top module name
TOP_MODULE = "tt_um_silicon_art"

# =============================================================================
# Pin Definitions (from TinyTapeout TT10 DEF file)
# All coordinates in micrometers, pins on met4 at top edge
# Pin rectangle: (-150 -500) to (150 500) in nm = 0.3um x 1.0um
# Pin Y position: 111.02um (placed so top of 1um pin aligns with die top at 111.52um)
# =============================================================================

# Pin dimensions from DEF: ( -150 -500 ) ( 150 500 ) in nm
PIN_WIDTH = 0.3    # 300nm = 0.3um
PIN_HEIGHT = 1.0   # 1000nm = 1.0um

# Pin center Y position (scaled for 202.08x154.98 die)
# Original 111.02 * (154.98/111.52) = 154.31
PIN_Y = 154.31     # um from bottom

# Scale factor for X positions: 202.08 / 161.0 = 1.2551
PINS = [
    # Control signals (x positions scaled for 202.08um width)
    ("clk", "INPUT", 180.70),
    ("ena", "INPUT", 184.16),
    ("rst_n", "INPUT", 177.24),
    
    # Input bus ui_in[7:0]
    ("ui_in[0]", "INPUT", 173.78),
    ("ui_in[1]", "INPUT", 170.32),
    ("ui_in[2]", "INPUT", 166.86),
    ("ui_in[3]", "INPUT", 163.40),
    ("ui_in[4]", "INPUT", 159.94),
    ("ui_in[5]", "INPUT", 156.48),
    ("ui_in[6]", "INPUT", 153.02),
    ("ui_in[7]", "INPUT", 149.56),
    
    # Bidirectional input bus uio_in[7:0]
    ("uio_in[0]", "INPUT", 146.10),
    ("uio_in[1]", "INPUT", 142.63),
    ("uio_in[2]", "INPUT", 139.17),
    ("uio_in[3]", "INPUT", 135.71),
    ("uio_in[4]", "INPUT", 132.25),
    ("uio_in[5]", "INPUT", 128.79),
    ("uio_in[6]", "INPUT", 125.33),
    ("uio_in[7]", "INPUT", 121.87),
    
    # Output enable bus uio_oe[7:0]
    ("uio_oe[0]", "OUTPUT", 62.93),
    ("uio_oe[1]", "OUTPUT", 59.47),
    ("uio_oe[2]", "OUTPUT", 56.01),
    ("uio_oe[3]", "OUTPUT", 52.55),
    ("uio_oe[4]", "OUTPUT", 49.08),
    ("uio_oe[5]", "OUTPUT", 45.62),
    ("uio_oe[6]", "OUTPUT", 42.16),
    ("uio_oe[7]", "OUTPUT", 38.70),
    
    # Bidirectional output bus uio_out[7:0]
    ("uio_out[0]", "OUTPUT", 90.65),
    ("uio_out[1]", "OUTPUT", 87.19),
    ("uio_out[2]", "OUTPUT", 83.72),
    ("uio_out[3]", "OUTPUT", 80.26),
    ("uio_out[4]", "OUTPUT", 76.80),
    ("uio_out[5]", "OUTPUT", 73.34),
    ("uio_out[6]", "OUTPUT", 69.88),
    ("uio_out[7]", "OUTPUT", 66.42),
    
    # Output bus uo_out[7:0]
    ("uo_out[0]", "OUTPUT", 118.41),
    ("uo_out[1]", "OUTPUT", 114.94),
    ("uo_out[2]", "OUTPUT", 111.48),
    ("uo_out[3]", "OUTPUT", 108.02),
    ("uo_out[4]", "OUTPUT", 104.56),
    ("uo_out[5]", "OUTPUT", 101.10),
    ("uo_out[6]", "OUTPUT", 97.64),
    ("uo_out[7]", "OUTPUT", 94.18),
]

# Power pin definitions (on met4, positioned for proper power grid connection)
# Requirements from precheck/pin_check.py:
#   - Must be on layer "met4"
#   - Width must be >= 1.2um
#   - Must be within 10um of both top and bottom edges
#   - Must be entirely within die area
POWER_PIN_WIDTH = 1.5    # um (must be >= 1.2um)
POWER_PIN_Y_START = 5.0  # um from bottom (within 10um of bottom edge)
POWER_PIN_Y_END = DIE_HEIGHT_UM - 5.0  # um (within 10um of top edge)
POWER_PIN_HEIGHT = POWER_PIN_Y_END - POWER_PIN_Y_START  # um

POWER_PINS = [
    # (name, use_type, x_center_position) - scaled for 202.08um width
    ("VGND", "GROUND", 6.28),   # Left side
    ("VPWR", "POWER", 10.04),   # Left side, next to VGND
]


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
    # 2. Add signal pin shapes on met4.pin layer
    # -------------------------------------------------------------------------
    for pin_name, direction, x_pos in PINS:
        # Pin rectangle on met4.pin layer (71/16)
        pin_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, PIN_Y - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, PIN_Y + PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(pin_rect)
        
        # Pin label on met4.label layer (71/5)
        label = gdstk.Label(
            pin_name,
            (x_pos, PIN_Y),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 2b. Add power pins (VGND, VPWR) on met4.pin layer
    # These must span nearly the full height, within 10um of top and bottom
    # -------------------------------------------------------------------------
    for pin_name, use_type, x_pos in POWER_PINS:
        # Power pin rectangle (vertical stripe)
        power_rect = gdstk.rectangle(
            (x_pos - POWER_PIN_WIDTH/2, POWER_PIN_Y_START),
            (x_pos + POWER_PIN_WIDTH/2, POWER_PIN_Y_END),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(power_rect)
        
        # Power pin label
        label = gdstk.Label(
            pin_name,
            (x_pos, (POWER_PIN_Y_START + POWER_PIN_Y_END) / 2),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 3. Add text art on met1.drawing layer (most visible layer)
    # -------------------------------------------------------------------------
    
    # Calculate text area (leave margins from edges and pins)
    # Power pins are on the left (~10um), signal pins at top (~5um from top)
    margin_left = 15.0    # Leave room for power pins on left
    margin_right = 5.0
    margin_bottom = 5.0
    margin_top = 10.0     # Leave room for signal pins at top
    
    text_area_width = DIE_WIDTH_UM - margin_left - margin_right
    text_area_height = DIE_HEIGHT_UM - margin_top - margin_bottom
    
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
        font_size = min(font_size, 20.0)  # Maximum 20um for smaller die
    
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
    
    # Center text in the available area (avoiding power pins on left and signal pins at top)
    center_x = margin_left + text_area_width / 2
    center_y = margin_bottom + text_area_height / 2
    
    offset_x = center_x - text_width / 2 - text_min_x
    offset_y = center_y - text_height / 2 - text_min_y
    
    # Add translated text polygons
    for poly in text_polys:
        translated = poly.translate(offset_x, offset_y)
        cell.add(translated)
    
    print(f"Text dimensions: {text_width:.2f} x {text_height:.2f} um")
    print(f"Text position: ({offset_x:.2f}, {offset_y:.2f})")
    
    # -------------------------------------------------------------------------
    # 4. Add decorative border on met1.drawing (optional, for aesthetics)
    # -------------------------------------------------------------------------
    border_width = 1.5
    border_margin_left = 12.0  # Leave room for power pins
    border_margin_right = 3.0
    border_margin_bottom = 3.0
    border_margin_top = 8.0    # Leave room for signal pins
    
    # Outer border
    outer = gdstk.rectangle(
        (border_margin_left, border_margin_bottom),
        (DIE_WIDTH_UM - border_margin_right, DIE_HEIGHT_UM - border_margin_top),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    # Inner cutout
    inner = gdstk.rectangle(
        (border_margin_left + border_width, border_margin_bottom + border_width),
        (DIE_WIDTH_UM - border_margin_right - border_width, DIE_HEIGHT_UM - border_margin_top - border_width)
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
    """
    Generate LEF file for the macro.
    
    The LEF file must match the template DEF pin positions exactly.
    Pin rectangles in LEF are specified as RECT llx lly urx ury (lower-left to upper-right).
    
    From DEF file:
    - Signal pins: LAYER met4 ( -150 -500 ) ( 150 500 ) at PLACED (x, 111020) N
      This means rectangle from (x-0.15, 110.52) to (x+0.15, 111.52) um
    """
    
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
    
    # Add power pin definitions (VGND, VPWR)
    # Power pins must be on met4 with width >= 1.2um and span nearly full height
    for pin_name, use_type, x_pos in POWER_PINS:
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER met4 ;
        RECT {x_pos - POWER_PIN_WIDTH/2:.3f} {POWER_PIN_Y_START:.3f} {x_pos + POWER_PIN_WIDTH/2:.3f} {POWER_PIN_Y_END:.3f} ;
    END
  END {pin_name}
"""
    
    # Add signal pin definitions
    # Pin positions must match the template DEF exactly
    # DEF has pins at y=111.02 with rectangle (-0.15, -0.5) to (0.15, 0.5)
    # So actual rectangle is (x-0.15, 110.52) to (x+0.15, 111.52)
    for pin_name, direction, x_pos in PINS:
        # Calculate exact rectangle bounds
        llx = x_pos - PIN_WIDTH/2   # lower left x
        lly = PIN_Y - PIN_HEIGHT/2  # lower left y (110.52)
        urx = x_pos + PIN_WIDTH/2   # upper right x
        ury = PIN_Y + PIN_HEIGHT/2  # upper right y (111.52)
        
        lef += f"""
  PIN {pin_name}
    DIRECTION {direction} ;
    USE SIGNAL ;
    PORT
      LAYER met4 ;
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
// This is a silicon art project - minimal functional logic

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
Font Size Guide (for 1x1 tile: 202.08 x 154.98 µm):
  20 µm  - Large text, ~8 chars, easy to read at 50x
  10 µm  - Medium text, ~60 chars, readable at 50x  
   5 µm  - Small text, ~250 chars, needs 100x microscope
   3 µm  - Tiny text, ~700 chars, needs 200x microscope
   2 µm  - Very tiny, ~1500 chars, needs 500x microscope
   1 µm  - Microscopic, ~6000 chars, needs SEM or 1000x
 0.5 µm  - Near DRC limit, ~24000 chars, SEM only

Sky130 minimum feature size: 0.14 µm (met1)
TinyTapeout 1x1 tile: 202.08 x 154.98 µm
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
    print(f"TinyTapeout 1x1 die size: {DIE_WIDTH_UM} x {DIE_HEIGHT_UM} µm")
    print(f"Output directory: {args.output}")
    print()
    
    gds_path = create_silicon_art_gds(text, args.output, font_size=args.font_size)
    
    if gds_path:
        print()
        print("=" * 60)
        print("SUCCESS! Files created for TinyTapeout:")
        print(f"  - {args.output}/{TOP_MODULE}.gds")
        print(f"  - {args.output}/{TOP_MODULE}.lef")
        print(f"  - {args.output}/{TOP_MODULE}.v")
        print(f"  - {args.output}/preview.svg")
        print("=" * 60)


if __name__ == '__main__':
    main()
