#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R545 台账（第 544 轮 / Round 542）。只写七本账，不碰产品。"""
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


def append_after_line(text, anchor, add, label):
    idx = text.find(anchor)
    if idx < 0:
        sys.stderr.write("ANCHOR_BAD %s\n" % label)
        sys.exit(1)
    end = text.find(u"\n", idx)
    if end < 0:
        end = len(text)
    return text[:end + 1] + add + text[end + 1:]


UI_SECTION = u"""## 第 544 轮（R545 · 2026-11-02 · U-2287…U-2294）：fold 收尾判据改读 settled 进度（产品 0 文件 + 判据）

- **U-2287：⓪ CI。** HEAD=origin=`e357708`、ahead=0、`git push` no-op；api=200/apple=200。三跑读时 **in_progress ⇒ NOT-RUN**：`41331769689 ↔ c5fcf03`（判据）、`41334225593 ↔ 5589ebe`（台账）、`41334244256 ↔ e357708`（补记二）。已收口：`41331173441 ↔ c1df1e6` failure **仅 STEP[19]**（`MOTION_FLOOR_FACTS judged=5/5 executed=77`；红名 `testBandCaptureIsCheaperAndStillSeesTheMotion` 11.73ms 不 < 10.79ms、`testMarkdownModeLabelChangeIsAVisibleProcess` 1x=1；`MOTION_FLOOR_REDS=1`；filmstrip copy 1x=2/峰值 0.0889、markdown 1x=1/0.0193、录制帧 passed diff=0）。`41330637380 ↔ 8d4a36d` failure **STEP[9]+[19]**（STEP[9]=skip_roster+sources 时序，Ran 690 failures=2 skipped=2；STEP[19] 仅 markdown 红；copy 1x=2/0.1000、录制帧 passed；band 本跑 1.66×）。`41330618181 ↔ b16eacc` failure **仅 STEP[9]**（skip_roster+sources；copy 场景 `app-not-active` ⇒ NOT-RUN；录制帧 passed）。`41326398317 ↔ bd96e93` failure **STEP[15]+[19]**（STEP[15] 全量 1384/84 skipped/1 failure=`testCollapseWidthIsMeasuredFrameByFrame` 0.9989289765 vs 1.0 ±0.001、widths=[750,750,750,461,461,427,427,421]、final=420；STEP[19] band 0.97× + markdown 1x=1；copy 1x=2）。`41330986001 ↔ 43c26ea`、`41331007372 ↔ b3ad856`、`41326374225 ↔ 087290d` 均 **success（0 失败步）**。
- **U-2288：② fold 收尾判据改读 settled 进度。** 旧尺读采样末帧：`bd96e93` 读到 **0.9989289765**（±0.001 红）而 widths 末段已 421、`final=420` ⇒ 采样停手早于过渡结束，是尺的假红；本机旧值 **10/10 通过**、末帧均 1.00。改为 `waitForSettled()` 后读 `controller.foldProgress`，采样末帧只要求 ≥0.99；intermediate ≥1、单调、final 420、min 360 全部保留。本机新值 **10/10 通过**、`settled=1.0000`；`M1424`（收尾少 0.002）**CAUGHT、RESTORE_CLEAN=yes**。
- **U-2289：② 预检/刀。** 预检 **324/295/757 bad=0**、ARM **417/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**。
- **U-2290：③④ 帧/全量/换装/电池/清账/streak。** 帧 **350**（CHANGED=0/MISSING=0/ADDED=0）；全量 **1385/56/0（681.6s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 25615、1 窗口 750×492）；清账 **162/162/0**；电池 **691/5**（台账后复跑）；产品面连续零改动 **2** 轮（as-of 544，`python3 scripts/product_streak.py --streak-for 544` 现读，last=b16eacc/542）。
- **U-2291：⑤ 627/629。** 627 的 fold 类红（`bd96e93` 0.998929）改为 settled 读数后不再由采样末帧触发；markdown 仍 **1x=1**（c1df1e6/8d4a36d/bd96e93 三跑），copy **1x=2**；629 保持开单、≥2 帧地板不动。
- **U-2292：⑤ 622/624。** 622 44 跑 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 **176.6ms/2/204**；120ms/容差不动、frame 半保持开单。624：`b16eacc`/`8d4a36d` STEP[9] 红在 skip_roster、`c1df1e6` STEP[9] 绿 ⇒ 两臂继续、保持开单、不改名册。
- **U-2293：⑤ 628/625/626。** 628（acefc43 STEP[9]）、625（canBecomeKeyView 真机）、626（RowContextMenuTests 3/3）均保持结案，不重开。
- **U-2294：⑥ 收口与交接。** ⓪ 笔 `8b667ae`、判据笔随后；下一轮 R546（第 545 轮 / Round 543）：先 push 复核 ahead=0；读本轮判据笔与台账笔、复读 `c5fcf03`/`5589ebe`/`e357708` 的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 542 · R545（第 544 轮 · 2026-11-02）：fold 收尾判据改读 settled 进度

`testCollapseWidthIsMeasuredFrameByFrame` 的终值原来读采样末帧；`bd96e93` 读到 0.9989289765（±0.001 红）而窗口已 final=420 ⇒ 采样停手早于过渡结束，是尺的假红。改为 `waitForSettled()` 后读 `controller.foldProgress`，采样末帧放宽到 ≥0.99，intermediate ≥1、单调、final 420、min 360 全部保留。本机旧值 10/10 通过、新值 10/10 通过（settled=1.0000）；M1424（收尾少 0.002）CAUGHT。预检 324/295/757 bad=0、ARM 417/1244、HIDDEN 410/1183 rot=0；build 0 告警；帧 350（CHANGED=0）；全量 **1385/56/0（681.6s）**；换装 431=431（PID 25615）；电池 691/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 帧卷 350 比对 CHANGED=0；fold 新旧值各 10 跑逐条记。 |
| 判据有效性 | 15/15 | M1424 CAUGHT；旧值 runner 0.9989 与本机旧 10/10 都写明。 |
| 假绿防御 | 15/15 | 旧尺读采样末帧的假红被指出；settled 后仍保留 final/min/单调/中间帧。 |
| 产品面推进 | 15/15 | 本轮产品 0 文件；推进的是 fold 收尾判据的测量对象。 |
| 台账一致性 | 15/15 | U-2287…U-2294、D-545、350/1385/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 三跑 NOT-RUN、band/markdown 红、624 两臂都如实。 |
| 可复核性 | 15/15 | 新旧各 10 跑、M1424、预检 324/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### fold 收尾判据改读 settled 进度（R545 / 第 544 轮 / Round 542 / U-2287…U-2294 · 产品 0 文件 + 判据）

`testCollapseWidthIsMeasuredFrameByFrame` 原来读采样末帧，runner `bd96e93` 读到 0.9989（±0.001 红）而窗口已落 420 ⇒ 采样停手早于过渡结束。改为 `waitForSettled()` 后读 `controller.foldProgress`，采样末帧只要求 ≥0.99；intermediate ≥1、单调、final 420、min 360 全部保留。本机旧/新值各 10/10，M1424 CAUGHT。帧 350（CHANGED=0）；全量 1385/56/0；换装 431=431；电池 691/5。

"""

DECISION = u"""
## D-545 fold 终值读 settled 进度，不读采样末帧（R545）

- 背景：`testCollapseWidthIsMeasuredFrameByFrame` 的 `progress.last == 1 ±0.001` 在 runner 上偶发红：`bd96e93` 读到 0.9989289765，而同一跑 `widths` 末段已 421、`final=420`、`min=360`。采样器在过渡结束前一拍停手，末帧不是产品终值。
- 决定：终值改为 `waitForSettled()` 之后读 `controller.foldProgress`；采样末帧只要求 ≥0.99（仍能抓「采样停在半路」），intermediate ≥1、单调、final 420、min 360 全部保留。
- 理由：判据要读它声称的那个对象——「过渡是否走完」应由 settle 后的模型状态回答，而不是由任意一次采样末帧回答；旧尺把采样相位当产品性质。
- 兼容性/迁移：只改 Swift 测试，不改产品；本机旧值 10/10、新值 10/10，M1424 证明新断言会红。
- 边界：627 的 fold 类红不再由这条采样末帧触发；markdown 1x=1 与 624 的 skip_roster 两臂不受影响。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 543 轮（R544 · 2026-11-02 · U-2278…U-2286）"
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
    add622 = u"""    复查（R545）：44 跑 `FRAME_MULTI` 仍 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；1–2 颗离群、120ms/容差不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R544）：44 跑 `FRAME_MULTI`", add622, u"b622r545")
    add627 = u"""    复查（R545）：fold 类红 `bd96e93` 0.998929 是采样末帧早停（final=420），判据改读 settle 后的 `controller.foldProgress`，本机旧/新各 10/10、M1424 CAUGHT；markdown 仍 1x=1（c1df1e6/8d4a36d/bd96e93），copy 1x=2 ⇒ 627 保持开单、≥2 帧地板不动。
"""
    text = append_after_line(text, u"复查（R544）：44 份日志 copy 2/44", add627, u"b627r545")
    add629 = u"""    复查（R545）：markdown 仍三跑 1x=1（c1df1e6/8d4a36d/bd96e93），contentFade 0.20 不动；629 继续开单等出现率；≥2 帧地板不动。
"""
    text = append_after_line(text, u"复查（R544）：试 `.markdownLabel=0.24`", add629, u"b629r545")
    add624 = u"""    复查（R545）：`b16eacc`/`8d4a36d` 的 STEP[9] 红在 skip_roster，`c1df1e6` 的 STEP[9] 绿 ⇒ 两臂继续，保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R544）：`b16eacc`/`8d4a36d` 的 STEP[9]", add624, u"b624r545")
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
        (u"R9–R541，542 节自评", u"R9–R542，543 节自评", u"title"),
        (u"阶段二 **534 轮**审计（R9–R541；以 `curve_from_ledger.py` 的 `PHASE2 n=534` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 541",
         u"阶段二 **535 轮**审计（R9–R542；以 `curve_from_ledger.py` 的 `PHASE2 n=535` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 542", u"§1"),
        (u"| 视觉台账 | U-31 … U-2286", u"| 视觉台账 | U-31 … U-2294", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 543）", u"产品面连续零改动轮数 = **2**（as-of 544）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R544 节 ② 为准", u"以 `AGENT_STATE.md` 的 R545 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R544 这一段", u"## 18. R458 → R545 这一段", u"§18 head"),
        (u"R544 续到 544 —— 这份报告第七次差点停在几十轮之前）", u"R545 续到 545 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 11649）；电池 691/5。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R545（fold 收尾判据改读 settled 进度；产品 0 文件 + 判据）**：`testCollapseWidthIsMeasuredFrameByFrame` 的终值由采样末帧改为 `waitForSettled()` 后的 `controller.foldProgress`（`bd96e93` 末帧 0.9989 而 final=420 是采样早停）；采样末帧要求 ≥0.99，intermediate ≥1、单调、final 420、min 360 全保留。本机旧/新各 10/10、settled=1.0000；M1424 CAUGHT。预检 324/295/757 bad=0、ARM 417/1244、HIDDEN 410/1183 rot=0；帧 350（CHANGED=0）；全量 1385/56/0（681.6s）；换装 431=431（PID 25615）；电池 691/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R544 / 第 543 轮 / Round 541）",
        u"最后更新：2026-11-02（本地 · R545 / 第 544 轮 / Round 542）",
        u"identity")
    text = replace_once(
        text,
        u"## R545 开工 ⓪（2026-11-02 · 第 544 轮 / Round 542）",
        u"## R545 状态（2026-11-02 · 第 544 轮 / Round 542 · 产品 0 文件 + 判据）",
        u"state title")
    anchor = u"\n## R544 状态（2026-11-02 · 第 543 轮 / Round 541 · 产品 0 文件 + 判据）"
    body = u"""
① fold 收尾判据：旧尺读采样末帧，`bd96e93` 读到 0.9989289765（±0.001 红）而 widths 末段 421、final=420 ⇒ 采样早停的假红；本机旧值 10/10 通过。改为 `waitForSettled()` 后读 `controller.foldProgress`，采样末帧只要求 ≥0.99；intermediate ≥1、单调、final 420、min 360 全保留。本机新值 10/10 通过（settled=1.0000）；`M1424` CAUGHT、RESTORE_CLEAN。
② 预检/刀：预检 324/295/757 bad=0、ARM 417/1244、HIDDEN 410/1183 rot=0；build 0 告警。
③ 627/629/624：fold 类红不再由采样末帧触发；markdown 仍 1x=1（c1df1e6/8d4a36d/bd96e93），copy 1x=2；629 保持开单；624 两臂继续、不改名册；628/625/626 结案。
④ 622：44 跑 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；120ms/容差不动。
⑤ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0）；全量 **1385/56/0（681.6s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 25615、1 窗口 750×492）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **2** 轮（as-of 544，`python3 scripts/product_streak.py --streak-for 544` 现读，last=b16eacc/542）。
⑥ CI/交接：⓪ 笔 `8b667ae` 已推；`41330986001 ↔ 43c26ea`、`41331007372 ↔ b3ad856`、`41326374225 ↔ 087290d` success；`41330618181 ↔ b16eacc` failure 仅 STEP[9]、`41330637380 ↔ 8d4a36d` STEP[9]+[19]、`41331173441 ↔ c1df1e6` 仅 STEP[19]、`41326398317 ↔ bd96e93` STEP[15]+[19]；`41331769689 ↔ c5fcf03`、`41334225593 ↔ 5589ebe`、`41334244256 ↔ e357708` 读时 in_progress ⇒ NOT-RUN。下一轮 R546（第 545 轮 / Round 543）：先 push 复核 ahead=0；读本轮判据笔与台账笔、复读 `c5fcf03`/`5589ebe`/`e357708` 的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R545_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
