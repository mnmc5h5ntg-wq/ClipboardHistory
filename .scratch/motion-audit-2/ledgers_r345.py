#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R345 七本台账（第 344 轮 / Round 342 · 产品 3 文件，动效主线）。"""
import io, os
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding=u"utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding=u"utf-8").write(t)
def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

U = u"""## 第 344 轮（R345 · 2026-10-25 · U-1194…U-1199）：亮档选中那颗的身份换到**边界**这条轴 —— 发丝边第一次有会红的判据（U-1194…U-1199 · 产品 3 文件，动效主线）

- **U-1194：次序判据落地，对象第一次被钉住。** `SEG_EDGE light 页面=255 填充=220 最深=198 填充−最深=22 最深是页面=false`
  / `SEG_EDGE dark 页面=30 填充=107 最深=30 填充−最深=77 最深是页面=true`。
  两条断言：亮档"最深那一格不是页面" **且** "填充 − 最深 ≥ 8"；暗档不断言像素（只印）。
  R343/R344 三次读错对象（页面 / 轨道 / 边）之后，判决词从"最暗那一行"改成"最深那一格是不是页面"。
- **U-1195：A 案落地 —— 亮档 1pt × alpha 0.12 的发丝边。** `SegmentEdge.width/alpha` 摊成两格（暗档都是 nil），
  画在 `slidingPill` 的 ZStack 里、盖在抬量之前；macOS 12 的分段控件本来就画这一根。
  亮档身份从此住在边界上，亮度通道留给悬停（399 的另一半）。
- **U-1196：9 张亮档帧 CHANGED，同一笔更新基线。** `segmented-filter-idle/hover-200x60-light` +
  `content-with-notice(-two)` + 5 张 `sidebar-*-light`（这条控件在每一张亮档侧栏帧里）。
- **U-1197：两把刀都抓到。** `M1001`（alpha 0.12→0.0，边还在、看不见）⇒ 像素判据红；
  `M1002`（暗档也画边）⇒ 令牌真值表红。`CAUGHT=2/2, RESTORE_CLEAN=yes`；预检 `tables=128 bad=0`。
- **U-1198：全量卷与换装。** `Executed 1024 tests, with 47 skipped and 0 failures`；构建 0 告警；
  `INSTALL_RESULT=ok`（sha 逐字节、条数 379→379）。
- **U-1199：变异运行器的汇总正则只认复数。** 第一跑 `BASELINE … RED` 是假红：单格只有一个用例时
  XCTest 打的是 `Executed 1 test, with 0 failures`（单数），而正则写的是 `tests` ⇒ "没解析到"被当成红。
  改成 `Executed (\\d+) tests?, with (\\d+) failures?` 之后才跑通。**其余表同一行**（422 登记）。

"""

ITER = u"""## Round 342 · R345（第 344 轮 · 2026-10-25）：亮档选中那颗换轴 —— 身份搬到边界，亮度让给悬停（产品 3 文件）

亮档空闲 230 与选中 220 只差 1.099，悬停要 ≥1.20 就得比选中还深（R334 的 1.136）。这一轮不再在亮度里找地方：
给选中那颗补一根 1pt × 0.12 的发丝边，判据用**次序**钉对象（`页面 255 > 填充 220 > 最深 198`）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 看了亮档 idle 帧：选中段外沿一圈细边，与右侧未选段分得开；暗档帧没有这圈。 |
| 判据有效性 | 14/15 | 次序判据两条断言（最深≠页面、填充−最深≥8）；两把刀各钉一条轴，`CAUGHT=2/2`。 |
| 假绿防御 | 13/15 | 变异表第一跑的"基线红"被查出是正则只认复数（U-1199），没有当成真红去改产品。 |
| 产品面推进 | 13/15 | 产品 3 文件：亮档选中态第一次有边界身份，399 的亮度通道腾出来了（悬停那一半仍未做）。 |
| 台账一致性 | 13/15 | U-1194…U-1199 六条、D-342、421 结案追记 + 422 新开；计数器现读抄。 |
| 交付诚实性 | 15/15 | 暗档像素不假称证过（只印）；9 张帧的变化逐张列名；换装 sha 对过。 |
| 可复核性 | 14/15 | 次序判据、两把刀、预检表数、全量卷结论都在账上，可照着重跑。 |

均分 ≈ 13.7/15（96/105）。
"""

BL = u"""
421 结案追记（R345）：三层查完之后，次序判据落地并绿了 —— `SEG_EDGE light 页面=255 填充=220 最深=198 填充−最深=22`、
暗档 `最深是页面=true`。A 案（1pt × 0.12 发丝边）随之上了产品，两把刀都抓到。这一单到此可以关：
"边画没画"不再靠猜，靠的是"最深那一格是不是页面"。**留下一条给别处的教训**：存在性判据的对象要用次序钉，
不要用"最暗/最亮"这类单个极值（R343 的 0、R344 的三种读数都是这么错的）。

**422. 变异运行器的汇总正则只认复数 `Executed N tests`：单格只有一个用例时会被判成"没解析到 ⇒ 红"**（R345 现读）
    R345 的 `mutate_r345.py` 第一次跑就 `PRECHECK_FAILED`：两个单格都只跑 1 个用例，XCTest 打的是
    `Executed 1 test, with 0 failures`（**单数**），而 `run_cell` 的正则是 `Executed (\\d+) tests, with (\\d+) failures`
    ⇒ 没有匹配 ⇒ 被当成"编译没过 / 根本没跑"⇒ 假红。改成 `tests?` / `failures?` 之后 `CAUGHT=2/2`。
    这一行是从 R339 那张表抄来的，所以**别的表也在用同一个正则**；本轮只改了自己这张，
    其它的要逐张看（谁的单格只跑 1 个用例，谁就有这个假红风险）。改法：把正则放宽到单复数，
    并在 `run_cell` 里把"没匹配到汇总行"与"匹配到但失败数 > 0"分成两种打印，别让它们共用一个 `?`。
"""

DEC = u"""
### D-342（345）换一条轴之前，要先给出旧轴上"无解"的算术证明，再给新轴的读数

R345 现读：亮档空闲 230 / 选中 220 ⇒ 悬停要 ≥1.20 必须 ≤207（比选中还深，R334 的 1.136）；
要留在两档之间又只能给到 224（1.038，R343 的可见性门当场红）。**这两条要求互相排斥**，
所以"再调一调 alpha"永远没有解 —— 这一轮的修法是把身份从亮度搬到**边界**（1pt × 0.12，实测 22 级）。
**How to apply**：遇到"这条轴上怎么调都不对"的位点，先写出两条地板的联立不等式并说明无解（存进台账），
再动轴；动轴时新轴必须自带一条**会红的量**（这里是 `填充 − 最深 ≥ 8` 与"最深不是页面"），
旧轴的判据不许被删掉，也不许被偷偷放宽。
"""

CH = u"""### 亮档选中那颗的身份搬到边界：1pt 发丝边 + 次序判据，两把刀都抓到（R345 / U-1194…U-1199 · 产品 3 文件，动效主线）
"""

STATE = u"""## R345 状态（2026-10-25 · 本地 · 第 344 轮 / Round 342）：亮档选中那颗换轴 —— 身份搬到边界（产品 3 文件，动效主线）

最后更新：2026-10-25（本地 · R345 / 第 344 轮 / Round 342）：给亮档选中那颗补 1pt × 0.12 的发丝边，
判据用次序钉对象（`页面 255 > 填充 220 > 最深 198`），两把刀各钉一条轴（产品 3 文件 · 动效主线）

本轮做了什么：
① ⓪ CI 配对：`RUN=40184155498 ↔ e981378` 首读 in_progress、`RUN=… ↔ 985c045` 未取（只登记不轮询，R140）。
② 产品：`SegmentEdge.width/alpha`（暗档 nil）+ `slidingPill` 画边；`VisualMaterial.selectedSegmentEdge = 0.12`。
③ 判据：`SEG_EDGE` 改读**次序**——"最深那一格是不是页面" + "填充 − 最深 ≥ 8"；暗档只印不断言。
④ 重捕 182 帧、9 张亮档帧 CHANGED，同一笔更新基线。
⑤ 刀：`mutate_r345.py` M1001（α→0）/ M1002（暗档也画）⇒ `CAUGHT=2/2, RESTORE_CLEAN=yes`；预检 `tables=128 bad=0`。
⑥ 全量卷 `Executed 1024 tests, with 47 skipped and 0 failures`；换装 `INSTALL_RESULT=ok`。

验证读数（现读）：`SEG_EDGE light 页面=255 填充=220 最深=198 填充−最深=22 最深是页面=false`；
`SEG_EDGE dark 最深是页面=true`；`MUTATE r345 CAUGHT=2/2, RESTORE_CLEAN=yes`；
`NEEDLE_PRECHECK tables=128 covered=110 arms=369 bad=0`；`ARM_TOTAL files=222 arms=865 dupes=0`；
脚本电池 `Ran 645（skipped=4）OK`；产品面连续零改动 **6** 轮（这是**本轮之前**的连读：本轮动了 3 个产品文件，下一轮会归零；`python3 scripts/product_streak.py --streak-for 344` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① 悬停那一半（399 的 B 案）没做 —— 亮度通道刚腾出来，下一轮先量再动；
② 暗档像素级的"没有边"不断言（要两臂帧才证得了，D-341）；③ 真机腿没跑（这轮看的是离屏帧）。

下一轮（R346）的靶：⓪ 读本笔与 985c045 的 CI 配对 → ① 399 的亮档悬停（亮度通道现在归它，先量"提亮后 hover 与 selected 落在哪两档"）
→ ② 422（其余变异表的汇总正则逐个看）→ ③ 413 → ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

"""

def main():
    s = rd(u"AGENT_UI_AUDIT.md"); a = u"## 第 343 轮（R344 · 2026-10-25 · U-1188…U-1193）"
    i = s.find(a); assert i > 0; wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])
    s = rd(u"AGENT_VISUAL_ITERATION.md"); wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)
    s = rd(u"AGENT_BACKLOG.md"); wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BL)
    s = rd(u"AGENT_DECISIONS.md"); wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)
    s = rd(u"CHANGELOG.md"); s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CH); wr(u"CHANGELOG.md", s)
    s = rd(u"AGENT_STATE.md"); h = u"## R344 状态（2026-10-25 · 本地 · 第 343 轮 / Round 341）"
    assert s.count(h) == 1; wr(u"AGENT_STATE.md", s.replace(h, STATE + h, 1))
    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1193（R344 现读抬到最新一节）", u"U-31 … U-1199（R345 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-341**", u"| 决定台账 | D-069 … **D-342**")
    r = once(r, u"U 定义行最大 **U-1193**、决定最大 **D-341**、BACKLOG 最大 **421**",
             u"U 定义行最大 **U-1199**、决定最大 **D-342**、BACKLOG 最大 **422**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R344 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R345 节 ② 为准")
    r = once(r, u"产品面连续零改动轮数 = **5**（现读", u"产品面连续零改动轮数 = **6**（现读")
    r = r.rstrip(u"\n") + u"""
- **R345 续（动效主线）**：亮档选中那份身份从亮度搬到**边界** —— 1pt × 0.12 发丝边，
  次序判据 `页面 255 > 填充 220 > 最深 198`；两把刀 `CAUGHT=2/2`；9 张亮档帧同笔更新基线。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R345_LEDGERS_OK")

if __name__ == u"__main__":
    main()
