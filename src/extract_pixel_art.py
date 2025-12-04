#!/usr/bin/env python3
"""
Extract Pixel Art from Image

Analyzes a pixel art image to extract:
- Grid/pixel size (detected from black eyes or smallest feature)
- Unique colors
- Position of each colored pixel

Usage:
    python extract_pixel_art.py "pixel_pig (4).png"
"""

import sys
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Error: Pillow and numpy required. Install with: pip install Pillow numpy")
    sys.exit(1)


def analyze_image(image_path, debug=True):
    """
    Analyze a pixel art image to extract pixel grid and colors.
    
    Returns:
        dict with:
            - 'pixel_size': detected pixel size in image pixels
            - 'grid_width': number of pixels horizontally
            - 'grid_height': number of pixels vertically
            - 'colors': dict mapping color tuples to list of (x, y) grid positions
            - 'color_names': dict mapping color tuples to descriptive names
    """
    img = Image.open(image_path)
    
    # Convert to RGB if necessary
    if img.mode == 'RGBA':
        # Create white background for transparency
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    img_array = np.array(img)
    height, width = img_array.shape[:2]
    
    if debug:
        print(f"Image size: {width} x {height} pixels")
    
    # Step 1: Find unique colors (ignoring near-white background)
    unique_colors = {}
    for y in range(height):
        for x in range(width):
            color = tuple(img_array[y, x])
            # Skip near-white pixels (background)
            if color[0] > 250 and color[1] > 250 and color[2] > 250:
                continue
            if color not in unique_colors:
                unique_colors[color] = 0
            unique_colors[color] += 1
    
    if debug:
        print(f"\nUnique colors found: {len(unique_colors)}")
        for color, count in sorted(unique_colors.items(), key=lambda x: -x[1]):
            print(f"  RGB{color}: {count} pixels")
    
    # Step 2: Find black pixels (eyes) to determine pixel size
    black_pixels = []
    for y in range(height):
        for x in range(width):
            color = tuple(img_array[y, x])
            # Find very dark pixels (black eyes)
            if color[0] < 50 and color[1] < 50 and color[2] < 50:
                black_pixels.append((x, y))
    
    if debug:
        print(f"\nBlack pixels found: {len(black_pixels)}")
    
    # Step 3: Detect pixel size by finding runs of same color
    # Look for horizontal runs to detect pixel width
    pixel_size = detect_pixel_size(img_array)
    
    if debug:
        print(f"Detected pixel size: {pixel_size} x {pixel_size} image pixels")
    
    # Step 4: Sample the image at pixel grid centers
    grid_width = width // pixel_size
    grid_height = height // pixel_size
    
    if debug:
        print(f"Grid size: {grid_width} x {grid_height} art pixels")
    
    # Step 5: Extract color at each grid position
    colors = defaultdict(list)
    offset = pixel_size // 2  # Sample from center of each pixel
    
    for gy in range(grid_height):
        for gx in range(grid_width):
            # Sample from center of the pixel cell
            sx = gx * pixel_size + offset
            sy = gy * pixel_size + offset
            
            if sx < width and sy < height:
                color = tuple(img_array[sy, sx])
                
                # Skip white/near-white background
                if color[0] > 250 and color[1] > 250 and color[2] > 250:
                    continue
                
                # Normalize similar colors
                color = normalize_color(color, unique_colors.keys())
                
                # Store with Y inverted (bottom-left origin for GDS)
                colors[color].append((gx, grid_height - 1 - gy))
    
    # Step 6: Name the colors
    color_names = name_colors(colors.keys())
    
    if debug:
        print(f"\nColors in grid:")
        for color in colors:
            name = color_names.get(color, 'unknown')
            print(f"  {name} RGB{color}: {len(colors[color])} pixels")
    
    return {
        'pixel_size': pixel_size,
        'grid_width': grid_width,
        'grid_height': grid_height,
        'colors': dict(colors),
        'color_names': color_names,
        'image_width': width,
        'image_height': height,
    }


def detect_pixel_size(img_array):
    """
    Detect the pixel size by analyzing runs of same color.
    """
    height, width = img_array.shape[:2]
    
    # Look for runs of same color along horizontal lines
    run_lengths = []
    
    for y in range(0, height, max(1, height // 20)):  # Sample some rows
        current_color = None
        run_length = 0
        
        for x in range(width):
            color = tuple(img_array[y, x])
            
            if color == current_color:
                run_length += 1
            else:
                if run_length > 2 and current_color is not None:
                    # Skip white runs
                    if not (current_color[0] > 250 and current_color[1] > 250 and current_color[2] > 250):
                        run_lengths.append(run_length)
                current_color = color
                run_length = 1
        
        if run_length > 2 and current_color is not None:
            if not (current_color[0] > 250 and current_color[1] > 250 and current_color[2] > 250):
                run_lengths.append(run_length)
    
    if not run_lengths:
        return 1
    
    # Find the GCD of common run lengths (likely the pixel size)
    from math import gcd
    from functools import reduce
    from collections import Counter
    
    # Get most common run lengths
    counter = Counter(run_lengths)
    common_lengths = [length for length, count in counter.most_common(10)]
    
    if common_lengths:
        # The pixel size should divide most run lengths evenly
        # Try common lengths as potential pixel sizes
        for size in sorted(set(common_lengths)):
            if size > 1:
                # Check if this size divides many runs
                divisible = sum(1 for r in run_lengths if r % size == 0)
                if divisible > len(run_lengths) * 0.5:
                    return size
        
        # Fall back to smallest common run length
        return min(common_lengths) if min(common_lengths) > 1 else max(1, common_lengths[0])
    
    return 1


def normalize_color(color, known_colors):
    """
    Normalize a color to the nearest known color.
    """
    min_dist = float('inf')
    nearest = color
    
    for known in known_colors:
        dist = sum((a - b) ** 2 for a, b in zip(color, known))
        if dist < min_dist:
            min_dist = dist
            nearest = known
    
    return nearest


def name_colors(colors):
    """
    Give descriptive names to colors based on RGB values.
    """
    names = {}
    
    for color in colors:
        r, g, b = color
        
        # Classify by color characteristics
        if r < 50 and g < 50 and b < 50:
            names[color] = 'black'
        elif r > 200 and g > 200 and b > 200:
            names[color] = 'white'
        elif r > 180 and g > 120 and b < 100 and g > b:
            names[color] = 'golden'
        elif r > g and r > b:
            if g > 100 and abs(r - g) < 80:
                names[color] = 'light_pink'
            else:
                names[color] = 'dark_pink'
        else:
            # Default based on dominant channel
            if r >= g and r >= b:
                names[color] = 'reddish'
            elif g >= r and g >= b:
                names[color] = 'greenish'
            else:
                names[color] = 'bluish'
    
    return names


def generate_pixel_arrays(data):
    """
    Generate Python code for pixel arrays.
    """
    colors = data['colors']
    color_names = data['color_names']
    grid_width = data['grid_width']
    grid_height = data['grid_height']
    
    print(f"\n# Grid size: {grid_width} x {grid_height}")
    print(f"# Pixel positions by color (x, y) with origin at bottom-left:\n")
    
    for color, positions in sorted(colors.items(), key=lambda x: -len(x[1])):
        name = color_names.get(color, 'unknown')
        print(f"# {name.upper()} - RGB{color}")
        print(f"{name.upper()}_PIXELS = [")
        
        # Sort by y then x for readability
        for pos in sorted(positions, key=lambda p: (p[1], p[0])):
            print(f"    {pos},")
        print("]\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_pixel_art.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    data = analyze_image(image_path)
    generate_pixel_arrays(data)
