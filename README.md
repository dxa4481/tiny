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

TinyTapeout offers different tile sizes:

| Size | Dimensions | Approximate Text Capacity |
|------|------------|---------------------------|
| 1x1  | 161 × 112 µm | ~20 characters |
| 1x2  | 161 × 224 µm | ~50 characters |
| 2x2  | 322 × 224 µm | ~100 characters |
| 4x2  | 644 × 224 µm | ~200 characters |
| 8x2  | 1288 × 224 µm | ~500+ characters |

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

When adding art to functional designs:
- Use upper metal layers (met3, met4) to avoid routing conflicts
- Maintain minimum spacing rules (~0.14 µm for met1)
- Avoid power/ground rails
- Leave margins from cell boundaries

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

## License

Apache 2.0 - See [LICENSE](LICENSE)

## Acknowledgments

- [TinyTapeout](https://tinytapeout.com/) for making chip fabrication accessible
- [Efabless](https://efabless.com/) and [Google](https://developers.google.com/silicon) for the Sky130 shuttle program
- The open-source silicon community
