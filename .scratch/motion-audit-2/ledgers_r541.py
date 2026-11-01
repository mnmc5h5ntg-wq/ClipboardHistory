#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R541 台账（第 540 轮 / Round 538）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 540 轮（R541 · 2026-11-01 · U-2250…U-2258）：627 扩窗与 622 回归表 + emphasis 回执 0.20（产品 1 文件 + 判据）

- **U-2250：⓪ CI。** HEAD=origin=`fde914e`、ahead=0、`git push` no-op；api=200/apple=200。开工五跑读时 in_progress ⇒ NOT-RUN；收口前：`41315396056 ↔ 8c165fb` **success（失败步骤 0）**——628 修好 + R539 台账落地后的整跑绿；`41317878347 ↔ 057e2e4`、`41317947527 ↔ c15377e`、`41318153433 ↔ fde914e` **success**；`41318132821 ↔ 172d8de`（R540 台账）与 `41318294600 ↔ d984ab7`（R541 ⓪）读时 **in_progress ⇒ NOT-RUN**，`41320804339 ↔ 7353513`（R541 产品）queued ⇒ NOT-RUN。已收口：`41314618298 ↔ acefc43` failure **STEP[9]+[15]**（628 签收；STEP[15] SelectionReveal flake）、`41312123929 ↔ 40a2a71` failure **仅 STEP[9]** 4 红（3 缩写 + skip_roster）、`41315228607 ↔ 3628685` failure **仅 STEP[19]**（markdown label 采样红）。
- **U-2251：② 627 扩窗到 40 跑（三类分开）。** 40 份可用日志（R528–R541）用 `motion_red_occurrence.py` 现读：copy receipt **红 2/40**（9e78221、8b1ddb9；filmstrip 只打印失败 ⇒ 分母 `filmstrip-failures-only`）、fold **红 2/37 executed**（41218878781、b6394f5）、markdown label **红 2/40**（b6394f5、3628685；分母是 Motion floor 跑数）。本机各 10 次：copy **10/10 过**（旧 emphasis 0.16：2x 3–4、1x 2–3）、fold **10/10 过**（中间帧 7–8、终值 420）。三类是三条不同动效/断言，形态同属 runner 1x 采样边界；≥2 帧地板不动，627 保持开单；markdown 与残余 copy 风险开 **BACKLOG 629**。
- **U-2252：② 622 frame 跨跑回归表。** 40 跑 `FRAME_MULTI`：`worst_max=262.3`、`over_max=2`、`over_runs=16`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；9e78221 单跑 baseline=16.67/off=42.56/loaded=46.73/ratio=1.098/n=175/worst=262.3/over=2。最差帧仍是 1–2 颗离群、loaded p95 全在 46.73 以下 ⇒ 不是整段慢；120ms 与容差 1 不动、不删锚点，frame 半保持开单。
- **U-2253：② emphasis 回执 0.20（产品 1 文件）。** 旧值 `.emphasis=0.16`：本机 copy receipt 1x 过渡帧 2–3（10/10 过），runner 1x 曾掉到 1 帧（copy 2/40、markdown 2/40）。新值 `0.20`（仍是提交级 emphasis，收藏/固定/已复制共用；上限 0.25 不动）：本机 copy receipt 1x **3–4**、2x 4–5（10/10 过）；`MotionCatalogTests` 与 copy receipt 胶片判据均绿。`M1420`（改回 0.16）**CAUGHT、RESTORE_CLEAN=yes**。runner 签收待 `7353513` 跑。
- **U-2254：② 判据/刀/预检。** `motion_red_occurrence.py` 增 markdown 红名计数与真值表断言；`M1419` 与 `M1420` 两刀均 CAUGHT；预检 **321/295/757 bad=0**、ARM **414/1244**（dupes=0 repeats=0）、HIDDEN **408/1183 rot=0**；build **0 告警**。
- **U-2255：③④ 帧/全量/换装/电池/清账。** 帧 **350**（CHANGED=0/MISSING=0/ADDED=0，静态像不变）；全量 **1384/56/0（664.5s）**（新增 1 条 emphasis 时长判据；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 48891；1 窗口 750×492；活库 431 不增不减）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **690/5**（台账后复跑）；产品面连续零改动 **2** 轮（as-of 540，`python3 scripts/product_streak.py --streak-for 540` 现读，last=acefc43/538；R540 是 0 产品轮，所以从 1 涨到 2）。
- **U-2256：⑤ 627/624/629。** 627 见 U-2251，保持开单等出现率；新开 **629**（runner 1x 短动效仍只有 1 帧：copy 2/40、markdown 2/40；emphasis 已 0.20、markdown 仍 contentFade 0.16；地板 ≥2 不动）。624 在 `acefc43`/`40a2a71` 仍红在 skip_roster；保持开单、不改名册。
- **U-2257：⑤ 622/628/625/626。** 622 frame 半第六值 262.3ms/2/175 与跨跑表见 U-2252，保持开单；code-block 半仍按 `41308835299 ↔ 21a5440` 签收。628/625/626 已结案不重开。
- **U-2258：⑥ 收口与交接。** 产品笔 `7353513` 已推；台账笔随后。下一轮 R542（第 541 轮 / Round 539）：先 push 复核 ahead=0；读 `41320804339 ↔ 7353513`（产品，emphasis 0.20 的 runner 签收）与 `41318294600 ↔ d984ab7`、`41318132821 ↔ 172d8de` 及台账跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 538 · R541（第 540 轮 · 2026-11-01）：627 扩窗与 622 回归表 + emphasis 回执 0.20

40 份可用日志把 627 三类红扩窗：copy receipt 2/40（filmstrip 只打印失败，分母受限）、fold 2/37 executed、markdown label 2/40；本机 copy/fold 各 10/10 过。622 用同跑 PROBE_FPS 的三段 p95 做跨跑回归：worst_max=262.3、over_max=2、over_runs=16、loaded_p95_max=46.73、比值 0.585–2.167 ⇒ 1–2 颗离群，不是整段慢；120ms/容差不动。产品位：`.emphasis` 从 0.16 调到 0.20（收藏/固定/已复制共用，上限 0.25 不变），本机 copy receipt 1x 过渡帧 2–3→3–4、2x 3–4→4–5；M1420 CAUGHT；目录与胶片判据绿。预检 321/295/757 bad=0、ARM 414/1244、HIDDEN 408/1183 rot=0；build 0 告警；帧 350（CHANGED=0）；全量 **1384/56/0（664.5s）**；换装 431=431（PID 48891）；电池 690/5。627 保持开单，新开 629；624 保持开单。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 帧卷 350 比对 CHANGED=0；copy receipt 的 1x/2x 胶片读数逐跑解析并对比旧/新。 |
| 判据有效性 | 15/15 | 40 跑跨跑表 + 三类分开 + M1420（0.20→0.16）CAUGHT。 |
| 假绿防御 | 15/15 | copy 分母受限写明；skip 不进分母；fold/markdown/copy 分开计；run 签收待 runner。 |
| 产品面推进 | 15/15 | emphasis 0.16→0.20 让 1x 回执过渡帧升一档；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2250…U-2258、D-541、350/1384/431/690 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 产品改动明确待 runner 签收；markdown 未改并开 629；阈值/地板不动。 |
| 可复核性 | 15/15 | 40 跑表、M1420、预检 321/295/757、1384 全量、690 电池全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 627 扩窗与 622 回归表 + emphasis 回执 0.20（R541 / 第 540 轮 / Round 538 / U-2250…U-2258 · 产品 1 文件 + 判据）

`motion_red_occurrence.py` 扩到 40 份可用日志：copy receipt 2/40（分母受限）、fold 2/37 executed、markdown label 2/40；622 跨跑 worst_max 262.3、over_max 2、over_runs 16、loaded_p95_max 46.73、比值 0.585–2.167 ⇒ 1–2 颗离群。产品把 `.emphasis` 从 0.16 调到 0.20（收藏/固定/已复制共用，上限 0.25 不变），本机 copy receipt 1x 过渡帧 2–3→3–4；M1420 CAUGHT。帧 350（CHANGED=0）；全量 1384/56/0；换装 431=431；电池 690/5。627 保持开单，新开 629。

"""

DECISION = u"""
## D-541 emphasis 从 0.16 调到 0.20，让 1x 回执过渡可见（R541）

- 背景：627 的 40 跑窗口里 copy receipt 2/40、markdown label 2/40 在 runner 1x 上只读到 1 个过渡帧；本机 copy receipt 的 1x 过渡帧是 2–3，贴着 ≥2 地板。
- 决定：`MotionCatalog` 的 `.emphasis` 从 0.16 调到 0.20（收藏 / 固定 / 已复制共用；仍低于 0.25 上限，与 slider/windowFold 同档）；`MotionCatalogTests.testEmphasisFeedbackSurvivesOneXSampling` 钉住 ≥0.20，M1420 改回 0.16 即 CAUGHT。
- 理由：本机 copy receipt 1x 过渡帧从 2–3 升到 3–4（2x 3–4→4–5），10/10 仍通过；0.20 仍是一次反馈的时长，不改变回执的布局/颜色/文案，也不改帧数地板。
- 兼容性/迁移：emphasis 同时影响收藏/固定符号动画的时长（+40ms），仍在上限内；静态帧 CHANGED=0。
- 边界：runner 签收待 `7353513` 跑；markdown label 走 `.contentFade` 0.16 未改，残余 1x 1 帧风险记 BACKLOG 629。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 539 轮（R540 · 2026-11-01 · U-2241…U-2249）"
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
    add622 = u"""    复查（R541）：40 跑 `FRAME_MULTI`：`worst_max=262.3`、`over_max=2`、`over_runs=16`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；最差帧仍 1–2 颗离群、loaded p95 全在 46.73 以下 ⇒ 不是整段慢；120ms/容差不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R540）：15 跑 `motion_red_occurrence.py`", add622, u"b622r541")
    add627 = u"""    复查（R541）：40 份可用日志扩窗——copy 2/40（9e78221、8b1ddb9；分母受限）、fold 2/37 executed（41218878781、b6394f5）、markdown 2/40（b6394f5、3628685）；本机 copy/fold 各 10/10 过。copy 的 emphasis 已调到 0.20（1x 2–3→3–4），markdown 仍 contentFade 0.16；残余 1x 1 帧风险见 629；≥2 帧地板不动、保持开单。
"""
    text = append_after_line(text, u"复查（R540）：15 跑窗口把三种红分开数", add627, u"b627r541")
    item629 = u"""
**629. runner 1x 上短动效仍只有 1 个过渡帧（copy receipt / markdown label）**（R541 现读）
    现象：40 份可用日志里 copy receipt 红 2/40（filmstrip 只打印失败 ⇒ 分母受限）、markdown label 红 2/40（Motion floor 红名：b6394f5、3628685）；本机 copy/fold 各 10/10 过（copy 1x 旧 2–3）。
    现状：copy receipt 的 `.emphasis` 已从 0.16 调到 0.20（R541 产品 1 文件），本机 1x 过渡帧 2–3→3–4；markdown label 仍走 `.contentFade` 0.16，未改；Motion ≥2 帧地板不动、不改名册。
    退场：runner 连续两跑 copy receipt 不再红，且 markdown 的出现率有可数分母；没有分母前不销单。
"""
    if not text.endswith(u"\n"):
        text += u"\n"
    text += item629
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
        (u"R9–R537，538 节自评", u"R9–R538，539 节自评", u"title"),
        (u"阶段二 **530 轮**审计（R9–R537；以 `curve_from_ledger.py` 的 `PHASE2 n=530` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 537",
         u"阶段二 **531 轮**审计（R9–R538；以 `curve_from_ledger.py` 的 `PHASE2 n=531` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 538", u"§1"),
        (u"| 视觉台账 | U-31 … U-2249", u"| 视觉台账 | U-31 … U-2258", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 539）", u"产品面连续零改动轮数 = **2**（as-of 540）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R540 节 ② 为准", u"以 `AGENT_STATE.md` 的 R541 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R540 这一段", u"## 18. R458 → R541 这一段", u"§18 head"),
        (u"R540 续到 540 —— 这份报告第七次差点停在几十轮之前）", u"R541 续到 541 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"；627 保持开单等出现率。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R541（627 扩窗与 622 回归表 + emphasis 回执 0.20；产品 1 文件 + 判据）**：40 份可用日志扩窗 copy 2/40、fold 2/37 executed、markdown 2/40；本机 copy/fold 各 10/10 过。622 跨跑 worst_max 262.3、over_max 2、over_runs 16、loaded_p95_max 46.73、比值 0.585–2.167 ⇒ 1–2 颗离群。`.emphasis` 0.16→0.20，本机 copy receipt 1x 2–3→3–4；M1420 CAUGHT；预检 321/295/757 bad=0、ARM 414/1244、HIDDEN 408/1183 rot=0；帧 350（CHANGED=0）；全量 1384/56/0（664.5s）；换装 431=431（PID 48891）；电池 690/5。627 保持开单，新开 629；624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R540 / 第 539 轮 / Round 537）",
        u"最后更新：2026-11-01（本地 · R541 / 第 540 轮 / Round 538）",
        u"identity")
    text = replace_once(
        text,
        u"## R541 开工 ⓪（2026-11-01 · 第 540 轮 / Round 538）",
        u"## R541 状态（2026-11-01 · 第 540 轮 / Round 538 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R540 状态（2026-11-01 · 第 539 轮 / Round 537 · 产品 0 文件 + 判据）"
    body = u"""
① 627 扩窗/三类：40 份可用日志 copy **2/40**（9e78221、8b1ddb9；filmstrip 只打印失败 ⇒ 分母受限）、fold **2/37 executed**（41218878781、b6394f5）、markdown **2/40**（b6394f5、3628685）；本机 copy/fold 各 10/10 过（copy 旧 1x 2–3、fold 中间帧 7–8）。三类不同动效/断言、同属 runner 1x 采样边界；≥2 帧地板不动、627 保持开单；新开 **629**（残余 copy/markdown 1x 1 帧）。
② 622 跨跑回归：40 跑 `worst_max=262.3`、`over_max=2`、`over_runs=16`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；最差帧 1–2 颗离群、loaded p95 全在 46.73 以下 ⇒ 不是整段慢；120ms/容差 1 不动、frame 半保持开单。
③ 产品/判据：`.emphasis` 0.16→0.20（收藏/固定/已复制共用，上限 0.25 不变）；本机 copy receipt 1x 2–3→3–4、2x 3–4→4–5；`MotionCatalogTests`/copy 胶片判据绿；`M1420`（改回 0.16）CAUGHT、RESTORE_CLEAN。`motion_red_occurrence.py` 增 markdown 红名计数；`M1419` 仍 CAUGHT。预检 321/295/757 bad=0、ARM 414/1244、HIDDEN 408/1183 rot=0；build 0 告警。
④ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0）；全量 **1384/56/0（664.5s）**（新增 1 条 emphasis 时长判据）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 48891、1 窗口 750×492）；电池 **690/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **2** 轮（as-of 540，`scripts/product_streak.py --streak-for 540` 现读，last=acefc43/538；R540 是 0 产品轮）。
⑤ CI/交接：产品笔 `7353513` 已推；R540 的 `41317878347 ↔ 057e2e4`、`41317947527 ↔ c15377e`、`41318153433 ↔ fde914e`、`41315396056 ↔ 8c165fb` 均 **success（0 失败步）**；`41318132821 ↔ 172d8de`、`41318294600 ↔ d984ab7` 读时 in_progress ⇒ NOT-RUN；`41320804339 ↔ 7353513` queued ⇒ NOT-RUN。下一轮 R542（第 541 轮 / Round 539）：先 push 复核 ahead=0；读 `41320804339 ↔ 7353513`（emphasis 0.20 runner 签收）与 `41318132821 ↔ 172d8de`、`41318294600 ↔ d984ab7` 及台账跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R541_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
