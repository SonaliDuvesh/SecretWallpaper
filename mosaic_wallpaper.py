#!/usr/bin/env python3
"""
mosaic_wallpaper.py

Create a mosaic wallpaper composed of many miniature variations of the same input image.
From far away it reads as the original image; zoom in to see thousands of tiny copies.

Usage:
    python mosaic_wallpaper.py --input input.jpg --out wallpaper.png --out_w 3840 --out_h 2160 \
        --tile 32 --variations 1000 --tint 0.12

Dependencies:
    pip install pillow numpy tqdm
"""

from PIL import Image, ImageOps, ImageEnhance
import numpy as np
import argparse
import os
import random
from math import ceil
from tqdm import tqdm

# -------------------------
# Utility image transforms
# -------------------------
def random_transform(img, crop_scale=(0.8, 1.0), rotate_range=(-10, 10), flip_prob=0.5,
                     hue_jitter=0.08, brightness_jitter=0.12, contrast_jitter=0.12):
    """
    Apply conservative random transforms to keep subject recognizable.
    Returns a PIL.Image.
    """
    w, h = img.size

    # Random crop (center-biased)
    scale = random.uniform(*crop_scale)
    new_w, new_h = int(w * scale), int(h * scale)
    left = random.randint(0, max(0, w - new_w))
    top = random.randint(0, max(0, h - new_h))
    cropped = img.crop((left, top, left + new_w, top + new_h))

    # Resize back to original tile source size later; for now keep crop
    # Small rotation
    angle = random.uniform(*rotate_range)
    rotated = cropped.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=None)

    # Random flip
    if random.random() < flip_prob:
        rotated = ImageOps.mirror(rotated)

    # Color jitter using PIL ImageEnhance and simple hue shift by converting to HSV via numpy
    # Brightness
    if brightness_jitter > 0:
        enhancer = ImageEnhance.Brightness(rotated)
        rotated = enhancer.enhance(1.0 + random.uniform(-brightness_jitter, brightness_jitter))

    # Contrast
    if contrast_jitter > 0:
        enhancer = ImageEnhance.Contrast(rotated)
        rotated = enhancer.enhance(1.0 + random.uniform(-contrast_jitter, contrast_jitter))

    # Hue jitter - operate on HSV numpy array
    if hue_jitter > 0:
        arr = np.array(rotated.convert('RGBA')).astype(np.uint8)
        # convert to HSV via PIL for simplicity
        hsv = rotated.convert('HSV')
        h_arr = np.array(hsv)  # H,S,V channels
        # shift H by small amount
        shift = int(random.uniform(-hue_jitter * 255, hue_jitter * 255))
        h_arr[..., 0] = (h_arr[..., 0].astype(int) + shift) % 256
        rotated = Image.fromarray(h_arr, mode='HSV').convert('RGBA')

    return rotated.convert('RGB')


def average_color(img):
    """Return average color as a length-3 numpy array (R,G,B) of a PIL image."""
    arr = np.array(img)
    if arr.ndim == 3:
        # shape (H,W,3)
        return arr.reshape(-1, arr.shape[-1]).mean(axis=0)
    else:
        # grayscale
        val = arr.mean()
        return np.array([val, val, val])


# -------------------------
# Tile library generation
# -------------------------
def generate_tile_library(source_img, target_tile_size, n_variations=1000, reuse_if_less=False):
    """
    Generate a list of tile images (PIL.Images) from source_img by applying transforms.
    Returns list of (tile_image_resized, avg_color_array).
    """
    tiles = []
    src_w, src_h = source_img.size

    # We'll sample crops at various spots across the image to produce variety.
    for i in range(n_variations):
        t = random_transform(source_img)
        # Resize to tile size (square)
        tile = t.resize((target_tile_size, target_tile_size), resample=Image.LANCZOS)
        avg = average_color(tile)
        tiles.append((tile, avg))

    # Optionally ensure some simple deterministic crops too (center, corners)
    extras = []
    for box in [
        (0, 0, src_w//2, src_h//2),
        (src_w//2, 0, src_w, src_h//2),
        (0, src_h//2, src_w//2, src_h),
        (src_w//4, src_h//4, 3*src_w//4, 3*src_h//4)
    ]:
        try:
            c = source_img.crop(box).resize((target_tile_size, target_tile_size), Image.LANCZOS)
            extras.append((c, average_color(c)))
        except Exception:
            pass
    tiles.extend(extras)

    # If user requested fewer than grid size, tiles will be reused (that's okay)
    return tiles


# -------------------------
# Matching / composition
# -------------------------
def find_best_tile(target_color, tile_colors):
    """
    target_color: (3,) array
    tile_colors: list of arrays
    Return index of best matching tile (euclidean in RGB).
    """
    # Vectorized distance calculation
    arr = np.array(tile_colors)  # shape (M,3)
    diffs = arr - target_color
    d2 = np.sum(diffs * diffs, axis=1)
    return int(np.argmin(d2))


def compose_mosaic(source_img, tiles, out_w, out_h, tile_size, tint_strength=0.0, reuse_tiles=True):
    """
    Compose the final mosaic image.
    tiles: list of (tile_img, avg_color)
    tint_strength: 0..1 - how much to tint placed tile to match cell color (0 = no tint)
    """
    # Prepare
    cols = out_w // tile_size
    rows = out_h // tile_size
    canvas = Image.new('RGB', (cols * tile_size, rows * tile_size), (0, 0, 0))

    # Resize source image to match mosaic grid for target sampling
    source_resized = source_img.resize((cols, rows), Image.BICUBIC)

    tile_images = [t[0] for t in tiles]
    tile_colors = [t[1] for t in tiles]

    # For progress
    it = range(rows * cols)
    for idx in tqdm(it, desc='Composing tiles', unit='tile'):
        r = idx // cols
        c = idx % cols
        # target average color: sample pixel at resized source
        px = source_resized.getpixel((c, r))
        target_color = np.array(px)  # R,G,B

        best_idx = find_best_tile(target_color, tile_colors)

        chosen_tile = tile_images[best_idx]
        # optionally tint: blend tile with a solid color image of target_color
        if tint_strength and tint_strength > 0:
            tint_layer = Image.new('RGB', (tile_size, tile_size),
                                   tuple(int(x) for x in target_color))
            chosen_tile = Image.blend(chosen_tile, tint_layer, alpha=tint_strength)

        # place tile
        canvas.paste(chosen_tile, (c * tile_size, r * tile_size))

    return canvas


# -------------------------
# Command-line interface
# -------------------------
def main():
    parser = argparse.ArgumentParser(description='Generate mosaic wallpaper from one image.')
    parser.add_argument('--input', '-i', required=True, help='Input image path')
    parser.add_argument('--out', '-o', default='mosaic_wallpaper.png', help='Output image path')
    parser.add_argument('--out_w', type=int, default=3840, help='Output wallpaper width (pixels)')
    parser.add_argument('--out_h', type=int, default=2160, help='Output wallpaper height (pixels)')
    parser.add_argument('--tile', type=int, default=32, help='Tile size in pixels (square)')
    parser.add_argument('--variations', type=int, default=800, help='Number of tile variations to generate')
    parser.add_argument('--tint', type=float, default=0.08, help='Tint strength 0.0..0.5 (helps fidelity)')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    parser.add_argument('--preview', action='store_true', help='Save low-res preview (1/4 size) in addition to final')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    if not os.path.isfile(args.input):
        raise SystemExit(f"Input file not found: {args.input}")

    # Load source image
    src = Image.open(args.input).convert('RGB')
    print(f"Loaded input image {args.input} size={src.size}")

    # Generate tile library
    print(f"Generating {args.variations} tile variations (tile size {args.tile}px)...")
    tiles = generate_tile_library(src, target_tile_size=args.tile, n_variations=args.variations)

    # Compose mosaic
    print(f"Composing mosaic {args.out_w}x{args.out_h} with tile size {args.tile}...")
    mosaic = compose_mosaic(src, tiles, args.out_w, args.out_h, args.tile, tint_strength=args.tint)

    # Save result
    mosaic.save(args.out, format='PNG', optimize=True)
    print(f"Saved mosaic wallpaper to {args.out}")

    if args.preview:
        preview = mosaic.resize((args.out_w // 4, args.out_h // 4), Image.LANCZOS)
        preview_path = os.path.splitext(args.out)[0] + '_preview.png'
        preview.save(preview_path)
        print(f"Saved preview to {preview_path}")


if __name__ == '__main__':
    main()
