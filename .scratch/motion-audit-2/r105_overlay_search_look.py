# R105 §4 视觉审查腿：浮层搜索那一行**只有字、没有框**这件事，量出来到底长什么样。
# 读数全部从已提交基线的那两张帧（fixture 假数据，不含用户剪贴板内容）解析，不手抄。
import io, os
from PIL import Image

SHOTS = "/tmp/r104_shots"
SCALE = 2
DEST = "/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/r105_overlay_search_look.log"
lines = []
def say(s):
    lines.append(s)

for tag, name in (("light", "quickpick-list-420x300-light.png"),
                  ("dark",  "quickpick-list-420x300-dark.png")):
    im = Image.open(os.path.join(SHOTS, name)).convert("RGBA")
    w, h = im.size
    px = im.load()
    def luma(x, y):
        r, g, b, a = px[x, y]
        return 0.299 * r + 0.587 * g + 0.114 * b
    def alpha(x, y):
        return px[x, y][3]
    say("QUICKPICK_LOOK %s 帧=%dx%dpx" % (tag, w, h))
    colx = int(4 * SCALE)
    solid = [y for y in range(h) if alpha(colx, y) >= 250]
    if not solid:
        say("  左缘 x=%dpx 整列 alpha<250 ⇒ 面板边不在这里，改用 x=40px" % colx)
        colx = int(40 * SCALE)
        solid = [y for y in range(h) if alpha(colx, y) >= 250]
    y0 = solid[0]
    lum = sorted(luma(colx, y) for y in range(y0, min(h, y0 + 40)))
    page = lum[len(lum) // 2]
    say("  参考列 x=%dpx 实心区 y=%d..%d 面板底档(中位)=%.0f" % (colx, y0, solid[-1], page))
    for y in range(y0, min(h, y0 + 100)):
        ink = first = last = None
        cnt = 0
        maxd = 0.0
        for x in range(w):
            if alpha(x, y) >= 250:
                d = abs(luma(x, y) - page)
                if d > 6:
                    cnt += 1
                    if first is None:
                        first = x
                    last = x
                    maxd = max(maxd, d)
        say("  y=%3dpx ink=%3d x=%s..%s maxd=%.0f" % (y, cnt, first, last, maxd))
    # 横向剖面：在搜索文字那一行（后面人读表挑）上，看左右有没有任何东西（框/分隔线）
    say("  --- 顶部 0..100px 每列的 ink 计数（找有没有可见的框/底线）---")
io.open(DEST, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("WROTE=%s lines=%d" % (DEST, len(lines)))
