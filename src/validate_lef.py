#!/usr/bin/env python3
"""
Local LEF/GDS validator for TinyTapeout custom_gds submissions.

This mimics some of the checks performed by TinyTapeout's precheck.
Run this locally before uploading to catch common issues.

Usage:
    python validate_lef.py gds/tt_um_silicon_art.lef
    python validate_lef.py gds/tt_um_silicon_art.lef gds/tt_um_silicon_art.gds
"""

import sys
import re
from pathlib import Path

# =============================================================================
# TinyTapeout 1x1 Tile Specifications (TT10)
# =============================================================================

# Die dimensions in micrometers
DIE_WIDTH_UM = 161.00
DIE_HEIGHT_UM = 111.52

# Pin dimensions from DEF: ( -150 -500 ) ( 150 500 ) in nm = 0.3um x 1.0um
PIN_WIDTH = 0.3
PIN_HEIGHT = 1.0

# Pin Y center position (signal pins at top edge)
# DEF has pins at y=111020nm = 111.02um, so center is at 111.02um
PIN_Y_CENTER = 111.02

# Power pin specifications
POWER_PIN_WIDTH_MIN = 1.2  # Minimum width for power pins

# Valid layer names that TinyTapeout accepts
VALID_LAYERS = ["Metal4", "Metal3", "Metal2", "Metal1", "met4", "met3", "met2", "met1"]

# =============================================================================
# Expected TinyTapeout pins with their positions (from TT10 template DEF)
# All coordinates in micrometers
# =============================================================================

# Signal pin positions: (name, direction, x_center)
# These are the EXACT positions from the TinyTapeout TT10 template
EXPECTED_SIGNAL_PINS = [
    # Control signals
    ("clk", "INPUT", 149.15),
    ("ena", "INPUT", 146.90),
    ("rst_n", "INPUT", 151.40),
    
    # Input bus ui_in[7:0] - right side, descending
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

# Power pin positions: (name, use_type, x_center)
EXPECTED_POWER_PINS = [
    ("VGND", "GROUND", 5.00),
    ("VPWR", "POWER", 8.00),
]

# Build lookup for required pins
REQUIRED_PINS = [pin[0] for pin in EXPECTED_SIGNAL_PINS + EXPECTED_POWER_PINS]


def parse_lef_pins(content):
    """
    Parse pin definitions from LEF file content.
    
    Returns dict: pin_name -> {
        'direction': str,
        'use': str,
        'layer': str,
        'rect': (llx, lly, urx, ury)
    }
    """
    pins = {}
    
    # Split by PIN blocks
    pin_blocks = re.split(r'\n\s*PIN\s+', content)
    for block in pin_blocks[1:]:  # Skip first (before any PIN)
        # Get pin name
        pin_name_match = re.match(r'(\S+)', block)
        if not pin_name_match:
            continue
        pin_name = pin_name_match.group(1)
        
        pin_info = {
            'direction': None,
            'use': None,
            'layer': None,
            'rect': None,
        }
        
        # Parse DIRECTION
        dir_match = re.search(r'DIRECTION\s+(\w+)', block)
        if dir_match:
            pin_info['direction'] = dir_match.group(1)
        
        # Parse USE
        use_match = re.search(r'USE\s+(\w+)', block)
        if use_match:
            pin_info['use'] = use_match.group(1)
        
        # Check for LAYER and RECT in PORT section
        port_match = re.search(r'PORT\s*\n(.*?)END', block, re.DOTALL)
        if port_match:
            port_content = port_match.group(1)
            
            # Parse LAYER
            layer_match = re.search(r'LAYER\s+(\w+)', port_content)
            if layer_match:
                pin_info['layer'] = layer_match.group(1)
            
            # Parse RECT
            rect_match = re.search(
                r'RECT\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)',
                port_content
            )
            if rect_match:
                pin_info['rect'] = tuple(float(x) for x in rect_match.groups())
        
        pins[pin_name] = pin_info
    
    return pins


def validate_pin_positions(pins, die_width=None, die_height=None, tolerance=0.01):
    """
    Validate pin positions against expected TinyTapeout template positions.
    
    Args:
        pins: Dict of parsed pins from parse_lef_pins()
        die_width: Actual die width in µm (for scaling)
        die_height: Actual die height in µm (for scaling)
        tolerance: Position tolerance in µm (default 0.01µm = 10nm)
    
    Returns:
        (errors, warnings) tuple of lists
    """
    errors = []
    warnings = []
    
    # Calculate scale factors if die size differs from template
    x_scale = die_width / DIE_WIDTH_UM if die_width else 1.0
    y_scale = die_height / DIE_HEIGHT_UM if die_height else 1.0
    
    # Check signal pins
    for pin_name, direction, expected_x in EXPECTED_SIGNAL_PINS:
        if pin_name not in pins:
            continue  # Missing pins are caught elsewhere
        
        pin = pins[pin_name]
        if pin['rect'] is None:
            continue  # Missing RECT is caught elsewhere
        
        llx, lly, urx, ury = pin['rect']
        
        # Calculate expected rectangle (scaled)
        exp_x_center = expected_x * x_scale
        exp_y_center = PIN_Y_CENTER * y_scale
        exp_llx = exp_x_center - PIN_WIDTH / 2
        exp_lly = exp_y_center - PIN_HEIGHT / 2
        exp_urx = exp_x_center + PIN_WIDTH / 2
        exp_ury = exp_y_center + PIN_HEIGHT / 2
        
        # Check position with tolerance
        x_center = (llx + urx) / 2
        y_center = (lly + ury) / 2
        
        x_diff = abs(x_center - exp_x_center)
        y_diff = abs(y_center - exp_y_center)
        
        if x_diff > tolerance or y_diff > tolerance:
            errors.append(
                f"Pin {pin_name} has port {llx:.2f},{lly:.2f},{urx:.2f},{ury:.2f} "
                f"on layer {pin['layer']}, expected {exp_llx:.2f},{exp_lly:.2f},"
                f"{exp_urx:.2f},{exp_ury:.2f}. "
                f"Did you export the LEF file with -pinonly?"
            )
    
    # Check power pins (position check is less strict, mainly check width)
    for pin_name, use_type, expected_x in EXPECTED_POWER_PINS:
        if pin_name not in pins:
            continue
        
        pin = pins[pin_name]
        if pin['rect'] is None:
            continue
        
        llx, lly, urx, ury = pin['rect']
        width = urx - llx
        
        if width < POWER_PIN_WIDTH_MIN:
            errors.append(
                f"{pin_name} width ({width:.3f}µm) is less than required "
                f"{POWER_PIN_WIDTH_MIN}µm"
            )
    
    return errors, warnings


def validate_lef(lef_path, check_positions=True):
    """
    Validate a LEF file for TinyTapeout compatibility.
    
    Args:
        lef_path: Path to LEF file
        check_positions: Whether to validate pin positions (default True)
    
    Returns:
        (errors, warnings) tuple of lists
    """
    errors = []
    warnings = []
    
    lef_path = Path(lef_path)
    if not lef_path.exists():
        return [f"LEF file not found: {lef_path}"], []
    
    content = lef_path.read_text()
    
    # Check for MACRO definition
    macro_match = re.search(r'MACRO\s+(\w+)', content)
    if not macro_match:
        errors.append("No MACRO definition found in LEF file")
        return errors, warnings
    
    macro_name = macro_match.group(1)
    print(f"Found MACRO: {macro_name}")
    
    # Check SIZE
    die_width = None
    die_height = None
    size_match = re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)', content)
    if size_match:
        die_width, die_height = float(size_match.group(1)), float(size_match.group(2))
        print(f"SIZE: {die_width} x {die_height} µm")
        
        # Check for reasonable TinyTapeout tile size
        if die_width < 100 or die_width > 1700:
            warnings.append(
                f"Unusual width: {die_width}µm (expected ~161-1610µm for 1x1 to 8x2)"
            )
        if die_height < 100 or die_height > 400:
            warnings.append(
                f"Unusual height: {die_height}µm (expected ~111-223µm for 1x1 to 8x2)"
            )
    else:
        errors.append("No SIZE definition found in LEF file")
    
    # Parse all PIN definitions
    pins = parse_lef_pins(content)
    
    print(f"\nFound {len(pins)} pins")
    
    # Check for required pins
    for required_pin in REQUIRED_PINS:
        if required_pin not in pins:
            errors.append(f"Missing required pin: {required_pin}")
    
    # Check for extra pins
    extra_pins = set(pins.keys()) - set(REQUIRED_PINS)
    if extra_pins:
        warnings.append(f"Extra pins found: {extra_pins}")
    
    # Validate each pin's properties
    for pin_name, pin_info in pins.items():
        # Check layer
        if pin_info['layer'] is None:
            errors.append(f"Pin {pin_name} is missing LAYER definition in PORT")
        elif pin_info['layer'] == "met4":
            errors.append(
                f"Pin {pin_name} uses layer 'met4' - should be 'Metal4'"
            )
        elif pin_info['layer'] not in ["Metal4", "Metal3", "Metal2", "Metal1"]:
            warnings.append(f"Pin {pin_name} uses unusual layer: {pin_info['layer']}")
        
        # Check RECT
        if pin_info['rect'] is None:
            errors.append(f"Pin {pin_name} is missing RECT definition in PORT")
    
    # Validate pin positions (critical for TinyTapeout precheck!)
    if check_positions and die_width and die_height:
        pos_errors, pos_warnings = validate_pin_positions(
            pins, die_width, die_height
        )
        errors.extend(pos_errors)
        warnings.extend(pos_warnings)
    
    # Power pin dimension checks
    for pin_name in ["VGND", "VPWR"]:
        if pin_name in pins and pins[pin_name]['rect']:
            llx, lly, urx, ury = pins[pin_name]['rect']
            width = urx - llx
            height = ury - lly
            print(f"  {pin_name}: {width:.2f} x {height:.2f} µm")
    
    return errors, warnings


def validate_gds(gds_path):
    """Basic GDS validation using klayout."""
    errors = []
    warnings = []
    
    gds_path = Path(gds_path)
    if not gds_path.exists():
        return [f"GDS file not found: {gds_path}"], []
    
    try:
        import klayout.db as kdb
        
        layout = kdb.Layout()
        layout.read(str(gds_path))
        
        print(f"\nGDS file: {gds_path}")
        print(f"  Cells: {[cell.name for cell in layout.each_cell()]}")
        
        top_cell = layout.top_cell()
        if top_cell:
            bbox = top_cell.bbox()
            # Convert from database units to microns
            dbu = layout.dbu
            width = bbox.width() * dbu
            height = bbox.height() * dbu
            print(f"  Bounding box: {width:.2f} x {height:.2f} µm")
        else:
            warnings.append("No top cell found in GDS")
        
        # Check for required layers
        layers_found = set()
        for li in layout.layer_indices():
            info = layout.get_info(li)
            layers_found.add((info.layer, info.datatype))
        
        print(f"  Layers found: {len(layers_found)}")
        
        # Check for met4.pin (71/16)
        if (71, 16) not in layers_found:
            warnings.append("Layer met4.pin (71/16) not found - pins may not be visible")
        
        # Check for boundary (235/4)
        if (235, 4) not in layers_found:
            warnings.append("Layer PR boundary (235/4) not found")
            
    except ImportError:
        warnings.append("klayout not available - skipping GDS validation")
    except Exception as e:
        errors.append(f"Error reading GDS: {e}")
    
    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_lef.py <lef_file> [gds_file]")
        print("\nExample:")
        print("  python validate_lef.py gds/tt_um_silicon_art.lef")
        print("  python validate_lef.py gds/tt_um_silicon_art.lef gds/tt_um_silicon_art.gds")
        sys.exit(1)
    
    lef_path = sys.argv[1]
    gds_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("=" * 60)
    print("TinyTapeout Local Validator")
    print("=" * 60)
    
    all_errors = []
    all_warnings = []
    
    # Validate LEF
    print(f"\nValidating LEF: {lef_path}")
    print("-" * 40)
    errors, warnings = validate_lef(lef_path)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # Validate GDS if provided
    if gds_path:
        print(f"\nValidating GDS: {gds_path}")
        print("-" * 40)
        errors, warnings = validate_gds(gds_path)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
    
    # Print results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    if all_warnings:
        print(f"\n⚠️  WARNINGS ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"   - {w}")
    
    if all_errors:
        print(f"\n❌ ERRORS ({len(all_errors)}):")
        for e in all_errors:
            print(f"   - {e}")
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
