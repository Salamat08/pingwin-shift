"""Готовит ассеты игры из исходных картинок Higgsfield.
Ожидает в SRC: lobby.png hall.png ... panel.png, npcA.png npcB.png npcC.png mgr2.png icons_src.png
Пишет в OUT: bg/*.webp, atlas.png, atlas.json, icons.png, me_portrait.webp
"""
import json, statistics, sys, os
from PIL import Image, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(f'{OUT}/bg', exist_ok=True)
BG = ['lobby','hall','bowling','machine','kitchen','balcony','vip1','vip2','vip3','wc','back','panel']
for n in BG:
    Image.open(f'{SRC}/{n}.png').convert('RGB').resize((960, 540), Image.LANCZOS).save(f'{OUT}/bg/{n}.webp', quality=80, method=6)

def bgcol(im):
    W, H = im.size; px = im.load()
    bs = [px[x, 2] for x in range(0, W, 7)] + [px[x, H - 3] for x in range(0, W, 7)]
    return tuple(statistics.median([p[i] for p in bs]) for i in range(3))

def mask(im, thr=42):
    W, H = im.size; px = im.load(); b = bgcol(im)
    m = Image.new('L', (W, H), 0); mp = m.load()
    for y in range(H):
        for x in range(W):
            r, g, bb = px[x, y]
            mp[x, y] = 255 if abs(r - b[0]) + abs(g - b[1]) + abs(bb - b[2]) > thr else 0
    return m.filter(ImageFilter.MedianFilter(3))

def figs(path, n):
    im = Image.open(path).convert('RGB'); W, H = im.size
    m = mask(im); mp = m.load()
    cols = [sum(1 for y in range(H) if mp[x, y]) for x in range(W)]
    runs = []; inr = False
    for x, cnt in enumerate(cols):
        if cnt > 3 and not inr: s = x; inr = True
        elif cnt <= 3 and inr:
            if x - s > 20: runs.append((s, x))
            inr = False
    if inr: runs.append((s, W))
    while len(runs) > n:
        g, i = min((runs[i + 1][0] - runs[i][1], i) for i in range(len(runs) - 1))
        runs[i] = (runs[i][0], runs[i + 1][1]); del runs[i + 1]
    rgba = im.convert('RGBA'); rgba.putalpha(m)
    out = []
    for a, b in runs:
        sub = rgba.crop((a, 0, b, H)); out.append(sub.crop(sub.getbbox()))
    return out

res = {}
for path, names in [('npcA.png', ['host','serik','timur','dana','sanzhar']), ('npcB.png', ['erlan','asel','kamila','viktor','dauren']), ('npcC.png', ['galina','bau','roza','book','coll'])]:
    for nm, f in zip(names, figs(f'{SRC}/{path}', 5)): res[nm] = (f, 150 / 600)
mg = figs(f'{SRC}/mgr2.png', 4)
res['me'] = (mg[0], 160 / 677); res['me_walk'] = (mg[1], 160 / 677)
p = mg[3]; w, h = p.size
p.crop((14, 14, w - 14, w - 14)).resize((192, 192), Image.LANCZOS).convert('RGB').save(f'{OUT}/me_portrait.webp', quality=82)

names = list(res); ims = []; meta = {}; x = 0
for n in names:
    im, s = res[n]
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    im.putalpha(im.getchannel('A').point(lambda v: 255 if v > 110 else 0))
    meta[n] = [x, 0, im.width, im.height]; ims.append(im); x += im.width + 2
H = max(i.height for i in ims)
at = Image.new('RGBA', (x, H), (0, 0, 0, 0))
for n, im in zip(names, ims):
    meta[n][1] = H - im.height; at.paste(im, (meta[n][0], meta[n][1]))
at.save(f'{OUT}/atlas.png', optimize=True)

# иконки: сетка 5×2
ic = Image.open(f'{SRC}/icons_src.png').convert('RGB'); W, Hh = ic.size
m = mask(ic, 50); rgba = ic.convert('RGBA'); rgba.putalpha(m)
cells = []; cw, ch = W / 5, Hh / 2
for r in range(2):
    for cI in range(5):
        cell = rgba.crop((int(cI * cw), int(r * ch), int((cI + 1) * cw), int((r + 1) * ch)))
        bb = cell.getbbox() or (0, 0, cell.width, cell.height)
        cell = cell.crop(bb); side = max(cell.size)
        sq = Image.new('RGBA', (side, side), (0, 0, 0, 0)); sq.paste(cell, ((side - cell.width) // 2, (side - cell.height) // 2))
        cells.append(sq.resize((96, 96), Image.LANCZOS))
sheet = Image.new('RGBA', (96 * 10, 96), (0, 0, 0, 0))
for i, cimg in enumerate(cells): sheet.paste(cimg, (i * 96, 0))
sheet.save(f'{OUT}/icons.png', optimize=True)
json.dump({'sprites': meta, 'icons': [[i * 96, 0, 96, 96] for i in range(10)]}, open(f'{OUT}/atlas.json', 'w'))
print('ok', at.size, {k: v[3] for k, v in meta.items()})
