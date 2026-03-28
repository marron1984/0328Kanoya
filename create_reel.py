"""Create an Instagram Reel (9:16 vertical) MP4 from Shikanoya images."""
import cv2
import numpy as np
from PIL import Image, ImageFilter
import os

BASE = '/home/user/0328Kanoya'

# Reel settings: 1080x1920 (9:16)
OUT_W, OUT_H = 1080, 1920
FPS = 30
DISPLAY_SEC = 2.5
TRANS_SEC = 0.8
DISPLAY_FRAMES = int(DISPLAY_SEC * FPS)
TRANS_FRAMES = int(TRANS_SEC * FPS)
FADE_FRAMES = int(1.0 * FPS)

# Image order (storytelling flow for Reel)
image_files = [
    'images/sakura_01.jpg',   # Opening: sakura
    '7C1A5099.JPG',           # Deer
    '7C1A5475.JPG',           # Garden night (portrait)
    '7C1A5128.JPG',           # Private dining
    '7C1A5496.JPG',           # Counter
    '7C1A5411.JPG',           # Chef
    '7C1A5450.JPG',           # Hands close-up
    '7C1A5225.JPG',           # Bedroom (portrait)
    'images/sakura_02.jpg',   # Closing: sakura
]


def fit_for_reel(pil_img):
    """
    Fit image to 1080x1920 Reel format.
    - Portrait images: scale to cover and center crop
    - Landscape images: blurred background fill + sharp centered image
    """
    iw, ih = pil_img.size
    is_landscape = iw > ih

    if is_landscape:
        # === Landscape: blurred background + centered sharp image ===

        # 1) Create blurred background (scale to cover 1080x1920)
        bg_scale = max(OUT_W / iw, OUT_H / ih)
        bg_w = int(iw * bg_scale)
        bg_h = int(ih * bg_scale)
        bg = pil_img.resize((bg_w, bg_h), Image.LANCZOS)
        left = (bg_w - OUT_W) // 2
        top = (bg_h - OUT_H) // 2
        bg = bg.crop((left, top, left + OUT_W, top + OUT_H))
        # Heavy blur + darken
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        bg_arr = np.array(bg).astype(np.float32) * 0.3  # darken to 30%
        bg = Image.fromarray(bg_arr.astype(np.uint8))

        # 2) Sharp foreground: fit width to 1080, maintain aspect ratio
        fg_scale = OUT_W / iw
        fg_w = OUT_W
        fg_h = int(ih * fg_scale)
        fg = pil_img.resize((fg_w, fg_h), Image.LANCZOS)

        # 3) Composite: paste centered on blurred background
        canvas = bg.copy()
        y_offset = (OUT_H - fg_h) // 2
        canvas.paste(fg, (0, y_offset))

        return np.array(canvas)

    else:
        # === Portrait: scale to cover and center crop ===
        scale = max(OUT_W / iw, OUT_H / ih)
        new_w = int(iw * scale)
        new_h = int(ih * scale)
        img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - OUT_W) // 2
        top = (new_h - OUT_H) // 2
        img = img.crop((left, top, left + OUT_W, top + OUT_H))
        return np.array(img)


def apply_ken_burns(frame_arr, progress, zoom_start=1.0, zoom_end=1.05):
    """Subtle Ken Burns zoom effect."""
    h, w = frame_arr.shape[:2]
    zoom = zoom_start + (zoom_end - zoom_start) * progress
    new_w = int(w * zoom)
    new_h = int(h * zoom)
    resized = cv2.resize(frame_arr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    x_off = (new_w - w) // 2
    y_off = (new_h - h) // 2
    return resized[y_off:y_off + h, x_off:x_off + w]


# Load images
print("Loading and formatting images for Reel (1080x1920)...")
images = []
for f in image_files:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        pil_img = Image.open(path).convert('RGB')
        arr = fit_for_reel(pil_img)
        images.append(arr)
        iw, ih = pil_img.size
        orient = "横→ぼかし背景" if iw > ih else "縦→フィット"
        print(f"  {f:30s} {orient}")
    else:
        print(f"  SKIP: {f}")

# Create video
output_path = os.path.join(BASE, 'shikanoya_reel.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, FPS, (OUT_W, OUT_H))

print("Generating Reel video...")

# Fade in from black
for f in range(FADE_FRAMES):
    alpha = f / FADE_FRAMES
    progress = f / (DISPLAY_FRAMES + FADE_FRAMES)
    frame = apply_ken_burns(images[0], progress)
    frame = (frame.astype(np.float32) * alpha).astype(np.uint8)
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

# Main slideshow
for idx in range(len(images)):
    img = images[idx]

    for f in range(DISPLAY_FRAMES):
        progress = f / DISPLAY_FRAMES
        frame = apply_ken_burns(img, progress)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # Crossfade to next
    if idx < len(images) - 1:
        next_img = images[idx + 1]
        for f in range(TRANS_FRAMES):
            alpha = f / TRANS_FRAMES
            frame1 = apply_ken_burns(img, 1.0).astype(np.float32)
            frame2 = apply_ken_burns(next_img, 0.0).astype(np.float32)
            blended = ((1 - alpha) * frame1 + alpha * frame2).astype(np.uint8)
            out.write(cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))

# Fade out to black
for f in range(FADE_FRAMES):
    alpha = 1.0 - f / FADE_FRAMES
    frame = apply_ken_burns(images[-1], 1.0)
    frame = (frame.astype(np.float32) * alpha).astype(np.uint8)
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

out.release()

size_mb = os.path.getsize(output_path) / (1024 * 1024)
total_frames = FADE_FRAMES * 2 + len(images) * DISPLAY_FRAMES + (len(images) - 1) * TRANS_FRAMES
duration = total_frames / FPS

print(f"\n=== Reel Video Created ===")
print(f"File: {output_path}")
print(f"Resolution: {OUT_W}x{OUT_H} (9:16)")
print(f"Duration: {duration:.1f} seconds")
print(f"Size: {size_mb:.1f} MB")
print(f"FPS: {FPS}")
