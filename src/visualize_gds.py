#!/usr/bin/env python3
"""
Simple GDS Visualization Script

Creates an ASCII art or SVG preview of a GDS file.
Useful for quickly checking what your silicon art looks like.

Usage:
    python visualize_gds.py input.gds [--format ascii|svg]
"""

import argparse
import sys

try:
    import gdstk
except ImportError:
    print("Error: gdstk library required. Install with: pip install gdstk")
    sys.exit(1)


def visualize_ascii(gds_file, width=80, height=40):
    """
    Create ASCII art visualization of a GDS file.
    
    Args:
        gds_file: Path to GDS file
        width: Character width of output
        height: Character height of output
    """
    lib = gdstk.read_gds(gds_file)
    
    if not lib.cells:
        print(f"No cells found in {gds_file}")
        return
    
    # Get top cell
    top_cells = lib.top_level()
    cell = top_cells[0] if top_cells else lib.cells[-1]
    
    print(f"\nCell: {cell.name}")
    print(f"Polygons: {len(cell.polygons)}")
    
    bbox = cell.bounding_box()
    if bbox is None:
        print("Cell has no geometry")
        return
    
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[1]
    cell_width = max_x - min_x
    cell_height = max_y - min_y
    
    print(f"Size: {cell_width:.2f} x {cell_height:.2f} um")
    print()
    
    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Scale factors
    scale_x = (width - 1) / cell_width if cell_width > 0 else 1
    scale_y = (height - 1) / cell_height if cell_height > 0 else 1
    
    # Rasterize polygons
    for poly in cell.polygons:
        points = poly.points
        
        # Simple point-based rasterization
        for point in points:
            x = int((point[0] - min_x) * scale_x)
            y = int((point[1] - min_y) * scale_y)
            
            if 0 <= x < width and 0 <= y < height:
                grid[height - 1 - y][x] = '#'
        
        # Fill in edges between points
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            
            x1 = int((p1[0] - min_x) * scale_x)
            y1 = int((p1[1] - min_y) * scale_y)
            x2 = int((p2[0] - min_x) * scale_x)
            y2 = int((p2[1] - min_y) * scale_y)
            
            # Bresenham's line algorithm (simplified)
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for s in range(steps + 1):
                t = s / steps
                x = int(x1 + t * (x2 - x1))
                y = int(y1 + t * (y2 - y1))
                
                if 0 <= x < width and 0 <= y < height:
                    grid[height - 1 - y][x] = '#'
    
    # Print grid with border
    print('┌' + '─' * width + '┐')
    for row in grid:
        print('│' + ''.join(row) + '│')
    print('└' + '─' * width + '┘')


def visualize_svg(gds_file, output_file=None, width=800, height=600):
    """
    Create SVG visualization of a GDS file.
    
    Args:
        gds_file: Path to GDS file
        output_file: Output SVG file (default: same name with .svg extension)
        width: SVG width in pixels
        height: SVG height in pixels
    """
    lib = gdstk.read_gds(gds_file)
    
    if not lib.cells:
        print(f"No cells found in {gds_file}")
        return
    
    # Get top cell
    top_cells = lib.top_level()
    cell = top_cells[0] if top_cells else lib.cells[-1]
    
    bbox = cell.bounding_box()
    if bbox is None:
        print("Cell has no geometry")
        return
    
    min_x, min_y = bbox[0]
    max_x, max_y = bbox[1]
    cell_width = max_x - min_x
    cell_height = max_y - min_y
    
    # Calculate scale to fit
    padding = 20
    scale = min((width - 2*padding) / cell_width, 
                (height - 2*padding) / cell_height)
    
    # Output file
    if output_file is None:
        output_file = gds_file.rsplit('.', 1)[0] + '.svg'
    
    # Generate SVG
    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'  <rect width="100%" height="100%" fill="white"/>',
        f'  <g transform="translate({padding},{height - padding}) scale({scale},-{scale}) translate({-min_x},{-min_y})">',
    ]
    
    # Add polygons
    colors = {
        68: '#4169E1',  # met1 - Royal Blue
        69: '#228B22',  # met2 - Forest Green
        70: '#FF6347',  # met3 - Tomato
        71: '#9370DB',  # met4 - Medium Purple
        67: '#FFD700',  # li1 - Gold
        66: '#FF69B4',  # poly - Hot Pink
    }
    
    for poly in cell.polygons:
        layer = poly.layer
        color = colors.get(layer, '#333333')
        
        points_str = ' '.join(f'{p[0]},{p[1]}' for p in poly.points)
        svg_parts.append(f'    <polygon points="{points_str}" fill="{color}" stroke="#000" stroke-width="{0.5/scale}"/>')
    
    svg_parts.extend([
        '  </g>',
        '</svg>'
    ])
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(svg_parts))
    
    print(f"SVG saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize a GDS file as ASCII art or SVG'
    )
    
    parser.add_argument('gds_file', help='GDS file to visualize')
    parser.add_argument('--format', '-f', default='ascii',
                       choices=['ascii', 'svg'],
                       help='Output format (default: ascii)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output file for SVG format')
    parser.add_argument('--width', '-W', type=int, default=80,
                       help='Width (characters for ASCII, pixels for SVG)')
    parser.add_argument('--height', '-H', type=int, default=40,
                       help='Height (characters for ASCII, pixels for SVG)')
    
    args = parser.parse_args()
    
    if args.format == 'ascii':
        visualize_ascii(args.gds_file, args.width, args.height)
    else:
        svg_width = args.width if args.width != 80 else 800
        svg_height = args.height if args.height != 40 else 600
        visualize_svg(args.gds_file, args.output, svg_width, svg_height)


if __name__ == '__main__':
    main()
