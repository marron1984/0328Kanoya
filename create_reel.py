"""Create an Instagram Reel (9:16 vertical) with promotional text overlays."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE = '/home/user/0328Kanoya'

# Reel settings
OUT_W, OUT_H = 1080, 1920
FPS = 30
DISPLAY_SEC = 3.0
TRANS_SEC = 0.8
DISPLAY_FRAMES = int(DISPLAY_SEC * FPS)
TRANS_FRAMES = int(TRANS_SEC * FPS)
FADE_FRAMES = int(1.0 * FPS)

# Fonts
FONT_PATH = '/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf'
FONT_MAIN = ImageFont.truetype(FONT_PATH, 52)
FONT_SUB = ImageFont.truetype(FONT_PATH, 34)
FONT_BRAND = ImageFont.truetype(FONT_PATH, 40)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 28)

# Image order + promotional captions
slides = [
    {
        'file': 'images/sakura_01.jpg',
        'main': '春、奈良へ。',
        'sub': '桜咲く古都で過ごす\n特別なひととき',
        'position': 'center',
    },
    {
        'file': '7C1A5099.JPG',
        'main': '神鹿の棲む杜',
        'sub': '千年の歴史が息づく\n奈良春日の地',
        'position': 'bottom',
    },
    {
        'file': '7C1A5475.JPG',
        'main': '宵に浮かぶ、和の庭',
        'sub': '四季の移ろいを\n灯りが照らす',
        'position': 'bottom',
    },
    {
        'file': '7C1A5128.JPG',
        'main': '森を望む、個室の贅',
        'sub': '春日の杜と向き合う\n静謐なダイニング',
        'position': 'bottom',
    },
    {
        'file': '7C1A5496.JPG',
        'main': '一枚板の特等席',
        'sub': '料理人の技を\n目の前で愉しむ',
        'position': 'bottom',
    },
    {
        'file': '7C1A5411.JPG',
        'main': '素材と向き合う',
        'sub': '旬を見極める\n料理人の眼差し',
        'position': 'bottom',
    },
    {
        'file': '7C1A5450.JPG',
        'main': '一つひとつ、手仕事で',
        'sub': '丁寧に紡ぐ\n奈良の味わい',
        'position': 'bottom',
    },
    {
        'file': '7C1A5225.JPG',
        'main': 'やすらぎの空間',
        'sub': '和の意匠に包まれ\n奈良の夜を、ゆっくりと',
        'position': 'bottom',
    },
    {
        'file': 'images/sakura_02.jpg',
        'main': '奈良春日 鹿のや',
        'sub': 'ご予約・お問い合わせは\nプロフィールリンクから',
        'position': 'center',
    },
]


def fit_for_reel(pil_img):
    """Fit image to 1080x1920 Reel format."""
    iw, ih = pil_img.size
    is_landscape = iw > ih

    if is_landscape:
        # Blurred dark background + sharp centered image
        bg_scale = max(OUT_W / iw, OUT_H / ih)
        bg_w, bg_h = int(iw * bg_scale), int(ih * bg_scale)
        bg = pil_img.resize((bg_w, bg_h), Image.LANCZOS)
        left = (bg_w - OUT_W) // 2
        top = (bg_h - OUT_H) // 2
        bg = bg.crop((left, top, left + OUT_W, top + OUT_H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        bg_arr = np.array(bg).astype(np.float32) * 0.3
        bg = Image.fromarray(bg_arr.astype(np.uint8))

        fg_scale = OUT_W / iw
        fg_w = OUT_W
        fg_h = int(ih * fg_scale)
        fg = pil_img.resize((fg_w, fg_h), Image.LANCZOS)

        canvas = bg.copy()
        y_offset = (OUT_H - fg_h) // 2
        canvas.paste(fg, (0, y_offset))
        return canvas
    else:
        scale = max(OUT_W / iw, OUT_H / ih)
        new_w, new_h = int(iw * scale), int(ih * scale)
        img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - OUT_W) // 2
        top = (new_h - OUT_H) // 2
        img = img.crop((left, top, left + OUT_W, top + OUT_H))
        return img


def draw_text_with_shadow(draw, xy, text, font, fill=(255, 255, 255, 255),
                          shadow_color=(0, 0, 0, 160), shadow_offset=3):
    """Draw text with drop shadow for readability."""
    x, y = xy
    # Shadow
    for line_i, line in enumerate(text.split('\n')):
        bbox = font.getbbox(line)
        line_h = bbox[3] - bbox[1]
        line_y = y + line_i * (line_h + 12)
        draw.text((x + shadow_offset, line_y + shadow_offset), line, font=font, fill=shadow_color)
    # Main text
    for line_i, line in enumerate(text.split('\n')):
        bbox = font.getbbox(line)
        line_h = bbox[3] - bbox[1]
        line_y = y + line_i * (line_h + 12)
        draw.text((x, line_y), line, font=font, fill=fill)


def get_text_block_size(text, font):
    """Calculate total size of a multiline text block."""
    lines = text.split('\n')
    max_w = 0
    total_h = 0
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += h + (12 if i < len(lines) - 1 else 0)
    return max_w, total_h


def add_caption_overlay(pil_img, slide, alpha=1.0):
    """Add promotional text overlay to a PIL image."""
    # Work in RGBA for transparency
    canvas = pil_img.convert('RGBA')
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    main_text = slide['main']
    sub_text = slide['sub']
    position = slide['position']

    # Semi-transparent gradient bar at text area
    if position == 'center':
        # Center: gradient overlay in middle
        bar_top = OUT_H // 2 - 180
        bar_bottom = OUT_H // 2 + 180
        for y in range(bar_top, bar_bottom):
            dist = abs(y - (bar_top + bar_bottom) // 2) / ((bar_bottom - bar_top) // 2)
            a = int(140 * (1 - dist * dist))  # quadratic falloff
            a = int(a * alpha)
            draw.line([(0, y), (OUT_W, y)], fill=(0, 0, 0, a))

        # Main text centered
        mw, mh = get_text_block_size(main_text, FONT_MAIN)
        mx = (OUT_W - mw) // 2
        my = OUT_H // 2 - mh - 30
        draw_text_with_shadow(draw, (mx, my), main_text, FONT_MAIN,
                              fill=(255, 255, 255, int(255 * alpha)),
                              shadow_color=(0, 0, 0, int(160 * alpha)))

        # Sub text centered
        sw, sh = get_text_block_size(sub_text, FONT_SUB)
        sx = (OUT_W - sw) // 2
        sy = OUT_H // 2 + 10
        draw_text_with_shadow(draw, (sx, sy), sub_text, FONT_SUB,
                              fill=(255, 255, 255, int(230 * alpha)),
                              shadow_color=(0, 0, 0, int(140 * alpha)))

    else:
        # Bottom: gradient bar at lower third
        bar_top = OUT_H - 480
        bar_bottom = OUT_H - 80
        for y in range(bar_top, bar_bottom):
            progress = (y - bar_top) / (bar_bottom - bar_top)
            a = int(160 * min(1, progress * 2))  # fade in from top
            a = int(a * alpha)
            draw.line([(0, y), (OUT_W, y)], fill=(0, 0, 0, a))

        # Main text
        mw, mh = get_text_block_size(main_text, FONT_MAIN)
        mx = (OUT_W - mw) // 2
        my = OUT_H - 400
        draw_text_with_shadow(draw, (mx, my), main_text, FONT_MAIN,
                              fill=(255, 255, 255, int(255 * alpha)),
                              shadow_color=(0, 0, 0, int(160 * alpha)))

        # Sub text
        sw, sh = get_text_block_size(sub_text, FONT_SUB)
        sx = (OUT_W - sw) // 2
        sy = OUT_H - 320
        draw_text_with_shadow(draw, (sx, sy), sub_text, FONT_SUB,
                              fill=(255, 255, 255, int(230 * alpha)),
                              shadow_color=(0, 0, 0, int(140 * alpha)))

    # Brand watermark at bottom
    brand = '奈良春日 鹿のや'
    bw, bh = get_text_block_size(brand, FONT_SMALL)
    bx = (OUT_W - bw) // 2
    by = OUT_H - 100
    draw_text_with_shadow(draw, (bx, by), brand, FONT_SMALL,
                          fill=(255, 255, 255, int(180 * alpha)),
                          shadow_color=(0, 0, 0, int(100 * alpha)),
                          shadow_offset=2)

    canvas = Image.alpha_composite(canvas, overlay)
    return canvas.convert('RGB')


def apply_ken_burns(frame_arr, progress, zoom_start=1.0, zoom_end=1.05):
    """Subtle Ken Burns zoom effect."""
    h, w = frame_arr.shape[:2]
    zoom = zoom_start + (zoom_end - zoom_start) * progress
    new_w, new_h = int(w * zoom), int(h * zoom)
    resized = cv2.resize(frame_arr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    x_off = (new_w - w) // 2
    y_off = (new_h - h) // 2
    return resized[y_off:y_off + h, x_off:x_off + w]


# Load images
print("Loading images for Reel with captions...")
reel_images = []  # PIL images (fitted to reel size)
for slide in slides:
    path = os.path.join(BASE, slide['file'])
    pil_img = Image.open(path).convert('RGB')
    fitted = fit_for_reel(pil_img)
    reel_images.append(fitted)
    iw, ih = pil_img.size
    orient = "横→ぼかし背景" if iw > ih else "縦→フィット"
    print(f"  {slide['file']:30s} {orient}  「{slide['main']}」")

# Create video
output_path = os.path.join(BASE, 'shikanoya_reel.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, FPS, (OUT_W, OUT_H))

TEXT_FADE_IN = int(0.6 * FPS)   # text fades in over 0.6s
TEXT_FADE_OUT = int(0.3 * FPS)  # text fades out over 0.3s

print("Generating Reel with captions...")

# Fade in from black (first slide)
for f in range(FADE_FRAMES):
    black_alpha = f / FADE_FRAMES
    progress = f / (DISPLAY_FRAMES + FADE_FRAMES)
    # Text alpha: starts appearing halfway through fade-in
    text_alpha = max(0, (f - FADE_FRAMES // 2) / (FADE_FRAMES // 2))
    captioned = add_caption_overlay(reel_images[0], slides[0], alpha=text_alpha)
    frame = apply_ken_burns(np.array(captioned), progress)
    frame = (frame.astype(np.float32) * black_alpha).astype(np.uint8)
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

# Main slideshow
for idx in range(len(reel_images)):
    pil_img = reel_images[idx]
    slide = slides[idx]

    for f in range(DISPLAY_FRAMES):
        progress = f / DISPLAY_FRAMES

        # Text fade in/out within each slide
        if f < TEXT_FADE_IN:
            text_alpha = f / TEXT_FADE_IN
        elif f > DISPLAY_FRAMES - TEXT_FADE_OUT:
            text_alpha = (DISPLAY_FRAMES - f) / TEXT_FADE_OUT
        else:
            text_alpha = 1.0

        captioned = add_caption_overlay(pil_img, slide, alpha=text_alpha)
        frame = apply_ken_burns(np.array(captioned), progress)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # Crossfade to next (no text during transition)
    if idx < len(reel_images) - 1:
        next_img = reel_images[idx + 1]
        for f in range(TRANS_FRAMES):
            alpha = f / TRANS_FRAMES
            frame1 = apply_ken_burns(np.array(pil_img), 1.0).astype(np.float32)
            frame2 = apply_ken_burns(np.array(next_img), 0.0).astype(np.float32)
            blended = ((1 - alpha) * frame1 + alpha * frame2).astype(np.uint8)
            out.write(cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))

# Fade out to black (last slide)
for f in range(FADE_FRAMES):
    black_alpha = 1.0 - f / FADE_FRAMES
    text_alpha = max(0, 1.0 - f / (FADE_FRAMES * 0.5))
    captioned = add_caption_overlay(reel_images[-1], slides[-1], alpha=text_alpha)
    frame = apply_ken_burns(np.array(captioned), 1.0)
    frame = (frame.astype(np.float32) * black_alpha).astype(np.uint8)
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

out.release()

size_mb = os.path.getsize(output_path) / (1024 * 1024)
total_frames = FADE_FRAMES * 2 + len(reel_images) * DISPLAY_FRAMES + (len(reel_images) - 1) * TRANS_FRAMES
duration = total_frames / FPS

print(f"\n=== Reel with Captions Created ===")
print(f"File: {output_path}")
print(f"Resolution: {OUT_W}x{OUT_H} (9:16)")
print(f"Duration: {duration:.1f} seconds")
print(f"Size: {size_mb:.1f} MB")
