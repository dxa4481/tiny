#!/usr/bin/env python3
"""
Unit tests for validate_lef.py

Tests the LEF file validator to ensure it catches common issues
before uploading to TinyTapeout.
"""

import pytest
import sys
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from validate_lef import (
    parse_lef_pins,
    validate_pin_positions,
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


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def valid_lef_content():
    """Generate a valid LEF file content with correct pin positions."""
    lef = """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE 161.000 BY 111.520 ;
  SYMMETRY X Y ;
"""
    
    # Add power pins
    for pin_name, use_type, x_pos in EXPECTED_POWER_PINS:
        lef += f"""
  PIN {pin_name}
    DIRECTION INOUT ;
    USE {use_type} ;
    PORT
      LAYER Metal4 ;
        RECT {x_pos - 0.75:.3f} 5.000 {x_pos + 0.75:.3f} 106.520 ;
    END
  END {pin_name}
"""
    
    # Add signal pins at correct positions
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
      LAYER Metal4 ;
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
def wrong_position_lef_content():
    """Generate a LEF file with clk at wrong position (the common error)."""
    # This mimics the error: clk at 180.55,153.81 instead of correct position
    lef = """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE 161.000 BY 111.520 ;
  SYMMETRY X Y ;

  PIN VGND
    DIRECTION INOUT ;
    USE GROUND ;
    PORT
      LAYER Metal4 ;
        RECT 4.250 5.000 5.750 106.520 ;
    END
  END VGND

  PIN VPWR
    DIRECTION INOUT ;
    USE POWER ;
    PORT
      LAYER Metal4 ;
        RECT 7.250 5.000 8.750 106.520 ;
    END
  END VPWR

  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT 143.55 110.52 143.85 111.52 ;
    END
  END clk
"""
    
    # Add remaining pins at correct positions (skip clk which we already added wrong)
    for pin_name, direction, x_pos in EXPECTED_SIGNAL_PINS:
        if pin_name == "clk":
            continue
        llx = x_pos - PIN_WIDTH / 2
        lly = PIN_Y_CENTER - PIN_HEIGHT / 2
        urx = x_pos + PIN_WIDTH / 2
        ury = PIN_Y_CENTER + PIN_HEIGHT / 2
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
    
    lef += """
END tt_um_silicon_art

END LIBRARY
"""
    return lef


@pytest.fixture
def missing_pin_lef_content():
    """Generate a LEF file missing required pins."""
    return """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE 161.000 BY 111.520 ;
  SYMMETRY X Y ;

  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT 149.00 110.52 149.30 111.52 ;
    END
  END clk

END tt_um_silicon_art

END LIBRARY
"""


@pytest.fixture
def wrong_layer_lef_content():
    """Generate a LEF file with wrong layer name (met4 instead of Metal4)."""
    return """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE 161.000 BY 111.520 ;
  SYMMETRY X Y ;

  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER met4 ;
        RECT 149.00 110.52 149.30 111.52 ;
    END
  END clk

END tt_um_silicon_art

END LIBRARY
"""


@pytest.fixture
def missing_layer_lef_content():
    """Generate a LEF file with missing LAYER definition."""
    return """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE 161.000 BY 111.520 ;
  SYMMETRY X Y ;

  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
        RECT 149.00 110.52 149.30 111.52 ;
    END
  END clk

END tt_um_silicon_art

END LIBRARY
"""


@pytest.fixture
def power_pin_too_narrow_lef_content():
    """Generate a LEF file with power pin that's too narrow."""
    return """VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO tt_um_silicon_art
  CLASS BLOCK ;
  FOREIGN tt_um_silicon_art 0 0 ;
  ORIGIN 0 0 ;
  SIZE 161.000 BY 111.520 ;
  SYMMETRY X Y ;

  PIN VGND
    DIRECTION INOUT ;
    USE GROUND ;
    PORT
      LAYER Metal4 ;
        RECT 4.500 5.000 5.500 106.520 ;
    END
  END VGND

  PIN VPWR
    DIRECTION INOUT ;
    USE POWER ;
    PORT
      LAYER Metal4 ;
        RECT 7.250 5.000 8.750 106.520 ;
    END
  END VPWR

END tt_um_silicon_art

END LIBRARY
"""


# =============================================================================
# Test parse_lef_pins
# =============================================================================

class TestParseLefPins:
    """Tests for the parse_lef_pins function."""
    
    def test_parse_single_pin(self):
        """Test parsing a single pin definition."""
        content = """
  PIN clk
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT 149.00 110.52 149.30 111.52 ;
    END
  END clk
"""
        pins = parse_lef_pins(content)
        assert "clk" in pins
        assert pins["clk"]["direction"] == "INPUT"
        assert pins["clk"]["use"] == "SIGNAL"
        assert pins["clk"]["layer"] == "Metal4"
        assert pins["clk"]["rect"] == (149.00, 110.52, 149.30, 111.52)
    
    def test_parse_power_pin(self):
        """Test parsing a power pin definition."""
        content = """
  PIN VGND
    DIRECTION INOUT ;
    USE GROUND ;
    PORT
      LAYER Metal4 ;
        RECT 4.25 5.00 5.75 106.52 ;
    END
  END VGND
"""
        pins = parse_lef_pins(content)
        assert "VGND" in pins
        assert pins["VGND"]["direction"] == "INOUT"
        assert pins["VGND"]["use"] == "GROUND"
        assert pins["VGND"]["layer"] == "Metal4"
        assert pins["VGND"]["rect"] == (4.25, 5.00, 5.75, 106.52)
    
    def test_parse_bus_pin(self):
        """Test parsing a bus pin with brackets."""
        content = """
  PIN ui_in[0]
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER Metal4 ;
        RECT 153.50 110.52 153.80 111.52 ;
    END
  END ui_in[0]
"""
        pins = parse_lef_pins(content)
        assert "ui_in[0]" in pins
        assert pins["ui_in[0]"]["direction"] == "INPUT"
    
    def test_parse_multiple_pins(self, valid_lef_content):
        """Test parsing multiple pins from a full LEF file."""
        pins = parse_lef_pins(valid_lef_content)
        
        # Should have all required pins
        assert len(pins) >= len(REQUIRED_PINS)
        
        # Check a few specific pins exist
        assert "clk" in pins
        assert "VGND" in pins
        assert "VPWR" in pins
        assert "ui_in[0]" in pins
        assert "uo_out[7]" in pins


# =============================================================================
# Test validate_pin_positions
# =============================================================================

class TestValidatePinPositions:
    """Tests for the validate_pin_positions function."""
    
    def test_correct_positions_pass(self, valid_lef_content):
        """Test that correct pin positions pass validation."""
        pins = parse_lef_pins(valid_lef_content)
        errors, warnings = validate_pin_positions(pins, DIE_WIDTH_UM, DIE_HEIGHT_UM)
        
        # Should have no position errors
        position_errors = [e for e in errors if "has port" in e]
        assert len(position_errors) == 0, f"Unexpected errors: {position_errors}"
    
    def test_wrong_position_detected(self, wrong_position_lef_content):
        """Test that wrong pin positions are detected."""
        pins = parse_lef_pins(wrong_position_lef_content)
        errors, warnings = validate_pin_positions(pins, DIE_WIDTH_UM, DIE_HEIGHT_UM)
        
        # Should detect the clk position error
        assert len(errors) > 0
        clk_errors = [e for e in errors if "clk" in e]
        assert len(clk_errors) > 0, "Should detect clk position error"
        assert "has port" in clk_errors[0]
        assert "expected" in clk_errors[0]
    
    def test_error_message_format(self, wrong_position_lef_content):
        """Test that error message matches TinyTapeout precheck format."""
        pins = parse_lef_pins(wrong_position_lef_content)
        errors, warnings = validate_pin_positions(pins, DIE_WIDTH_UM, DIE_HEIGHT_UM)
        
        clk_errors = [e for e in errors if "clk" in e]
        assert len(clk_errors) > 0
        
        error_msg = clk_errors[0]
        # Should match format: "Pin clk has port X,Y,X,Y on layer L, expected X,Y,X,Y"
        assert "Pin clk has port" in error_msg
        assert "on layer" in error_msg
        assert "expected" in error_msg
        assert "-pinonly" in error_msg
    
    def test_power_pin_width_check(self, power_pin_too_narrow_lef_content):
        """Test that narrow power pins are detected."""
        pins = parse_lef_pins(power_pin_too_narrow_lef_content)
        errors, warnings = validate_pin_positions(pins, DIE_WIDTH_UM, DIE_HEIGHT_UM)
        
        # Should detect VGND is too narrow (1.0um < 1.2um required)
        vgnd_errors = [e for e in errors if "VGND" in e and "width" in e]
        assert len(vgnd_errors) > 0, "Should detect VGND width error"


# =============================================================================
# Test validate_lef (full validation)
# =============================================================================

class TestValidateLef:
    """Tests for the full validate_lef function."""
    
    def test_valid_lef_passes(self, valid_lef_content):
        """Test that a valid LEF file passes all checks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(valid_lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            
            # Should have no errors
            assert len(errors) == 0, f"Unexpected errors: {errors}"
    
    def test_missing_file_error(self):
        """Test that missing file is reported."""
        errors, warnings = validate_lef("/nonexistent/path/file.lef")
        assert len(errors) == 1
        assert "not found" in errors[0]
    
    def test_missing_macro_error(self):
        """Test that missing MACRO definition is reported."""
        content = """VERSION 5.8 ;
BUSBITCHARS "[]" ;
END LIBRARY
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            assert any("MACRO" in e for e in errors)
    
    def test_missing_size_error(self):
        """Test that missing SIZE definition is reported."""
        content = """VERSION 5.8 ;
MACRO tt_um_test
  CLASS BLOCK ;
END tt_um_test
END LIBRARY
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            assert any("SIZE" in e for e in errors)
    
    def test_missing_pins_error(self, missing_pin_lef_content):
        """Test that missing required pins are reported."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(missing_pin_lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            
            # Should report missing pins
            missing_errors = [e for e in errors if "Missing required pin" in e]
            assert len(missing_errors) > 0
    
    def test_wrong_layer_error(self, wrong_layer_lef_content):
        """Test that wrong layer name (met4 instead of Metal4) is reported."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(wrong_layer_lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            
            # Should report wrong layer
            layer_errors = [e for e in errors if "met4" in e and "Metal4" in e]
            assert len(layer_errors) > 0
    
    def test_missing_layer_error(self, missing_layer_lef_content):
        """Test that missing LAYER definition is reported."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(missing_layer_lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            
            # Should report missing layer
            layer_errors = [e for e in errors if "missing LAYER" in e]
            assert len(layer_errors) > 0
    
    def test_position_validation_enabled_by_default(self, wrong_position_lef_content):
        """Test that position validation is enabled by default."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(wrong_position_lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name, check_positions=True)
            
            # Should detect position errors
            position_errors = [e for e in errors if "has port" in e]
            assert len(position_errors) > 0
    
    def test_position_validation_can_be_disabled(self, wrong_position_lef_content):
        """Test that position validation can be disabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(wrong_position_lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name, check_positions=False)
            
            # Should NOT detect position errors when disabled
            position_errors = [e for e in errors if "has port" in e]
            assert len(position_errors) == 0


# =============================================================================
# Test Required Pins List
# =============================================================================

class TestRequiredPins:
    """Tests for the required pins configuration."""
    
    def test_all_tinytapeout_pins_required(self):
        """Test that all standard TinyTapeout pins are in required list."""
        expected_pins = [
            "clk", "ena", "rst_n",
            "VGND", "VPWR",
        ]
        
        for i in range(8):
            expected_pins.extend([
                f"ui_in[{i}]",
                f"uo_out[{i}]",
                f"uio_in[{i}]",
                f"uio_out[{i}]",
                f"uio_oe[{i}]",
            ])
        
        for pin in expected_pins:
            assert pin in REQUIRED_PINS, f"Missing required pin: {pin}"
    
    def test_required_pins_count(self):
        """Test that we have exactly the right number of required pins."""
        # 3 control + 2 power + 8*5 buses = 45 pins
        expected_count = 3 + 2 + 40
        assert len(REQUIRED_PINS) == expected_count


# =============================================================================
# Integration Tests
# =============================================================================

# Check if gdstk is available (required for create_silicon_art imports)
try:
    import gdstk
    GDSTK_AVAILABLE = True
except ImportError:
    GDSTK_AVAILABLE = False


class TestIntegration:
    """Integration tests that combine multiple components."""
    
    @pytest.mark.skipif(not GDSTK_AVAILABLE, reason="gdstk not installed")
    def test_generator_creates_valid_lef(self):
        """Test that create_silicon_art.py generates a valid LEF file."""
        # Import the generator
        from create_silicon_art import generate_lef, DIE_WIDTH_UM, DIE_HEIGHT_UM
        
        # Generate LEF content
        lef_content = generate_lef()
        
        # Save to temp file and validate
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            
            # Should pass validation
            assert len(errors) == 0, f"Generator created invalid LEF: {errors}"
    
    @pytest.mark.skipif(not GDSTK_AVAILABLE, reason="gdstk not installed")
    def test_scaled_generator_creates_valid_lef(self):
        """Test that scaled die sizes produce valid LEF files."""
        from create_silicon_art import generate_lef
        
        # Test with 2x scale
        scaled_width = DIE_WIDTH_UM * 2
        scaled_height = DIE_HEIGHT_UM * 2
        
        lef_content = generate_lef(scaled_width, scaled_height)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lef', delete=False) as f:
            f.write(lef_content)
            f.flush()
            
            errors, warnings = validate_lef(f.name)
            
            # Should pass validation (positions should scale correctly)
            assert len(errors) == 0, f"Scaled generator created invalid LEF: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
