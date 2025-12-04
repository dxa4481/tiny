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

# Expected TinyTapeout pins
REQUIRED_PINS = [
    "clk", "ena", "rst_n",
    "ui_in[0]", "ui_in[1]", "ui_in[2]", "ui_in[3]",
    "ui_in[4]", "ui_in[5]", "ui_in[6]", "ui_in[7]",
    "uo_out[0]", "uo_out[1]", "uo_out[2]", "uo_out[3]",
    "uo_out[4]", "uo_out[5]", "uo_out[6]", "uo_out[7]",
    "uio_in[0]", "uio_in[1]", "uio_in[2]", "uio_in[3]",
    "uio_in[4]", "uio_in[5]", "uio_in[6]", "uio_in[7]",
    "uio_out[0]", "uio_out[1]", "uio_out[2]", "uio_out[3]",
    "uio_out[4]", "uio_out[5]", "uio_out[6]", "uio_out[7]",
    "uio_oe[0]", "uio_oe[1]", "uio_oe[2]", "uio_oe[3]",
    "uio_oe[4]", "uio_oe[5]", "uio_oe[6]", "uio_oe[7]",
    "VGND", "VPWR",
]

# Valid layer names that TinyTapeout accepts
VALID_LAYERS = ["Metal4", "Metal3", "Metal2", "Metal1", "met4", "met3", "met2", "met1"]


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
    
    # Check SIZE
    size_match = re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)', content)
    if size_match:
        width, height = float(size_match.group(1)), float(size_match.group(2))
        print(f"SIZE: {width} x {height} µm")
        
        # Check for reasonable TinyTapeout tile size
        if width < 100 or width > 1700:
            warnings.append(f"Unusual width: {width}µm (expected ~161-1610µm for 1x1 to 8x2)")
        if height < 100 or height > 400:
            warnings.append(f"Unusual height: {height}µm (expected ~111-223µm for 1x1 to 8x2)")
    else:
        errors.append("No SIZE definition found in LEF file")
    
    # Parse all PIN definitions
    pin_pattern = re.compile(
        r'PIN\s+(\S+)\s*\n'
        r'(?:.*?\n)*?'
        r'\s*PORT\s*\n'
        r'(?:\s*LAYER\s+(\w+)\s*;)?'
        r'(?:.*?\n)*?'
        r'\s*END\s+\1',
        re.MULTILINE | re.DOTALL
    )
    
    # Simpler approach - find all PINs and check for LAYER
    pins_found = {}
    
    # Split by PIN blocks
    pin_blocks = re.split(r'\n\s*PIN\s+', content)
    for block in pin_blocks[1:]:  # Skip first (before any PIN)
        # Get pin name
        pin_name_match = re.match(r'(\S+)', block)
        if not pin_name_match:
            continue
        pin_name = pin_name_match.group(1)
        
        # Check for LAYER in PORT section
        port_match = re.search(r'PORT\s*\n(.*?)END', block, re.DOTALL)
        if port_match:
            port_content = port_match.group(1)
            layer_match = re.search(r'LAYER\s+(\w+)', port_content)
            if layer_match:
                layer = layer_match.group(1)
                pins_found[pin_name] = layer
                
                # Check layer name - TinyTapeout expects "Metal4" not "met4"
                if layer == "met4":
                    errors.append(f"Pin {pin_name} uses layer 'met4' - should be 'Metal4'")
                elif layer not in ["Metal4", "Metal3", "Metal2", "Metal1"]:
                    warnings.append(f"Pin {pin_name} uses unusual layer: {layer}")
            else:
                errors.append(f"Pin {pin_name} is missing LAYER definition in PORT")
        else:
            errors.append(f"Pin {pin_name} is missing PORT section")
    
    print(f"\nFound {len(pins_found)} pins with layers defined")
    
    # Check for required pins
    for required_pin in REQUIRED_PINS:
        if required_pin not in pins_found:
            errors.append(f"Missing required pin: {required_pin}")
    
    # Check for extra pins
    extra_pins = set(pins_found.keys()) - set(REQUIRED_PINS)
    if extra_pins:
        warnings.append(f"Extra pins found: {extra_pins}")
    
    # Power pin checks
    for power_pin in ["VGND", "VPWR"]:
        if power_pin in pins_found:
            # Check for proper RECT dimensions
            for block in pin_blocks[1:]:
                if block.startswith(power_pin):
                    rect_match = re.search(r'RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', block)
                    if rect_match:
                        llx, lly, urx, ury = [float(x) for x in rect_match.groups()]
                        width = urx - llx
                        height = ury - lly
                        if width < 1.2:
                            errors.append(f"{power_pin} width ({width:.3f}µm) is less than required 1.2µm")
                        print(f"  {power_pin}: {width:.2f} x {height:.2f} µm")
    
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
