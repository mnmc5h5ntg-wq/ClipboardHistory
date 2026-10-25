#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R342 七本台账（第 341 轮 / Round 339 · 产品 0 文件，验证账）。"""
import io
import os

ROOT = u"/Users/wangziyi/Codex_Project0"


def rd(n):
    return io.open(os.path.join(ROOT, n), encoding=u"utf-8").read()


def wr(n, t):
    io.open(os.path.join(ROOT, n), u"w", encoding=u"utf-8").write(t)


def once(t, a, b):
    assert t.count(a) == 1, u"锚点命中 %d：%.60s" % (t.count(a), a)
    return t.replace(a, b, 1)


U = u"""## 第 341 轮（R342 · 2026-10-25 · U-1178…U-1182）：暗档那颗抬量第一次有同一条件的改前/改后 —— 换装两次，只变一个 token（U-1178…U-1182 · 产品 0 文件，验证账）

- **U-1178：真机 A/B 落地，只变 `SegmentKnob.liftAlpha` 一个变量。** 同一台机、同一外观（dark）、同一把尺
  （`real_screen_filter_pill.py`）、同一个空库窗口，两臂是**两次连续运行**：
  改前（`liftAlpha` 返回 nil）`页底=52.0 轨道档=80.0 药丸档=70.0 差=−10.0` ⇒ `pill_darker`；
  改后（`liftAlpha`=0.20）`页底=52.0 轨道档=80.0 药丸档=107.0 差=+27.0` ⇒ `pill_lighter`。
  选中那颗从轨道**下面 10 级**挪到**上面 27 级** —— 395 欠的那半（同一条件的 before）到此有读数。
- **U-1179：两次换装都过了逐字节校验。** 两跑各打 `INSTALL_RESULT=ok`（`INSTALL_SHA_MATCH=1`、
  条数 379→379 不变），旧包各自留在 `~/Documents/Codex_Project0_backups/before-r342-{before,after}`；
  两次之间源码用 `git checkout --` 回到干净，`git status` 现读空 ⇒ 装回去的就是已提交的那份。
- **U-1180：两臂的帧落在了同一条 `/tmp/r330_real/pill.png` 上，第二臂把第一臂覆盖了。**
  所以看图腿只有 after 那一张（左段明显亮于右段），before 只剩数字。教训：**每臂拍完立刻改名/换目录**，
  否则「两臂都拍过」这句话在盘上没有对象（与「同一路径被后一次覆盖」同族：结果通道会吃掉前一次的证据）。
- **U-1181：与 R341 的 `+25.0` 同向，差 2 级是两次运行的正常抖动**（轨道档 82 对 80）。
  两句合起来才成立：R341 的是**换形状后同一帧**的判法，本轮的是**换代码后同一条件**的因果。
- **U-1182：亮档这一对不适用。** `liftAlpha(light)` 本来就是 nil ⇒ 两臂同码，亮档的 399 仍然**只印不判**；
  本轮的 A/B 只签暗档这一半，不许被读成「亮档也验过了」。

"""

ITER = u"""## Round 339 · R342（第 341 轮 · 2026-10-25）：换装两次、只变一个 token —— 真机上那颗选中的药丸从轨道下 10 级挪到上 27 级（产品 0 文件）

这一轮不写产品代码，写的是**因果**：把 `liftAlpha` 临时关掉装一次、量一次，再装回真的、再量一次。
两臂落在同一把尺、同一外观、同一个空库窗口上：`差=−10.0`（`pill_darker`）→ `差=+27.0`（`pill_lighter`）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | after 那一帧看过（左段明显亮于右段、轨道与页底分明）；before 的帧被第二臂覆盖，只剩数字 —— 不冒充看过。 |
| 判据有效性 | 14/15 | A/B 只变一个 token，两臂同尺同外观；两次换装都有 sha 校验与回滚目录；改前改后各一个判词。 |
| 假绿防御 | 14/15 | 「装回了真的」由 `git status` 空 + `INSTALL_SHA_MATCH=1` 两处对账；亮档明写「不适用」而不是顺手算过。 |
| 产品面推进 | 8/15 | 产品 0 文件（变体已还原）；但这次量到的是一条**产品事实**（抬量值 +37 级），399 的亮档若要修，必须另配一支 token。 |
| 台账一致性 | 13/15 | U-1178…U-1182 五条定义、D-339、395/399 两条追记；计数器现读抄。 |
| 交付诚实性 | 15/15 | 帧被覆盖这件事写进 U-1180；变体只在 /tmp 与本机装过一次，仓库里没有半件产品改动。 |
| 可复核性 | 14/15 | 两次换装的标签（`r342-before` / `r342-after`）、回滚路径、两行判词都在账上；读的人可以照着重跑。 |

均分 ≈ 12.9/15（90/105）。
"""

BACKLOG = u"""
395 追记（R342 同条件 A/B）：暗档那一半**签掉了**。同一台机、同一外观、同一把尺、只变 `SegmentKnob.liftAlpha`：
    改前 `页底=52.0 轨道=80.0 药丸=70.0 差=−10.0`（`pill_darker`）→ 改后 `差=+27.0`（`pill_lighter`）。
    与 R341 的 `+25.0` 同向（轨道 82 对 80 的两次抖动）。亮档两臂同码（`liftAlpha(light)=nil`）⇒ 这一对不适用。
    这一单里剩下的：392 那三格（347/305 按下档、373 快速选取色、265 菜单栏悬停）——它们要的是**人的眼**
    或另一种取证通道，与解锁无关。

399 追记（R342 现读）：本轮 A/B 给了一条新事实 —— **抬量这条路在暗档有效（−10 → +27），在亮档没有对象**
    （`liftAlpha(light)` 一直是 nil）。所以 B 案（悬停改提亮）若要落到亮档，必须给它**单独一支 token**，
    并且先量「提亮之后的 hover 与 selected 落在哪两档」；否则会顺手把暗档 A/B 刚签下的那条链改坏。
"""

DEC = u"""
### D-339（342）A/B 要「只变一个变量 + 重装两次」，而不是比两轮各自的读数

R342 现读：同一天里 R341 的 `+25.0` 与本轮的 `+27.0` 是两次运行；把它们相减只能说明「同向」，
说明不了「这个 token 管这件事」。真正签下因果的是**同一条件、只动一个 token、重新装两次**：
改前 `−10.0` / 改后 `+27.0`，其余（外观、尺、窗口、空库）逐字相同。
**How to apply**：以后凡是要判「某个产品参数是不是这个读数的成因」，照这一轮的形状做：
① 变体只改那一处，装一次、量一次；② `git checkout` 还原，装第二次、量第二次；③ 两次都要 sha 校验；
④ 每臂的帧**立刻改名**（U-1180 是同一条的现场反例：第二臂把第一臂覆盖了）。
"""

CHANGELOG = u"""### 真机 A/B：暗档那颗选中的药丸，抬量之后从轨道下 10 级挪到上 27 级（R342 / U-1178…U-1182 · 产品 0 文件，验证账）
"""

STATE = u"""## R342 状态（2026-10-25 · 本地 · 第 341 轮 / Round 339）：换装两次、只变一个 token（产品 0 文件，验证账）

最后更新：2026-10-25（本地 · R342 / 第 341 轮 / Round 339）：把 395 欠的那半「同一条件的 before」在真机上量出来 ——
`liftAlpha` 关掉装一次 `差=−10.0`，装回真的 `差=+27.0`（产品 0 文件 · 验证账）

本轮做了什么：
① ⓪ CI 配对：`RUN=40182636083 ↔ db05698`（首读 in_progress ⇒ 只登记不轮询）。
② 变体 `SegmentKnob.liftAlpha → nil`，`install_local.sh --label r342-before`；暗档量一次。
③ `git checkout --` 还原，`--label r342-after` 再装一次；暗档再量一次。
④ 两臂同尺同外观同空库窗口：改前 `页底=52 轨道=80 药丸=70 差=−10.0`；改后 `页底=52 轨道=80 药丸=107 差=+27.0`。
⑤ 记下帧被覆盖的教训（U-1180）：两臂落在同一条 /tmp 路径上，看图腿只剩 after。

验证读数（现读）：两次换装 `INSTALL_RESULT=ok`（sha 逐字节、条数 379→379）；源码两次之间 `git status` 空；
脚本电池 `Ran 645（skipped=4）OK`；帧 182（本轮无产品改动，未重捕）；清账表 `格子=162 已清账=162`；
产品面连续零改动 **3** 轮（`python3 scripts/product_streak.py --streak-for 341` 现读，口径差一挂 412）。

NOT-RUN（分开写）：① **亮档 A/B 不适用**（`liftAlpha(light)=nil`，两臂同码）；② 本轮无变异刀（产品 0 文件，
而且变体已还原）；③ 看图腿只有 after 一张（before 的帧被第二臂覆盖，U-1180）。

下一轮（R343）的靶：⓪ 读 `db05698` / 本笔的 CI 配对 → ① BACKLOG 399（亮档悬停：先量「提亮后 hover 与 selected
落在哪两档」，再决定要不要单独一支 token）→ ② 392 那三格（347/305 按下档、373 快速选取色、265 菜单栏悬停，
需要人的眼）→ ③ 413（backing 名册 + 两档材质帧）→ ④ 动效主线 397 / 390 / 389 / 384 / 387① / 376 / 367。

"""


def main():
    s = rd(u"AGENT_UI_AUDIT.md")
    a = u"## 第 340 轮（R341 · 2026-10-25 · U-1172…U-1177）"
    i = s.find(a)
    assert i > 0
    wr(u"AGENT_UI_AUDIT.md", s[:i] + U + s[i:])

    s = rd(u"AGENT_VISUAL_ITERATION.md")
    wr(u"AGENT_VISUAL_ITERATION.md", s.rstrip(u"\n") + u"\n\n" + ITER)

    s = rd(u"AGENT_BACKLOG.md")
    wr(u"AGENT_BACKLOG.md", s.rstrip(u"\n") + u"\n" + BACKLOG)

    s = rd(u"AGENT_DECISIONS.md")
    wr(u"AGENT_DECISIONS.md", s.rstrip(u"\n") + u"\n" + DEC)

    s = rd(u"CHANGELOG.md")
    s = once(s, u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CHANGELOG)
    wr(u"CHANGELOG.md", s)

    s = rd(u"AGENT_STATE.md")
    h = u"## R341 状态（2026-10-25 · 本地 · 第 340 轮 / Round 338）"
    assert s.count(h) == 1
    wr(u"AGENT_STATE.md", s.replace(h, STATE + h, 1))

    r = rd(u"AGENT_FINAL_REPORT.md")
    r = once(r, u"U-31 … U-1177（R341 现读抬到最新一节）", u"U-31 … U-1182（R342 现读抬到最新一节）")
    r = once(r, u"| 决定台账 | D-069 … **D-338**", u"| 决定台账 | D-069 … **D-339**")
    r = once(r, u"U 定义行最大 **U-1177**、决定最大 **D-338**、BACKLOG 最大 **420**",
             u"U 定义行最大 **U-1182**、决定最大 **D-339**、BACKLOG 最大 **420**")
    r = once(r, u"完整名单以 `AGENT_STATE.md` 的 R341 节 ② 为准", u"完整名单以 `AGENT_STATE.md` 的 R342 节 ② 为准")
    r = once(r, u"产品面连续零改动轮数 = **2**", u"产品面连续零改动轮数 = **3**")
    r = r.rstrip(u"\n") + u"""
- **R342 续（验证账）**：真机 A/B 只变 `SegmentKnob.liftAlpha`，换装两次（两次都 `INSTALL_RESULT=ok`）：
  改前 `页底=52 轨道=80 药丸=70 差=−10.0`、改后 `差=+27.0`；亮档两臂同码 ⇒ 那一对不适用。
""" + u"\n"
    wr(u"AGENT_FINAL_REPORT.md", r)
    print(u"R342_LEDGERS_OK")


if __name__ == u"__main__":
    main()
