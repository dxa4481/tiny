#!/usr/bin/env python3
"""
Text to GDS Generator for TinyTapeout Silicon Art

This script generates GDS files with text rendered as polygons on metal layers.
The text will be visible under a microscope when the chip is fabricated.

Usage:
    python text_to_gds.py "Hello World!" output.gds

For TinyTapeout:
    - 1x1 tile is approximately 161.0 x 111.52 um
    - Text is rendered on metal layer 1 (met1) by default
    - Layer 68, datatype 20 = met1.drawing in Sky130 PDK
    
Sky130 Metal Layers:
    - met1: layer=68, datatype=20 (closest to silicon, most visible)
    - met2: layer=69, datatype=20
    - met3: layer=70, datatype=20
    - met4: layer=71, datatype=20
    - met5: layer=72, datatype=20 (topmost, but not available in TinyTapeout)
"""

import argparse
import sys
import math
from pathlib import Path

try:
    import gdstk
except ImportError:
    print("Error: gdstk library required. Install with: pip install gdstk")
    sys.exit(1)


# Sky130 PDK layer definitions
SKY130_LAYERS = {
    'met1': {'layer': 68, 'datatype': 20},  # Metal 1 drawing
    'met2': {'layer': 69, 'datatype': 20},  # Metal 2 drawing  
    'met3': {'layer': 70, 'datatype': 20},  # Metal 3 drawing
    'met4': {'layer': 71, 'datatype': 20},  # Metal 4 drawing
    'li1':  {'layer': 67, 'datatype': 20},  # Local interconnect
    'poly': {'layer': 66, 'datatype': 20},  # Polysilicon
    'nwell':{'layer': 64, 'datatype': 20},  # N-well (deep, very visible)
}

# TinyTapeout tile dimensions in micrometers
# 1x1 tile: 161.0 x 111.52 um (internal usable area slightly smaller)
TILE_WIDTH_UM = 161.0
TILE_HEIGHT_UM = 111.52

# Margins from edge (to avoid DRC issues and overlap with standard cells)
MARGIN_UM = 10.0


class SiliconTextGenerator:
    """Generates GDS text for silicon art on TinyTapeout."""
    
    def __init__(self, tile_size="1x1", layer="met1"):
        """
        Initialize the text generator.
        
        Args:
            tile_size: TinyTapeout tile size ("1x1", "1x2", "2x2", etc.)
            layer: Which metal layer to use for text
        """
        # Parse tile size
        parts = tile_size.lower().split('x')
        self.tiles_x = int(parts[0])
        self.tiles_y = int(parts[1])
        
        # Calculate available area
        self.width = TILE_WIDTH_UM * self.tiles_x - 2 * MARGIN_UM
        self.height = TILE_HEIGHT_UM * self.tiles_y - 2 * MARGIN_UM
        
        # Layer configuration
        if layer not in SKY130_LAYERS:
            raise ValueError(f"Unknown layer: {layer}. Available: {list(SKY130_LAYERS.keys())}")
        self.layer = SKY130_LAYERS[layer]['layer']
        self.datatype = SKY130_LAYERS[layer]['datatype']
        
        # Create library
        self.lib = gdstk.Library()
        
    def text_to_polygons(self, text, font_size, position=(0, 0)):
        """
        Convert text to GDS polygons.
        
        Args:
            text: String to render
            font_size: Height of characters in micrometers
            position: (x, y) position tuple
            
        Returns:
            List of gdstk.Polygon objects
        """
        polygons = gdstk.text(
            text,
            font_size,
            position,
            layer=self.layer,
            datatype=self.datatype
        )
        return polygons
    
    def calculate_optimal_font_size(self, text, max_width=None, max_height=None):
        """
        Calculate the optimal font size to fit text within bounds.
        
        Args:
            text: Text string to fit
            max_width: Maximum width (default: available tile width)
            max_height: Maximum height (default: available tile height)
            
        Returns:
            Optimal font size in micrometers
        """
        max_width = max_width or self.width
        max_height = max_height or self.height
        
        # Handle multiline text
        lines = text.split('\n')
        max_line_len = max(len(line) for line in lines)
        num_lines = len(lines)
        
        # gdstk text: aspect ratio is 1:2, character spacing is 9/16 of height
        # Line spacing is 5/4 of height
        char_width_ratio = 9/16  # Width of one character relative to height
        line_spacing_ratio = 5/4  # Line spacing relative to height
        
        # Calculate text dimensions for font_size = 1
        text_width_per_size = max_line_len * char_width_ratio
        text_height_per_size = 1 + (num_lines - 1) * line_spacing_ratio
        
        # Calculate max font size that fits
        max_font_by_width = max_width / text_width_per_size if text_width_per_size > 0 else float('inf')
        max_font_by_height = max_height / text_height_per_size if text_height_per_size > 0 else float('inf')
        
        return min(max_font_by_width, max_font_by_height)
    
    def create_text_cell(self, text, cell_name="text_art", font_size=None, center=True):
        """
        Create a GDS cell with the text.
        
        Args:
            text: Text to render
            cell_name: Name of the GDS cell
            font_size: Font size in um (auto-calculated if None)
            center: Whether to center the text in the tile
            
        Returns:
            gdstk.Cell object
        """
        # Auto-calculate font size if not specified
        if font_size is None:
            font_size = self.calculate_optimal_font_size(text) * 0.9  # 90% to leave some margin
        
        # Create text polygons at origin first
        polygons = self.text_to_polygons(text, font_size, (0, 0))
        
        if not polygons:
            raise ValueError(f"No polygons generated for text: {text}")
        
        # Calculate bounding box
        all_points = []
        for poly in polygons:
            all_points.extend(poly.points)
        
        if all_points:
            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            text_width = max(xs) - min(xs)
            text_height = max(ys) - min(ys)
            text_min_x = min(xs)
            text_min_y = min(ys)
        else:
            text_width = text_height = text_min_x = text_min_y = 0
        
        # Calculate offset to center or position text
        if center:
            # Center in the tile area (accounting for margins)
            tile_center_x = TILE_WIDTH_UM * self.tiles_x / 2
            tile_center_y = TILE_HEIGHT_UM * self.tiles_y / 2
            
            offset_x = tile_center_x - text_width / 2 - text_min_x
            offset_y = tile_center_y - text_height / 2 - text_min_y
        else:
            offset_x = MARGIN_UM - text_min_x
            offset_y = MARGIN_UM - text_min_y
        
        # Create cell and add translated polygons
        cell = self.lib.new_cell(cell_name)
        for poly in polygons:
            translated = poly.translate(offset_x, offset_y)
            cell.add(translated)
        
        return cell
    
    def create_multiline_art(self, lines, cell_name="book_art", font_size=None):
        """
        Create multi-line text art (for books, poems, etc.)
        
        Args:
            lines: List of text lines
            cell_name: Name of the GDS cell
            font_size: Font size in um (auto-calculated if None)
            
        Returns:
            gdstk.Cell object
        """
        text = '\n'.join(lines)
        return self.create_text_cell(text, cell_name, font_size)
    
    def add_border(self, cell, border_width=1.0):
        """
        Add a decorative border around the tile.
        
        Args:
            cell: Cell to add border to
            border_width: Width of the border in um
        """
        # Outer rectangle
        outer = gdstk.rectangle(
            (0, 0),
            (TILE_WIDTH_UM * self.tiles_x, TILE_HEIGHT_UM * self.tiles_y),
            layer=self.layer,
            datatype=self.datatype
        )
        
        # Inner rectangle (to cut out)
        inner = gdstk.rectangle(
            (border_width, border_width),
            (TILE_WIDTH_UM * self.tiles_x - border_width, 
             TILE_HEIGHT_UM * self.tiles_y - border_width)
        )
        
        # Create border by boolean difference
        border = gdstk.boolean(outer, inner, "not", 
                              layer=self.layer, datatype=self.datatype)
        for poly in border:
            cell.add(poly)
    
    def save(self, filename):
        """Save the library to a GDS file."""
        self.lib.write_gds(filename)
        print(f"GDS file saved to: {filename}")
        
        # Print some stats
        for cell in self.lib.cells:
            bbox = cell.bounding_box()
            if bbox:
                width = bbox[1][0] - bbox[0][0]
                height = bbox[1][1] - bbox[0][1]
                print(f"Cell '{cell.name}': {width:.2f} x {height:.2f} um")
                print(f"  Polygons: {len(cell.polygons)}")


def create_hello_world_gds(output_file="text_art.gds", tile_size="1x1"):
    """Create a simple 'Hello World!' GDS file."""
    gen = SiliconTextGenerator(tile_size=tile_size, layer="met1")
    
    # Create the text cell
    cell = gen.create_text_cell("Hello\nWorld!", cell_name="hello_world")
    
    # Add a border
    gen.add_border(cell, border_width=2.0)
    
    # Save
    gen.save(output_file)
    return output_file


def create_book_gds(text, output_file="book_art.gds", tile_size="2x2", title=None):
    """
    Create a GDS file with book content.
    
    Args:
        text: The book text to render
        output_file: Output GDS filename
        tile_size: TinyTapeout tile size
        title: Optional title for the cell
    """
    gen = SiliconTextGenerator(tile_size=tile_size, layer="met1")
    
    cell_name = title.replace(" ", "_")[:20] if title else "book_text"
    cell = gen.create_text_cell(text, cell_name=cell_name)
    
    gen.add_border(cell, border_width=3.0)
    gen.save(output_file)
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate GDS files with text for TinyTapeout silicon art',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple text
  python text_to_gds.py "Hello World!" hello.gds
  
  # Multi-line text
  python text_to_gds.py "Line 1\\nLine 2\\nLine 3" multiline.gds
  
  # Larger tile for more text
  python text_to_gds.py --tile-size 2x2 "More space for text!" large.gds
  
  # Use different metal layer
  python text_to_gds.py --layer met2 "On metal 2" met2.gds
  
  # Custom font size
  python text_to_gds.py --font-size 5.0 "Tiny text" tiny.gds
  
  # Read from file
  python text_to_gds.py --from-file poem.txt poem.gds
        """
    )
    
    parser.add_argument('text', nargs='?', help='Text to render (use \\n for newlines)')
    parser.add_argument('output', nargs='?', default='text_art.gds', 
                       help='Output GDS file (default: text_art.gds)')
    parser.add_argument('--tile-size', '-t', default='1x1',
                       choices=['1x1', '1x2', '2x2', '3x2', '4x2', '6x2', '8x2'],
                       help='TinyTapeout tile size (default: 1x1)')
    parser.add_argument('--layer', '-l', default='met1',
                       choices=list(SKY130_LAYERS.keys()),
                       help='Metal layer for text (default: met1)')
    parser.add_argument('--font-size', '-s', type=float, default=None,
                       help='Font size in micrometers (auto-calculated if not specified)')
    parser.add_argument('--no-border', action='store_true',
                       help='Do not add decorative border')
    parser.add_argument('--from-file', '-f', type=str,
                       help='Read text from file instead of command line')
    parser.add_argument('--hello-world', action='store_true',
                       help='Generate a simple Hello World example')
    
    args = parser.parse_args()
    
    # Handle hello world mode
    if args.hello_world:
        create_hello_world_gds(args.output, args.tile_size)
        return
    
    # Get text from file or command line
    if args.from_file:
        with open(args.from_file, 'r') as f:
            text = f.read().strip()
    elif args.text:
        # Handle escaped newlines
        text = args.text.replace('\\n', '\n')
    else:
        parser.print_help()
        print("\nError: Please provide text or use --hello-world")
        sys.exit(1)
    
    # Create generator
    gen = SiliconTextGenerator(tile_size=args.tile_size, layer=args.layer)
    
    # Create text cell
    cell = gen.create_text_cell(text, font_size=args.font_size)
    
    # Add border if requested
    if not args.no_border:
        gen.add_border(cell, border_width=2.0)
    
    # Save
    gen.save(args.output)


if __name__ == '__main__':
    main()
