"""HD-ассеты: фоны 1920x1080 (assets/bg_hd), атлас спрайтов x2 (SPH=320) и иконки 192px.
Запуск: python3 tools/build_hd.py /home/claude/src assets
"""
import json, statistics, sys, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
SRC, OUT = sys.argv[1], sys.argv[2]
F = 2  # множитель к старому атласу (SPH 160 -> 320)
t = open(os.path.join(os.path.dirname(__file__), 'build_assets.py')).read()
exec(t[t.index('def bgcol'):t.index('res = {}')])

# --- фоны
BG = ['lobby','hall','bowling','machine','kitchen','balcony','vip1','vip2','vip3','wc','back','panel',
      'c_tablet','c_pin','c_cctv','c_locker','c_dress','c_cake','c_score','c_gen','c_sofa']
os.makedirs(f'{OUT}/bg_hd', exist_ok=True)
for n in BG:
    im = Image.open(f'{SRC}/{n}.png').convert('RGB').resize((1920, 1080), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))
    im.save(f'{OUT}/bg_hd/{n}.webp', quality=82, method=6)

def fin(im, s):
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    im.putalpha(im.getchannel('A').point(lambda v: 255 if v > 110 else 0)); return im

res = {}
for path, names in [('npcA.png', ['host','serik','timur','dana','sanzhar']), ('npcB.png', ['erlan','asel','kamila','viktor','dauren']), ('npcC.png', ['galina','bau','roza','book','coll'])]:
    for nm, f in zip(names, figs(f'{SRC}/{path}', 5)): res[nm] = fin(f, F * 150 / 600)
mg = figs(f'{SRC}/mgr2.png', 4)
res['me'] = fin(mg[0], F * 160 / 677); res['me_walk'] = fin(mg[1], F * 160 / 677)
# новые NPC — по высоте соседей
d = figs(f'{SRC}/npcD.png', 2)
res['aliya'] = fin(d[0], res['coll'].height / d[0].height); res['aidos'] = fin(d[1], res['erlan'].height / d[1].height)

# --- кадры ходьбы (пользовательские) и позы
im0 = Image.open(f'{SRC}/up/walk5b.png').convert('RGBA'); A = np.array(im0.convert('RGB')).astype(int); H, W = A.shape[:2]
m = np.array(im0.getchannel('A')) > 128
l0, n0 = ndimage.label(m); sz0 = ndimage.sum(m, l0, range(1, n0 + 1)); m = np.isin(l0, [i + 1 for i, v in enumerate(sz0) if v > m.size * 0.002])
cols = m.sum(0); runs = []; inr = False
for x, cn in enumerate(cols):
    if cn > 3 and not inr: s0 = x; inr = True
    elif cn <= 3 and inr:
        if x - s0 > 40: runs.append((s0, x))
        inr = False
if inr: runs.append((s0, W))
frames = []
for a, b in runs:
    sub = m[:, a:b]; l2, n2 = ndimage.label(sub); sizes = ndimage.sum(sub, l2, range(1, n2 + 1)); k = int(np.argmax(sizes)) + 1
    keep = l2 == k
    for i, sz in enumerate(sizes, 1):
        if i != k and sz > sizes[k - 1] * 0.003: keep |= l2 == i
    ys, xs = np.where(keep); top, bot = ys.min(), ys.max()
    bx = np.where(keep[top:top + int((bot - top) * 0.35)])[1].mean()
    rgba = np.zeros((H, b - a, 4), np.uint8); rgba[..., :3] = A[:, a:b]; rgba[..., 3] = keep * 255
    frames.append((Image.fromarray(rgba), bx, top, bot, xs.min(), xs.max()))
L = max(f[1] - f[4] for f in frames); R = max(f[5] - f[1] for f in frames); Ht = max(f[3] - f[2] for f in frames)
out = [f[0].crop((int(f[1] - L) - 1, int(f[3] - Ht) - 1, int(f[1] + R) + 2, int(f[3]) + 1)) for f in frames]
sw = F * 160 / statistics.median([f[3] - f[2] for f in frames])
for i, f in enumerate(out): res[f'mw{i}'] = fin(f, sw)
act = figs(f'{SRC}/actsheet.png', 6)
for i, f in enumerate(act): res[f'ma{i}'] = fin(f, F * 160 / act[0].height)

# --- упаковка полками в ширину 2048
MAXW = 2048; x = y = rowh = 0; meta = {}
order = sorted(res, key=lambda k: -res[k].height)
for k in order:
    im = res[k]
    if x + im.width > MAXW: x = 0; y += rowh + 2; rowh = 0
    meta[k] = [x, y, im.width, im.height]; x += im.width + 2; rowh = max(rowh, im.height)
at = Image.new('RGBA', (MAXW, y + rowh), (0, 0, 0, 0))
for k in order: at.paste(res[k], (meta[k][0], meta[k][1]))
at.save(f'{OUT}/atlas_hd.png', optimize=True)

# --- иконки 192
def cells(path, ncol, nrow, thr=50):
    ic = Image.open(path).convert('RGB'); W2, H2 = ic.size; mm = mask(ic, thr); rg = ic.convert('RGBA'); rg.putalpha(mm); outc = []
    for r in range(nrow):
        for c_ in range(ncol):
            cell = rg.crop((int(c_ * W2 / ncol), int(r * H2 / nrow), int((c_ + 1) * W2 / ncol), int((r + 1) * H2 / nrow)))
            cell = cell.crop(cell.getbbox() or (0, 0, cell.width, cell.height)); side = max(cell.size)
            sq = Image.new('RGBA', (side, side), (0, 0, 0, 0)); sq.paste(cell, ((side - cell.width) // 2, (side - cell.height) // 2))
            outc.append(sq.resize((192, 192), Image.LANCZOS))
    return outc
ics = cells(f'{SRC}/icons_src.png', 5, 2) + cells(f'{SRC}/icons2.png', 2, 1)
sheet = Image.new('RGBA', (192 * len(ics), 192), (0, 0, 0, 0))
for i, c_ in enumerate(ics): sheet.paste(c_, (i * 192, 0))
sheet.save(f'{OUT}/icons_hd.png', optimize=True)
json.dump({'sph': 320, 'sprites': meta, 'icons': [[i * 192, 0, 192, 192] for i in range(len(ics))]}, open(f'{OUT}/atlas_hd.json', 'w'))
print('atlas', at.size, 'icons', len(ics))
