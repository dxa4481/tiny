#!/usr/bin/env python3
"""
Local LEF/GDS validator for TinyTapeout custom_gds submissions.

This mimics the checks performed by TinyTapeout's precheck.
Run this locally before uploading to catch common issues.

Usage:
    python validate_lef.py gds/tt_um_silicon_art.lef
    python validate_lef.py gds/tt_um_silicon_art.lef gds/tt_um_silicon_art.gds
"""

import sys
import re
from pathlib import Path

# =============================================================================
# TinyTapeout TT10 1x1 Tile Specifications
# These values are EXACT from: tt-support-tools/def/tt_block_1x1_pg.def
# =============================================================================

# Die dimensions (from DIEAREA in DEF) - in micrometers
DIE_WIDTH_UM = 161.0
DIE_HEIGHT_UM = 111.52

# Pin dimensions: ( -150 -500 ) ( 150 500 ) in nm = 0.3µm x 1.0µm
PIN_WIDTH = 0.3
PIN_HEIGHT = 1.0

# Signal pin Y center (PLACED at y=111020nm = 111.02µm)
PIN_Y_CENTER = 111.02

# Power pin requirements
POWER_PIN_WIDTH_MIN = 1.2  # Minimum width in µm

# =============================================================================
# EXACT pin positions from TT10 template DEF (in micrometers)
# =============================================================================

EXPECTED_SIGNAL_PINS = [
    # Control signals
    ("clk", "INPUT", 143.980),
    ("ena", "INPUT", 146.740),
    ("rst_n", "INPUT", 141.220),
    
    # Input bus ui_in[7:0]
    ("ui_in[0]", "INPUT", 138.460),
    ("ui_in[1]", "INPUT", 135.700),
    ("ui_in[2]", "INPUT", 132.940),
    ("ui_in[3]", "INPUT", 130.180),
    ("ui_in[4]", "INPUT", 127.420),
    ("ui_in[5]", "INPUT", 124.660),
    ("ui_in[6]", "INPUT", 121.900),
    ("ui_in[7]", "INPUT", 119.140),
    
    # Bidirectional input bus uio_in[7:0]
    ("uio_in[0]", "INPUT", 116.380),
    ("uio_in[1]", "INPUT", 113.620),
    ("uio_in[2]", "INPUT", 110.860),
    ("uio_in[3]", "INPUT", 108.100),
    ("uio_in[4]", "INPUT", 105.340),
    ("uio_in[5]", "INPUT", 102.580),
    ("uio_in[6]", "INPUT", 99.820),
    ("uio_in[7]", "INPUT", 97.060),
    
    # Output enable bus uio_oe[7:0]
    ("uio_oe[0]", "OUTPUT", 50.140),
    ("uio_oe[1]", "OUTPUT", 47.380),
    ("uio_oe[2]", "OUTPUT", 44.620),
    ("uio_oe[3]", "OUTPUT", 41.860),
    ("uio_oe[4]", "OUTPUT", 39.100),
    ("uio_oe[5]", "OUTPUT", 36.340),
    ("uio_oe[6]", "OUTPUT", 33.580),
    ("uio_oe[7]", "OUTPUT", 30.820),
    
    # Bidirectional output bus uio_out[7:0]
    ("uio_out[0]", "OUTPUT", 72.220),
    ("uio_out[1]", "OUTPUT", 69.460),
    ("uio_out[2]", "OUTPUT", 66.700),
    ("uio_out[3]", "OUTPUT", 63.940),
    ("uio_out[4]", "OUTPUT", 61.180),
    ("uio_out[5]", "OUTPUT", 58.420),
    ("uio_out[6]", "OUTPUT", 55.660),
    ("uio_out[7]", "OUTPUT", 52.900),
    
    # Output bus uo_out[7:0]
    ("uo_out[0]", "OUTPUT", 94.300),
    ("uo_out[1]", "OUTPUT", 91.540),
    ("uo_out[2]", "OUTPUT", 88.780),
    ("uo_out[3]", "OUTPUT", 86.020),
    ("uo_out[4]", "OUTPUT", 83.260),
    ("uo_out[5]", "OUTPUT", 80.500),
    ("uo_out[6]", "OUTPUT", 77.740),
    ("uo_out[7]", "OUTPUT", 74.980),
]

EXPECTED_POWER_PINS = [
    ("VGND", "GROUND"),
    ("VPWR", "POWER"),
]

REQUIRED_PINS = [pin[0] for pin in EXPECTED_SIGNAL_PINS] + [pin[0] for pin in EXPECTED_POWER_PINS]


def parse_lef_pins(content):
    """Parse pin definitions from LEF file content."""
    pins = {}
    
    pin_blocks = re.split(r'\n\s*PIN\s+', content)
    for block in pin_blocks[1:]:
        pin_name_match = re.match(r'(\S+)', block)
        if not pin_name_match:
            continue
        pin_name = pin_name_match.group(1)
        
        pin_info = {'direction': None, 'use': None, 'layer': None, 'rect': None}
        
        dir_match = re.search(r'DIRECTION\s+(\w+)', block)
        if dir_match:
            pin_info['direction'] = dir_match.group(1)
        
        use_match = re.search(r'USE\s+(\w+)', block)
        if use_match:
            pin_info['use'] = use_match.group(1)
        
        port_match = re.search(r'PORT\s*\n(.*?)END', block, re.DOTALL)
        if port_match:
            port_content = port_match.group(1)
            
            layer_match = re.search(r'LAYER\s+(\w+)', port_content)
            if layer_match:
                pin_info['layer'] = layer_match.group(1)
            
            rect_match = re.search(
                r'RECT\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)',
                port_content
            )
            if rect_match:
                pin_info['rect'] = tuple(float(x) for x in rect_match.groups())
        
        pins[pin_name] = pin_info
    
    return pins


def validate_lef(lef_path):
    """Validate a LEF file for TinyTapeout compatibility."""
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
    
    # Check SIZE - must match TT10 1x1 tile exactly
    size_match = re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)', content)
    if size_match:
        die_width = float(size_match.group(1))
        die_height = float(size_match.group(2))
        print(f"SIZE: {die_width} x {die_height} µm")
        
        # Must match exactly (with small tolerance for floating point)
        if abs(die_width - DIE_WIDTH_UM) > 0.01 or abs(die_height - DIE_HEIGHT_UM) > 0.01:
            errors.append(
                f"Die size {die_width} x {die_height} does not match TT10 1x1 template "
                f"({DIE_WIDTH_UM} x {DIE_HEIGHT_UM}). Use a valid tile size!"
            )
    else:
        errors.append("No SIZE definition found in LEF file")
        return errors, warnings
    
    # Parse all PIN definitions
    pins = parse_lef_pins(content)
    print(f"Found {len(pins)} pins")
    
    # Check for required pins
    for required_pin in REQUIRED_PINS:
        if required_pin not in pins:
            errors.append(f"Missing required pin: {required_pin}")
    
    # Validate each pin
    for pin_name, pin_info in pins.items():
        # Check layer - must be "met4" (lowercase)
        if pin_info['layer'] is None:
            errors.append(f"Pin {pin_name} is missing LAYER definition")
        elif pin_info['layer'] == "Metal4":
            errors.append(f"Pin {pin_name} uses 'Metal4' - must be 'met4' (lowercase)")
        elif pin_info['layer'] not in ["met4", "met3", "met2", "met1"]:
            warnings.append(f"Pin {pin_name} uses unusual layer: {pin_info['layer']}")
        
        if pin_info['rect'] is None:
            errors.append(f"Pin {pin_name} is missing RECT definition")
    
    # Validate signal pin positions (must match template exactly)
    tolerance = 0.01  # 10nm tolerance
    for pin_name, direction, expected_x in EXPECTED_SIGNAL_PINS:
        if pin_name not in pins:
            continue
        
        pin = pins[pin_name]
        if pin['rect'] is None:
            continue
        
        llx, lly, urx, ury = pin['rect']
        actual_x = (llx + urx) / 2
        actual_y = (lly + ury) / 2
        
        # Expected rectangle
        exp_llx = expected_x - PIN_WIDTH / 2
        exp_lly = PIN_Y_CENTER - PIN_HEIGHT / 2
        exp_urx = expected_x + PIN_WIDTH / 2
        exp_ury = PIN_Y_CENTER + PIN_HEIGHT / 2
        
        if abs(actual_x - expected_x) > tolerance or abs(actual_y - PIN_Y_CENTER) > tolerance:
            errors.append(
                f"Pin {pin_name} has port {llx:.3f},{lly:.3f},{urx:.3f},{ury:.3f} "
                f"on layer {pin['layer']}, expected {exp_llx:.3f},{exp_lly:.3f},"
                f"{exp_urx:.3f},{exp_ury:.3f}"
            )
    
    # Validate power pins
    for pin_name, use_type in EXPECTED_POWER_PINS:
        if pin_name not in pins:
            continue
        
        pin = pins[pin_name]
        if pin['rect'] is None:
            continue
        
        llx, lly, urx, ury = pin['rect']
        width = urx - llx
        
        if width < POWER_PIN_WIDTH_MIN:
            errors.append(f"{pin_name} width ({width:.3f}µm) < required {POWER_PIN_WIDTH_MIN}µm")
        
        if lly > 10.0:
            errors.append(f"{pin_name} too far from bottom edge: {lly:.3f}µm > 10µm")
        
        if DIE_HEIGHT_UM - ury > 10.0:
            errors.append(f"{pin_name} too far from top edge: {DIE_HEIGHT_UM - ury:.3f}µm > 10µm")
    
    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_lef.py <lef_file>")
        sys.exit(1)
    
    lef_path = sys.argv[1]
    
    print("=" * 60)
    print("TinyTapeout TT10 Local Validator")
    print("=" * 60)
    print(f"\nValidating LEF: {lef_path}")
    print("-" * 40)
    
    errors, warnings = validate_lef(lef_path)
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"   - {w}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"   - {e}")
        print("\n❌ VALIDATION FAILED")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
