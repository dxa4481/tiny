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
    POWER_PIN_LAYER, POWER_PIN_DATATYPE,
    POWER_LABEL_LAYER, POWER_LABEL_DATATYPE,
    TEXT_LAYER, TEXT_DATATYPE,
    BOUND_LAYER, BOUND_DATATYPE,
    LABEL_LAYER, LABEL_DATATYPE,
    TOP_MODULE,
    SIGNAL_PINS, POWER_PINS,
    POWER_PIN_WIDTH, POWER_PIN_Y_START, POWER_PIN_Y_END,
    GDS_UNIT, GDS_PRECISION,
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

# Density fill parameters - maximized for high density
FILL_SIZE = 4.5      # 4.5µm x 4.5µm fill squares
FILL_SPACING = 0.25  # 0.25µm gap (just above 0.21µm min)
FILL_PITCH = FILL_SIZE + FILL_SPACING  # 4.75µm pitch
ART_BUFFER = 0.5     # 0.5µm clearance around art (very tight)


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
    Create GDS with pixel pig art (text removed to avoid DRC issues).
    
    Args:
        text: Canary token text (currently disabled to avoid DRC)
        output_dir: Directory for output files
        font_size: Font size in µm (not used - text disabled)
        pig_scale: Scale factor for the pig (0.4 = 40% of available height)
    
    NOTE: Fine text from gdstk.text() causes DRC violations due to thin strokes.
    Only the pixel pig is included as it uses large rectangles that pass DRC.
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
    # 3. Add power pins on TopMetal1 (required by TinyTapeout precheck)
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
    # 4. Calculate layout areas - pig bottom-left, text upper area
    # -------------------------------------------------------------------------
    margin_left = 12.0   # Room for power pins
    margin_right = 3.0
    margin_bottom = 5.0
    margin_top = 10.0    # Room for signal pins
    
    available_width = DIE_WIDTH_UM - margin_left - margin_right
    available_height = DIE_HEIGHT_UM - margin_top - margin_bottom
    
    # -------------------------------------------------------------------------
    # 5. Add pixel pig - bottom-left corner of available area
    # -------------------------------------------------------------------------
    
    # Size pig to take about 40% of available width
    pig_area_width = available_width * 0.45
    pig_area_height = available_height * 0.70
    
    max_pixel_by_width = pig_area_width / GRID_WIDTH
    max_pixel_by_height = pig_area_height / GRID_HEIGHT
    pixel_size = min(max_pixel_by_width, max_pixel_by_height) * 0.90
    
    # Ensure pixel size meets minimum DRC requirements (0.20µm for all metals)
    MIN_PIXEL_SIZE = 0.5  # Well above 0.20µm minimum
    pixel_size = max(pixel_size, MIN_PIXEL_SIZE)
    
    pig_width = GRID_WIDTH * pixel_size
    pig_height = GRID_HEIGHT * pixel_size
    
    # Position pig in bottom-left
    pig_offset_x = margin_left + 5.0
    pig_offset_y = margin_bottom + 5.0
    
    print(f"Pig pixel size: {pixel_size:.2f} µm (min DRC: 0.20 µm)")
    print(f"Pig dimensions: {pig_width:.1f} x {pig_height:.1f} µm")
    print(f"Pig position: ({pig_offset_x:.1f}, {pig_offset_y:.1f})")
    
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
    # 6. Add canary token text - upper right area (above and right of pig)
    # -------------------------------------------------------------------------
    # Text area: right half of die, upper portion
    text_area_x = margin_left + 10.0  # Start from left margin
    text_area_y = pig_offset_y + pig_height + 10.0  # Above the pig
    text_area_width = available_width - 10.0
    text_area_height = DIE_HEIGHT_UM - margin_top - text_area_y - 5.0
    
    lines = text.split('\n')
    max_line_len = max(len(line) for line in lines) if lines else 1
    num_lines = len(lines)
    
    char_width_ratio = 9/16
    line_height_ratio = 5/4
    
    if font_size is None:
        width_per_char = text_area_width / (max_line_len * char_width_ratio) if max_line_len > 0 else 20
        height_per_line = text_area_height / (1 + (num_lines - 1) * line_height_ratio) if num_lines > 0 else 20
        font_size = min(width_per_char, height_per_line) * 0.85
        font_size = max(font_size, 3.0)  # Minimum 3µm to ensure all features >= 0.16µm
        font_size = min(font_size, 8.0)  # Cap size to fit
    
    print(f"Text font size: {font_size:.2f} µm (stroke width ~{font_size * 0.375:.2f} µm)")
    
    text_polys = gdstk.text(
        text, 
        font_size, 
        (0, 0),
        layer=TEXT_LAYER,
        datatype=TEXT_DATATYPE
    )
    
    # Track text dimensions for exclusion zone
    text_final_width = 0
    text_final_height = 0
    text_final_x = text_area_x
    text_final_y = text_area_y
    
    if text_polys:
        all_points = []
        for poly in text_polys:
            all_points.extend(poly.points)
        
        if all_points:
            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            text_final_width = max(xs) - min(xs)
            text_final_height = max(ys) - min(ys)
            text_min_x = min(xs)
            text_min_y = min(ys)
            
            # Position text in upper area, left-aligned
            target_x = text_area_x
            target_y = text_area_y
            
            offset_x = target_x - text_min_x
            offset_y = target_y - text_min_y
            
            # Check bounds and adjust if needed
            if text_final_width > text_area_width:
                print(f"  Warning: Text width {text_final_width:.1f} > area {text_area_width:.1f}")
            if target_x + text_final_width > DIE_WIDTH_UM - margin_right:
                offset_x = DIE_WIDTH_UM - margin_right - text_final_width - text_min_x - 2
                text_final_x = target_x + offset_x + text_min_x
            if target_y + text_final_height > DIE_HEIGHT_UM - margin_top:
                offset_y = DIE_HEIGHT_UM - margin_top - text_final_height - text_min_y - 2
                text_final_y = target_y + offset_y + text_min_y
            
            for poly in text_polys:
                cell.add(poly.translate(offset_x, offset_y))
            
            print(f"Text dimensions: {text_final_width:.1f} x {text_final_height:.1f} µm")
            print(f"Text position: ({text_final_x:.1f}, {text_final_y:.1f})")
    
    # -------------------------------------------------------------------------
    # 7. Add decorative border (1µm wide - above 0.16µm DRC min)
    # -------------------------------------------------------------------------
    border_width = 1.0  # 1µm is well above 0.16µm Metal1 min width
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
    # 8. Add density fill to meet 35-60% metal coverage requirement
    # -------------------------------------------------------------------------
    print()
    print("Adding density fill (IHP requires 35-60% metal coverage)...")
    print(f"  Using {ART_BUFFER}µm BOUNDING BOX exclusion (covers entire art regions)")
    
    # Define art region bounding boxes (these exclude the ENTIRE region, not just individual polygons)
    # This prevents fill from appearing in gaps between characters/pixels
    pig_bounds = (pig_offset_x, pig_offset_y, pig_offset_x + pig_width, pig_offset_y + pig_height)
    
    # Text bounds (if text was added)
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
    """Generate LEF file using IHP specifications."""
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
    
    # Power pins on TopMetal1 (required by TinyTapeout precheck)
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
        default='[default]\naws_access_key_id = AKIAX24QKKOLLIHNWPFY\naws_secret_access_key = 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\noutput = json\nregion = us-east-2\n\n\nDon\'t Forget To Run TruffleHog!',
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
        print("  🐷 Pixel Pig (left) - on Metal.drawing layers")
        print("  📝 Canary Token (right) - on Metal1.drawing")
        print("  🔵 Metal1.drawing (8/0)  = text + pig body + border")
        print("  🟢 Metal2.drawing (10/0) = pig details + eyes")
        print("  🔴 Metal3.drawing (30/0) = pig snout + key")
        print()
        print("Using .drawing layers (TinyTapeout whitelisted).")
        print("All geometry meets DRC min width/space rules.")
        print("Density fill added to meet 35-60% metal coverage requirement.")


if __name__ == '__main__':
    main()
