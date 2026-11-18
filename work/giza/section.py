"""南北向正投影剖面：切在 x=xc，往西看 depth 格；空腔顯示後牆（加暗），切面後方的空腔以淡色虛影表示。"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import render as R

FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'


def section(W, V, xc, depth, z0, z1, y0, y1, s=5, bg=(236, 240, 244)):
    col, kind, opaque = R.classify(W.names)
    a = W.a[xc - depth:xc + 1, y0:y1, z0:z1][::-1]          # [d, y, z]，d=0 為切面
    v = V[xc - depth:xc + 1, y0:y1, z0:z1][::-1] > 0
    D, Hh, Zn = a.shape
    img = np.zeros((Hh, Zn, 3), np.float32); img[:] = bg
    cut = a[0]
    solid0 = cut != 0
    img[solid0] = col[cut[solid0]] * 0.92
    # 切面上的空腔：往後找第一個實心
    hole = (~solid0) & v[0]
    nz = a != 0
    first = np.argmax(nz, axis=0)                             # 第一個非空氣的深度
    has = nz.any(axis=0)
    back = np.take_along_axis(a, first[None], 0)[0]
    dark = np.clip(0.62 - first * 0.025, 0.25, 0.62)[..., None]
    m = hole & has
    img[m] = (col[back] * dark)[m]
    img[hole & ~has] = (25, 22, 20)
    # 後方空腔虛影（通氣孔、密封空腔）
    ghost = solid0 & v[1:].any(axis=0)
    img[ghost] = img[ghost] * 0.45 + np.array([60, 50, 44]) * 0.55
    # 層線
    for y in range(Hh):
        if y % 2 == 0:
            row = solid0[y]
            img[y, row] *= 0.97
    im = Image.fromarray(np.clip(img[::-1], 0, 255).astype(np.uint8)).resize((Zn * s, Hh * s), Image.NEAREST)
    return im


def annotate(im, labels, z0, y1, s, font_size=26):
    """labels: [(文字, z, y, dx, dy)]，在 (z,y) 方塊處畫指示線到偏移 (dx,dy) 像素。"""
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, font_size)
    for text, z, y, dx, dy in labels:
        px = (z - z0) * s + s // 2; py = (y1 - 1 - y) * s + s // 2
        tx, ty = px + dx, py + dy
        dr.line([(px, py), (tx, ty)], fill=(150, 30, 30), width=3)
        dr.ellipse([px - 5, py - 5, px + 5, py + 5], outline=(150, 30, 30), width=3)
        bb = dr.textbbox((tx, ty), text, font=f)
        w = bb[2] - bb[0]
        ox = tx + 6 if dx >= 0 else tx - w - 6
        oy = ty - (bb[3] - bb[1]) // 2 - 4
        dr.rectangle([ox - 4, oy - 2, ox + w + 4, oy + (bb[3] - bb[1]) + 10], fill=(255, 255, 255), outline=(150, 30, 30))
        dr.text((ox, oy), text, fill=(40, 30, 30), font=f)
    return im


def annotate2(im, labels, z0, y1, s, pad=470, font_size=26, bg=(236, 240, 244)):
    """左右兩欄標註。labels: [(文字, z, y, 'L'|'R', 文字中心 y 像素)]"""
    W0, H0 = im.size
    out = Image.new('RGB', (W0 + 2 * pad, H0 + 40), bg)
    out.paste(im, (pad, 20))
    dr = ImageDraw.Draw(out)
    f = ImageFont.truetype(FONT, font_size)
    for text, z, y, side, ty in labels:
        px = pad + (z - z0) * s + s // 2; py = 20 + (y1 - 1 - y) * s + s // 2
        bb = dr.textbbox((0, 0), text, font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
        if side == 'L':
            bx0 = 16; bx1 = bx0 + w + 16; ax = bx1
        else:
            bx1 = W0 + 2 * pad - 16; bx0 = bx1 - w - 16; ax = bx0
        by0 = ty - h // 2 - 8; by1 = ty + h // 2 + 10
        dr.line([(px, py), (ax, ty)], fill=(150, 30, 30), width=3)
        dr.ellipse([px - 6, py - 6, px + 6, py + 6], outline=(150, 30, 30), width=3)
        dr.rectangle([bx0, by0, bx1, by1], fill=(255, 255, 255), outline=(150, 30, 30), width=2)
        dr.text((bx0 + 8, by0 + 4), text, fill=(40, 30, 30), font=f)
    return out
