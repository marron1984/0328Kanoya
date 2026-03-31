"""Instagram Reel - Cinematic trailer style, beat-synced to BGM."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

BASE = '/home/user/0328Kanoya'

OUT_W, OUT_H = 1080, 1920
FPS = 30

# Noto Serif JP
FONT_PATH = '/tmp/NotoSerifJP.ttf'

# BGM: 120 BPM = 0.5s per beat, ~30s total
# Structure: cinematic trailer
#   [0.0 - 2.0]   Black → Title fade in "奈良春日"
#   [2.0 - 4.0]   Title hold + subtitle "鹿のや"
#   [4.0 - 5.0]   Quick flash white → first image
#   [5.0 - 7.0]   Deer - slow, atmospheric (2 beats long)
#   [7.0 - 7.5]   Quick cut
#   [7.5 - 9.0]   Garden night
#   [9.0 - 9.5]   Quick cut
#   [9.5 - 11.0]  Private dining
#   [11.0 - 11.5] Quick cut
#   [11.5 - 13.0] Counter
#   [13.0 - 14.0] BLACK + text "五感を、満たす"
#   [14.0 - 15.5] Chef (wide)
#   [15.5 - 16.0] Flash cut
#   [16.0 - 17.0] Hands close-up (fast zoom)
#   [17.0 - 17.5] Flash cut
#   [17.5 - 19.5] Bedroom (slow, dreamy)
#   [19.5 - 20.5] BLACK + text "春、ここへ。"
#   [20.5 - 23.0] Sakura 1 (slow)
#   [23.0 - 25.0] Quick montage: all images rapid flash
#   [25.0 - 30.0] Brand card: logo + sakura bg, slow fade out

# Timeline: list of (start_sec, end_sec, type, data)
# Types: 'black', 'image', 'flash_white', 'title', 'montage', 'brand'

TIMELINE = [
    # Opening: dramatic black with title
    (0.0,  2.5,  'title',       {'main': '奈良春日', 'sub': '', 'fade_in': 1.5, 'fade_out': 0.5}),
    (2.5,  4.5,  'title',       {'main': '鹿のや', 'sub': '', 'fade_in': 0.8, 'fade_out': 0.3}),
    (4.5,  4.65, 'flash_white', {}),

    # Act 1: Space & atmosphere - longer cuts, breathing room
    (4.65, 7.0,  'image',       {'file': '7C1A5099.JPG', 'transition_in': 'cut', 'zoom': 'slow'}),
    (7.0,  7.15, 'flash_white', {}),
    (7.15, 9.0,  'image',       {'file': '7C1A5475.JPG', 'transition_in': 'cut', 'zoom': 'slow'}),
    (9.0,  9.15, 'flash_white', {}),
    (9.15, 11.0, 'image',       {'file': '7C1A5128.JPG', 'transition_in': 'cut', 'zoom': 'push'}),
    (11.0, 11.15,'flash_white', {}),
    (11.15,13.0, 'image',       {'file': '7C1A5496.JPG', 'transition_in': 'cut', 'zoom': 'slow'}),

    # Interlude: black + phrase
    (13.0, 14.5, 'title',       {'main': '五感を、満たす', 'sub': '', 'fade_in': 0.6, 'fade_out': 0.4}),

    # Act 2: Craft - tighter cuts, building intensity
    (14.5, 16.0, 'image',       {'file': '7C1A5411.JPG', 'transition_in': 'cut', 'zoom': 'push'}),
    (16.0, 16.1, 'flash_white', {}),
    (16.1, 17.5, 'image',       {'file': '7C1A5450.JPG', 'transition_in': 'cut', 'zoom': 'fast'}),

    # Act 3: Rest & beauty
    (17.5, 17.6, 'flash_white', {}),
    (17.6, 19.5, 'image',       {'file': '7C1A5225.JPG', 'transition_in': 'cut', 'zoom': 'slow'}),

    # Transition phrase
    (19.5, 21.0, 'title',       {'main': '春、ここへ。', 'sub': '', 'fade_in': 0.6, 'fade_out': 0.5}),

    # Sakura
    (21.0, 23.5, 'image',       {'file': 'images/sakura_01.jpg', 'transition_in': 'cut', 'zoom': 'slow'}),

    # Rapid montage: quick flashes of all images
    (23.5, 25.5, 'montage',     {'files': [
        '7C1A5099.JPG', '7C1A5475.JPG', '7C1A5128.JPG', '7C1A5496.JPG',
        '7C1A5411.JPG', '7C1A5450.JPG', '7C1A5225.JPG',
    ]}),

    # Brand card: final
    (25.5, 30.0, 'brand',       {
        'bg': 'images/sakura_02.jpg',
        'main': '奈良春日 鹿のや',
        'sub': 'Nara Kasuga  Kanoya',
        'fade_in': 1.5,
        'fade_out': 2.0,
    }),
]


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_quart(t):
    return 1 - (1 - t) ** 4

def ease_in_expo(t):
    return 0 if t == 0 else 2 ** (10 * t - 10)


# Pre-load and prepare all images
image_cache = {}

def load_image(filename):
    if filename in image_cache:
        return image_cache[filename]
    path = os.path.join(BASE, filename)
    pil_img = Image.open(path).convert('RGB')
    iw, ih = pil_img.size

    if iw > ih:
        # Landscape → blurred bg + centered sharp
        bg_scale = max(OUT_W / iw, OUT_H / ih)
        bg_w, bg_h = int(iw * bg_scale), int(ih * bg_scale)
        bg = pil_img.resize((bg_w, bg_h), Image.LANCZOS)
        left, top = (bg_w - OUT_W) // 2, (bg_h - OUT_H) // 2
        bg = bg.crop((left, top, left + OUT_W, top + OUT_H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        bg_arr = (np.array(bg).astype(np.float32) * 0.2).astype(np.uint8)
        bg = Image.fromarray(bg_arr)
        fg_scale = OUT_W / iw
        fg_w, fg_h = OUT_W, int(ih * fg_scale)
        fg = pil_img.resize((fg_w, fg_h), Image.LANCZOS)
        canvas = bg.copy()
        canvas.paste(fg, (0, (OUT_H - fg_h) // 2))
        arr = np.array(canvas)
    else:
        scale = max(OUT_W / iw, OUT_H / ih)
        new_w, new_h = int(iw * scale), int(ih * scale)
        img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        left, top = (new_w - OUT_W) // 2, (new_h - OUT_H) // 2
        img = img.crop((left, top, left + OUT_W, top + OUT_H))
        arr = np.array(img)

    image_cache[filename] = arr
    return arr


def apply_zoom(frame, progress, mode='slow'):
    """Ken Burns with different zoom speeds/directions."""
    h, w = frame.shape[:2]
    if mode == 'slow':
        zoom = 1.0 + 0.03 * progress
    elif mode == 'push':
        zoom = 1.0 + 0.06 * ease_out_cubic(progress)
    elif mode == 'fast':
        zoom = 1.0 + 0.08 * progress
    elif mode == 'pull':
        zoom = 1.06 - 0.06 * progress
    else:
        zoom = 1.0

    new_w, new_h = int(w * zoom), int(h * zoom)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    x_off, y_off = (new_w - w) // 2, (new_h - h) // 2
    return resized[y_off:y_off + h, x_off:x_off + w]


def render_title_frame(main_text, sub_text, opacity, progress=0):
    """Render cinematic title card on black."""
    canvas = Image.new('RGB', (OUT_W, OUT_H), (0, 0, 0))
    if opacity <= 0.01:
        return np.array(canvas)

    draw = ImageDraw.Draw(canvas)

    # Main title - large, centered
    font_size = 72 if len(main_text) <= 5 else 58
    font = ImageFont.truetype(FONT_PATH, font_size)
    bbox = font.getbbox(main_text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (OUT_W - tw) // 2
    ty = (OUT_H - th) // 2 - 20

    # Warm cream color with opacity
    r, g, b = 248, 240, 228
    alpha_r = int(r * opacity)
    alpha_g = int(g * opacity)
    alpha_b = int(b * opacity)
    draw.text((tx, ty), main_text, font=font, fill=(alpha_r, alpha_g, alpha_b))

    # Sub text (English) below
    if sub_text:
        sub_font = ImageFont.truetype(FONT_PATH, 24)
        sbbox = sub_font.getbbox(sub_text)
        stw = sbbox[2] - sbbox[0]
        stx = (OUT_W - stw) // 2
        sty = ty + th + 40
        sub_op = opacity * 0.7
        sr, sg, sb = int(200 * sub_op), int(185 * sub_op), int(160 * sub_op)
        draw.text((stx, sty), sub_text, font=sub_font, fill=(sr, sg, sb))

    return np.array(canvas)


def render_brand_frame(bg_arr, main_text, sub_text, opacity):
    """Render final brand card with background image."""
    # Darken background
    frame = (bg_arr.astype(np.float32) * 0.35).astype(np.uint8)
    pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil)

    if opacity <= 0.01:
        return np.array(pil)

    # Decorative top line
    line_w = int(200 * min(1, opacity * 1.5))
    cx = OUT_W // 2
    cy_line = OUT_H // 2 - 80
    line_color = (int(212 * opacity), int(185 * opacity), int(140 * opacity))
    if line_w > 10:
        draw.line([(cx - line_w // 2, cy_line), (cx + line_w // 2, cy_line)],
                  fill=line_color, width=1)

    # Main brand name
    font = ImageFont.truetype(FONT_PATH, 64)
    bbox = font.getbbox(main_text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (OUT_W - tw) // 2
    ty = OUT_H // 2 - 40
    r, g, b = 248, 240, 228
    draw.text((tx, ty), main_text, font=font,
              fill=(int(r * opacity), int(g * opacity), int(b * opacity)))

    # English subtitle
    sub_font = ImageFont.truetype(FONT_PATH, 22)
    sbbox = sub_font.getbbox(sub_text)
    stw = sbbox[2] - sbbox[0]
    stx = (OUT_W - stw) // 2
    sty = ty + th + 35
    sub_op = opacity * 0.65
    draw.text((stx, sty), sub_text, font=sub_font,
              fill=(int(200 * sub_op), int(185 * sub_op), int(160 * sub_op)))

    # Decorative bottom line
    cy_line2 = sty + 50
    if line_w > 10:
        draw.line([(cx - line_w // 2, cy_line2), (cx + line_w // 2, cy_line2)],
                  fill=line_color, width=1)

    return np.array(pil)


print("Pre-loading all images...")
all_files = set()
for seg in TIMELINE:
    data = seg[3]
    if 'file' in data:
        all_files.add(data['file'])
    if 'files' in data:
        all_files.update(data['files'])
    if 'bg' in data:
        all_files.add(data['bg'])

for f in sorted(all_files):
    load_image(f)
    print(f"  Loaded: {f}")

# Generate video
output_path = os.path.join(BASE, 'shikanoya_reel.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

total_duration = TIMELINE[-1][1]
total_frames = int(total_duration * FPS)
out = cv2.VideoWriter(output_path, fourcc, FPS, (OUT_W, OUT_H))

print(f"Generating cinematic reel ({total_duration:.1f}s, {total_frames} frames)...")

for frame_idx in range(total_frames):
    t = frame_idx / FPS  # current time in seconds

    # Find which segment we're in
    seg = None
    for s in TIMELINE:
        if s[0] <= t < s[1]:
            seg = s
            break

    if seg is None:
        # Black frame (shouldn't happen)
        frame = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
        out.write(frame)
        continue

    start, end, seg_type, data = seg
    seg_duration = end - start
    seg_progress = (t - start) / seg_duration  # 0..1

    if seg_type == 'title':
        fade_in = data.get('fade_in', 1.0)
        fade_out = data.get('fade_out', 0.5)
        elapsed = t - start
        remaining = end - t

        if elapsed < fade_in:
            opacity = ease_out_quart(elapsed / fade_in)
        elif remaining < fade_out:
            opacity = ease_in_out_sine(remaining / fade_out)
        else:
            opacity = 1.0

        frame = render_title_frame(data['main'], data.get('sub', ''), opacity, seg_progress)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    elif seg_type == 'image':
        img = load_image(data['file'])
        zoom_mode = data.get('zoom', 'slow')
        frame = apply_zoom(img, seg_progress, zoom_mode)

        # Slight vignette for cinematic feel
        # (darken edges)
        if seg_progress < 0.08:
            # Quick fade in from cut
            alpha = ease_out_cubic(seg_progress / 0.08)
            frame = (frame.astype(np.float32) * alpha).astype(np.uint8)

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    elif seg_type == 'flash_white':
        # Quick white flash that fades
        brightness = 1.0 - ease_out_cubic(seg_progress)
        val = int(255 * brightness)
        frame = np.full((OUT_H, OUT_W, 3), val, dtype=np.uint8)
        frame_bgr = frame

    elif seg_type == 'montage':
        files = data['files']
        # Rapid cuts: each image gets equal time
        n = len(files)
        img_idx = min(int(seg_progress * n), n - 1)
        sub_progress = (seg_progress * n) - img_idx

        img = load_image(files[img_idx])
        frame = apply_zoom(img, sub_progress, 'fast')

        # Flash effect between montage cuts
        if sub_progress < 0.08:
            flash = 1.0 - sub_progress / 0.08
            frame = np.clip(frame.astype(np.float32) + 200 * flash, 0, 255).astype(np.uint8)

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    elif seg_type == 'brand':
        bg = load_image(data['bg'])
        bg_zoomed = apply_zoom(bg, seg_progress * 0.3, 'slow')

        fade_in = data.get('fade_in', 1.5)
        fade_out = data.get('fade_out', 2.0)
        elapsed = t - start
        remaining = end - t

        if elapsed < fade_in:
            opacity = ease_out_quart(elapsed / fade_in)
        elif remaining < fade_out:
            opacity = ease_in_out_sine(remaining / fade_out)
        else:
            opacity = 1.0

        frame = render_brand_frame(bg_zoomed, data['main'], data['sub'], opacity)

        # Final fade to black in last 1.5s
        if remaining < 1.5:
            black_fade = remaining / 1.5
            frame = (frame.astype(np.float32) * black_fade).astype(np.uint8)

        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    else:
        frame_bgr = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)

    out.write(frame_bgr)

out.release()

size_mb = os.path.getsize(output_path) / (1024 * 1024)
print(f"\n=== Cinematic Reel ===")
print(f"Duration: {total_duration:.1f}s")
print(f"Size: {size_mb:.1f} MB")
print(f"Resolution: {OUT_W}x{OUT_H}")
print(f"Style: Movie trailer / beat-synced cuts")
