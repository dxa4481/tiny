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
# TinyTapeout IHP-SG13G2 1x1 Tile Specifications
# These values are EXACT from: tt-support-tools/tech/ihp-sg13g2/def/tt_block_1x1_pgvdd.def
# =============================================================================

# Die dimensions (from DIEAREA in DEF) - in micrometers
DIE_WIDTH_UM = 202.08
DIE_HEIGHT_UM = 154.98

# Pin dimensions: ( -150 -500 ) ( 150 500 ) in nm = 0.3µm x 1.0µm
PIN_WIDTH = 0.3
PIN_HEIGHT = 1.0

# Signal pin Y center (PLACED at y=154480nm = 154.48µm)
PIN_Y_CENTER = 154.48

# Power pin requirements
POWER_PIN_WIDTH_MIN = 1.2  # Minimum width in µm

# =============================================================================
# EXACT pin positions from IHP template DEF (in micrometers)
# =============================================================================

EXPECTED_SIGNAL_PINS = [
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
    
    # Check SIZE - must match IHP 1x1 tile exactly
    size_match = re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)', content)
    if size_match:
        die_width = float(size_match.group(1))
        die_height = float(size_match.group(2))
        print(f"SIZE: {die_width} x {die_height} µm")
        
        # Must match exactly (with small tolerance for floating point)
        if abs(die_width - DIE_WIDTH_UM) > 0.01 or abs(die_height - DIE_HEIGHT_UM) > 0.01:
            errors.append(
                f"Die size {die_width} x {die_height} does not match IHP 1x1 template "
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
        if pin_info['layer'] is None:
            errors.append(f"Pin {pin_name} is missing LAYER definition")
        elif pin_name in ['VPWR', 'VGND']:
            # Power pins must use TopMetal1 for IHP
            if pin_info['layer'] != "TopMetal1":
                errors.append(f"Power pin {pin_name} uses '{pin_info['layer']}' - must be 'TopMetal1' for IHP")
        else:
            # Signal pins must use Metal4 for IHP
            if pin_info['layer'] == "met4":
                errors.append(f"Pin {pin_name} uses 'met4' - must be 'Metal4' (capital M) for IHP")
            elif pin_info['layer'] != "Metal4":
                errors.append(f"Signal pin {pin_name} uses '{pin_info['layer']}' - must be 'Metal4' for IHP")
        
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
    print("TinyTapeout IHP Local Validator")
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
