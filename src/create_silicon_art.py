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

# gdstk is optional - only needed for GDS generation, not LEF generation
try:
    import gdstk
    GDSTK_AVAILABLE = True
except ImportError:
    GDSTK_AVAILABLE = False

# =============================================================================
# TinyTapeout 1x1 Tile Specifications
# These values must match the expected tile dimensions for TinyTapeout
# =============================================================================

# TinyTapeout TT10 template dimensions (1x1 tile)
# Pin positions are defined relative to this template size
TEMPLATE_WIDTH_UM = 161.00
TEMPLATE_HEIGHT_UM = 111.52

# Output die dimensions in micrometers
# Pin positions will be scaled from template to these dimensions
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
# All coordinates in micrometers for the TEMPLATE die (161.0 x 111.52 um)
# Pin rectangle size: 0.3um x 1.0um (fixed, does not scale)
# Signal pins are positioned with top edge at die boundary
# =============================================================================

# Pin dimensions from DEF: ( -150 -500 ) ( 150 500 ) in nm = 0.3um x 1.0um
PIN_WIDTH = 0.3    # 300nm = 0.3um (fixed size)
PIN_HEIGHT = 1.0   # 1000nm = 1.0um (fixed size)

# Signal pins are at top edge: pin top aligns with die top
# PIN_Y_CENTER = die_height - PIN_HEIGHT/2
# For template: 111.52 - 0.5 = 111.02
TEMPLATE_PIN_Y = 111.02

# Signal pin template X positions (from TT10 DEF)
# These are the exact positions for the 161.0 x 111.52 um template
TEMPLATE_SIGNAL_PINS = [
    # Control signals
    ("clk", "INPUT", 149.15),
    ("ena", "INPUT", 146.90),
    ("rst_n", "INPUT", 151.40),
    
    # Input bus ui_in[7:0]
    ("ui_in[0]", "INPUT", 153.65),
    ("ui_in[1]", "INPUT", 155.90),
    ("ui_in[2]", "INPUT", 158.15),
    ("ui_in[3]", "INPUT", 136.40),
    ("ui_in[4]", "INPUT", 138.65),
    ("ui_in[5]", "INPUT", 140.90),
    ("ui_in[6]", "INPUT", 143.15),
    ("ui_in[7]", "INPUT", 145.40),
    
    # Bidirectional input bus uio_in[7:0]
    ("uio_in[0]", "INPUT", 119.15),
    ("uio_in[1]", "INPUT", 121.40),
    ("uio_in[2]", "INPUT", 123.65),
    ("uio_in[3]", "INPUT", 125.90),
    ("uio_in[4]", "INPUT", 128.15),
    ("uio_in[5]", "INPUT", 130.40),
    ("uio_in[6]", "INPUT", 132.65),
    ("uio_in[7]", "INPUT", 134.90),
    
    # Output enable bus uio_oe[7:0]
    ("uio_oe[0]", "OUTPUT", 50.15),
    ("uio_oe[1]", "OUTPUT", 47.40),
    ("uio_oe[2]", "OUTPUT", 44.65),
    ("uio_oe[3]", "OUTPUT", 41.90),
    ("uio_oe[4]", "OUTPUT", 39.15),
    ("uio_oe[5]", "OUTPUT", 36.40),
    ("uio_oe[6]", "OUTPUT", 33.65),
    ("uio_oe[7]", "OUTPUT", 30.90),
    
    # Bidirectional output bus uio_out[7:0]
    ("uio_out[0]", "OUTPUT", 72.15),
    ("uio_out[1]", "OUTPUT", 69.40),
    ("uio_out[2]", "OUTPUT", 66.65),
    ("uio_out[3]", "OUTPUT", 63.90),
    ("uio_out[4]", "OUTPUT", 61.15),
    ("uio_out[5]", "OUTPUT", 58.40),
    ("uio_out[6]", "OUTPUT", 55.65),
    ("uio_out[7]", "OUTPUT", 52.90),
    
    # Output bus uo_out[7:0]
    ("uo_out[0]", "OUTPUT", 94.15),
    ("uo_out[1]", "OUTPUT", 91.40),
    ("uo_out[2]", "OUTPUT", 88.65),
    ("uo_out[3]", "OUTPUT", 85.90),
    ("uo_out[4]", "OUTPUT", 83.15),
    ("uo_out[5]", "OUTPUT", 80.40),
    ("uo_out[6]", "OUTPUT", 77.65),
    ("uo_out[7]", "OUTPUT", 74.90),
]

# Power pin definitions (on met4, positioned for proper power grid connection)
# Requirements from precheck/pin_check.py:
#   - Must be on layer "met4"
#   - Width must be >= 1.2um
#   - Must be within 10um of both top and bottom edges
#   - Must be entirely within die area
POWER_PIN_WIDTH = 1.5    # um (must be >= 1.2um)
POWER_PIN_Y_START = 5.0  # um from bottom (within 10um of bottom edge)

# Template power pin X positions
TEMPLATE_POWER_PINS = [
    ("VGND", "GROUND", 5.00),
    ("VPWR", "POWER", 8.00),
]


def get_scaled_pins(die_width, die_height):
    """
    Get pin positions scaled for the given die dimensions.
    
    Signal pin X positions scale proportionally with die width.
    Signal pin Y positions are fixed at (die_height - PIN_HEIGHT/2) so pin top
    aligns with die boundary.
    Pin rectangle size (0.3 x 1.0 um) is fixed and does not scale.
    
    Note: Scaled positions are rounded to the nearest 0.05 µm (50nm grid)
    to match TinyTapeout's expected pin positions.
    """
    x_scale = die_width / TEMPLATE_WIDTH_UM
    
    # Signal pin Y: top of pin aligns with die top
    pin_y = die_height - PIN_HEIGHT / 2
    
    # Scale signal pin X positions and round to nearest 0.05 µm (50nm grid)
    pins = []
    for name, direction, template_x in TEMPLATE_SIGNAL_PINS:
        scaled_x = template_x * x_scale
        # Round to nearest 0.05 µm to match TinyTapeout's expected pin grid
        scaled_x = round(scaled_x / 0.05) * 0.05
        pins.append((name, direction, scaled_x))
    
    return pins, pin_y


def get_scaled_power_pins(die_width, die_height):
    """
    Get power pin positions scaled for the given die dimensions.
    
    Power pins span from POWER_PIN_Y_START to (die_height - 5.0).
    X positions scale proportionally with die width.
    
    Note: Scaled positions are rounded to the nearest 0.05 µm (50nm grid)
    to match TinyTapeout's expected pin positions.
    """
    x_scale = die_width / TEMPLATE_WIDTH_UM
    
    power_pin_y_end = die_height - 5.0
    power_pin_height = power_pin_y_end - POWER_PIN_Y_START
    
    power_pins = []
    for name, use_type, template_x in TEMPLATE_POWER_PINS:
        scaled_x = template_x * x_scale
        # Round to nearest 0.05 µm to match TinyTapeout's expected pin grid
        scaled_x = round(scaled_x / 0.05) * 0.05
        power_pins.append((name, use_type, scaled_x))
    
    return power_pins, POWER_PIN_Y_START, power_pin_y_end


def create_silicon_art_gds(text="HELLO\nWORLD", output_dir="gds", font_size=None, 
                          min_feature_size=0.14, die_width=None, die_height=None):
    """
    Create a complete TinyTapeout-compatible GDS with text art.
    
    Args:
        text: Text to render on the chip
        output_dir: Directory for output files
        font_size: Font size in µm (None = auto-calculate to fit)
        min_feature_size: Minimum feature size in µm (Sky130 met1 = 0.14 µm)
        die_width: Die width in µm (None = use default 202.08)
        die_height: Die height in µm (None = use default 154.98)
    
    Sky130 Design Rules (for reference):
        - met1 min width: 0.14 µm
        - met1 min spacing: 0.14 µm
        - Recommended for visibility: ≥1 µm features (optical microscope)
    """
    if not GDSTK_AVAILABLE:
        print("Error: gdstk library required. Install with: pip install gdstk")
        sys.exit(1)
    
    # Use default dimensions if not specified
    actual_die_width = die_width if die_width else DIE_WIDTH_UM
    actual_die_height = die_height if die_height else DIE_HEIGHT_UM
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Get scaled pin positions
    pins, pin_y = get_scaled_pins(actual_die_width, actual_die_height)
    power_pins, power_y_start, power_y_end = get_scaled_power_pins(
        actual_die_width, actual_die_height
    )
    
    # Create GDS library
    lib = gdstk.Library()
    
    # Create main cell
    cell = lib.new_cell(TOP_MODULE)
    
    # -------------------------------------------------------------------------
    # 1. Add boundary rectangle (PR boundary)
    # -------------------------------------------------------------------------
    boundary = gdstk.rectangle(
        (0, 0), 
        (actual_die_width, actual_die_height),
        layer=BOUND_LAYER,
        datatype=BOUND_DATATYPE
    )
    cell.add(boundary)
    
    # -------------------------------------------------------------------------
    # 2. Add signal pin shapes on met4.pin layer
    # -------------------------------------------------------------------------
    for pin_name, direction, x_pos in pins:
        # Pin rectangle on met4.pin layer (71/16)
        pin_rect = gdstk.rectangle(
            (x_pos - PIN_WIDTH/2, pin_y - PIN_HEIGHT/2),
            (x_pos + PIN_WIDTH/2, pin_y + PIN_HEIGHT/2),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(pin_rect)
        
        # Pin label on met4.label layer (71/5)
        label = gdstk.Label(
            pin_name,
            (x_pos, pin_y),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 2b. Add power pins (VGND, VPWR) on met4.pin layer
    # These must span nearly the full height, within 10um of top and bottom
    # -------------------------------------------------------------------------
    for pin_name, use_type, x_pos in power_pins:
        # Power pin rectangle (vertical stripe)
        power_rect = gdstk.rectangle(
            (x_pos - POWER_PIN_WIDTH/2, power_y_start),
            (x_pos + POWER_PIN_WIDTH/2, power_y_end),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(power_rect)
        
        # Power pin label
        label = gdstk.Label(
            pin_name,
            (x_pos, (power_y_start + power_y_end) / 2),
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
    
    text_area_width = actual_die_width - margin_left - margin_right
    text_area_height = actual_die_height - margin_top - margin_bottom
    
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
        (actual_die_width - border_margin_right, actual_die_height - border_margin_top),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    # Inner cutout
    inner = gdstk.rectangle(
        (border_margin_left + border_width, border_margin_bottom + border_width),
        (actual_die_width - border_margin_right - border_width, actual_die_height - border_margin_top - border_width)
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
    lef_content = generate_lef(actual_die_width, actual_die_height)
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


def generate_lef(die_width=None, die_height=None):
    """
    Generate LEF file for the macro.
    
    The LEF file must match the template DEF pin positions exactly.
    Pin rectangles in LEF are specified as RECT llx lly urx ury (lower-left to upper-right).
    
    Args:
        die_width: Die width in µm (None = use template 161.0)
        die_height: Die height in µm (None = use template 111.52)
    
    From DEF file:
    - Signal pins: LAYER Metal4 ( -150 -500 ) ( 150 500 ) at PLACED (x, 111020) N
      This means rectangle from (x-0.15, 110.52) to (x+0.15, 111.52) um
    """
    # Use template dimensions if not specified
    actual_die_width = die_width if die_width else DIE_WIDTH_UM
    actual_die_height = die_height if die_height else DIE_HEIGHT_UM
    
    # Get scaled pin positions
    pins, pin_y = get_scaled_pins(actual_die_width, actual_die_height)
    power_pins, power_y_start, power_y_end = get_scaled_power_pins(
        actual_die_width, actual_die_height
    )
    
    lef = f"""VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO {TOP_MODULE}
  CLASS BLOCK ;
  FOREIGN {TOP_MODULE} 0 0 ;
  ORIGIN 0 0 ;
  SIZE {actual_die_width:.2f} BY {actual_die_height:.2f} ;
  SYMMETRY X Y ;
"""
    
    # Add power pin definitions (VGND, VPWR)
    # Power pins must be on met4 with width >= 1.2um and span nearly full height
    for pin_name, use_type, x_pos in power_pins:
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER Metal4 ;
        RECT {x_pos - POWER_PIN_WIDTH/2:.2f} {power_y_start:.2f} {x_pos + POWER_PIN_WIDTH/2:.2f} {power_y_end:.2f} ;
    END
  END {pin_name}
"""
    
    # Add signal pin definitions
    # Pin positions must match the template DEF exactly
    # Signal pins have top edge at die boundary
    for pin_name, direction, x_pos in pins:
        # Calculate exact rectangle bounds
        llx = x_pos - PIN_WIDTH/2   # lower left x
        lly = pin_y - PIN_HEIGHT/2  # lower left y
        urx = x_pos + PIN_WIDTH/2   # upper right x
        ury = pin_y + PIN_HEIGHT/2  # upper right y (= die_height)
        
        lef += f"""
  PIN {pin_name}
    DIRECTION {direction} ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT {llx:.2f} {lly:.2f} {urx:.2f} {ury:.2f} ;
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
Font Size Guide (for die: 202.08 x 154.98 µm):
  20 µm  - Large text, ~8 chars, easy to read at 50x
  10 µm  - Medium text, ~60 chars, readable at 50x  
   5 µm  - Small text, ~250 chars, needs 100x microscope
   3 µm  - Tiny text, ~700 chars, needs 200x microscope
   2 µm  - Very tiny, ~1500 chars, needs 500x microscope
   1 µm  - Microscopic, ~6000 chars, needs SEM or 1000x
 0.5 µm  - Near DRC limit, ~24000 chars, SEM only

Sky130 minimum feature size: 0.14 µm (met1)
Die size: 202.08 x 154.98 µm (pin positions scaled from TT10 template)
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
        print("SUCCESS! Files created for TinyTapeout:")
        print(f"  - {args.output}/{TOP_MODULE}.gds")
        print(f"  - {args.output}/{TOP_MODULE}.lef")
        print(f"  - {args.output}/{TOP_MODULE}.v")
        print(f"  - {args.output}/preview.svg")
        print("=" * 60)


if __name__ == '__main__':
    main()
