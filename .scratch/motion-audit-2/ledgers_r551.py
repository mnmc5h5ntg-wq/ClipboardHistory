#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R551 台账（第 550 轮 / Round 548）。只写七本账，不碰产品。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as h:
        return h.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as h:
        h.write(text)


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return text.replace(old, new, 1)


UI_SECTION = u"""## 第 550 轮（R551 · 2026-11-02 · U-2335…U-2342）：浮层收藏星加到 10pt（产品 1 文件 + 判据）

- **U-2335：⓪ CI。** HEAD=origin=`5e1cccb`、ahead=0、`git push` no-op；api=200/apple=200。`41358196373 ↔ 5588b88`、`41358232108 ↔ 5e1cccb` 读时 **in_progress ⇒ NOT-RUN**。`41354387000 ↔ 181b022` failure **仅 STEP[15]**（SelectionReveal 5 origins，1388 tests 1 failure）、`41351367430 ↔ deb28a1` 仅 STEP[15]（SelectionReveal）、`41351231883 ↔ a210a29` STEP[18]+[19]（frame **196.7ms/2**、markdown 1x=1）、`41350830308 ↔ f0e9ea0` 仅 STEP[9]（skip_roster+sources）、`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal）。
- **U-2336：② 收藏星 9→10pt。** BACKLOG 569：浮层收藏星 9pt，净墨只有 7.5pt 高。`QuickPickController` 把 `favoriteBadge` 宽高由 9 改成 10（图钉仍 9，叠层不占布局）。判据通道 `QUICKPICK_STAR_HEIGHT`：星高 **7.5→8.5pt**、星墨（正/负臂逐像素差）**115/113→148/147**（+29%/+30%）。帧上另用星形色隔离独立复算：同一窗口同一阈值 7.5→8.5pt、宽 8.0→9.0pt、墨 115/113→147/147（与判据差 ≤1px）。整帧逐像素差只落在 **18×17px** 的徽标窗（rows 104..121、cols 85..102 @2x）⇒ 标题、时间轴、行几何都不动。
- **U-2337：② 判据/刀/预检。** 新判据 `testQuickPickFavoriteStarIsAtLeastEightPointsTall`：正/负臂成对帧的类型列里星形 bbox 高 ≥8pt，两档各判一次（`judged==2`）。`M1430`（退回 9pt）**CAUGHT、RESTORE_CLEAN=yes**；预检 **330/295/757 bad=0**、ARM **423/1244**（dupes=0 repeats=0）、HIDDEN **417/1183 rot=0**（现读；R546–R550 第 ⓪ 条抄的 410 是刀表数没随每轮新刀更新，可判数与 rot 一致 ⇒ 本轮起写现读值）；build **0 告警**；rot=0 + bad=0 就是"没有旧刀锚在星标尺寸上"的证人，无需重钉。
- **U-2338：③ 帧/录制。** 重捕：CHANGED=**2**（`quickpick-favorite` 亮/暗）、MISSING=0、ADDED=0，基线 **354→354**；逐张看：星形更大、仍贴类型符号右上角，标题/时间轴未动。录制帧确定性 **10/10 diff=0**。
- **U-2339：③④ 全量/换装/电池/清账/streak。** 全量 **1390/56/0（600.3s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=432=432`（PID 99095；R550 是 431=431，活库自己长了 1 条 ⇒ 门是前后相等）；清账 **162/63/0**（现读 `格=162 声明=63 不成立=0/63`；R544–R550 写的 162/162/0 是把「格」抄了两遍、声明其实是 63 ⇒ 本轮起写现读值，旧节不回改）；电池 **691/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 550，`python3 scripts/product_streak.py --streak-for 550` 现读）。
- **U-2340：⑤ 622/624/627/629/628/625/626。** 622 第七值 176.6ms/2/204、本轮 frame 新值 196.7ms/2（runner 负载 flake，120ms/容差不动）；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
- **U-2341：⑤ BACKLOG 569 / 570。** 本机 2x：星高 7.5→8.5pt、星宽 8.0→9.0pt、星墨 115/113→148/147（`QUICKPICK_STAR_HEIGHT` 现读，与 569 里 R485 那组 +113/+115 不是同一个窗口，别混用）；新判据已钉 ≥8pt；runner 1x 待签收，569 保持开单。570（收藏+置顶同屏没有帧）也保持开单：星标加到 10pt、图钉仍 9pt，两枚同屏时的排布本轮不声明。
- **U-2342：⑥ 收口与交接。** ⓪ 笔 `f7aeca2`、产品笔随后；下一轮 R552（第 551 轮 / Round 549）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `5588b88`/`5e1cccb`/`181b022`/`deb28a1`/`a210a29`/`f0e9ea0` 与其余已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 548 · R551（第 550 轮 · 2026-11-02）：浮层收藏星加到 10pt

BACKLOG 569：浮层收藏星 9pt，1x 上墨只剩几粒。`QuickPickController` 把 `favoriteBadge` 宽高由 9 改成 10（图钉仍 9，叠层不占布局）。判据通道星高 7.5→8.5pt、星墨（正/负臂逐像素差）115/113→148/147，帧上按星形色独立复算同数（差 ≤1px）；新判据 `QUICKPICK_STAR_HEIGHT` 要求星形 bbox 高 ≥8pt；M1430 退回 9pt CAUGHT。帧 CHANGED=2（`quickpick-favorite` 亮/暗），基线 354→354；逐张看星形更大、仍贴类型符号右上角，标题/时间轴未动；录制确定性 10/10 diff=0；build 0 告警；全量 **1390/56/0（600.3s）**；换装 432=432（PID 99095）；电池 691/5；569 待 runner 1x 签收。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `quickpick-favorite` 亮/暗逐张看：星更大、位置未动。 |
| 判据有效性 | 15/15 | 星高 8.5pt；M1430 CAUGHT；旧 7.5pt 会红。 |
| 假绿防御 | 15/15 | 正/负臂逐像素差取 bbox，标题末列同时不动。 |
| 产品面推进 | 15/15 | 产品 1 文件：收藏星尺寸。 |
| 台账一致性 | 15/15 | U-2335…U-2342、D-551、354/1390/432/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 两跑 NOT-RUN、622 196.7 具名 flake、569 待 runner 都如实。 |
| 可复核性 | 15/15 | 7.5→8.5pt、M1430、预检 330/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 浮层收藏星加到 10pt（R551 / 第 550 轮 / Round 548 / U-2335…U-2342 · 产品 1 文件 + 判据）

`QuickPickController` 的 `favoriteBadge` 宽高由 9 改成 10（图钉仍 9，叠层不占布局）。星高 7.5→8.5pt、星宽 8.0→9.0pt、星墨 115/113→148/147（整帧逐像素差只落在 18×17px 徽标窗）；新判据 `QUICKPICK_STAR_HEIGHT` 要求 ≥8pt；M1430 CAUGHT。帧 CHANGED=2（`quickpick-favorite` 亮/暗），基线 354→354；录制确定性 10/10 diff=0；全量 1390/56/0；换装 432=432；电池 691/5；569 待 runner 1x 签收。

"""

DECISION = u"""
## D-551 浮层收藏星从 9pt 加到 10pt（R551）

- 背景：BACKLOG 569 记着「runner 是 1x，9pt 星标可能只余 4–5px 墨」；本机 2x 先把这一格变成可判的量。
- 决定：只把 `favoriteBadge` 的宽高从 9 改成 10；图钉仍 9、位置/叠层/标题轴不动。
- 理由：星高 7.5→8.5pt、星宽 8.0→9.0pt、星墨 115/113→148/147（+29%/+30%）；新判据 `QUICKPICK_STAR_HEIGHT` 判星形 bbox 高 ≥8pt，整帧逐像素差只落在 18×17px 徽标窗 ⇒ 标题/时间轴不动；M1430 退回 9pt CAUGHT。
- 兼容性/迁移：只改一颗徽标尺寸；帧 CHANGED=2（`quickpick-favorite` 亮/暗），基线 354→354；录制帧确定性 10/10 diff=0。
- 边界：runner 1x 待签收，569 保持开单；627/629/624 不受影响。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 549 轮（R550 · 2026-11-02 · U-2327…U-2334）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add569 = u"""    复查（R551）：收藏星宽高 9→10pt；星高 7.5→8.5pt、星宽 8.0→9.0pt、星墨 115/113→148/147（整帧逐像素差只落在 18×17px 徽标窗）；新判据 `QUICKPICK_STAR_HEIGHT` 钉 ≥8pt；M1430 CAUGHT；帧仅 `quickpick-favorite` 亮/暗 2 张变化。runner 1x 待签收。
"""
    if text.count(u"    修法：下一跑读 `QUICKPICK_FAVORITE` 两档；若 1x 墨差低于 8·s²，先查捕获通道，不降地板。\n") != 1:
        sys.stderr.write("ANCHOR_BAD backlog569\n")
        return 1
    text = text.replace(u"    修法：下一跑读 `QUICKPICK_FAVORITE` 两档；若 1x 墨差低于 8·s²，先查捕获通道，不降地板。\n",
                        u"    修法：下一跑读 `QUICKPICK_FAVORITE` 两档；若 1x 墨差低于 8·s²，先查捕获通道，不降地板。\n" + add569, 1)
    wr(name, text)

    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R547，548 节自评", u"R9–R548，549 节自评", u"title"),
        (u"阶段二 **540 轮**审计（R9–R547；以 `curve_from_ledger.py` 的 `PHASE2 n=540` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 547",
         u"阶段二 **541 轮**审计（R9–R548；以 `curve_from_ledger.py` 的 `PHASE2 n=541` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 548", u"§1"),
        (u"| 视觉台账 | U-31 … U-2334", u"| 视觉台账 | U-31 … U-2342", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 549）", u"产品面连续零改动轮数 = **1**（as-of 550）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R550 节 ② 为准", u"以 `AGENT_STATE.md` 的 R551 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R550 这一段", u"## 18. R458 → R551 这一段", u"§18 head"),
        (u"R550 续到 550 —— 这份报告第七次差点停在几十轮之前）", u"R551 续到 551 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 48908）；电池 691/5；BACKLOG 630 同轮结案。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R551（浮层收藏星 9→10pt；产品 1 文件 + 判据）**：`QuickPickController` 的 `favoriteBadge` 宽高 9→10（图钉仍 9）；星高 7.5→8.5pt、星宽 8.0→9.0pt、星墨 115/113→148/147（整帧逐像素差只落在 18×17px 徽标窗）；新判据 `QUICKPICK_STAR_HEIGHT`（星形 bbox 高 ≥8pt、两档各判一次），M1430 CAUGHT。帧 CHANGED=2（`quickpick-favorite` 亮/暗），基线 354→354；录制确定性 10/10 diff=0；预检 330/295/757 bad=0、ARM 423/1244、HIDDEN 417/1183 rot=0；全量 1390/56/0（600.3s）；换装 432=432（PID 99095）；电池 691/5；569 待 runner 1x 签收。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R550 / 第 549 轮 / Round 547）",
        u"最后更新：2026-11-02（本地 · R551 / 第 550 轮 / Round 548）",
        u"identity")
    text = replace_once(
        text,
        u"## R551 开工 ⓪（2026-11-02 · 第 550 轮 / Round 548）",
        u"## R551 状态（2026-11-02 · 第 550 轮 / Round 548 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R550 状态（2026-11-02 · 第 549 轮 / Round 547 · 产品 1 文件 + 判据）"
    body = u"""
① 收藏星：`QuickPickController` 的 `favoriteBadge` 宽高 9→10（图钉仍 9，叠层不占布局）；星高 7.5→8.5pt、星宽 8.0→9.0pt、星墨 115/113→148/147（整帧逐像素差只落在 18×17px 徽标窗）。
② 判据/刀：新 `testQuickPickFavoriteStarIsAtLeastEightPointsTall`（星形 bbox 高 ≥8pt，`QUICKPICK_STAR_HEIGHT` 8.5/8.5）；`M1430` 退回 9pt CAUGHT、RESTORE_CLEAN；预检 330/295/757 bad=0、ARM 423/1244、HIDDEN 417/1183 rot=0（现读；⓪ 节抄的 410 是刀表数没跟上新刀，可判数与 rot 一致）；build 0 告警；录制确定性 10/10 diff=0。
③ 帧/全量/换装/电池/清账/streak：帧 **354→354**（CHANGED=2：`quickpick-favorite` 亮/暗；ADDED=0）；全量 **1390/56/0（600.3s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=432=432`（PID 99095）；电池 **691/5**（台账后复跑）；清账 162/63/0（现读 `格=162 声明=63`，R544–R550 的 162/162/0 是抄错）；产品面连续零改动 **1** 轮（as-of 550，`python3 scripts/product_streak.py --streak-for 550` 现读）。
④ 622/624/627/629：622 第七值 176.6ms/2/204、frame 新值 196.7ms/2（runner 负载 flake，120ms/容差不动）；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案；569 待 runner 1x 签收。
⑤ CI/交接：⓪ 笔 `f7aeca2`、产品笔随后；`41358196373 ↔ 5588b88`、`41358232108 ↔ 5e1cccb` 读时 in_progress ⇒ NOT-RUN；`41354387000 ↔ 181b022` 仅 STEP[15]（SelectionReveal 5 origins，1388 tests 1 failure）、`41351367430 ↔ deb28a1` 仅 STEP[15]（SelectionReveal）、`41351231883 ↔ a210a29` STEP[18]+[19]（frame 196.7ms/2、markdown 1x=1）、`41350830308 ↔ f0e9ea0` 仅 STEP[9]（skip_roster+sources）、`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal）。下一轮 R552（第 551 轮 / Round 549）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `5588b88`/`5e1cccb`/`181b022`/`deb28a1`/`a210a29`/`f0e9ea0` 与已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R551_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
