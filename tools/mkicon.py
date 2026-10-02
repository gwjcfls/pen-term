#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkicon.py —— 生成 PenTerm 终端应用图标（150x150 RGBA，笔上 app_icon.png 的规格）

用法: python mkicon.py <输出.png> [尺寸=150]
设计：深色圆角窗 + 标题栏三点 + 绿色提示符 '>' + 光标块 + 几行灰色“输出”
"""
import sys
from PIL import Image, ImageDraw, ImageFont

BG = (11, 15, 20, 255)          # #0b0f14 终端底色
BAR = (22, 27, 34, 255)         # #161b22 标题栏
BORDER = (48, 54, 61, 255)      # #30363d
FG = (201, 209, 217, 255)       # #c9d1d9
DIM = (110, 118, 129, 255)      # #6e7681
GREEN = (63, 185, 80, 255)      # #3fb950
DOTS = [(248, 81, 73), (210, 153, 34), (63, 185, 80)]

SS = 4                          # 超采样倍数


def rounded(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "app_icon.png"
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    S = size * SS
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    pad = int(S * 0.055)
    r = int(S * 0.22)
    # 窗体
    rounded(d, [pad, pad, S - pad, S - pad], r, BG, BORDER, max(1, int(S * 0.008)))
    # 标题栏
    barh = int(S * 0.26)          # 必须 >= 圆角半径，否则标题栏形状不成立
    # 标题栏：把"窗口圆角形状"单独画一层，只取上半段贴上去 → 上圆下方，底边平直
    bar_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(bar_layer).rounded_rectangle([pad, pad, S - pad, S - pad], radius=r, fill=BAR)
    im.paste(bar_layer.crop((0, 0, S, pad + barh)), (0, 0))
    d.rectangle([pad, pad + barh, S - pad, pad + barh + max(1, int(S * 0.006))], fill=BORDER)
    # 三个圆点
    dot_r = int(S * 0.026)
    cy = pad + barh // 2
    for i, col in enumerate(DOTS):
        cx = pad + int(S * 0.075) + i * int(S * 0.085)
        d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=col + (255,))

    # 提示符 '>' + 光标 + 输出行
    try:
        f = ImageFont.truetype("consola.ttf", int(S * 0.17))
        fb = ImageFont.truetype("consolab.ttf", int(S * 0.17))
    except Exception:
        try:
            f = fb = ImageFont.truetype("cour.ttf", int(S * 0.17))
        except Exception:
            f = fb = ImageFont.load_default()

    x0 = pad + int(S * 0.10)
    y0 = pad + barh + int(S * 0.09)
    d.text((x0, y0), ">", font=fb, fill=GREEN)
    # 光标块
    cw, ch = int(S * 0.10), int(S * 0.145)
    cx = x0 + int(S * 0.115)
    d.rectangle([cx, y0 + int(S * 0.022), cx + cw, y0 + int(S * 0.022) + ch], fill=FG)
    # 三行输出
    for i, w in enumerate((0.62, 0.46, 0.30)):
        yy = y0 + int(S * 0.24) + i * int(S * 0.14)
        d.rounded_rectangle([x0, yy, x0 + int(S * w), yy + int(S * 0.055)],
                            radius=int(S * 0.028), fill=DIM)

    im = im.resize((size, size), Image.LANCZOS)
    im.save(out)
    print("生成 %s (%dx%d)" % (out, size, size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
