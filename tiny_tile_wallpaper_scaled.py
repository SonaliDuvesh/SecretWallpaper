#!/usr/bin/env python3
"""
tiny_tile_wallpaper_scaled.py

Tiny-tile wallpaper generator with high-resolution scale option to preserve zoom detail.

- Repeats the SAME input image in a grid.
- Use --scale to render at N× the target resolution (improves zoom clarity).
- Supports PNG or JPEG output (use JPEG for smaller files; set quality).
- Includes preview mode and safety checks.

Example (phone 1080x1920, good balance):
  # preview
  python3 tiny_tile_wallpaper_scaled.py -i myphoto.jpg -o phone_preview.png --tile 48 --out_w 1080 --out_h 1920 --scale 3 --preview

  # final (3× scale -> 3240x5760)
  python3 tiny_tile_wallpaper_scaled.py -i myphoto.jpg -o phone_wallpaper_1080x1920_scale3.jpg --tile 48 --out_w 1080 --out_h 1920 --scale 3 --format jpg --jpg_quality 92

Notes:
  - scale=1 => same behavior as earlier script (1080x1920)
  - higher scale => better zoom detail but larger files (scale 2 or 3 usually enough for phone zoom)
  - use --preview to check quickly (it downsamples final for speed)
"""
from PIL import Image
import argparse, os, math
from tqdm import tqdm

def compute_grid_from_dimensions(out_w, out_h, tile, scale):
    """Compute cols, rows based on scaled output dims."""
    scaled_w = out_w * scale
    scaled_h = out_h * scale
    cols = math.ceil(scaled_w / tile)
    rows = math.ceil(scaled_h / tile)
    return cols, rows, scaled_w, scaled_h

def create_tiled_canvas_simple(source_img, cols, rows, tile_size, final_w, final_h, preview_scale=1):
    """
    Create canvas by resizing source to 'tile_size' and tiling cols x rows.
    preview_scale > 1: downscale the large final image by preview_scale for quick preview/save.
    """
    tile = source_img.resize((tile_size, tile_size), Image.LANCZOS)
    src_w, src_h = tile.size
    final_w_calc = cols * src_w
    final_h_calc = rows * src_h

    # Create canvas
    canvas = Image.new('RGB', (final_w_calc, final_h_calc), (0,0,0))

    for r in tqdm(range(rows), desc='Rows'):
        y = r * src_h
        for c in range(cols):
            x = c * src_w
            canvas.paste(tile, (x, y))

    # If requested, crop/exact to final_w/final_h
    canvas = canvas.crop((0, 0, final_w, final_h))

    if preview_scale and preview_scale > 1:
        preview_w = max(1, final_w // preview_scale)
        preview_h = max(1, final_h // preview_scale)
        canvas = canvas.resize((preview_w, preview_h), Image.LANCZOS)
    return canvas

def parse_args():
    p = argparse.ArgumentParser(description='Tiny-tile wallpaper generator with high-res scaling for zoom clarity.')
    p.add_argument('-i', '--input', required=True, help='Input image')
    p.add_argument('-o', '--out', default='tiled_wallpaper.png', help='Output filename')
    p.add_argument('--tile', type=int, default=48, help='Tile size (square) in pixels (8,12,16,24,32,48...). Smaller => more tiles.')
    p.add_argument('--out_w', type=int, default=1080, help='Target phone width (unscaled)')
    p.add_argument('--out_h', type=int, default=1920, help='Target phone height (unscaled)')
    p.add_argument('--scale', type=int, default=1, help='Scale factor (render at scale× the target resolution). Use 2 or 3 for better zoom.')
    p.add_argument('--cols', type=int, default=None, help='Optional: exact columns (overrides out_w/scale).')
    p.add_argument('--rows', type=int, default=None, help='Optional: exact rows (overrides out_h/scale).')
    p.add_argument('--format', choices=['png','jpg'], default='png', help='Output format (png or jpg)')
    p.add_argument('--jpg_quality', type=int, default=92, help='JPEG quality (only if --format jpg).')
    p.add_argument('--max_pixels', type=int, default=600_000_000, help='Max allowed pixels (safety). Default 600M.')
    p.add_argument('--preview', action='store_true', help='Save a low-res preview (fast); output filename will have _preview appended.')
    p.add_argument('--preview_scale', type=int, default=6, help='When --preview, scale down final by this factor for quick check.')
    p.add_argument('--force', action='store_true', help='Force even if output exceeds max_pixels (dangerous).')
    return p.parse_args()

def main():
    args = parse_args()
    if not os.path.isfile(args.input):
        raise SystemExit("Input image not found.")

    src = Image.open(args.input).convert('RGB')
    src_w, src_h = src.size
    tile = max(1, int(args.tile))
    scale = max(1, int(args.scale))

    # Compute grid/size
    if args.cols and args.rows:
        cols = args.cols
        rows = args.rows
        final_w = cols * tile
        final_h = rows * tile
    else:
        cols, rows, final_w, final_h = compute_grid_from_dimensions(args.out_w, args.out_h, tile, scale)

    total_pixels = final_w * final_h
    print(f"Input: {args.input} ({src_w}x{src_h}), tile={tile}px, cols={cols}, rows={rows}, scale={scale}")
    print(f"Final image size: {final_w}x{final_h} = {total_pixels} pixels")

    if total_pixels > args.max_pixels and not args.force:
        raise SystemExit(f"Output exceeds safety limit ({args.max_pixels} pixels). Reduce scale/cols/rows or use --force to override.")

    out_path = args.out
    if args.preview:
        # produce preview quickly (downscaled)
        preview_canvas = create_tiled_canvas_simple(src, cols, rows, tile, final_w, final_h, preview_scale=args.preview_scale)
        root, ext = os.path.splitext(out_path)
        preview_path = f"{root}_preview{ext or '.png'}"
        preview_canvas.save(preview_path, optimize=True)
        print(f"Saved preview: {preview_path} (scaled down by {args.preview_scale}x)")
        return

    # Generate final canvas (this can be large)
    canvas = create_tiled_canvas_simple(src, cols, rows, tile, final_w, final_h, preview_scale=1)

    # Save in requested format
    if args.format == 'png':
        canvas.save(out_path, format='PNG', optimize=True)
    else:
        canvas.save(out_path, format='JPEG', quality=max(10, min(100, args.jpg_quality)), optimize=True)
    print(f"Saved final tiled wallpaper: {out_path}")

if __name__ == '__main__':
    main()
