# TinyTapeout Silicon Art - Text on a Chip

[![gds](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/gds.yaml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/gds.yaml)

> Put a book on a chip! Create silicon art with text visible under a microscope.

## Overview

This project demonstrates how to create **silicon art** using [TinyTapeout](https://tinytapeout.com/) - putting text, characters, or even entire books onto a silicon wafer that can be viewed under a microscope.

![Hello World Preview](docs/hello_world_preview.svg)

### What You'll Get

- Text rendered as metal polygons on silicon
- Characters approximately 5-15 micrometers tall (depending on tile size)
- Visible under an optical microscope at 50-500x magnification
- A real fabricated chip with your art!

## Project Structure

```
├── src/
│   ├── project.v           # Minimal Verilog design (required by TinyTapeout)
│   ├── config.json         # OpenLane configuration
│   ├── text_to_gds.py      # Generate standalone text GDS
│   └── add_text_to_gds.py  # Add text to existing GDS (post-process)
├── test/
│   ├── test.py             # Cocotb testbench
│   └── Makefile
├── docs/
│   └── info.md             # Project documentation
├── .github/workflows/
│   ├── gds.yaml            # Build GDS + viewer
│   ├── test.yaml           # Run tests
│   └── docs.yaml           # Build docs
├── info.yaml               # TinyTapeout project info
└── README.md
```

## How It Works

### The Strategy

TinyTapeout uses the OpenLane flow to synthesize Verilog into a GDS (GDSII) file - the format used for chip fabrication. The GDS contains multiple layers representing different materials on the silicon.

For silicon art, we:
1. Create a minimal valid Verilog design (required for TinyTapeout submission)
2. Generate text as polygons on metal layers
3. These metal layers are physically created during fabrication
4. The metal patterns are visible under a microscope!

### Metal Layers (Sky130 PDK)

| Layer | GDS # | Notes |
|-------|-------|-------|
| met1  | 68:20 | Closest to silicon, most visible |
| met2  | 69:20 | Good visibility |
| met3  | 70:20 | Good visibility |
| met4  | 71:20 | Top layer available in TinyTapeout |
| li1   | 67:20 | Local interconnect |

### Tile Sizes

TinyTapeout offers different tile sizes. Dimensions vary by PDK:

**IHP-SG13G2 PDK:**
| Size | Dimensions | Approximate Text Capacity |
|------|------------|---------------------------|
| 1x1  | 202 × 155 µm | ~25 characters |
| 1x2  | 202 × 314 µm | ~60 characters |
| 2x2  | 420 × 314 µm | ~120 characters |

**Sky130 PDK:**
| Size | Dimensions | Approximate Text Capacity |
|------|------------|---------------------------|
| 1x1  | 161 × 112 µm | ~20 characters |
| 1x2  | 161 × 226 µm | ~50 characters |
| 2x2  | 335 × 226 µm | ~100 characters |

## Quick Start

### 1. Generate a "Hello World!" GDS

```bash
# Install dependencies
pip install gdstk

# Generate Hello World GDS
cd src
python text_to_gds.py --hello-world

# Or custom text
python text_to_gds.py "Hello\nWorld!" hello.gds
```

### 2. View the GDS

After pushing to GitHub, the GDS viewer will be available at:
```
https://YOUR_USERNAME.github.io/YOUR_REPO/
```

Or locally with KLayout:
```bash
pip install klayout
klayout text_art.gds
```

### 3. Customize Your Text

```bash
# Simple text
python text_to_gds.py "Your Name" name.gds

# Multi-line
python text_to_gds.py "Line 1\nLine 2\nLine 3" multiline.gds

# Larger tile for more text
python text_to_gds.py --tile-size 2x2 "More space!" large.gds

# From a file (for books/long text)
python text_to_gds.py --tile-size 8x2 --from-file book.txt book.gds

# Different metal layer
python text_to_gds.py --layer met2 "On Metal 2" met2.gds

# Custom font size (in micrometers)
python text_to_gds.py --font-size 3.0 "Tiny Text" tiny.gds
```

### 4. Add Text to Existing Design

If you have a GDS from OpenLane and want to add art:

```bash
python add_text_to_gds.py runs/wokwi/results/final/gds/tt_um_example.gds \
    output.gds "Hello World!" --layer met4
```

## For TinyTapeout Submission

### Method 1: Standalone Art (Recommended for Pure Art)

1. Fork this repository
2. Modify `src/text_to_gds.py` to generate your desired text
3. Update `info.yaml` with your project details
4. Push to GitHub - the Actions will build everything
5. Submit to TinyTapeout

### Method 2: Art + Functional Design

1. Create your functional Verilog design in `src/project.v`
2. After the GDS is built, use `add_text_to_gds.py` to add art
3. The text will be added to an upper metal layer (met4)

### Method 3: Custom Macro Integration

For advanced users, you can integrate the text GDS as a macro:

1. Generate text GDS with `text_to_gds.py`
2. Modify OpenLane config to include it as `EXTRA_GDS_FILES`
3. This merges the art directly into the build

## Viewing Your Chip

Once fabricated, you can view your silicon art with:

- **Optical Microscope**: 50-500x magnification
  - Metallurgical/reflected light microscope works best
  - Dark field illumination enhances metal visibility
  
- **Electron Microscope**: For ultimate detail
  - SEM (Scanning Electron Microscope) for surface detail
  - University labs often have access

### What to Expect

The metal layers appear as:
- **Bright/reflective** areas under optical microscope
- Different metal layers have slightly different colors
- Text will be approximately 5-20 µm tall depending on settings

## Putting a Book on a Chip

Yes, you can put actual book content on silicon! Here's how:

```bash
# Prepare your text file
echo "It was the best of times..." > excerpt.txt

# Generate with largest tile size
python text_to_gds.py --tile-size 8x2 --from-file excerpt.txt book.gds
```

**Capacity estimates** (approximate, depends on font size):
- 1x1 tile: ~50-100 bytes of text
- 8x2 tile: ~1-2 KB of text

For larger texts, consider:
- Multiple tiles
- Smaller font sizes (minimum ~1-2 µm)
- Abbreviations or encoding schemes

## Technical Details

### GDS Generation

The `text_to_gds.py` script uses [gdstk](https://heitzmann.github.io/gdstk/) to:
1. Render text using a built-in font
2. Convert characters to polygon paths
3. Place polygons on the specified metal layer
4. Output a GDSII file

### Font Characteristics

- Aspect ratio: 1:2 (width:height)
- Character spacing: 9/16 × font_size
- Line spacing: 5/4 × font_size
- Minimum recommended size: 2 µm

### DRC Considerations

**IHP-SG13G2 DRC Rules:**
- Metal1: min width 0.16µm, min space 0.18µm, density 35-60%
- Metal2-4: min width 0.20µm, min space 0.21µm, density 35-60%
- TopMetal1: min width 1.64µm, min space 1.64µm, density 25-70%

**Solution: Use `.filler` layers instead of `.drawing` layers!**

To avoid DRC violations from silicon art (text, pixel art, etc.), this project uses
**Metal.filler layers (datatype 22)** instead of Metal.drawing layers (datatype 0):

| Purpose | Layer | Datatype | DRC Checked? |
|---------|-------|----------|--------------|
| Normal routing | Metal1.drawing | 8/0 | ✅ Yes - width/space rules |
| **Art/Fill** | **Metal1.filler** | **8/22** | **❌ No width/space checks** |
| Pins | Metal4.pin | 50/2 | Pin enclosure only |

Key benefits of using `.filler` layers:
- **No min width/space DRC** - Fine text strokes allowed
- **Counts toward density** - Helps meet 35-60% requirement
- **Still fabricated** - Real metal visible under microscope
- **Standard approach** - Same as fill patterns added by tools

When adding art to functional designs:
- Use `.filler` layers for art (avoids DRC conflicts)
- Leave margins from cell boundaries
- Avoid power/ground rail areas

## Resources

- [TinyTapeout](https://tinytapeout.com/) - Submit your design
- [TinyTapeout Discord](https://tinytapeout.com/discord) - Community support
- [Sky130 PDK](https://skywater-pdk.readthedocs.io/) - Process documentation
- [gdstk Documentation](https://heitzmann.github.io/gdstk/) - GDS library
- [KLayout](https://www.klayout.de/) - GDS viewer/editor

## Examples

### Simple Hello World
```python
from text_to_gds import SiliconTextGenerator

gen = SiliconTextGenerator(tile_size="1x1", layer="met1")
cell = gen.create_text_cell("Hello\nWorld!")
gen.add_border(cell)
gen.save("hello_world.gds")
```

### Custom Book Content
```python
gen = SiliconTextGenerator(tile_size="8x2", layer="met1")

text = """In the beginning
was the Word,
and the Word was
with God..."""

cell = gen.create_text_cell(text, font_size=8)
gen.add_border(cell, border_width=3)
gen.save("genesis.gds")
```

## Troubleshooting: Die Area Mismatch Error

### The Error
```
Die area mismatch: expected 202.08x154.98 µm (1x1 tiles), got 161x111.52 µm
```

### Root Cause
This project was originally written for **Sky130 PDK** but TinyTapeout shuttles may use **IHP-SG13G2 PDK** which has completely different tile dimensions:

| PDK | 1x1 Tile Size | Pin Y Position | Layer Name |
|-----|---------------|----------------|------------|
| Sky130 | 161.0 × 111.52 µm | 111.02 µm | `met4` (lowercase) |
| **IHP-SG13G2** | **202.08 × 154.98 µm** | **154.48 µm** | **`Metal4`** (capital M) |

### What Was Changed (Dec 2024)
To fix for IHP PDK:

1. **Die dimensions**: Updated from 161×111.52 to **202.08×154.98 µm**

2. **PIN_Y_CENTER**: Changed from 111.02 to **154.48 µm** (pins at top edge)

3. **All 43 signal pin X positions**: Completely different coordinates extracted from:
   `tt-support-tools/tech/ihp-sg13g2/def/tt_block_1x1_pgvdd.def`

4. **LEF layer name**: Changed from `met4` to `Metal4` (IHP uses capital M)

5. **GDS layer numbers**: Updated to IHP layer scheme

### How to Verify Your PDK
Check which PDK your TinyTapeout shuttle uses:
- Look at the error message dimensions
- Check `tt-support-tools/tech/<pdk>/tile_sizes.yaml` for your shuttle

### Key Files Modified
- `src/create_silicon_art.py` - Main generator with all dimensions/pins
- `src/validate_lef.py` - Local validator 
- `test/test_validate_lef.py` - Tests

### Reference: IHP Pin Positions
Signal pins are at Y=154.48µm (center). X positions from DEF:
- clk: 187.20, ena: 191.04, rst_n: 183.36
- ui_in[0-7]: 179.52 → 152.64 (step -3.84)
- uio_in[0-7]: 148.80 → 121.92
- uo_out[0-7]: 118.08 → 91.20
- uio_out[0-7]: 87.36 → 60.48
- uio_oe[0-7]: 56.64 → 29.76

## Troubleshooting: DRC Violations (47 errors)

### The Error
```
INFO: Running klayout sg13g2 on tt_um_silicon_art.gds
WARNING: Layout dbu value (0.0009999999999999998) deviates from rule file dbu value (0.001)
Number of DRC errors: 47
ERROR: KLayout SG13G2 DRC ❌ Fail: Klayout sg13g2 failed with 47 DRC violations
```

### Root Causes
1. **Floating-point precision**: GDS database unit was 0.0009999... instead of exact 0.001
2. **Wrong layer datatypes**: Art was on `.drawing` layers which have strict width/space DRC rules

### The Fix (Dec 2024)

**1. Fixed DBU precision issue:**
```python
# Before (floating-point issues)
lib = gdstk.Library()

# After (exact precision)
lib = gdstk.Library(unit=1e-6, precision=1e-9)  # DBU = 0.001 exactly
```

**2. Changed art layers from `.drawing` to `.filler`:**
```python
# Before (DRC violations)
TEXT_LAYER = 8      # Metal1.drawing
TEXT_DATATYPE = 0   # .drawing - checked for min width/space

# After (no DRC issues)
TEXT_LAYER = 8      # Metal1
TEXT_DATATYPE = 22  # .filler - NOT checked for width/space DRC
```

### IHP Layer Reference
| Layer Name | GDS | Purpose | DRC? |
|------------|-----|---------|------|
| Metal1.drawing | 8/0 | Normal routing | ✅ Width/space |
| Metal1.filler | 8/22 | Fill patterns, art | ❌ No width/space |
| Metal1.pin | 8/2 | Pin markers | Enclosure only |
| Metal2.drawing | 10/0 | Normal routing | ✅ Width/space |
| Metal2.filler | 10/22 | Fill patterns, art | ❌ No width/space |
| Metal3.filler | 30/22 | Fill patterns, art | ❌ No width/space |
| Metal4.pin | 50/2 | Signal pins | Enclosure only |
| TopMetal1.pin | 126/2 | Power pins | Enclosure only |
| prBoundary | 189/4 | Die boundary | N/A |

### Key Insight
**Silicon art requires using `.filler` layers (datatype 22)** to avoid DRC violations.
The `.filler` datatype:
- Is still fabricated as real metal (visible under microscope)
- Counts toward density requirements  
- Is NOT checked for min width/space rules (allows fine text strokes)

## License

Apache 2.0 - See [LICENSE](LICENSE)

## Acknowledgments

- [TinyTapeout](https://tinytapeout.com/) for making chip fabrication accessible
- [Efabless](https://efabless.com/) and [Google](https://developers.google.com/silicon) for the Sky130 shuttle program
- The open-source silicon community
