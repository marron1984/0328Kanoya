"""Instagram Reel - Luxury hotel film style. No black cards. Images breathe."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

BASE = '/home/user/0328Kanoya'
OUT_W, OUT_H = 1080, 1920
FPS = 30
FONT_PATH = '/tmp/NotoSerifJP.ttf'

# Color palette
CREAM = (248, 240, 228)
GOLD = (212, 185, 140)
WARM_SHADOW = (20, 12, 5)

# Each slide: image, duration, optional text, zoom style
# Total ~30s to match BGM
# Transitions are overlapping crossfades (shared time)
CROSSFADE_SEC = 1.2

slides = [
    {
        'file': '7C1A5099.JPG',
        'duration': 6.5,
        'zoom': 'slow_out',
        'text_main': '奈良春日 鹿のや',
        'text_sub': '',
        'text_timing': (0.35, 0.85),
        'text_pos': 'center',
    },
    {
        'file': '7C1A5128.JPG',
        'duration': 4.5,
        'zoom': 'slow_in',
        'text_main': '',
        'text_sub': '',
        'text_timing': None,
        'text_pos': None,
    },
    {
        'file': '7C1A5496.JPG',
        'duration': 4.2,
        'zoom': 'slow_right',
        'text_main': '',
        'text_sub': '',
        'text_timing': None,
        'text_pos': None,
    },
    {
        'file': '7C1A5411.JPG',
        'duration': 3.8,
        'zoom': 'slow_in',
        'text_main': '',
        'text_sub': '',
        'text_timing': None,
        'text_pos': None,
    },
    {
        'file': '7C1A5450.JPG',
        'duration': 3.8,
        'zoom': 'slow_out',
        'text_main': '五感を、満たす',
        'text_sub': '',
        'text_timing': (0.25, 0.80),
        'text_pos': 'lower',
    },
    {
        'file': '7C1A5225.JPG',
        'duration': 5.0,
        'zoom': 'slow_up',
        'text_main': '',
        'text_sub': '',
        'text_timing': None,
        'text_pos': None,
    },
    {
        'file': '7C1A5475.JPG',
        'duration': 9.4,
        'zoom': 'slow_in',
        'text_main': '奈良春日 鹿のや',
        'text_sub': 'Nara Kasuga Kanoya',
        'text_timing': (0.25, 0.90),
        'text_pos': 'center',
    },
]


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_out_quart(t):
    return 1 - (1 - t) ** 4

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


image_cache = {}

def load_image(filename):
    if filename in image_cache:
        return image_cache[filename]
    path = os.path.join(BASE, filename)
    pil_img = Image.open(path).convert('RGB')
    iw, ih = pil_img.size

    if iw > ih:
        # Landscape: blurred bg + centered sharp (slightly larger ratio)
        bg_scale = max(OUT_W / iw, OUT_H / ih)
        bg_w, bg_h = int(iw * bg_scale), int(ih * bg_scale)
        bg = pil_img.resize((bg_w, bg_h), Image.LANCZOS)
        left, top = (bg_w - OUT_W) // 2, (bg_h - OUT_H) // 2
        bg = bg.crop((left, top, left + OUT_W, top + OUT_H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=35))
        bg_arr = (np.array(bg).astype(np.float32) * 0.18).astype(np.uint8)
        bg = Image.fromarray(bg_arr)
        fg_scale = OUT_W / iw
        fg_w, fg_h = OUT_W, int(ih * fg_scale)
        fg = pil_img.resize((fg_w, fg_h), Image.LANCZOS)
        canvas = bg.copy()
        canvas.paste(fg, (0, (OUT_H - fg_h) // 2))
        arr = np.array(canvas)
    else:
        # Portrait: fit with slight extra for zoom headroom
        scale = max(OUT_W / iw, OUT_H / ih) * 1.08
        new_w, new_h = int(iw * scale), int(ih * scale)
        img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        left, top = (new_w - OUT_W) // 2, (new_h - OUT_H) // 2
        img = img.crop((left, top, left + OUT_W, top + OUT_H))
        arr = np.array(img)

    image_cache[filename] = arr
    return arr


def apply_zoom(frame, progress, mode='slow_in'):
    """Various slow, elegant camera movements."""
    h, w = frame.shape[:2]
    amount = 0.035  # subtle

    if mode == 'slow_in':
        zoom = 1.0 + amount * ease_in_out_sine(progress)
        cx, cy = 0.5, 0.5
    elif mode == 'slow_out':
        zoom = (1.0 + amount) - amount * ease_in_out_sine(progress)
        cx, cy = 0.5, 0.5
    elif mode == 'slow_up':
        zoom = 1.0 + amount * 0.5
        cx = 0.5
        cy = 0.5 + 0.02 * (1 - ease_in_out_sine(progress))
    elif mode == 'slow_right':
        zoom = 1.0 + amount * 0.5
        cx = 0.48 + 0.04 * ease_in_out_sine(progress)
        cy = 0.5
    else:
        zoom = 1.0
        cx, cy = 0.5, 0.5

    new_w, new_h = int(w * zoom), int(h * zoom)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    x_off = int((new_w - w) * cx)
    y_off = int((new_h - h) * cy)
    x_off = max(0, min(x_off, new_w - w))
    y_off = max(0, min(y_off, new_h - h))

    cropped = resized[y_off:y_off + h, x_off:x_off + w]
    # Ensure exact output size
    if cropped.shape[0] != h or cropped.shape[1] != w:
        cropped = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
    return cropped


def get_text_size(text, font):
    lines = text.split('\n')
    max_w, total_h = 0, 0
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        max_w = max(max_w, bbox[2] - bbox[0])
        total_h += bbox[3] - bbox[1] + (20 if i < len(lines) - 1 else 0)
    return max_w, total_h


def add_text_overlay(frame_arr, slide, progress):
    """Add elegant text overlay on image. Minimal, refined."""
    if not slide.get('text_main') or slide['text_timing'] is None:
        return frame_arr

    t_start, t_end = slide['text_timing']

    # Text opacity curve: gentle rise and fall
    if progress < t_start:
        opacity = 0.0
    elif progress < t_start + 0.12:
        opacity = ease_out_quart((progress - t_start) / 0.12)
    elif progress > t_end - 0.10:
        if progress > t_end:
            opacity = 0.0
        else:
            opacity = ease_in_out_sine((t_end - progress) / 0.10)
    else:
        opacity = 1.0

    if opacity < 0.01:
        return frame_arr

    pil = Image.fromarray(frame_arr).convert('RGBA')
    overlay = Image.new('RGBA', pil.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    main_text = slide['text_main']
    sub_text = slide.get('text_sub', '')
    pos = slide['text_pos']

    # Font sizes
    main_size = 52 if len(main_text) <= 8 else 44
    font_main = ImageFont.truetype(FONT_PATH, main_size)
    font_sub = ImageFont.truetype(FONT_PATH, 22)

    mw, mh = get_text_size(main_text, font_main)

    if pos == 'center':
        mx = (OUT_W - mw) // 2
        my = OUT_H // 2 - mh // 2 - 20
    elif pos == 'lower':
        mx = (OUT_W - mw) // 2
        my = OUT_H - 380

    # Subtle dark scrim behind text (very soft gradient, not a bar)
    scrim_cy = my + mh // 2 + 20
    scrim_h = 280
    for y in range(max(0, scrim_cy - scrim_h), min(OUT_H, scrim_cy + scrim_h)):
        dist = abs(y - scrim_cy) / scrim_h
        a = int(80 * opacity * (1 - dist * dist))
        draw.line([(0, y), (OUT_W, y)], fill=(0, 0, 0, a))

    # Main text with soft multi-layer shadow
    shadow_a = int(120 * opacity)
    main_a = int(255 * opacity)

    # Soft glow behind text
    for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1),(0,-2),(0,2),(-2,0),(2,0)]:
        draw.text((mx + dx * 2, my + dy * 2), main_text, font=font_main,
                  fill=(WARM_SHADOW[0], WARM_SHADOW[1], WARM_SHADOW[2], shadow_a // 3))
    # Shadow
    draw.text((mx + 2, my + 2), main_text, font=font_main,
              fill=(WARM_SHADOW[0], WARM_SHADOW[1], WARM_SHADOW[2], shadow_a))
    # Main
    draw.text((mx, my), main_text, font=font_main,
              fill=(CREAM[0], CREAM[1], CREAM[2], main_a))

    # Decorative thin line
    line_y = my + mh + 18
    line_w = int(min(mw * 0.6, 200) * min(1, opacity * 1.5))
    if line_w > 5:
        lcx = OUT_W // 2
        line_a = int(150 * opacity)
        draw.line([(lcx - line_w // 2, line_y), (lcx + line_w // 2, line_y)],
                  fill=(GOLD[0], GOLD[1], GOLD[2], line_a), width=1)

    # Sub text (English)
    if sub_text:
        sw, sh = get_text_size(sub_text, font_sub)
        sx = (OUT_W - sw) // 2
        sy = line_y + 16
        sub_a = int(180 * opacity)
        draw.text((sx + 1, sy + 1), sub_text, font=font_sub,
                  fill=(WARM_SHADOW[0], WARM_SHADOW[1], WARM_SHADOW[2], sub_a // 2))
        draw.text((sx, sy), sub_text, font=font_sub,
                  fill=(GOLD[0], GOLD[1], GOLD[2], sub_a))

    result = Image.alpha_composite(pil, overlay)
    return np.array(result.convert('RGB'))


# Pre-load images
print("Loading images...")
for slide in slides:
    img = load_image(slide['file'])
    iw_orig = Image.open(os.path.join(BASE, slide['file'])).size[0]
    ih_orig = Image.open(os.path.join(BASE, slide['file'])).size[1]
    orient = "横" if iw_orig > ih_orig else "縦"
    label = slide['text_main'] or '(映像のみ)'
    print(f"  {slide['file']:30s} {orient}  {label}")


# Build timeline: calculate absolute start/end times
# Each slide overlaps with next by CROSSFADE_SEC
abs_times = []
current_t = 0.0
for i, slide in enumerate(slides):
    start = current_t
    end = current_t + slide['duration']
    abs_times.append((start, end))
    # Next slide starts CROSSFADE_SEC before this one ends
    if i < len(slides) - 1:
        current_t = end - CROSSFADE_SEC

total_duration = abs_times[-1][1]
total_frames = int(total_duration * FPS)

print(f"\nTimeline ({total_duration:.1f}s):")
for i, (s, e) in enumerate(abs_times):
    print(f"  [{s:5.1f} - {e:5.1f}]  {slides[i]['file']}")

# Generate video
output_path = os.path.join(BASE, 'shikanoya_reel.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, FPS, (OUT_W, OUT_H))

# Fade from black duration
FADE_IN_SEC = 2.0
FADE_OUT_SEC = 2.5

print(f"Rendering {total_frames} frames...")

for frame_idx in range(total_frames):
    t = frame_idx / FPS

    # Find all slides active at time t (could be 2 during crossfade)
    active = []
    for i, (start, end) in enumerate(abs_times):
        if start <= t < end:
            progress = (t - start) / (end - start)
            active.append((i, progress))

    if len(active) == 0:
        frame = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
    elif len(active) == 1:
        idx, prog = active[0]
        slide = slides[idx]
        img = load_image(slide['file'])
        frame = apply_zoom(img, prog, slide['zoom'])
        frame = add_text_overlay(frame, slide, prog)
    else:
        # Crossfade between two slides
        idx1, prog1 = active[0]
        idx2, prog2 = active[1]
        slide1 = slides[idx1]
        slide2 = slides[idx2]

        img1 = load_image(slide1['file'])
        img2 = load_image(slide2['file'])

        f1 = apply_zoom(img1, prog1, slide1['zoom'])
        f1 = add_text_overlay(f1, slide1, prog1)
        f2 = apply_zoom(img2, prog2, slide2['zoom'])
        f2 = add_text_overlay(f2, slide2, prog2)

        # Crossfade alpha based on how far into overlap we are
        overlap_start = abs_times[idx2][0]
        overlap_end = abs_times[idx1][1]
        if overlap_end > overlap_start:
            alpha = ease_in_out_cubic((t - overlap_start) / (overlap_end - overlap_start))
        else:
            alpha = 0.5

        frame = ((1 - alpha) * f1.astype(np.float32) + alpha * f2.astype(np.float32)).astype(np.uint8)

    # Global fade in from black
    if t < FADE_IN_SEC:
        fade = ease_out_quart(t / FADE_IN_SEC)
        frame = (frame.astype(np.float32) * fade).astype(np.uint8)

    # Global fade out to black
    remaining = total_duration - t
    if remaining < FADE_OUT_SEC:
        fade = ease_in_out_sine(remaining / FADE_OUT_SEC)
        frame = (frame.astype(np.float32) * fade).astype(np.uint8)

    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

out.release()

size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"\n=== Luxury Film Reel ===")
print(f"Duration: {total_duration:.1f}s")
print(f"Size: {size_mb:.1f} MB")
print(f"Crossfade: {CROSSFADE_SEC}s")
print(f"Fade in: {FADE_IN_SEC}s / Fade out: {FADE_OUT_SEC}s")
