"""Create a slideshow MP4 video from the Shikanoya images with Ken Burns effect."""
import cv2
import numpy as np
from PIL import Image
import os

BASE = '/home/user/0328Kanoya'

# Image order for the video (storytelling flow)
image_files = [
    'images/sakura_01.jpg',   # Opening: cherry blossom
    '7C1A5099.JPG',           # Deer in Nara
    '7C1A5475.JPG',           # Garden at night
    '7C1A5128.JPG',           # Private dining room
    '7C1A5496.JPG',           # Counter seats
    '7C1A5411.JPG',           # Chef preparing
    '7C1A5450.JPG',           # Close-up hands
    '7C1A5225.JPG',           # Bedroom
    'images/sakura_02.jpg',   # Closing: cherry blossom
]

# Video settings
OUTPUT_W, OUTPUT_H = 1920, 1080
FPS = 30
DISPLAY_SEC = 3.0       # Each image shown for 3 seconds
TRANSITION_SEC = 1.0    # 1 second crossfade transition
DISPLAY_FRAMES = int(DISPLAY_SEC * FPS)
TRANS_FRAMES = int(TRANSITION_SEC * FPS)


def load_and_resize(path):
    """Load image and resize to fill output dimensions (center crop)."""
    img = Image.open(path).convert('RGB')
    iw, ih = img.size

    # Scale to cover output area
    scale = max(OUTPUT_W / iw, OUTPUT_H / ih)
    new_w = int(iw * scale)
    new_h = int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - OUTPUT_W) // 2
    top = (new_h - OUTPUT_H) // 2
    img = img.crop((left, top, left + OUTPUT_W, top + OUTPUT_H))

    return np.array(img)


def apply_ken_burns(frame_arr, progress, zoom_start=1.0, zoom_end=1.08):
    """Apply subtle Ken Burns (slow zoom) effect."""
    h, w = frame_arr.shape[:2]
    zoom = zoom_start + (zoom_end - zoom_start) * progress

    new_w = int(w * zoom)
    new_h = int(h * zoom)
    resized = cv2.resize(frame_arr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    x_off = (new_w - w) // 2
    y_off = (new_h - h) // 2
    cropped = resized[y_off:y_off + h, x_off:x_off + w]
    return cropped


def add_text_overlay(frame, text, position, font_scale=1.2, thickness=2):
    """Add text with shadow effect."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    x, y = position
    # Shadow
    cv2.putText(frame, text, (x + 2, y + 2), font, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    # Main text
    cv2.putText(frame, text, (x, y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return frame


def create_fade_black(frames_count, w, h, fade_in=True):
    """Create fade from/to black frames."""
    result = []
    for i in range(frames_count):
        alpha = i / frames_count if fade_in else 1.0 - i / frames_count
        result.append(alpha)
    return result


print("Loading images...")
images = []
for f in image_files:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        images.append(load_and_resize(path))
        print(f"  Loaded: {f}")
    else:
        print(f"  SKIP (not found): {f}")

if len(images) < 2:
    print("Not enough images!")
    exit(1)

# Create video
output_path = os.path.join(BASE, 'shikanoya_spring.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, FPS, (OUTPUT_W, OUTPUT_H))

FADE_FRAMES = int(1.5 * FPS)  # 1.5s fade in/out from black

print("Generating video...")

# Fade in from black for first image
for f in range(FADE_FRAMES):
    alpha = f / FADE_FRAMES
    progress = f / (DISPLAY_FRAMES + FADE_FRAMES)
    frame = apply_ken_burns(images[0], progress)
    frame = (frame.astype(np.float32) * alpha).astype(np.uint8)
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    out.write(frame_bgr)

# Main slideshow with crossfade transitions
for idx in range(len(images)):
    img = images[idx]

    # Display frames with Ken Burns
    for f in range(DISPLAY_FRAMES):
        progress = f / DISPLAY_FRAMES
        frame = apply_ken_burns(img, progress)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)

    # Crossfade to next image (if not last)
    if idx < len(images) - 1:
        next_img = images[idx + 1]
        for f in range(TRANS_FRAMES):
            alpha = f / TRANS_FRAMES
            p1 = 1.0 - alpha * 0.02  # Continuing zoom
            p2 = alpha * 0.02
            frame1 = apply_ken_burns(img, 1.0).astype(np.float32)
            frame2 = apply_ken_burns(next_img, 0.0).astype(np.float32)
            blended = ((1 - alpha) * frame1 + alpha * frame2).astype(np.uint8)
            frame_bgr = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)

# Fade out to black for last image
for f in range(FADE_FRAMES):
    alpha = 1.0 - f / FADE_FRAMES
    frame = apply_ken_burns(images[-1], 1.0)
    frame = (frame.astype(np.float32) * alpha).astype(np.uint8)
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    out.write(frame_bgr)

out.release()

# Check file size
size_mb = os.path.getsize(output_path) / (1024 * 1024)
total_frames = FADE_FRAMES + len(images) * DISPLAY_FRAMES + (len(images) - 1) * TRANS_FRAMES + FADE_FRAMES
duration = total_frames / FPS

print(f"\nVideo created: {output_path}")
print(f"Duration: {duration:.1f} seconds")
print(f"File size: {size_mb:.1f} MB")
print(f"Resolution: {OUTPUT_W}x{OUTPUT_H} @ {FPS}fps")
