"""Animated graphics drawn with Pillow. Each graphic: fn(t_local, dur, p) -> (RGBA image, x, y) or None."""
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONTS = Path(__file__).resolve().parent.parent / "assets/fonts"
YELLOW = (255, 212, 0, 255)
RED = (235, 45, 45, 255)
GREEN = (40, 200, 90, 255)


@lru_cache(None)
def font(name, size):
    # All bundled fonts are redistributable OFL fonts, never proprietary OS fonts.
    aliases = {"ariblk.ttf": "Inter.ttf", "segoeuib.ttf": "Inter.ttf", "bahnschrift.ttf": "Inter.ttf"}
    f = ImageFont.truetype(str(FONTS / aliases.get(name, name)), size)
    if aliases.get(name, name) == "Inter.ttf":
        axes = f.get_variation_axes()
        f.set_variation_by_axes([800 if a["name"] == b"Weight" else a["default"] for a in axes])
    return f


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(p):
    return 1 - (1 - clamp(p)) ** 3


def ease_back(p, s=1.7):
    p = clamp(p) - 1
    return 1 + p * p * ((s + 1) * p + s)


def pop_scale(t, dur, t_in=0.28, t_out=0.18):
    """Overshoot pop in, quick shrink out. Returns (scale, alpha)."""
    if t < t_in:
        return 0.6 + 0.4 * ease_back(t / t_in), clamp(t / 0.08)
    if t > dur - t_out:
        p = (t - (dur - t_out)) / t_out
        return 1 - 0.15 * ease_out(p), 1 - ease_out(p)
    return 1.0, 1.0


def finish(img, scale, alpha, cx, cy):
    if scale != 1.0:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    if alpha < 1.0:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img.putalpha(a)
    return img, int(cx - img.width / 2), int(cy - img.height / 2)


def shadowed(card, radius=18, offset=8, opacity=150):
    """Add a soft drop shadow around an RGBA card."""
    pad = radius * 2
    out = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, opacity), (pad, pad + offset, pad + card.width, pad + offset + card.height), card.getchannel("A"))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(radius)))
    out.alpha_composite(card, (pad, pad))
    return out


def text_size(f, s):
    b = f.getbbox(s)
    return b[2] - b[0], b[3] - b[1], b


# ---------- hook title ----------
@lru_cache(None)
def _title_card(title, sub, logo):
    f1, f2 = font("ariblk.ttf", 80), font("segoeuib.ttf", 42)
    tw, th, tb = text_size(f1, title)
    eye = 92
    w1 = eye + 28 + tw + 80
    card = Image.new("RGBA", (w1, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, w1 - 1, 149), 40, fill=(12, 12, 16, 235))
    # eye icon
    ex, ey = 44, 75
    d.ellipse((ex - 6, ey - 30, ex + eye - 6, ey + 30), outline=YELLOW, width=7)
    d.ellipse((ex + eye / 2 - 24, ey - 18, ex + eye / 2 + 12, ey + 18), fill=YELLOW)
    d.ellipse((ex + eye / 2 - 14, ey - 8, ex + eye / 2 + 2, ey + 8), fill=(12, 12, 16, 255))
    d.text((eye + 68 - tb[0], 75 - th / 2 - tb[1]), title, font=f1, fill="white")
    # badge
    sw, sh, sb = text_size(f2, sub)
    lg = Image.open(FONTS.parent.parent / logo).convert("RGBA")
    lg.thumbnail((48, 48))
    w2 = 30 + lg.width + 16 + sw + 34
    badge = Image.new("RGBA", (w2, 76), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle((0, 0, w2 - 1, 75), 38, fill=(255, 255, 255, 245))
    badge.alpha_composite(lg, (30, (76 - lg.height) // 2))
    bd.text((30 + lg.width + 16 - sb[0], 38 - sh / 2 - sb[1]), sub, font=f2, fill=(20, 20, 20))
    out = Image.new("RGBA", (max(w1, w2), 150 + 18 + 76), (0, 0, 0, 0))
    out.alpha_composite(card, ((out.width - w1) // 2, 0))
    out.alpha_composite(badge, ((out.width - w2) // 2, 168))
    return shadowed(out)


def title(t, dur, p):
    img = _title_card(p["text"], p["sub"], p["logo"])
    s, a = pop_scale(t, dur)
    return finish(img.copy(), s, a, W / 2, p.get("y", 260))


# ---------- HUD over the montage ----------
def hud(t, dur, p):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    a = int(255 * clamp(t / 0.15) * clamp((dur - t) / 0.15))
    c = (255, 255, 255, int(a * 0.85))
    m, L, wd = 60, 90, 6
    for x, y, sx, sy in ((m, m + 120, 1, 1), (W - m, m + 120, -1, 1), (m, H - m - 120, 1, -1), (W - m, H - m - 120, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=c, width=wd)
        d.line((x, y, x, y + sy * L), fill=c, width=wd)
    f = font("bahnschrift.ttf", 40)
    if int(t * 2.5) % 2 == 0:
        d.ellipse((m + 14, m + 150, m + 44, m + 180), fill=(255, 40, 40, a))
    d.text((m + 58, m + 142), p.get('label', 'VISUAL OVERLAY'), font=f, fill=c)
    d.text((m + 14, H - m - 190), 'ILLUSTRATIVE - NOT LIVE DATA', font=font("bahnschrift.ttf", 28), fill=c)
    # crosshair
    cx, cy, r = W / 2, H * 0.42, 70
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, int(a * 0.55)), width=4)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.line((cx + dx * (r - 25), cy + dy * (r - 25), cx + dx * (r + 30), cy + dy * (r + 30)),
               fill=(255, 255, 255, int(a * 0.55)), width=4)
    return img, 0, 0


# ---------- logo card ----------
@lru_cache(None)
def _logo_card(logo, tag):
    lg = Image.open(FONTS.parent.parent / logo).convert("RGBA")
    lg.thumbnail((640, 160))
    w, h = lg.width + 120, lg.height + 120
    card = Image.new("RGBA", (w, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 40, w - 1, h + 39), 36, fill=(255, 255, 255, 250))
    card.alpha_composite(lg, (60, 100))
    f = font("ariblk.ttf", 44)
    tw, th, tb = text_size(f, tag)
    d.rounded_rectangle((w / 2 - tw / 2 - 28, 0, w / 2 + tw / 2 + 28, 80), 24, fill=GREEN)
    d.text((w / 2 - tw / 2 - tb[0], 40 - th / 2 - tb[1]), tag, font=f, fill="white")
    return shadowed(card)


def logo_card(t, dur, p):
    s, a = pop_scale(t, dur)
    return finish(_logo_card(p["logo"], p["tag"]).copy(), s, a, W / 2, p.get("y", 330))


# ---------- stamp (red X / green check) ----------
@lru_cache(None)
def _stamp(text, kind):
    col = RED if kind == "x" else GREEN
    f = font("ariblk.ttf", 84)
    tw, th, tb = text_size(f, text)
    icon = 110
    w, h = icon + 40 + tw + 90, 170
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=(12, 12, 16, 230), outline=col, width=9)
    ix, iy = 40, (h - icon) // 2
    d.ellipse((ix, iy, ix + icon, iy + icon), fill=col)
    if kind == "x":
        k = 30
        d.line((ix + k, iy + k, ix + icon - k, iy + icon - k), fill="white", width=14)
        d.line((ix + icon - k, iy + k, ix + k, iy + icon - k), fill="white", width=14)
    else:
        d.line((ix + 28, iy + 58, ix + 48, iy + 80, ix + 84, iy + 34), fill="white", width=14, joint="curve")
    d.text((ix + icon + 36 - tb[0], h / 2 - th / 2 - tb[1]), text, font=f, fill="white")
    if kind == "x":  # strike through the text
        d.line((ix + icon + 26, h / 2 + 4, w - 50, h / 2 - 4), fill=col, width=12)
    return shadowed(img.rotate(p_rot(kind), resample=Image.BICUBIC, expand=True))


def p_rot(kind):
    return 4 if kind == "x" else -3


def stamp(t, dur, p):
    img = _stamp(p["text"], p["kind"])
    if t < 0.16:  # slam in from big
        s, a = 1.7 - 0.7 * ease_out(t / 0.16), clamp(t / 0.06)
    elif t > dur - 0.18:
        q = (t - (dur - 0.18)) / 0.18
        s, a = 1 - 0.1 * q, 1 - q
    else:
        s, a = 1.0, 1.0
    return finish(img.copy(), s, a, W / 2, p.get("y", 330))


# ---------- comment box typing ----------
def comment(t, dur, p):
    full = p["text"]
    tt = t - p.get("type_at", 1.0)
    n = 0 if tt < 0 else min(len(full), int(tt / p.get("per_char", 0.08)) + 1)
    typed = full[:n]
    w, h = 900, 150
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 75, fill=(255, 255, 255, 250))
    d.ellipse((24, 24, 126, 126), fill=(255, 160, 0))
    d.ellipse((36, 36, 114, 114), fill=(255, 255, 255))
    d.ellipse((50, 50, 100, 100), fill=(230, 60, 120))
    f = font("segoeuib.ttf", 56)
    x0 = 160
    if typed:
        d.text((x0, 38), typed, font=f, fill=(15, 15, 15))
        x0 += d.textlength(typed, font=f) + 6
    else:
        d.text((x0, 38), p.get("placeholder", "Izoh qoldiring..."), font=f, fill=(150, 150, 150))
    if int(t * 2.2) % 2 == 0 or 0 < n < len(full):
        d.rectangle((x0, 42, x0 + 5, 108), fill=(0, 120, 255))
    # send button lights up when typing is done
    done = n == len(full)
    d.ellipse((w - 130, 25, w - 30, 125), fill=(0, 120, 255) if done else (200, 200, 200))
    d.polygon([(w - 100, 52), (w - 50, 75), (w - 100, 98), (w - 92, 75)], fill="white")
    s, a = pop_scale(t, dur)
    if done and tt - len(full) * p.get("per_char", 0.08) < 0.15:
        s *= 1.04
    return finish(shadowed(img), s, a, W / 2, p.get("y", 330))


# ---------- captions ----------
@lru_cache(None)
def _caption(words, colors, size=76):
    f = font("ariblk.ttf", size)
    space = f.getlength(" ")
    widths = [f.getlength(w) for w in words]
    lines, cur, cw = [], [], 0
    for wd, wi in zip(words, widths):  # wrap at 940 px
        if cur and cw + space + wi > 940:
            lines.append(cur)
            cur, cw = [], 0
        cw += (space if cur else 0) + wi
        cur.append((wd, wi))
    lines.append(cur)
    lh = int(size * 1.18)
    img = Image.new("RGBA", (W, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = 0
    for li, line in enumerate(lines):
        lw = sum(wi for _, wi in line) + space * (len(line) - 1)
        x = (W - lw) / 2
        for wd, wi in line:
            d.text((x, 20 + li * lh), wd, font=f, fill=colors[k], stroke_width=10, stroke_fill=(0, 0, 0))
            x += wi + space
            k += 1
    return img


def caption_img(words, highlight, size=76, accent='#ffd400', pill=False, font_name='ariblk.ttf'):
    if size == 76 and accent == '#ffd400' and not pill and font_name == 'ariblk.ttf':
        colors = tuple(YELLOW if w.strip(".,!?").upper() in highlight else (255, 255, 255, 255) for w in words)
        return _caption(tuple(words), colors)
    f = font(font_name, size)
    while f.getlength(' '.join(words)) > 920:
        size -= 2
        f = font(font_name, size)
    width = int(f.getlength(' '.join(words))) + 56
    img = Image.new('RGBA', (width, size + 56))
    d = ImageDraw.Draw(img)
    if pill:
        d.rounded_rectangle((0, 0, width-1, img.height-1), 24, fill=(10, 16, 24, 225))
    x = 28
    for word in words:
        color = accent if word.strip('.,!?').upper() in highlight else 'white'
        d.text((x, 16), word, font=f, fill=color, stroke_width=0 if pill else 4, stroke_fill='black')
        x += f.getlength(word + ' ')
    return img

def text_hook(t, dur, p):
    lines = p['text'].split('\n')
    f = font('segoeuib.ttf', p.get('size', 82))
    img = Image.new('RGBA', (980, 140 * len(lines) + 60))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 979, img.height-1), 36, fill=(8, 16, 24, 210))
    for i, line in enumerate(lines):
        d.text((490, 30 + i*140), line, anchor='mt', font=f, fill=p.get('color', '#65e9ff'))
    s, a = pop_scale(t, dur)
    return finish(img, s, a, W/2, p.get('y', 480))


GRAPHICS = {"title": title, "hud": hud, "logo_card": logo_card, "stamp": stamp, "comment": comment, 'text_hook': text_hook}
