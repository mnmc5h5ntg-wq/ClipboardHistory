from PIL import Image

SHOTS = u"/tmp/r100_shots/"

def left_ink(im, d, w, y0, y1, fill, gate, x0=0):
    for x in range(x0, w):
        for y in range(y0, y1):
            if abs(d[x, y] - fill) >= gate:
                return x
    return None

for name, fill in [(u"quickpick-list-420x300-dark.png", 30),
                   (u"quickpick-typed-420x300-dark.png", 30),
                   (u"quickpick-list-420x300-light.png", 250)]:
    im = Image.open(SHOTS + name).convert(u"L")
    w, h = im.size
    d = im.load()
    # find the inked horizontal bands (rows of the panel)
    rows = []
    y = 0
    while y < h:
        hit = any(abs(d[x, y] - fill) >= 40 for x in range(0, w, 3))
        if hit:
            y1 = y
            while y1 + 1 < h and any(abs(d[x, y1 + 1] - fill) >= 40 for x in range(0, w, 3)):
                y1 += 1
            rows.append((y, y1))
            y = y1 + 1
        else:
            y += 1
    print(u"### %s size=%s  墨带=%d" % (name, im.size, len(rows)))
    for (a, b) in rows[:6]:
        lx = left_ink(im, d, w, a, b + 1, fill, 40)
        print(u"   band %4.1f..%-5.1fpt  最左墨 x=%s pt" % (a / 2.0, (b + 1) / 2.0,
              (u"%.1f" % (lx / 2.0)) if lx is not None else u"none"))
