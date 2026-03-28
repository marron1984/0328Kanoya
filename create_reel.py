"""Create Instagram Reel with varied text animations, matched to BGM duration."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

BASE = '/home/user/0328Kanoya'

# Reel settings
OUT_W, OUT_H = 1080, 1920
FPS = 30

# Match BGM duration (~30s)
# 9 slides x 2.4s + 8 transitions x 0.6s + fade in 1.0s + fade out 1.0s = 28.4s
DISPLAY_SEC = 2.4
TRANS_SEC = 0.6
DISPLAY_FRAMES = int(DISPLAY_SEC * FPS)
TRANS_FRAMES = int(TRANS_SEC * FPS)
FADE_FRAMES = int(1.0 * FPS)

# Fonts
FONT_PATH = '/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf'
FONT_MAIN = ImageFont.truetype(FONT_PATH, 54)
FONT_SUB = ImageFont.truetype(FONT_PATH, 34)
FONT_BRAND = ImageFont.truetype(FONT_PATH, 28)

# Animation types
ANIM_FADE_CENTER = 'fade_center'       # Gentle fade at center
ANIM_SLIDE_UP = 'slide_up'             # Slide up from below
ANIM_SLIDE_LEFT = 'slide_left'         # Slide in from right to left
ANIM_SLIDE_RIGHT = 'slide_right'       # Slide in from left to right
ANIM_TYPEWRITER = 'typewriter'          # Characters appear one by one
ANIM_SCALE_UP = 'scale_up'             # Zoom in from small

slides = [
    {
        'file': 'images/sakura_01.jpg',
        'main': '春、奈良へ。',
        'sub': '桜咲く古都で過ごす\n特別なひととき',
        'position': 'center',
        'anim': ANIM_FADE_CENTER,
    },
    {
        'file': '7C1A5099.JPG',
        'main': '神鹿の棲む杜',
        'sub': '千年の歴史が息づく\n奈良春日の地',
        'position': 'bottom',
        'anim': ANIM_SLIDE_UP,
    },
    {
        'file': '7C1A5475.JPG',
        'main': '宵に浮かぶ、和の庭',
        'sub': '四季の移ろいを\n灯りが照らす',
        'position': 'bottom',
        'anim': ANIM_SLIDE_LEFT,
    },
    {
        'file': '7C1A5128.JPG',
        'main': '森を望む、個室の贅',
        'sub': '春日の杜と向き合う\n静謐なダイニング',
        'position': 'bottom',
        'anim': ANIM_SLIDE_RIGHT,
    },
    {
        'file': '7C1A5496.JPG',
        'main': '一枚板の特等席',
        'sub': '料理人の技を\n目の前で愉しむ',
        'position': 'bottom',
        'anim': ANIM_SCALE_UP,
    },
    {
        'file': '7C1A5411.JPG',
        'main': '素材と向き合う',
        'sub': '旬を見極める\n料理人の眼差し',
        'position': 'bottom',
        'anim': ANIM_SLIDE_UP,
    },
    {
        'file': '7C1A5450.JPG',
        'main': '一つひとつ、手仕事で',
        'sub': '丁寧に紡ぐ\n奈良の味わい',
        'position': 'bottom',
        'anim': ANIM_TYPEWRITER,
    },
    {
        'file': '7C1A5225.JPG',
        'main': 'やすらぎの空間',
        'sub': '和の意匠に包まれ\n奈良の夜を、ゆっくりと',
        'position': 'bottom',
        'anim': ANIM_SLIDE_LEFT,
    },
    {
        'file': 'images/sakura_02.jpg',
        'main': '奈良春日 鹿のや',
        'sub': 'ご予約・お問い合わせは\nプロフィールリンクから',
        'position': 'center',
        'anim': ANIM_FADE_CENTER,
    },
]


def ease_out_cubic(t):
    """Ease-out cubic for smooth deceleration."""
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    """Ease-out with slight overshoot for playful feel."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * ((t - 1) ** 3) + c1 * ((t - 1) ** 2)


def ease_in_quad(t):
    return t * t


def fit_for_reel(pil_img):
    iw, ih = pil_img.size
    if iw > ih:
        bg_scale = max(OUT_W / iw, OUT_H / ih)
        bg_w, bg_h = int(iw * bg_scale), int(ih * bg_scale)
        bg = pil_img.resize((bg_w, bg_h), Image.LANCZOS)
        left, top = (bg_w - OUT_W) // 2, (bg_h - OUT_H) // 2
        bg = bg.crop((left, top, left + OUT_W, top + OUT_H))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        bg_arr = (np.array(bg).astype(np.float32) * 0.3).astype(np.uint8)
        bg = Image.fromarray(bg_arr)
        fg_scale = OUT_W / iw
        fg_w, fg_h = OUT_W, int(ih * fg_scale)
        fg = pil_img.resize((fg_w, fg_h), Image.LANCZOS)
        canvas = bg.copy()
        canvas.paste(fg, (0, (OUT_H - fg_h) // 2))
        return canvas
    else:
        scale = max(OUT_W / iw, OUT_H / ih)
        new_w, new_h = int(iw * scale), int(ih * scale)
        img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        left, top = (new_w - OUT_W) // 2, (new_h - OUT_H) // 2
        return img.crop((left, top, left + OUT_W, top + OUT_H))


def get_text_size(text, font):
    lines = text.split('\n')
    max_w, total_h = 0, 0
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        max_w = max(max_w, bbox[2] - bbox[0])
        total_h += bbox[3] - bbox[1] + (14 if i < len(lines) - 1 else 0)
    return max_w, total_h


def draw_multiline(draw, x, y, text, font, fill, shadow_color, shadow_off=3):
    """Draw multiline text with shadow."""
    for line in text.split('\n'):
        bbox = font.getbbox(line)
        lh = bbox[3] - bbox[1]
        draw.text((x + shadow_off, y + shadow_off), line, font=font, fill=shadow_color)
        draw.text((x, y), line, font=font, fill=fill)
        y += lh + 14


def draw_gradient_bar(draw, top, bottom, max_alpha):
    """Draw semi-transparent gradient background bar."""
    for y in range(top, bottom):
        if top == bottom:
            break
        progress = (y - top) / (bottom - top)
        # Smooth bell curve for center position, ramp for bottom position
        a = int(max_alpha * math.sin(progress * math.pi))
        draw.line([(0, y), (OUT_W, y)], fill=(0, 0, 0, a))


def add_caption_animated(pil_img, slide, frame_progress):
    """
    Add animated caption overlay.
    frame_progress: 0.0 to 1.0 over the display duration.
    """
    canvas = pil_img.convert('RGBA')
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    anim = slide['anim']
    position = slide['position']
    main_text = slide['main']
    sub_text = slide['sub']

    # Animation timing: text appears 10%-80% of display, fades out at end
    TEXT_IN_START = 0.08
    TEXT_IN_END = 0.30
    TEXT_HOLD_END = 0.82
    TEXT_OUT_END = 0.95

    if frame_progress < TEXT_IN_START:
        anim_progress = 0.0
        opacity = 0.0
    elif frame_progress < TEXT_IN_END:
        t = (frame_progress - TEXT_IN_START) / (TEXT_IN_END - TEXT_IN_START)
        anim_progress = ease_out_cubic(t)
        opacity = ease_out_cubic(t)
    elif frame_progress < TEXT_HOLD_END:
        anim_progress = 1.0
        opacity = 1.0
    elif frame_progress < TEXT_OUT_END:
        t = (frame_progress - TEXT_HOLD_END) / (TEXT_OUT_END - TEXT_HOLD_END)
        anim_progress = 1.0
        opacity = 1.0 - ease_in_quad(t)
    else:
        anim_progress = 1.0
        opacity = 0.0

    if opacity <= 0.01:
        return canvas.convert('RGB')

    # Calculate base text positions
    mw, mh = get_text_size(main_text, FONT_MAIN)
    sw, sh = get_text_size(sub_text, FONT_SUB)

    if position == 'center':
        base_mx, base_my = (OUT_W - mw) // 2, OUT_H // 2 - mh - 30
        base_sx, base_sy = (OUT_W - sw) // 2, OUT_H // 2 + 15
        bar_top, bar_bottom = OUT_H // 2 - 200, OUT_H // 2 + 200
    else:
        base_mx, base_my = (OUT_W - mw) // 2, OUT_H - 420
        base_sx, base_sy = (OUT_W - sw) // 2, OUT_H - 340
        bar_top, bar_bottom = OUT_H - 500, OUT_H - 80

    # Draw gradient background bar (fades with text)
    bar_alpha = int(150 * opacity)
    draw_gradient_bar(draw, bar_top, bar_bottom, bar_alpha)

    # Apply animation-specific transforms
    main_fill = (255, 255, 255, int(255 * opacity))
    sub_fill = (255, 255, 255, int(220 * opacity))
    shadow_main = (0, 0, 0, int(160 * opacity))
    shadow_sub = (0, 0, 0, int(130 * opacity))

    if anim == ANIM_FADE_CENTER:
        # Simple fade with slight upward drift
        drift = int(30 * (1 - anim_progress))
        draw_multiline(draw, base_mx, base_my + drift, main_text,
                       FONT_MAIN, main_fill, shadow_main)
        # Sub text appears slightly delayed
        sub_delay_progress = max(0, (anim_progress - 0.3) / 0.7) if anim_progress > 0.3 else 0
        sub_opacity_factor = ease_out_cubic(sub_delay_progress) if sub_delay_progress > 0 else 0
        sub_drift = int(20 * (1 - sub_delay_progress))
        sub_fill_delayed = (255, 255, 255, int(220 * opacity * sub_opacity_factor))
        shadow_sub_delayed = (0, 0, 0, int(130 * opacity * sub_opacity_factor))
        draw_multiline(draw, base_sx, base_sy + sub_drift, sub_text,
                       FONT_SUB, sub_fill_delayed, shadow_sub_delayed)

    elif anim == ANIM_SLIDE_UP:
        # Main slides up from below
        offset_main = int(120 * (1 - ease_out_back(anim_progress)))
        draw_multiline(draw, base_mx, base_my + offset_main, main_text,
                       FONT_MAIN, main_fill, shadow_main)
        # Sub slides up with delay
        sub_p = max(0, (anim_progress - 0.25) / 0.75)
        offset_sub = int(100 * (1 - ease_out_cubic(sub_p)))
        sub_op = ease_out_cubic(sub_p) if sub_p > 0 else 0
        sf = (255, 255, 255, int(220 * opacity * sub_op))
        ss = (0, 0, 0, int(130 * opacity * sub_op))
        draw_multiline(draw, base_sx, base_sy + offset_sub, sub_text, FONT_SUB, sf, ss)

    elif anim == ANIM_SLIDE_LEFT:
        # Main slides in from right
        offset_main = int(OUT_W * 0.4 * (1 - ease_out_cubic(anim_progress)))
        draw_multiline(draw, base_mx + offset_main, base_my, main_text,
                       FONT_MAIN, main_fill, shadow_main)
        # Sub slides from right with delay
        sub_p = max(0, (anim_progress - 0.2) / 0.8)
        offset_sub = int(OUT_W * 0.3 * (1 - ease_out_cubic(sub_p)))
        sub_op = ease_out_cubic(sub_p) if sub_p > 0 else 0
        sf = (255, 255, 255, int(220 * opacity * sub_op))
        ss = (0, 0, 0, int(130 * opacity * sub_op))
        draw_multiline(draw, base_sx + offset_sub, base_sy, sub_text, FONT_SUB, sf, ss)

    elif anim == ANIM_SLIDE_RIGHT:
        # Main slides in from left
        offset_main = int(-OUT_W * 0.4 * (1 - ease_out_cubic(anim_progress)))
        draw_multiline(draw, base_mx + offset_main, base_my, main_text,
                       FONT_MAIN, main_fill, shadow_main)
        sub_p = max(0, (anim_progress - 0.2) / 0.8)
        offset_sub = int(-OUT_W * 0.3 * (1 - ease_out_cubic(sub_p)))
        sub_op = ease_out_cubic(sub_p) if sub_p > 0 else 0
        sf = (255, 255, 255, int(220 * opacity * sub_op))
        ss = (0, 0, 0, int(130 * opacity * sub_op))
        draw_multiline(draw, base_sx + offset_sub, base_sy, sub_text, FONT_SUB, sf, ss)

    elif anim == ANIM_SCALE_UP:
        # Main text scales up (rendered at different font sizes)
        scale_factor = 0.6 + 0.4 * ease_out_back(anim_progress)
        scaled_size = max(16, int(54 * scale_factor))
        scaled_font = ImageFont.truetype(FONT_PATH, scaled_size)
        smw, smh = get_text_size(main_text, scaled_font)
        smx = (OUT_W - smw) // 2
        smy = base_my + (mh - smh) // 2
        draw_multiline(draw, smx, smy, main_text, scaled_font, main_fill, shadow_main)
        # Sub appears after main settles
        sub_p = max(0, (anim_progress - 0.4) / 0.6)
        sub_op = ease_out_cubic(sub_p) if sub_p > 0 else 0
        sub_drift = int(15 * (1 - sub_p))
        sf = (255, 255, 255, int(220 * opacity * sub_op))
        ss = (0, 0, 0, int(130 * opacity * sub_op))
        draw_multiline(draw, base_sx, base_sy + sub_drift, sub_text, FONT_SUB, sf, ss)

    elif anim == ANIM_TYPEWRITER:
        # Main text: characters revealed one by one
        total_chars = len(main_text)
        visible_chars = int(total_chars * min(1.0, anim_progress * 1.5))
        visible_text = main_text[:visible_chars]
        # Cursor blink effect
        if anim_progress < 0.7 and visible_chars < total_chars:
            if int(anim_progress * 20) % 2 == 0:
                visible_text += '｜'
        draw_multiline(draw, base_mx, base_my, visible_text,
                       FONT_MAIN, main_fill, shadow_main)
        # Sub appears after typewriter finishes
        sub_p = max(0, (anim_progress - 0.6) / 0.4)
        sub_op = ease_out_cubic(sub_p) if sub_p > 0 else 0
        sf = (255, 255, 255, int(220 * opacity * sub_op))
        ss = (0, 0, 0, int(130 * opacity * sub_op))
        draw_multiline(draw, base_sx, base_sy, sub_text, FONT_SUB, sf, ss)

    # Brand watermark (always gentle fade)
    brand = '奈良春日 鹿のや'
    bw, _ = get_text_size(brand, FONT_BRAND)
    bx = (OUT_W - bw) // 2
    by = OUT_H - 90
    brand_fill = (255, 255, 255, int(160 * opacity))
    brand_shadow = (0, 0, 0, int(80 * opacity))
    draw_multiline(draw, bx, by, brand, FONT_BRAND, brand_fill, brand_shadow, shadow_off=2)

    canvas = Image.alpha_composite(canvas, overlay)
    return canvas.convert('RGB')


def apply_ken_burns(frame_arr, progress, zoom_start=1.0, zoom_end=1.04):
    h, w = frame_arr.shape[:2]
    zoom = zoom_start + (zoom_end - zoom_start) * progress
    new_w, new_h = int(w * zoom), int(h * zoom)
    resized = cv2.resize(frame_arr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    x_off, y_off = (new_w - w) // 2, (new_h - h) // 2
    return resized[y_off:y_off + h, x_off:x_off + w]


# Load
print("Loading images...")
reel_images = []
for slide in slides:
    path = os.path.join(BASE, slide['file'])
    pil_img = Image.open(path).convert('RGB')
    fitted = fit_for_reel(pil_img)
    reel_images.append(fitted)
    iw, ih = pil_img.size
    orient = "横→ぼかし背景" if iw > ih else "縦→フィット"
    print(f"  {slide['file']:30s} {orient}  [{slide['anim']}] 「{slide['main']}」")

# Create video
output_path = os.path.join(BASE, 'shikanoya_reel.mp4')
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, FPS, (OUT_W, OUT_H))

print("Generating Reel...")

# Fade in from black
for f in range(FADE_FRAMES):
    black_alpha = f / FADE_FRAMES
    kb_progress = f / (DISPLAY_FRAMES + FADE_FRAMES)
    text_progress = f / (FADE_FRAMES + DISPLAY_FRAMES)  # text starts during fade
    captioned = add_caption_animated(reel_images[0], slides[0], text_progress)
    frame = apply_ken_burns(np.array(captioned), kb_progress)
    frame = (frame.astype(np.float32) * black_alpha).astype(np.uint8)
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

# Main slideshow
for idx in range(len(reel_images)):
    pil_img = reel_images[idx]
    slide = slides[idx]

    for f in range(DISPLAY_FRAMES):
        kb_progress = f / DISPLAY_FRAMES
        if idx == 0:
            # First slide: account for fade-in period in text timing
            text_progress = (FADE_FRAMES + f) / (FADE_FRAMES + DISPLAY_FRAMES)
        else:
            text_progress = f / DISPLAY_FRAMES

        captioned = add_caption_animated(pil_img, slide, text_progress)
        frame = apply_ken_burns(np.array(captioned), kb_progress)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # Crossfade (no text)
    if idx < len(reel_images) - 1:
        next_img = reel_images[idx + 1]
        for f in range(TRANS_FRAMES):
            alpha = f / TRANS_FRAMES
            # Smooth ease for crossfade
            alpha = ease_out_cubic(alpha)
            f1 = apply_ken_burns(np.array(pil_img), 1.0).astype(np.float32)
            f2 = apply_ken_burns(np.array(next_img), 0.0).astype(np.float32)
            blended = ((1 - alpha) * f1 + alpha * f2).astype(np.uint8)
            out.write(cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))

# Fade out to black
for f in range(FADE_FRAMES):
    black_alpha = 1.0 - f / FADE_FRAMES
    text_progress = 1.0 - (f / FADE_FRAMES) * 0.1  # text is fading out
    captioned = add_caption_animated(reel_images[-1], slides[-1], text_progress)
    frame = apply_ken_burns(np.array(captioned), 1.0)
    frame = (frame.astype(np.float32) * black_alpha).astype(np.uint8)
    out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

out.release()

size_mb = os.path.getsize(output_path) / (1024 * 1024)
total_frames = FADE_FRAMES * 2 + len(reel_images) * DISPLAY_FRAMES + (len(reel_images) - 1) * TRANS_FRAMES
duration = total_frames / FPS

print(f"\n=== Reel Created ===")
print(f"Duration: {duration:.1f}s (BGM: ~30s)")
print(f"Size: {size_mb:.1f} MB")
print(f"Resolution: {OUT_W}x{OUT_H}")
