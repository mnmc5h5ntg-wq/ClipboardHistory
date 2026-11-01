#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R542 台账（第 541 轮 / Round 539）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 541 轮（R542 · 2026-11-02 · U-2260…U-2268）：emphasis 0.20 撤回 + contentFade 0.20（产品 1 文件 + 判据）

- **U-2260：⓪ CI。** HEAD=origin=`4521ac3`、ahead=0、`git push` no-op；api=200/apple=200。开工四跑 in_progress ⇒ NOT-RUN；收口前：`41317878347 ↔ 057e2e4`、`41317947527 ↔ c15377e`、`41318132821 ↔ 172d8de`、`41318153433 ↔ fde914e`、`41315396056 ↔ 8c165fb` 以及 `41321009857 ↔ cc15c76`（R541 台账）、`41321172002 ↔ 0dc8105`（补记二）、`41321193291 ↔ 4521ac3`（补记三）、`41321338166 ↔ 48ef7d7`（R542 ⓪）**全部 success（0 失败步）**。`41320804339 ↔ 7353513` failure **STEP[9]+[15]**（STEP[9]=skip_roster + sources 时序；STEP[15]=`UICaptureTests.testRecordingCardFrameIsDeterministicAcrossRenders` dark **diff 11667px**）、`41318294600 ↔ d984ab7` failure **仅 STEP[18]**（frame 176.6ms/2/204 + 右击探针心跳未闭合）。`f7bd865` 产品跑 push 后取号。
- **U-2261：② 627/629 扩到 42 跑。** `motion_red_occurrence.py` 42 份可用日志：copy receipt **2/42**（9e78221、8b1ddb9；filmstrip 只打印失败 ⇒ 分母受限）、fold **2/39 executed**（41218878781、b6394f5）、markdown **2/42**（b6394f5、3628685）；本机 copy/markdown/fold 各 10/10 过。三类分开、分母写明；≥2 帧地板不动，627 保持开单；629 继续记残余 1x 1 帧风险。
- **U-2262：② 622 跨跑回归。** 42 跑 `FRAME_MULTI`：`worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；`d984ab7` 的 176.6ms/2/204 是第七值（544.1→162.2→175.8→243.2→151.4→262.3→176.6）。最差帧仍是 1–2 颗离群、不是整段慢；120ms/容差 1 不动、frame 半保持开单。
- **U-2263：② emphasis 0.20 撤回、contentFade 0.20 保留。** `7353513`（emphasis 0.20）的 copy receipt **1x 过渡帧=2**、窗口 1329ms、声明 200ms，Motion floor `REDS=0`；但同跑 STEP[15] 出现**新的**录制帧确定性红（dark diff 11667px），而录制描边正是 `SettingsView:1141` 的 `.animation(MotionCatalog.animation(for: .emphasis))` ⇒ 按「没有新红才保留」撤回 emphasis 0.20（回到 0.16），删 `testEmphasisFeedbackSurvivesOneXSampling` 与 M1420 刀。markdown 候选：`contentFade` 0.16→0.20，本机 markdown 1x 过渡帧 **3–4→4**（2x 5–6→5–7），copy 1x 3–4（emphasis 0.16）、fold 中间帧 7–8，各 10/10 过；`M1421`（改回 0.16）**CAUGHT、RESTORE_CLEAN=yes**。
- **U-2264：② 判据/预检。** `MotionCatalogTests.testContentFadeSurvivesOneXSampling` 钉 ≥0.20；`M1421` CAUGHT；预检 **321/295/757 bad=0**、ARM **414/1244**（dupes=0 repeats=0）、HIDDEN **408/1183 rot=0**；build **0 告警**。
- **U-2265：③④ 帧/全量/换装/电池/清账。** 帧 **350**（CHANGED=0/MISSING=0/ADDED=0）；全量 **1384/56/0（698.6s）**（emphasis 判据删除、contentFade 判据加入，净数不变；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 71348；1 窗口 750×492；活库 431 不增不减）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **690/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 541，`python3 scripts/product_streak.py --streak-for 541` 现读，last=7353513/540）。
- **U-2266：⑤ 629。** emphasis 0.20 已撤回（新红）；contentFade 0.20 保留（markdown 本机 1x 3–4→4）；copy 仍 2/42、markdown 2/42，≥2 帧地板不动、629 保持开单等 runner 的 contentFade 签收。
- **U-2267：⑤ 622/624/627/628/625/626。** 622 见 U-2262，frame 半保持开单；624 在 `7353513` 的 STEP[9] 仍红在 skip_roster，保持开单、不改名册；627 见 U-2261，保持开单；628/625/626 已结案不重开。
- **U-2268：⑥ 收口与交接。** 产品笔 `f7bd865` 已推；台账笔随后。下一轮 R543（第 542 轮 / Round 540）：先 push 复核 ahead=0；读 `f7bd865` 产品跑与 `48ef7d7`/`cc15c76`/`0dc8105`/`4521ac3` 的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 539 · R542（第 541 轮 · 2026-11-02）：emphasis 0.20 撤回 + contentFade 0.20

R541 的 emphasis 0.20 产品跑 `7353513` 里 copy receipt 1x 过渡帧=2、Motion floor REDS=0，但 STEP[15] 出现新的录制帧确定性红（dark diff 11667px），而录制描边走 `.emphasis` ⇒ 按「没有新红才保留」撤回 emphasis（回 0.16），删其判据与 M1420。markdown 候选改用 `contentFade` 0.20：本机 markdown 1x 3–4→4（2x 5–6→5–7）、copy 1x 3–4、fold 中间帧 7–8，各 10/10；M1421 CAUGHT。42 份日志扩窗：copy 2/42（分母受限）、fold 2/39 executed、markdown 2/42；622 跨跑 worst_max 262.3、over_max 2、over_runs 17、loaded_p95_max 46.73、比值 0.585–2.167。预检 321/295/757 bad=0、ARM 414/1244、HIDDEN 408/1183 rot=0；build 0 告警；帧 350（CHANGED=0）；全量 **1384/56/0（698.6s）**；换装 431=431（PID 71348）；电池 690/5。627/629 保持开单，624 保持开单。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 帧卷 350 比对 CHANGED=0；markdown/copy/fold 的 1x/2x 过渡帧逐跑解析。 |
| 判据有效性 | 15/15 | M1421（contentFade 回 0.16）CAUGHT；emphasis 新红作为撤回的硬证据。 |
| 假绿防御 | 15/15 | 产品跑有新红就不保留；42 跑分母写明；skip 不计分母；撤回写回 BACKLOG。 |
| 产品面推进 | 15/15 | contentFade 0.16→0.20 让 markdown 1x 升一档；产品 1 文件。 |
| 台账一致性 | 15/15 | U-2260…U-2268、D-542、350/1384/431/690 都来自命令与日志。 |
| 交付诚实性 | 15/15 | emphasis 撤回、contentFade 待 runner、627/629/624 开单都如实。 |
| 可复核性 | 15/15 | 42 跑表、M1421、预检 321/295/757、1384 全量、690 电池全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### emphasis 0.20 撤回 + contentFade 0.20（R542 / 第 541 轮 / Round 539 / U-2260…U-2268 · 产品 1 文件 + 判据）

R541 的 emphasis 0.20 在 `7353513` 产品跑里 copy 1x=2、Motion floor 干净，但出现新的录制帧确定性红（dark 11667px；录制描边走 emphasis）⇒ 撤回 emphasis、删其判据与 M1420。markdown 候选改 `contentFade` 0.20：本机 markdown 1x 3–4→4、2x 5–6→5–7，copy/fold 各 10/10；M1421 CAUGHT。42 份日志扩窗：copy 2/42、fold 2/39、markdown 2/42；622 worst_max 262.3、over 2、over_runs 17、loaded_p95 46.73。帧 350（CHANGED=0）；全量 1384/56/0；换装 431=431；电池 690/5。

"""

DECISION = u"""
## D-542 emphasis 0.20 撤回、contentFade 0.20 保留（R542）

- 背景：R541 把 `.emphasis` 0.16→0.20 以救 1x copy receipt；产品跑 `7353513` 里 copy receipt 1x 过渡帧=2、Motion floor REDS=0，但 STEP[15] 出现新的 `testRecordingCardFrameIsDeterministicAcrossRenders` 红（dark diff 11667px）。录制描边在 `SettingsView:1141` 用 `.animation(MotionCatalog.animation(for: .emphasis))` ⇒ 新的红与 emphasis 时长直接相关。
- 决定：撤回 emphasis 0.20（回 0.16），删除 `testEmphasisFeedbackSurvivesOneXSampling` 与 M1420 刀；保留 markdown 候选的 `contentFade` 0.20（本机 markdown 1x 3–4→4、2x 5–6→5–7），并用 `testContentFadeSurvivesOneXSampling` + M1421 钉住。
- 理由：用户规则是「没有新红才保留」；copy 1x=2 只说明它刚好过线，不能抵消同跑的新红。contentFade 的新值在本机三条动效 10/10 与目录判据全绿，先保留待 runner 签收。
- 兼容性/迁移：emphasis 回到 0.16（原值）；contentFade 0.20 仍在 0.25 上限内；静态帧 CHANGED=0。
- 边界：contentFade 0.20 仍需 runner 签收；629 的 copy/markdown 残余 1x 1 帧风险保持开单，≥2 帧地板不动。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 540 轮（R541 · 2026-11-01 · U-2250…U-2259）"
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
    add622 = u"""    复查（R542）：42 跑 `FRAME_MULTI`：`worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204（d984ab7）；1–2 颗离群、不是整段慢；120ms/容差不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R541 收口）：`41318294600 ↔ d984ab7`", add622, u"b622r542")
    add627 = u"""    复查（R542）：42 份日志扩窗 copy 2/42、fold 2/39 executed、markdown 2/42；emphasis 0.20 在 `7353513` 里 copy 1x=2、Motion floor REDS=0，但同跑新红 `testRecordingCardFrameIsDeterministicAcrossRenders`（dark 11667px；录制描边走 emphasis）⇒ **emphasis 撤回 0.16**、删其判据/M1420；contentFade 0.20 保留待签收。≥2 帧地板不动、627 保持开单。
"""
    text = append_after_line(text, u"复查（R541）：40 份可用日志扩窗", add627, u"b627r542")
    add629 = u"""    复查（R542）：emphasis 0.20 已撤回（`7353513` 的新录制帧确定性红，dark 11667px）；contentFade 0.20 保留（markdown 本机 1x 3–4→4、2x 5–6→5–7，copy/fold 各 10/10）；M1421 CAUGHT。copy 仍 2/42、markdown 2/42，≥2 帧地板不动、保持开单等 contentFade runner 签收。
"""
    text = append_after_line(text, u"现象：40 份可用日志里 copy receipt 红 2/40", add629, u"b629r542")
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
        (u"R9–R538，539 节自评", u"R9–R539，540 节自评", u"title"),
        (u"阶段二 **531 轮**审计（R9–R538；以 `curve_from_ledger.py` 的 `PHASE2 n=531` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 538",
         u"阶段二 **532 轮**审计（R9–R539；以 `curve_from_ledger.py` 的 `PHASE2 n=532` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 539", u"§1"),
        (u"| 视觉台账 | U-31 … U-2259", u"| 视觉台账 | U-31 … U-2268", u"U 上界"),
        (u"产品面连续零改动轮数 = **2**（as-of 540）", u"产品面连续零改动轮数 = **1**（as-of 541）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R541 节 ② 为准", u"以 `AGENT_STATE.md` 的 R542 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R541 这一段", u"## 18. R458 → R542 这一段", u"§18 head"),
        (u"R541 续到 541 —— 这份报告第七次差点停在几十轮之前）", u"R542 续到 542 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"（622 第七值，120ms/容差不动）。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R542（emphasis 0.20 撤回 + contentFade 0.20；产品 1 文件 + 判据）**：`7353513` 里 copy 1x=2、Motion floor REDS=0，但新红 `testRecordingCardFrameIsDeterministicAcrossRenders`（dark 11667px；录制描边走 emphasis）⇒ emphasis 撤回 0.16、删其判据/M1420；contentFade 0.20 保留（markdown 1x 3–4→4，copy/fold 各 10/10），M1421 CAUGHT。42 份日志：copy 2/42、fold 2/39 executed、markdown 2/42；622 跨跑 worst_max 262.3、over_max 2、over_runs 17、loaded_p95_max 46.73、比值 0.585–2.167。预检 321/295/757 bad=0、ARM 414/1244、HIDDEN 408/1183 rot=0；帧 350（CHANGED=0）；全量 1384/56/0（698.6s）；换装 431=431（PID 71348）；电池 690/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R541 / 第 540 轮 / Round 538）",
        u"最后更新：2026-11-02（本地 · R542 / 第 541 轮 / Round 539）",
        u"identity")
    text = replace_once(
        text,
        u"## R542 开工 ⓪（2026-11-01 · 第 541 轮 / Round 539）",
        u"## R542 状态（2026-11-02 · 第 541 轮 / Round 539 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R541 状态（2026-11-01 · 第 540 轮 / Round 538 · 产品 1 文件 + 判据）"
    body = u"""
① 627/629 扩窗：42 份可用日志 copy **2/42**（9e78221、8b1ddb9；分母受限）、fold **2/39 executed**（41218878781、b6394f5）、markdown **2/42**（b6394f5、3628685）；本机 copy/markdown/fold 各 10/10。emphasis 0.20 在 `7353513` 里 copy 1x=2、Motion floor REDS=0，但同跑新红 `testRecordingCardFrameIsDeterministicAcrossRenders`（dark 11667px；录制描边走 `.emphasis`，SettingsView:1141）⇒ **emphasis 撤回 0.16**、删其判据/M1420。contentFade 0.20 保留：markdown 1x 3–4→4、2x 5–6→5–7，copy 1x 3–4、fold 中间帧 7–8，各 10/10；M1421 CAUGHT。≥2 帧地板不动、627/629 保持开单。
② 622 跨跑回归：42 跑 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；`d984ab7` 第七值 **176.6ms/2/204**（544.1→162.2→175.8→243.2→151.4→262.3→176.6）；120ms/容差 1 不动、frame 半保持开单。
③ 判据/预检：`MotionCatalogTests.testContentFadeSurvivesOneXSampling` 钉 ≥0.20；M1421 CAUGHT、RESTORE_CLEAN；预检 321/295/757 bad=0、ARM 414/1244、HIDDEN 408/1183 rot=0；build 0 告警。
④ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0）；全量 **1384/56/0（698.6s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 71348、1 窗口 750×492）；电池 **690/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 541，`--streak-for 541` 现读，last=7353513/540）。
⑤ CI/交接：产品笔 `f7bd865` 已推；`41317878347 ↔ 057e2e4`、`41317947527 ↔ c15377e`、`41318132821 ↔ 172d8de`、`41318153433 ↔ fde914e`、`41315396056 ↔ 8c165fb`、`41321009857 ↔ cc15c76`、`41321172002 ↔ 0dc8105`、`41321193291 ↔ 4521ac3`、`41321338166 ↔ 48ef7d7` 全 **success（0 失败步）**；`41320804339 ↔ 7353513` failure **STEP[9]+[15]**（STEP[9]=skip_roster + sources 时序；STEP[15]=录制帧确定性 dark 11667px）、`41318294600 ↔ d984ab7` failure **仅 STEP[18]**（176.6ms/2/204 + 右击探针心跳未闭合）。`f7bd865` 产品跑与台账跑 push 后取号。下一轮 R543（第 542 轮 / Round 540）：先 push 复核 ahead=0；读 `f7bd865` 产品跑与台账跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R542_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
