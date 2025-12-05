#!/usr/bin/env python3
"""
TinyTapeout Silicon Art Generator

Creates a complete GDS and LEF file for TinyTapeout custom_gds submission.
The design includes text art (canary token) visible on silicon.

This generates all required files for the custom_gds workflow:
- GDS file with text art and proper pin definitions  
- LEF file for the macro
- Verilog stub

Usage:
    python create_silicon_art.py

Output files are created in the gds/ directory.

IMPORTANT: Pin positions and die size MUST match the TinyTapeout IHP template EXACTLY.
           These values come from: tt-support-tools/tech/ihp-sg13g2/def/tt_block_1x1_pgvdd.def
"""

import sys
from pathlib import Path

try:
    import gdstk
    GDSTK_AVAILABLE = True
except ImportError:
    GDSTK_AVAILABLE = False

# =============================================================================
# TinyTapeout IHP-SG13G2 1x1 Tile Specifications
# These values are EXACT and come from the official IHP template DEF file:
# https://github.com/TinyTapeout/tt-support-tools/blob/main/tech/ihp-sg13g2/def/tt_block_1x1_pgvdd.def
# =============================================================================

# Die dimensions in micrometers (from DIEAREA in DEF)
# DIEAREA ( 0 0 ) ( 202080 154980 ) → 202.08 x 154.98 µm
DIE_WIDTH_UM = 202.08
DIE_HEIGHT_UM = 154.98

# Pin dimensions from DEF: ( -150 -500 ) ( 150 500 ) in nm = 0.3µm x 1.0µm
PIN_WIDTH = 0.3
PIN_HEIGHT = 1.0

# Signal pin Y center: PLACED at y=154480nm = 154.48µm
# With pin height 1.0µm, center is at 154.48µm, top edge at 154.98µm (= die top)
PIN_Y_CENTER = 154.48

# GDS Layers for IHP-SG13G2
# Layer numbers from: IHP-Open-PDK/ihp-sg13g2/libs.tech/klayout/tech/sg13g2.lyp

# Signal pin layer (Metal4)
PIN_LAYER = 50        # Metal4.pin
PIN_DATATYPE = 2      # pin datatype

# Power pin layer (TopMetal1 - required by TinyTapeout precheck)
POWER_PIN_LAYER = 126      # TopMetal1.pin
POWER_PIN_DATATYPE = 2     # pin datatype

# Text layer (Metal1.drawing - most visible under microscope)
TEXT_LAYER = 8  
TEXT_DATATYPE = 0

# Boundary/PR boundary layers (prBoundary.boundary = 189/4)
BOUND_LAYER = 189     # prBoundary
BOUND_DATATYPE = 4    # boundary datatype

# Label layer for pin names (Metal4.label = 50/1)
LABEL_LAYER = 50      # Metal4
LABEL_DATATYPE = 1    # label datatype

# Power pin label layer (TopMetal1.label = 126/1)
POWER_LABEL_LAYER = 126    # TopMetal1
POWER_LABEL_DATATYPE = 1   # label datatype

# Top module name
TOP_MODULE = "tt_um_silicon_art"

# =============================================================================
# Pin Definitions - EXACT values from IHP template DEF
# All coordinates in micrometers (converted from nanometers in DEF)
# =============================================================================

# Signal pins: (name, direction, x_center_um)
# These are the EXACT positions from the TinyTapeout IHP template DEF
SIGNAL_PINS = [
    # Control signals
    ("clk", "INPUT", 187.20),
    ("ena", "INPUT", 191.04),
    ("rst_n", "INPUT", 183.36),
    
    # Input bus ui_in[7:0]
    ("ui_in[0]", "INPUT", 179.52),
    ("ui_in[1]", "INPUT", 175.68),
    ("ui_in[2]", "INPUT", 171.84),
    ("ui_in[3]", "INPUT", 168.00),
    ("ui_in[4]", "INPUT", 164.16),
    ("ui_in[5]", "INPUT", 160.32),
    ("ui_in[6]", "INPUT", 156.48),
    ("ui_in[7]", "INPUT", 152.64),
    
    # Bidirectional input bus uio_in[7:0]
    ("uio_in[0]", "INPUT", 148.80),
    ("uio_in[1]", "INPUT", 144.96),
    ("uio_in[2]", "INPUT", 141.12),
    ("uio_in[3]", "INPUT", 137.28),
    ("uio_in[4]", "INPUT", 133.44),
    ("uio_in[5]", "INPUT", 129.60),
    ("uio_in[6]", "INPUT", 125.76),
    ("uio_in[7]", "INPUT", 121.92),
    
    # Output enable bus uio_oe[7:0]
    ("uio_oe[0]", "OUTPUT", 56.64),
    ("uio_oe[1]", "OUTPUT", 52.80),
    ("uio_oe[2]", "OUTPUT", 48.96),
    ("uio_oe[3]", "OUTPUT", 45.12),
    ("uio_oe[4]", "OUTPUT", 41.28),
    ("uio_oe[5]", "OUTPUT", 37.44),
    ("uio_oe[6]", "OUTPUT", 33.60),
    ("uio_oe[7]", "OUTPUT", 29.76),
    
    # Bidirectional output bus uio_out[7:0]
    ("uio_out[0]", "OUTPUT", 87.36),
    ("uio_out[1]", "OUTPUT", 83.52),
    ("uio_out[2]", "OUTPUT", 79.68),
    ("uio_out[3]", "OUTPUT", 75.84),
    ("uio_out[4]", "OUTPUT", 72.00),
    ("uio_out[5]", "OUTPUT", 68.16),
    ("uio_out[6]", "OUTPUT", 64.32),
    ("uio_out[7]", "OUTPUT", 60.48),
    
    # Output bus uo_out[7:0]
    ("uo_out[0]", "OUTPUT", 118.08),
    ("uo_out[1]", "OUTPUT", 114.24),
    ("uo_out[2]", "OUTPUT", 110.40),
    ("uo_out[3]", "OUTPUT", 106.56),
    ("uo_out[4]", "OUTPUT", 102.72),
    ("uo_out[5]", "OUTPUT", 98.88),
    ("uo_out[6]", "OUTPUT", 95.04),
    ("uo_out[7]", "OUTPUT", 91.20),
]

# Power pins: width must be >= 1.2µm, must be within 10µm of top and bottom edges
# Using 1.5µm width for safety margin
POWER_PIN_WIDTH = 1.5
POWER_PIN_Y_START = 5.0  # Within 10µm of bottom
POWER_PIN_Y_END = DIE_HEIGHT_UM - 5.0  # Within 10µm of top

# Power pin X positions (these don't have to match template exactly, just need to be valid)
POWER_PINS = [
    ("VGND", "GROUND", 5.0),
    ("VPWR", "POWER", 8.0),
]


def create_silicon_art_gds(text="HELLO\nWORLD", output_dir="gds", font_size=None):
    """
    Create a complete TinyTapeout-compatible GDS with text art.
    
    Args:
        text: Text to render on the chip (canary token)
        output_dir: Directory for output files
        font_size: Font size in µm (None = auto-calculate to fit)
    """
    if not GDSTK_AVAILABLE:
        print("Error: gdstk library required. Install with: pip install gdstk")
        sys.exit(1)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create GDS library
    lib = gdstk.Library()
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
    # 2. Add signal pin shapes on Metal4 layer
    # -------------------------------------------------------------------------
    for pin_name, direction, x_pos in SIGNAL_PINS:
        # Pin rectangle centered at (x_pos, PIN_Y_CENTER)
        pin_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, PIN_Y_CENTER - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, PIN_Y_CENTER + PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(pin_rect)
        
        # Pin label
        label = gdstk.Label(
            pin_name,
            (x_pos, PIN_Y_CENTER),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 3. Add power pins on TopMetal1 layer (required by TinyTapeout precheck)
    # -------------------------------------------------------------------------
    for pin_name, use_type, x_pos in POWER_PINS:
        power_rect = gdstk.rectangle(
            (x_pos - POWER_PIN_WIDTH/2, POWER_PIN_Y_START),
            (x_pos + POWER_PIN_WIDTH/2, POWER_PIN_Y_END),
            layer=POWER_PIN_LAYER,
            datatype=POWER_PIN_DATATYPE
        )
        cell.add(power_rect)
        
        label = gdstk.Label(
            pin_name,
            (x_pos, (POWER_PIN_Y_START + POWER_PIN_Y_END) / 2),
            layer=POWER_LABEL_LAYER,
            texttype=POWER_LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 4. Add text art on Metal1.drawing layer
    # -------------------------------------------------------------------------
    
    # Calculate text area (leave margins)
    margin_left = 12.0   # Room for power pins
    margin_right = 3.0
    margin_bottom = 3.0
    margin_top = 8.0     # Room for signal pins
    
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
        width_per_char = text_area_width / (max_line_len * char_width_ratio) if max_line_len > 0 else 20
        height_per_line = text_area_height / (1 + (num_lines - 1) * line_height_ratio) if num_lines > 0 else 20
        font_size = min(width_per_char, height_per_line) * 0.85
        font_size = max(font_size, 0.5)
        font_size = min(font_size, 20.0)
    
    print(f"Using font size: {font_size:.2f} µm")
    
    # Generate text polygons
    text_polys = gdstk.text(
        text, 
        font_size, 
        (0, 0),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    if text_polys:
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
            
            # Center text in available area
            center_x = margin_left + text_area_width / 2
            center_y = margin_bottom + text_area_height / 2
            
            offset_x = center_x - text_width / 2 - text_min_x
            offset_y = center_y - text_height / 2 - text_min_y
            
            for poly in text_polys:
                cell.add(poly.translate(offset_x, offset_y))
            
            print(f"Text dimensions: {text_width:.2f} x {text_height:.2f} µm")
    
    # -------------------------------------------------------------------------
    # 5. Add decorative border
    # -------------------------------------------------------------------------
    border_width = 1.0
    border_margin = 3.0
    
    outer = gdstk.rectangle(
        (margin_left - 2, border_margin),
        (DIE_WIDTH_UM - border_margin, DIE_HEIGHT_UM - margin_top + 2),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    inner = gdstk.rectangle(
        (margin_left - 2 + border_width, border_margin + border_width),
        (DIE_WIDTH_UM - border_margin - border_width, DIE_HEIGHT_UM - margin_top + 2 - border_width)
    )
    border_polys = gdstk.boolean(outer, inner, "not", layer=TEXT_LAYER, datatype=TEXT_DATATYPE)
    for poly in border_polys:
        cell.add(poly)
    
    # -------------------------------------------------------------------------
    # 6. Save files
    # -------------------------------------------------------------------------
    gds_path = output_path / f"{TOP_MODULE}.gds"
    lib.write_gds(gds_path)
    print(f"GDS saved to: {gds_path}")
    
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
    Generate LEF file for the macro.
    
    CRITICAL: 
    - Die size must match template DEF exactly (202.08 x 154.98)
    - Pin positions must match template DEF exactly
    - Layer name must be "Metal4" (capital M) for IHP PDK
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
    
    # Power pins - must use "TopMetal1" for IHP (required by precheck)
    for pin_name, use_type, x_pos in POWER_PINS:
        llx = x_pos - POWER_PIN_WIDTH/2
        urx = x_pos + POWER_PIN_WIDTH/2
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER TopMetal1 ;
        RECT {llx:.3f} {POWER_PIN_Y_START:.3f} {urx:.3f} {POWER_PIN_Y_END:.3f} ;
    END
  END {pin_name}
"""
    
    # Signal pins - must use "Metal4" (capital M) and exact positions
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

    // Simple pass-through with XOR pattern
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
        return
    
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[1]
    cell_width = max_x - min_x
    cell_height = max_y - min_y
    
    padding = 20
    scale = min((width - 2*padding) / cell_width, (height - 2*padding) / cell_height)
    
    # IHP layer colors: Metal1=8, Metal4=50, TopMetal1=126, prBoundary=189
    colors = {8: '#4169E1', 50: '#FF6347', 126: '#FFD700', 189: '#CCCCCC'}
    
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
    
    parser = argparse.ArgumentParser(description='Create TinyTapeout silicon art GDS')
    parser.add_argument('--text', '-t', default='HELLO\nWORLD',
                       help='Text to render (use \\n for newlines)')
    parser.add_argument('--output', '-o', default='gds',
                       help='Output directory')
    parser.add_argument('--font-size', '-s', type=float, default=None,
                       help='Font size in µm (default: auto-fit to tile)')
    
    args = parser.parse_args()
    text = args.text.replace('\\n', '\n')
    
    print(f"Creating silicon art with text: {repr(text)}")
    print(f"Die size: {DIE_WIDTH_UM} x {DIE_HEIGHT_UM} µm (IHP 1x1 tile)")
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
