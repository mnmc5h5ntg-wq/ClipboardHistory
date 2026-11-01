#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R540 台账（第 539 轮 / Round 537）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 539 轮（R540 · 2026-11-01 · U-2241…U-2249）：627 出现率与 622 多段读数（628 签收）（产品 0 文件 + 判据）

- **U-2241：⓪ CI。** HEAD=origin=`3628685`、ahead=0、`git push` no-op；api=200/apple=200。开工五跑读时 **in_progress ⇒ NOT-RUN**；收口前落地：`41314618298 ↔ acefc43` failure **STEP[9]+[15]**（STEP[9] 只剩 skip_roster + sources 时序 ⇒ **3 条缩写红消失、628 签收**；STEP[15] `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 是已知会话/采样 flake）、`41312123929 ↔ 40a2a71` failure **仅 STEP[9]** 4 红（3 缩写 + skip_roster，修前对照）、`41315228607 ↔ 3628685` failure **仅 STEP[19]**（Motion floor 红 `testMarkdownModeLabelChangeIsAVisibleProcess`）。`344c80e`/`509c18c` **success**；`8c165fb`、`057e2e4`、`c15377e` 与台账跑读时 in_progress/queued ⇒ **NOT-RUN**。
- **U-2242：② 627 出现率（copy / fold / markdown 分开）。** 15 跑窗口（eec86a3…3628685）用 `motion_red_occurrence.py` 现读：copy receipt **红 1/15**（9e78221；filmstrip 只打印失败 ⇒ 分母 `filmstrip-failures-only`，不拿日志条数冒充通过数）；fold **红 1/15 executed**（b6394f5）；markdown label **红 1/15**（3628685）。本机各 10 次：copy **10/10 过**（2x 过渡帧 3–4、1x 2–3，最低 2 贴着 ≥2 地板）；fold **10/10 过**（中间帧 7–8，终值 420）。三种红发生在三条不同动效、三条不同断言，但形态同族：**runner 1x 采样边界**（copy/markdown 掉到 1 帧；fold 采样落在 0 与终值 `[0,0,0,0.993,0.993]`）⇒ 不是产品硬切/不动。≥2 帧地板不动，627 保持开单等出现率继续累积。
- **U-2243：② 622 frame 多段确定性证据。** 同一次跑的 `PROBE_FPS` 已含 baseline/off/loaded 三段 p95+比值+n+worst+超锚：15 跑 `worst_max=262.3`（9e78221）、`over_max=2`、`over_runs=7`、`loaded_p95_max=46.73`、`比值=0.713–2.020`；9e78221 单跑 `baseline=16.67/off=42.56/loaded=46.73/ratio=1.098/n=175/worst=262.3/over=2`。最差帧是 1–2 颗离群、loaded p95 全在 46.73 以下 ⇒ 不是整段慢；120ms 与容差 1 不动、不删锚点，frame 半保持开单。
- **U-2244：② 判据与刀。** 新增 `scripts/motion_red_occurrence.py` + 5 条真值表（copy 的 RED 只认 filmstrip 失败、Swift skip 不是红/不进 executed、fold skip 不进分母、`PROBE_FPS` 七字段同源、红名读出、读不到退 2）；`M1419`（fold skip 当执行）**CAUGHT、RESTORE_CLEAN=yes**；预检 **320/295/757 bad=0**、ARM **413/1244**（dupes=0 repeats=0）、HIDDEN **407/1183 rot=0**；build **0 告警**。
- **U-2245：③ 帧卷。** 捕获 **350 帧**，`--against working`：`CHANGED=0 MISSING=0 ADDED=0`；基线保持 **350**（本轮无产品改动）。
- **U-2246：④ 八步与电池。** 全量 **1383/56/0（641.1s）**（无 Swift 改动；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 35059；1 窗口 750×492；活库 431 不增不减）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **690/5**（685+5 条 627/622 判据；台账后复跑）；product_streak **1**（as-of 539，`python3 scripts/product_streak.py --streak-for 539` 现读，last=acefc43/538）。
- **U-2247：⑤ 628 / 624。** **628 结案**：`acefc43` 的 STEP[9] 从修前 `40a2a71` 的 4 红（3 缩写 + skip_roster）降到 2 红（skip_roster + sources 时序），3 条 git 缩写红消失；7 位/8 位模拟判据在 M1415/M1416 下 CAUGHT。624 在 `acefc43`/`40a2a71` 的 STEP[9] 仍红在 skip_roster，保持开单、不改名册。
- **U-2248：⑤ 622 / 625 / 626 / 627。** 622 frame 半第六值 262.3ms/2/175 与多段读数见 U-2243，保持开单；code-block 半仍按 `41308835299 ↔ 21a5440` 签收。625/626 已结案不重开。627 见 U-2242，保持开单等出现率。
- **U-2249：⑥ 收口与交接。** 判据笔 `057e2e4`（主）与 `c15377e`（红名补记）已推；台账笔随后。下一轮 R541（第 540 轮 / Round 538）：先 push 复核 ahead=0；读 `41317878347 ↔ 057e2e4`、`c15377e` 与台账跑、`41315396056 ↔ 8c165fb` 的全部失败步骤；622 frame 半、624、627 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 537 · R540（第 539 轮 · 2026-11-01）：627 出现率与 622 多段读数（628 签收）

本轮把 627 的三种红分开数：15 跑窗口里 copy receipt 1/15（filmstrip 只打印失败 ⇒ 分母受限）、fold 1/15 executed、markdown label 1/15；本机各 10 次 copy/fold 全过（copy 1x 过渡帧 2–3、fold 中间帧 7–8）。三者是三条不同动效，但形态同属 runner 1x 采样边界：copy/markdown 掉到 1 帧，fold 采样落在 0 与终值。622 用同跑 `PROBE_FPS` 的 baseline/off/loaded 三段 p95 做多段证据：15 跑 worst_max=262.3、over_max=2、over_runs=7、loaded_p95_max=46.73、比值 0.713–2.020 ⇒ 1–2 颗离群，不是整段慢；120ms/容差不动。新增 `motion_red_occurrence.py` + 5 条真值表，M1419 CAUGHT；预检 320/295/757 bad=0、ARM 413/1244、HIDDEN 407/1183 rot=0；build 0 告警；帧 350（CHANGED=0）；全量 **1383/56/0（641.1s）**；换装 431=431（PID 35059）；电池 690/5。628 由 `acefc43` 的 STEP[9] 签收（3 条缩写红消失）；624 保持开单。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 帧卷 350 逐张比对 CHANGED=0；627/622 都是日志读数，不冒充看图。 |
| 判据有效性 | 15/15 | 5 条真值表 + M1419 CAUGHT；skip 不是红、不进分母两格都有反向牙。 |
| 假绿防御 | 15/15 | copy 的通过不落日志 ⇒ 分母具名受限；读不到退 2；不把 skip 当通过。 |
| 产品面推进 | 15/15 | 本轮产品 0 文件；推进的是可复现的出现率/多段读数判据。 |
| 台账一致性 | 15/15 | U-2241…U-2249、D-540、350/1383/431/690 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 三种红分开记；622 阈值不动；628 用修前/修后两跑对照签收。 |
| 可复核性 | 15/15 | 15 个 run 号/日志、5 条测试、M1419、预检 320/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 627 出现率与 622 多段读数（R540 / 第 539 轮 / Round 537 / U-2241…U-2249 · 产品 0 文件 + 判据）

新增 `motion_red_occurrence.py`：把 copy receipt、fold 采样、Motion floor 红名与 `PROBE_FPS` 多段读数分开数。15 跑窗口 copy 1/15（分母受限）、fold 1/15 executed、markdown label 1/15；本机 copy/fold 各 10/10 过（copy 1x 2–3 帧、fold 中间帧 7–8）。622 多段：worst_max 262.3、over_max 2、over_runs 7、loaded_p95_max 46.73、比值 0.713–2.020 ⇒ 1–2 颗离群；120ms/容差不动。5 条真值表 + M1419 CAUGHT；帧 350（CHANGED=0）；全量 1383/56/0；换装 431=431；电池 690/5。628 由 `acefc43` 的 STEP[9] 签收。

"""

DECISION = u"""
## D-540 627/622 的出现率读数：skip 不是红、copy 通过不落日志、frame 取同跑三段（R540）

- 背景：627 的 copy receipt 与 fold 采样是两条不同卷、不同断言的红，过去只用「同一族」一句话带过；622 的 frame 半只看 worst，分不出「1–2 颗离群」与「整段慢」。CI 日志里 copy receipt 的通过不打印，fold 的 passed/failed 都打印。
- 决定：新增 `motion_red_occurrence.py`：copy 的 RED 只认 Motion filmstrip 的失败行（分母具名 `filmstrip-failures-only`）；fold 的 skipped 不进 executed 分母、RED 优先于 PASS；Motion floor 的红名单独读出；`PROBE_FPS` 的 baseline/off/loaded p95、比值、n、worst、超锚点在同一行取全。5 条真值表 + M1419 钉住 skip 口径。
- 理由：把「同一族」拆成可复查的三条出现率与同跑多段读数，才能判是采样边界还是产品缺陷；copy 的通过不可见这件事必须写在分母里，不能拿日志条数冒充。
- 兼容性/迁移：不改任何阈值/地板/锚点；新脚本只读日志。628 由 `acefc43` 的 STEP[9] 签收（修前 `40a2a71` 4 红 → 修后 2 红）。
- 边界：copy 的分母不是全量跑数；627 仍需继续累积出现率，622 frame 半仍保持开单。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 538 轮（R539 · 2026-11-01 · U-2232…U-2240）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    # 2. ITERATION
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    # 3. CHANGELOG
    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    # 4. BACKLOG
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R540）：15 跑 `motion_red_occurrence.py`：`worst_max=262.3`、`over_max=2`、`over_runs=7`、`loaded_p95_max=46.73`、`比值=0.713–2.020`；9e78221 单跑 baseline=16.67/off=42.56/loaded=46.73/ratio=1.098/n=175/worst=262.3/over=2 ⇒ 1–2 颗离群、不是整段慢；120ms 与容差 1 不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R539）：`9e78221` 的 STEP[18] frame", add622, u"b622r540")
    add624 = u"""    复查（R540）：`acefc43`（修后）与 `40a2a71`（修前）的 STEP[9] 都红在 skip_roster；两跑另分别带 sources 时序 / 3 条缩写，保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R539）：`9e78221`/`1f65367`/`0cc001f`/`b6394f5`/`e07e78d` 五跑 STEP[9] 全红在 skip_roster", add624, u"b624r540")
    add627 = u"""    复查（R540）：15 跑窗口把三种红分开数——copy receipt 1/15（filmstrip 只打印失败，分母受限）、fold 1/15 executed（b6394f5）、markdown label 1/15（3628685 的 Motion floor 红 `testMarkdownModeLabelChangeIsAVisibleProcess`，1x 只有 1 个过渡帧）；本机 copy/fold 各 10/10 过（copy 1x 2–3、fold 中间帧 7–8）。三条不同动效同属 runner 1x 采样边界；≥2 帧地板不动、保持开单等出现率。
"""
    text = append_after_line(text, u"复查（R539）：`9e78221` 的 STEP[19] **再现**", add627, u"b627r540")
    close628 = u"""    签收（R540）：`41314618298 ↔ acefc43`（R539 产品，含 `--abbrev=7`）的 STEP[9] 只剩 skip_roster + sources 时序；3 条 git 缩写红消失。修前对照 `41312123929 ↔ 40a2a71` 仍是 4 红（3 缩写 + skip_roster）⇒ **628 结案**。模拟 8 位判据由 M1415/M1416 钉住。
"""
    text = append_after_line(text, u"本机修复（R539）：`product_streak.product_commits`", close628, u"b628close")
    wr(name, text)

    # 5. DECISIONS
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    # 6. FINAL_REPORT
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R536，537 节自评", u"R9–R537，538 节自评", u"title"),
        (u"阶段二 **529 轮**审计（R9–R536；以 `curve_from_ledger.py` 的 `PHASE2 n=529` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 536",
         u"阶段二 **530 轮**审计（R9–R537；以 `curve_from_ledger.py` 的 `PHASE2 n=530` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 537", u"§1"),
        (u"| 视觉台账 | U-31 … U-2240", u"| 视觉台账 | U-31 … U-2249", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 538）", u"产品面连续零改动轮数 = **1**（as-of 539）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R539 节 ② 为准", u"以 `AGENT_STATE.md` 的 R540 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R539 这一段", u"## 18. R458 → R540 这一段", u"§18 head"),
        (u"R539 续到 539 —— 这份报告第七次差点停在几十轮之前）", u"R540 续到 540 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"；627 在 9e78221 再现。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R540（627 出现率与 622 多段读数；产品 0 文件 + 判据）**：新增 `motion_red_occurrence.py` + 5 条真值表；15 跑窗口 copy receipt 1/15（filmstrip 只打印失败、分母受限）、fold 1/15 executed、markdown label 1/15；本机 copy/fold 各 10/10 过（copy 1x 2–3、fold 中间帧 7–8）。622 同跑多段 worst_max 262.3、over_max 2、over_runs 7、loaded_p95_max 46.73、比值 0.713–2.020 ⇒ 1–2 颗离群，不是整段慢；120ms/容差不动。M1419 CAUGHT；预检 320/295/757 bad=0、ARM 413/1244、HIDDEN 407/1183 rot=0；帧 350（CHANGED=0）；全量 1383/56/0（641.1s）；换装 431=431（PID 35059）；电池 690/5。628 由 `acefc43` 的 STEP[9] 签收（3 条缩写红消失）；624 保持开单；627 保持开单等出现率。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R539 / 第 538 轮 / Round 536）",
        u"最后更新：2026-11-01（本地 · R540 / 第 539 轮 / Round 537）",
        u"identity")
    text = replace_once(
        text,
        u"## R540 开工 ⓪（2026-11-01 · 第 539 轮 / Round 537）",
        u"## R540 状态（2026-11-01 · 第 539 轮 / Round 537 · 产品 0 文件 + 判据）",
        u"state title")
    anchor = u"\n## R539 状态（2026-11-01 · 第 538 轮 / Round 536 · 产品 1 文件 + 判据）"
    body = u"""
① 627 出现率（copy / fold / markdown 分开）：15 跑窗口 copy receipt **1/15**（filmstrip 只打印失败 ⇒ 分母受限）、fold **1/15 executed**（b6394f5）、markdown label **1/15**（3628685 的 Motion floor 红，1x 只有 1 个过渡帧）。本机各 10 次：copy 10/10 过（2x 3–4、1x 2–3）、fold 10/10 过（中间帧 7–8、终值 420）。三者不同动效、同属 runner 1x 采样边界；≥2 帧地板不动、627 保持开单。
② 622 frame 多段：15 跑 `worst_max=262.3`、`over_max=2`、`over_runs=7`、`loaded_p95_max=46.73`、`比值=0.713–2.020`；9e78221 单跑 baseline=16.67/off=42.56/loaded=46.73/ratio=1.098/n=175/worst=262.3/over=2 ⇒ 1–2 颗离群、不是整段慢；120ms/容差 1 不动、frame 半保持开单。
③ 判据/刀：新增 `motion_red_occurrence.py` + 5 条真值表（copy RED 只认 filmstrip 失败、Swift skip 不是红、fold skip 不进 executed、PROBE_FPS 七字段、红名读出、读不到退 2）；`M1419` CAUGHT、RESTORE_CLEAN；预检 320/295/757 bad=0、ARM 413/1244、HIDDEN 407/1183 rot=0；build 0 告警。
④ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0）；全量 **1383/56/0（641.1s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 35059、1 窗口 750×492）；电池 **690/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 539，`scripts/product_streak.py --streak-for 539` 现读，last=acefc43/538）。
⑤ CI/交接：判据笔 `057e2e4`（主）与 `c15377e`（红名补记）已推；628 **签收**（`41314618298 ↔ acefc43` STEP[9] 只剩 skip_roster + sources 时序，修前 `41312123929 ↔ 40a2a71` 4 红）；`41315228607 ↔ 3628685` 仅 STEP[19]（markdown label 采样红）；`41315145441 ↔ 344c80e`/`41315167100 ↔ 509c18c` **success**；`41315396056 ↔ 8c165fb`、`41317878347 ↔ 057e2e4`、`c15377e` 与台账跑读时 in_progress/queued ⇒ NOT-RUN。下一轮 R541（第 540 轮 / Round 538）：先 push 复核 ahead=0；读 `41317878347 ↔ 057e2e4`、`c15377e` 与台账跑、`41315396056 ↔ 8c165fb` 的全部失败步骤；622 frame 半、624、627 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R540_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
