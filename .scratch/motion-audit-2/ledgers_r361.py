#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R361 七本台账（第 360 轮 / Round 358 · 产品 0 文件，判据账）。"""
import io, os, re, subprocess
ROOT = u"/Users/wangziyi/Codex_Project0"
rd = lambda n: io.open(os.path.join(ROOT, n), encoding="utf-8").read()
wr = lambda n, t: io.open(os.path.join(ROOT, n), u"w", encoding="utf-8").write(t)
LOG = lambda n: io.open(os.path.join(u"/tmp", n), encoding="utf-8", errors="replace").read()

def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)

STREAK = int(re.search(u"streak=(\\d+)", subprocess.run(
    [u"python3", u"scripts/product_streak.py", u"--streak-for", u"360"],
    cwd=ROOT, stdout=subprocess.PIPE).stdout.decode(u"utf-8")).group(1))
battery = LOG(u"r361_py.log")
BAT_N = re.search(u"Ran (\\d+) tests", battery).group(1)
assert re.search(r"^OK \(skipped=4\)$", battery, re.M), u"电池不是 OK"

U = u"""## 第 360 轮（R361 · 2026-10-25 · U-1264…U-1266）：367 第一步 —— 四张新表自己声明针，已声明 2→6（U-1264…U-1266 · 产品 0 文件，判据账）

- **U-1264：四张新表声明 NEEDLES（r355/r356/r358/r360）。** 367 的出口只有一条：表自己把针标出来，
  尺不再猜。四张表各加一行 `NEEDLES = {刀号: [NEEDLE]}`（值与 ARMS 同一个模块常量）；
  `scripts/hidden_arms.py` 现读 `表=221 可判=804 rot=33 抽不出=6 已声明表=6 已声明死针=0 处置=ok`。
- **U-1265：声明**不等于**修好 —— rot 一个数都没动。** 四张表从"启发式判活"改成"自己声明"之后，
  `rot=33 / 抽不出=6` 与改前逐字相同：那四把针本来就是活的。收益是**已判从下界变成确数**
  （`已声明死针`可加总、可点名），不是让下界箱变小。棘轮 `DECLARED_TABLES_CEILING` 2→6，
  注释写明这条读数；守卫 `test_hidden_arms` 用等式钉住（加/删 NEEDLES 都要同步改上界）。
- **U-1266：下一步该改哪些表，有读数了。** 工具现读可按 `rot=33 / 抽不出=6` 两箱点名到表
  （`HIDDEN_OPAQUE` / `HIDDEN_ROT` 明细），下一批应按这两箱点，而不是按"最新的表"点 ——
  本轮四张表是示范（同一份常量、同一把刀），它们本来就不在 rot 箱里。
  **仍欠**：33 + 6 个臂所在表的声明；以及"声明值必须等于 ARMS 真用的那一根"这条**只在测试里有对账**，
  工具本身不做（它判针在不在盘上，不判它是不是这一臂的针）。

"""

ITER = u"""## Round 358 · R361（第 360 轮 · 2026-10-25）：367 第一步 —— 四张新表声明 NEEDLES（产品 0 文件）

r355/r356/r358/r360 各加 `NEEDLES = {刀号: [NEEDLE]}`；`hidden_arms` 现读 已声明表=6、死针=0、rot=33、抽不出=6；
棘轮 2→6，test_hidden_arms 8/8。**rot 没动** —— 声明把"已判"从下界变确数，不替人修死针。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮是静态名册工具，无画面；读数来自 `hidden_arms` 的逐表明细。 |
| 判据有效性 | 14/15 | 等式棘轮 + 8 格测试；加/删声明两个方向都会红。 |
| 假绿防御 | 14/15 | 明确写出"rot 没动"；不把"已声明"当"已修好"；抽查箱点名到表。 |
| 产品面推进 | 8/15 | 产品 0 文件；推进在"隐藏臂的判活从启发式变声明式"。 |
| 台账一致性 | 13/15 | U-1264…U-1266、D-360、367 追记；计数器现读。 |
| 交付诚实性 | 15/15 | 下一批该改哪些表由两箱点名，留给下一轮；未声称覆盖 75 张。 |
| 可复核性 | 15/15 | 一条 `hidden_arms.py` + 一条测试；四张表各一行声明。 |

均分 = 89/105 ≈ 12.7/15（85）。

"""

BL = u"""
367 追记（R361）：第一步 —— r355/r356/r358/r360 各声明 `NEEDLES = {刀号: [NEEDLE]}`，
    `hidden_arms` 现读 `表=221 可判=804 rot=33 抽不出=6 已声明表=6 已声明死针=0 处置=ok`；
    棘轮 `DECLARED_TABLES_CEILING` 2→6，`test_hidden_arms` 8/8。
    **重要读数**：rot / 抽不出一个都没动（33/6）—— 那四把针本来就是活的；声明把"已判"从下界变成确数，
    不替人修死针。下一步按 `HIDDEN_ROT` / `HIDDEN_OPAQUE` 两箱点名到表去改，不再按"最新的表"改。

"""

DEC = u"""
### D-360（361）"表自己声明针"把下界变成确数，不等于把 rot 修小

367 的出口是让表写出 `NEEDLES = {刀号: [针]}`，尺不再猜；R361 给四张表加了声明，
`已声明表` 2→6、`已声明死针=0`，而 `rot=33 / 抽不出=6` 与改前**逐字相同** —— 因为那四把针本来就活着。
**Why**：声明改变的是**判定的性质**（从"至少一根候选命中"的下界，变成逐根可加总的确数），
不是死的数量；把"已声明"读成"已修好"，下一轮就会拿着 33 去问"为什么没降"。
**How to apply**：每加一张声明表，同时改 `DECLARED_TABLES_CEILING` 并**重抄** rot / 抽不出两箱；
两箱没动就照实写"没动"。下一批要改的表由 `HIDDEN_ROT` / `HIDDEN_OPAQUE` 的点名清单给，按箱走。

"""

CH = u"""### 367 第一步：四张新表自己声明针（已声明 2→6），rot/抽不出 33/6 原样 —— 声明把下界变确数（R361 / U-1264…U-1266 · 产品 0 文件，判据账）
"""

STATE = u"""## R361 状态（2026-10-25 · 本地 · 第 360 轮 / Round 358）：367 第一步 —— 四张新表声明 NEEDLES（产品 0 文件，判据账）

最后更新：2026-10-25（本地 · R361 / 第 360 轮 / Round 358）：r355/r356/r358/r360 各加 `NEEDLES = {刀号: [NEEDLE]}`；
`hidden_arms` 现读 已声明表=6 / 死针=0 / rot=33 / 抽不出=6，棘轮 2→6；**rot 没动**（那四把针本来就活着，声明把下界变确数）；
`test_hidden_arms` 8/8、电池 `Ran @BAT@（skipped=4）OK`（产品 0 文件 · 判据账）

本轮做了什么：
① ⓪ CI：`queue` 现读 R357–R360 四跑仍在队里（queued/in_progress），只登记不轮询。
② 367：四张新表声明 NEEDLES（值与 ARMS 同一常量）；`hidden_arms.py` 处置=ok。
③ 棘轮：`DECLARED_TABLES_CEILING` 2→6，注释写明"rot/抽不出 一个数都没动"的原因。
④ 测试：`test_hidden_arms` 8/8；本机不动 Swift/产品 ⇒ 全量/胶片/基线沿用。

验证读数（现读）：`HIDDEN_ARMS 表=221 可判=804 rot=33 抽不出=6 已声明表=6 已声明死针=0 上界 … 处置=ok`；
脚本电池 `Ran @BAT@（skipped=4）OK`；产品面连续零改动 **@STREAK@** 轮（`python3 scripts/product_streak.py --streak-for 360` 现读）。

NOT-RUN（分开写）：① 下一批 33 + 6 个臂的声明（按两箱点名，未做）；② 工具不判"声明值是不是这一臂真用的那根"
（只有 `test_hidden_arms` 的合成对账）；③ runner 的 R357–R360 四跑（下一轮读）；④ 真机腿没跑。

下一轮（R362）的靶：⓪ 读四跑（`MOTION_REDUCE_SOURCES` 三源 + 376 的出口文本）；
① 367 下一批：按 `HIDDEN_ROT` / `HIDDEN_OPAQUE` 的点名表挑 2–3 张声明；② 426（刀的 diff 判法）。

"""
UP_UI = u"""## 第 359 轮（R360 · 2026-10-25 · U-1261…U-1263）：376 —— 三臂不可分先分叉：reduce-on 是产品行为，不是「这台机器看不见」（U-1261…U-1263 · 产品 0 文件，判据账）"""
UP = u"""## R360 状态（2026-10-25 · 本地 · 第 359 轮 / Round 357）：376 出口先分叉 —— reduce-on 记产品行为（产品 0 文件，判据账）"""

def fill(text):
    pairs = {u"@BAT@": BAT_N, u"@STREAK@": str(STREAK)}
    for k, v in pairs.items():
        text = text.replace(k, v)
    leftover = re.findall(u"@[A-Z0-9]{2,}@", text)
    assert not leftover, u"还有占位符：%s" % u",".join(sorted(set(leftover)))
    return text

def main():
    ui = rd(u"AGENT_UI_AUDIT.md")
    ui = once(ui, UP_UI, fill(U) + UP_UI)
    wr(u"AGENT_UI_AUDIT.md", ui)

    it = rd(u"AGENT_VISUAL_ITERATION.md")
    if not it.endswith(u"\n"):
        it += u"\n"
    wr(u"AGENT_VISUAL_ITERATION.md", it + fill(ITER))

    bl = rd(u"AGENT_BACKLOG.md")
    if not bl.endswith(u"\n"):
        bl += u"\n"
    wr(u"AGENT_BACKLOG.md", bl + fill(BL))

    de = rd(u"AGENT_DECISIONS.md")
    if not de.endswith(u"\n"):
        de += u"\n"
    wr(u"AGENT_DECISIONS.md", de + fill(DEC))

    ch = rd(u"CHANGELOG.md")
    ch = once(ch, u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + fill(CH) + u"\n")
    wr(u"CHANGELOG.md", ch)

    st = rd(u"AGENT_STATE.md")
    before = st.count(u"\n## R")
    st = once(st, UP, fill(STATE) + UP)
    wr(u"AGENT_STATE.md", st)
    st2 = rd(u"AGENT_STATE.md")
    assert UP in st2 and st2.count(u"\n## R") == before + 1, u"STATE 轮换后上一轮标记丢了或层数不对"

    fr = rd(u"AGENT_FINAL_REPORT.md")
    fr = once(fr, u"| 决定台账 | D-069 … **D-359**", u"| 决定台账 | D-069 … **D-360**")
    fr = once(fr, u"| 视觉台账 | U-31 … U-1263（R360 现读抬到最新一节）",
              u"| 视觉台账 | U-31 … U-1266（R361 现读抬到最新一节）")
    fr = once(fr, u"U 定义行最大 **U-1263**、决定最大 **D-359**",
              u"U 定义行最大 **U-1266**、决定最大 **D-360**")
    fr = once(fr, u"产品面连续零改动轮数 = **5**", u"产品面连续零改动轮数 = **6**")
    fr = once(fr, u"`AGENT_STATE.md` 的 R360 节 ② 为准", u"`AGENT_STATE.md` 的 R361 节 ② 为准")
    bullet = u"""- **R361 续（判据账）**：367 第一步 —— r355/r356/r358/r360 声明 NEEDLES，`已声明表` 2→6、死针=0；
  `rot=33 / 抽不出=6` **原样没动**（那四把针本来就活着，声明把下界变确数，D-360）；`test_hidden_arms` 8/8。
"""
    if not fr.endswith(u"\n"):
        fr += u"\n"
    fr += fill(bullet)
    wr(u"AGENT_FINAL_REPORT.md", fr)
    print(u"R361_LEDGERS_OK U=1266 D=360 battery=@BAT@".replace(u"@BAT@", BAT_N))

if __name__ == u"__main__":
    main()
