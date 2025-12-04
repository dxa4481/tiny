#!/usr/bin/env python3
"""
Pixel Pig + Canary Token Silicon Art Generator

Creates a combined design with:
- Canary token text (AWS credentials)
- Pixel pig artwork

Uses IHP-SG13G2 PDK layer specifications from create_silicon_art.py

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
    TEXT_LAYER, TEXT_DATATYPE,
    BOUND_LAYER, BOUND_DATATYPE,
    LABEL_LAYER, LABEL_DATATYPE,
    TOP_MODULE,
    SIGNAL_PINS, POWER_PINS,
    POWER_PIN_WIDTH, POWER_PIN_Y_START, POWER_PIN_Y_END,
)

# =============================================================================
# IHP-SG13G2 Layer Definitions for Pixel Art
# Using different metal layers for different colors
# =============================================================================

# 5 colors mapped to IHP metal layers (all datatype 0 for visibility)
# Using only Metal1, Metal2, Metal3 which are known to be visible in GDS viewer
PIXEL_LAYERS = {
    'light_pink':  {'layer': 8,   'datatype': 0, 'name': 'Metal1'},   # Body (same as text)
    'dark_pink':   {'layer': 10,  'datatype': 0, 'name': 'Metal2'},   # Details/ears  
    'medium_pink': {'layer': 30,  'datatype': 0, 'name': 'Metal3'},   # Snout
    'golden':      {'layer': 30,  'datatype': 0, 'name': 'Metal3'},   # Key (same as snout - both visible)
    'black':       {'layer': 10,  'datatype': 0, 'name': 'Metal2'},   # Eyes (same as dark - visible as dark)
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


def create_combined_gds(text, output_dir="gds", font_size=None, pig_scale=0.4):
    """
    Create GDS with both canary token text and pixel pig.
    
    Args:
        text: Canary token text to render
        output_dir: Directory for output files
        font_size: Font size in µm (None = auto)
        pig_scale: Scale factor for the pig (0.4 = 40% of available height)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
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
    for pin_name, direction, x_pos in SIGNAL_PINS:
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
    # 3. Add power pins
    # -------------------------------------------------------------------------
    for pin_name, use_type, x_pos in POWER_PINS:
        power_rect = gdstk.rectangle(
            (x_pos - POWER_PIN_WIDTH/2, POWER_PIN_Y_START),
            (x_pos + POWER_PIN_WIDTH/2, POWER_PIN_Y_END),
            layer=PIN_LAYER,
            datatype=PIN_DATATYPE
        )
        cell.add(power_rect)
        
        label = gdstk.Label(
            pin_name,
            (x_pos, (POWER_PIN_Y_START + POWER_PIN_Y_END) / 2),
            layer=LABEL_LAYER,
            texttype=LABEL_DATATYPE
        )
        cell.add(label)
    
    # -------------------------------------------------------------------------
    # 4. Calculate layout areas
    # -------------------------------------------------------------------------
    margin_left = 12.0   # Room for power pins
    margin_right = 3.0
    margin_bottom = 3.0
    margin_top = 8.0     # Room for signal pins
    
    available_width = DIE_WIDTH_UM - margin_left - margin_right
    available_height = DIE_HEIGHT_UM - margin_top - margin_bottom
    
    # Split: pig on left (30%), text on right (70%)
    pig_area_width = available_width * 0.28
    text_area_width = available_width * 0.70
    gap = available_width * 0.02
    
    pig_area_x = margin_left
    text_area_x = margin_left + pig_area_width + gap
    
    # -------------------------------------------------------------------------
    # 5. Add pixel pig (scaled down)
    # -------------------------------------------------------------------------
    
    # Calculate pixel size to fit pig in its area
    max_pixel_by_width = pig_area_width / GRID_WIDTH
    max_pixel_by_height = available_height / GRID_HEIGHT
    pixel_size = min(max_pixel_by_width, max_pixel_by_height) * 0.85
    
    pig_width = GRID_WIDTH * pixel_size
    pig_height = GRID_HEIGHT * pixel_size
    
    # Center pig in its area
    pig_offset_x = pig_area_x + (pig_area_width - pig_width) / 2
    pig_offset_y = margin_bottom + (available_height - pig_height) / 2
    
    print(f"Pig pixel size: {pixel_size:.2f} µm")
    print(f"Pig dimensions: {pig_width:.1f} x {pig_height:.1f} µm")
    
    # Add all pig pixels
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
            x = pig_offset_x + gx * pixel_size
            y = pig_offset_y + gy * pixel_size
            
            rect = gdstk.rectangle(
                (x, y),
                (x + pixel_size, y + pixel_size),
                layer=layer_info['layer'],
                datatype=layer_info['datatype']
            )
            cell.add(rect)
            total_pixels += 1
    
    print(f"Pig pixels: {total_pixels}")
    
    # -------------------------------------------------------------------------
    # 6. Add canary token text
    # -------------------------------------------------------------------------
    lines = text.split('\n')
    max_line_len = max(len(line) for line in lines)
    num_lines = len(lines)
    
    char_width_ratio = 9/16
    line_height_ratio = 5/4
    
    if font_size is None:
        width_per_char = text_area_width / (max_line_len * char_width_ratio) if max_line_len > 0 else 20
        height_per_line = available_height / (1 + (num_lines - 1) * line_height_ratio) if num_lines > 0 else 20
        font_size = min(width_per_char, height_per_line) * 0.85
        font_size = max(font_size, 0.5)
        font_size = min(font_size, 15.0)
    
    print(f"Text font size: {font_size:.2f} µm")
    
    text_polys = gdstk.text(
        text, 
        font_size, 
        (0, 0),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    if text_polys:
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
            
            # Center text in its area
            center_x = text_area_x + text_area_width / 2
            center_y = margin_bottom + available_height / 2
            
            offset_x = center_x - text_width / 2 - text_min_x
            offset_y = center_y - text_height / 2 - text_min_y
            
            for poly in text_polys:
                cell.add(poly.translate(offset_x, offset_y))
            
            print(f"Text dimensions: {text_width:.1f} x {text_height:.1f} µm")
    
    # -------------------------------------------------------------------------
    # 7. Add decorative border
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
    # 8. Save files
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
    """Generate LEF file using IHP specifications."""
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
    
    for pin_name, use_type, x_pos in POWER_PINS:
        llx = x_pos - POWER_PIN_WIDTH/2
        urx = x_pos + POWER_PIN_WIDTH/2
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER Metal4 ;
        RECT {llx:.3f} {POWER_PIN_Y_START:.3f} {urx:.3f} {POWER_PIN_Y_END:.3f} ;
    END
  END {pin_name}
"""
    
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
    
    # IHP layer colors (only Metal1-4 and boundary)
    colors = {
        8:   '#4169E1',  # Metal1 - Blue (text + pig body)
        10:  '#32CD32',  # Metal2 - Green (pig details + eyes)
        30:  '#FF6347',  # Metal3 - Tomato (pig snout + key)
        36:  '#9370DB',  # Metal4 - Purple (pins)
        63:  '#CCCCCC',  # prBndry - Gray (boundary)
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
        opacity = 0.3 if layer == 63 else 0.9
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
        default='[default]\naws_access_key_id = AKIAX24QKKOLLIHNWPFY\naws_secret_access_key = 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\noutput = json\nregion = us-east-2',
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
        print("SUCCESS! Combined design created:")
        print(f"  - {args.output}/{TOP_MODULE}.gds")
        print(f"  - {args.output}/{TOP_MODULE}.lef")
        print(f"  - {args.output}/{TOP_MODULE}.v")
        print(f"  - {args.output}/preview.svg")
        print("=" * 65)
        print()
        print("Design contents:")
        print("  🐷 Pixel Pig (left side) - on Metal1, Metal2, Metal3")
        print("  📝 Canary Token (right side) - on Metal1")
        print("  🔵 Metal1 (layer 8)  = text + pig body")
        print("  🟢 Metal2 (layer 10) = pig details + eyes")
        print("  🔴 Metal3 (layer 30) = pig snout + key")


if __name__ == '__main__':
    main()
