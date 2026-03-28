"""Generate artistic cherry blossom images using Pillow."""
import random
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(42)

def draw_petal(draw, cx, cy, size, angle, color):
    """Draw a single cherry blossom petal."""
    pts = []
    for i in range(20):
        t = i / 20 * 2 * math.pi
        # Petal shape: cardioid-like
        r = size * (0.5 + 0.5 * math.cos(t)) * (0.8 + 0.2 * math.sin(2 * t))
        x = cx + r * math.cos(t + angle)
        y = cy + r * math.sin(t + angle)
        pts.append((x, y))
    draw.polygon(pts, fill=color)

def draw_branch(draw, x1, y1, x2, y2, width, color):
    """Draw a branch line."""
    draw.line([(x1, y1), (x2, y2)], fill=color, width=max(1, int(width)))

def create_sakura_image_1():
    """Sakura branch with soft pink background - landscape orientation."""
    w, h = 1920, 1280
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)

    # Gradient sky background (soft spring sky)
    for y in range(h):
        ratio = y / h
        r = int(220 + 35 * (1 - ratio))
        g = int(200 + 40 * (1 - ratio))
        b = int(230 + 25 * (1 - ratio))
        draw.line([(0, y), (w, y)], fill=(min(255, r), min(255, g), min(255, b)))

    # Draw branches
    branches = [
        (0, 200, 600, 300, 8),
        (600, 300, 1000, 250, 6),
        (600, 300, 900, 450, 5),
        (1000, 250, 1400, 200, 4),
        (1000, 250, 1300, 350, 4),
        (900, 450, 1200, 500, 3),
        (1400, 200, 1700, 180, 3),
        (1300, 350, 1600, 400, 3),
        (0, 500, 400, 550, 6),
        (400, 550, 700, 520, 4),
        (400, 550, 600, 650, 3),
    ]
    branch_color = (90, 60, 40)
    for bx1, by1, bx2, by2, bw in branches:
        draw_branch(draw, bx1, by1, bx2, by2, bw, branch_color)

    # Draw cherry blossom clusters
    petal_colors = [
        (255, 182, 193), (255, 192, 203), (255, 174, 185),
        (255, 200, 210), (248, 170, 180), (255, 160, 175),
        (255, 210, 220), (252, 185, 195),
    ]

    blossom_centers = []
    for bx1, by1, bx2, by2, bw in branches:
        for _ in range(15):
            t = random.uniform(0.1, 0.9)
            cx = bx1 + t * (bx2 - bx1) + random.randint(-30, 30)
            cy = by1 + t * (by2 - by1) + random.randint(-30, 30)
            blossom_centers.append((cx, cy))

    # Draw blossoms
    for cx, cy in blossom_centers:
        num_petals = random.randint(4, 6)
        size = random.randint(12, 25)
        for i in range(num_petals):
            angle = (2 * math.pi * i / num_petals) + random.uniform(-0.3, 0.3)
            color = random.choice(petal_colors)
            px = cx + size * 0.5 * math.cos(angle)
            py = cy + size * 0.5 * math.sin(angle)
            draw_petal(draw, px, py, size * 0.7, angle, color)
        # Center of flower
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 230, 150))

    # Falling petals
    for _ in range(60):
        px = random.randint(0, w)
        py = random.randint(0, h)
        size = random.randint(5, 12)
        angle = random.uniform(0, 2 * math.pi)
        color = random.choice(petal_colors)
        alpha_color = (color[0], color[1], color[2])
        draw_petal(draw, px, py, size, angle, alpha_color)

    # Soft blur for dreamy effect
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))

    img.save('/home/user/0328Kanoya/images/sakura_01.jpg', 'JPEG', quality=95)
    print("sakura_01.jpg created")

def create_sakura_image_2():
    """Sakura petals floating on water - landscape orientation."""
    w, h = 1920, 1280
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)

    # Water-like gradient background
    for y in range(h):
        ratio = y / h
        r = int(180 + 50 * ratio)
        g = int(200 + 30 * ratio)
        b = int(220 + 20 * (1 - ratio))
        draw.line([(0, y), (w, y)], fill=(min(255, r), min(255, g), min(255, b)))

    # Subtle water ripples
    for _ in range(30):
        cx = random.randint(0, w)
        cy = random.randint(h // 3, h)
        rx = random.randint(80, 200)
        ry = random.randint(15, 40)
        ripple_color = (190 + random.randint(0, 30), 210 + random.randint(0, 20), 230)
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=ripple_color, width=1)

    # Sakura petals on water surface
    petal_colors = [
        (255, 182, 193), (255, 192, 203), (255, 174, 185),
        (255, 200, 210), (248, 170, 180), (255, 210, 220),
    ]

    for _ in range(120):
        px = random.randint(50, w - 50)
        py = random.randint(50, h - 50)
        size = random.randint(8, 22)
        angle = random.uniform(0, 2 * math.pi)
        color = random.choice(petal_colors)
        draw_petal(draw, px, py, size, angle, color)

    # Top portion: overhanging branches with blossoms
    branch_color = (80, 55, 35)
    top_branches = [
        (0, 0, 500, 150, 10),
        (500, 150, 900, 100, 7),
        (500, 150, 800, 280, 5),
        (900, 100, 1300, 80, 5),
        (1300, 80, 1600, 120, 4),
        (1600, 120, 1920, 80, 4),
        (800, 280, 1100, 300, 3),
    ]
    for bx1, by1, bx2, by2, bw in top_branches:
        draw_branch(draw, bx1, by1, bx2, by2, bw, branch_color)

    for bx1, by1, bx2, by2, bw in top_branches:
        for _ in range(12):
            t = random.uniform(0.1, 0.9)
            cx = bx1 + t * (bx2 - bx1) + random.randint(-20, 20)
            cy = by1 + t * (by2 - by1) + random.randint(-20, 20)
            num_petals = random.randint(4, 6)
            size = random.randint(10, 20)
            for i in range(num_petals):
                a = (2 * math.pi * i / num_petals) + random.uniform(-0.3, 0.3)
                c = random.choice(petal_colors)
                ppx = cx + size * 0.5 * math.cos(a)
                ppy = cy + size * 0.5 * math.sin(a)
                draw_petal(draw, ppx, ppy, size * 0.7, a, c)
            draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 230, 150))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.save('/home/user/0328Kanoya/images/sakura_02.jpg', 'JPEG', quality=95)
    print("sakura_02.jpg created")

create_sakura_image_1()
create_sakura_image_2()
print("Done!")
