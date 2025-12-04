#!/usr/bin/env python3
"""
Unit tests for validate_lef.py
"""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from validate_lef import (
    parse_lef_pins,
    validate_lef,
    REQUIRED_PINS,
    EXPECTED_SIGNAL_PINS,
    EXPECTED_POWER_PINS,
    DIE_WIDTH_UM,
    DIE_HEIGHT_UM,
    PIN_WIDTH,
    PIN_HEIGHT,
    PIN_Y_CENTER,
)


@pytest.fixture
def valid_lef_content():
    """Generate a valid LEF file content with correct pin positions."""
    lef = f"""VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE {DIE_WIDTH_UM:.3f} BY {DIE_HEIGHT_UM:.3f} ;
  SYMMETRY X Y ;
"""
    
    # Add power pins with met4 (lowercase)
    power_width = 1.5
    for pin_name, use_type in EXPECTED_POWER_PINS:
        x_pos = 5.0 if pin_name == "VGND" else 8.0
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER met4 ;
        RECT {x_pos - power_width/2:.3f} 5.000 {x_pos + power_width/2:.3f} 106.520 ;
    END
  END {pin_name}
"""
    
    # Add signal pins at correct positions with met4 (lowercase)
    for pin_name, direction, x_pos in EXPECTED_SIGNAL_PINS:
        llx = x_pos - PIN_WIDTH / 2
        lly = PIN_Y_CENTER - PIN_HEIGHT / 2
        urx = x_pos + PIN_WIDTH / 2
        ury = PIN_Y_CENTER + PIN_HEIGHT / 2
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
    
    lef += """
END tt_um_silicon_art

END LIBRARY
"""
    return lef


@pytest.fixture
def wrong_layer_lef_content():
    """LEF with wrong layer name (Metal4 instead of met4)."""
    return f"""VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  SIZE {DIE_WIDTH_UM:.3f} BY {DIE_HEIGHT_UM:.3f} ;

  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT 143.830 110.520 144.130 111.520 ;
    END
  END clk

END tt_um_silicon_art
END LIBRARY
"""


@pytest.fixture
def wrong_size_lef_content():
    """LEF with wrong die size."""
    return """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  SIZE 202.080 BY 154.980 ;

  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER met4 ;
        RECT 143.830 110.520 144.130 111.520 ;
    END
  END clk

END tt_um_silicon_art
END LIBRARY
"""


class TestParseLefPins:
    def test_parse_single_pin(self):
        content = """
  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER met4 ;
        RECT 143.830 110.520 144.130 111.520 ;
    END
  END clk
"""
        pins = parse_lef_pins(content)
        assert "clk" in pins
        assert pins["clk"]["direction"] == "INPUT"
        assert pins["clk"]["layer"] == "met4"
        assert pins["clk"]["rect"] == (143.830, 110.520, 144.130, 111.520)

    def test_parse_power_pin(self):
        content = """
  PIN VGND
    DIRECTION INOUT ;
    USE GROUND ;
    PORT
      LAYER met4 ;
        RECT 4.25 5.00 5.75 106.52 ;
    END
  END VGND
"""
        pins = parse_lef_pins(content)
        assert "VGND" in pins
        assert pins["VGND"]["use"] == "GROUND"
        assert pins["VGND"]["layer"] == "met4"


class TestValidateLef:
    def test_valid_lef_passes(self, valid_lef_content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(valid_lef_content)
            f.flush()
            errors, warnings = validate_lef(f.name)
            assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_wrong_layer_detected(self, wrong_layer_lef_content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(wrong_layer_lef_content)
            f.flush()
            errors, warnings = validate_lef(f.name)
            layer_errors = [e for e in errors if "Metal4" in e and "met4" in e]
            assert len(layer_errors) > 0, "Should detect wrong layer name"

    def test_wrong_size_detected(self, wrong_size_lef_content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(wrong_size_lef_content)
            f.flush()
            errors, warnings = validate_lef(f.name)
            size_errors = [e for e in errors if "size" in e.lower()]
            assert len(size_errors) > 0, "Should detect wrong die size"

    def test_missing_file_error(self):
        errors, warnings = validate_lef("/nonexistent/file.lef")
        assert len(errors) == 1
        assert "not found" in errors[0]


class TestRequiredPins:
    def test_all_tinytapeout_pins_required(self):
        expected_pins = ["clk", "ena", "rst_n", "VGND", "VPWR"]
        for i in range(8):
            expected_pins.extend([
                f"ui_in[{i}]", f"uo_out[{i}]",
                f"uio_in[{i}]", f"uio_out[{i}]", f"uio_oe[{i}]",
            ])
        for pin in expected_pins:
            assert pin in REQUIRED_PINS, f"Missing required pin: {pin}"

    def test_required_pins_count(self):
        # 3 control + 2 power + 8*5 buses = 45 pins
        assert len(REQUIRED_PINS) == 45


class TestIntegration:
    def test_generator_creates_valid_lef(self):
        """Test that create_silicon_art.py generates a valid LEF file."""
        try:
            from create_silicon_art import generate_lef
        except ImportError:
            pytest.skip("gdstk not installed")
        
        lef_content = generate_lef()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(lef_content)
            f.flush()
            errors, warnings = validate_lef(f.name)
            assert len(errors) == 0, f"Generator created invalid LEF: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
