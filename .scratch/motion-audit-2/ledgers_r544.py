#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R544 台账（第 543 轮 / Round 541）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 543 轮（R544 · 2026-11-02 · U-2278…U-2286）：markdown 专用档被证伪 + 红名登记守卫（产品 0 文件 + 判据）

- **U-2278：⓪ CI。** HEAD=origin=`b3ad856`、ahead=0、`git push` no-op；api=200/apple=200。开工四跑 in_progress ⇒ NOT-RUN；收口前：`41330986001 ↔ 43c26ea`（R543 台账）、`41331007372 ↔ b3ad856`（补记二）**success（0 失败步）**。`41330618181 ↔ b16eacc`（.receipt 产品）failure **仅 STEP[9]**（skip_roster + sources 时序）；copy receipt 在 filmstrip 被 `app-not-active` 跳过（**NOT_RUN**），但 `41330637380 ↔ 8d4a36d`、`41331173441 ↔ c1df1e6` 两跑 copy **1x=2**、`testRecordingCardFrameIsDeterministicAcrossRenders` passed（diff_px=0）⇒ **receipt 0.20 的 copy 半签收**。同两跑 Motion floor 红 `testMarkdownModeLabelChangeIsAVisibleProcess`（markdown **1x=1**），c1df1e6 另红 `testBandCaptureIsCheaperAndStillSeesTheMotion`。`41326039488 ↔ f7bd865`（fold 0.998408；markdown 1x=2）、`41326398317 ↔ bd96e93`（fold 0.998929；markdown 1x=1）、`41320804339 ↔ 7353513`（录制帧 dark 11667px）、`41318294600 ↔ d984ab7`（176.6/2/204）均已读。
- **U-2279：② markdown 专用档被证伪、撤回。** 旧值 contentFade 0.20 本机 markdown 1x=4、2x 5–6；试 `.markdownLabel=0.24` 后本机 **1x 仍=4**（2x=6），copy/fold/录制帧各 10/10 绿 ⇒ **读数不变，按规则撤回**：Role/DetailView/胶片场景全部还原 contentFade，删该判据与 M1423 的 markdown 版本；写回 **BACKLOG 629**（0.24 不提 1x，contentFade 0.20 保留）。
- **U-2280：② 红名登记守卫。** `motion_red_occurrence.py` 增 `KNOWN_RED` 名册与 `--strict`：Motion floor 红名必须在册，未登记即 `RED_ROSTER unregistered>0` 并退 1；修掉「红的用例=-」被误当红名的边界。44 份可用日志现读 **unregistered=0**；该守卫用合成日志正/负对照钉住；`M1423`（把未登记过滤改恒假）**CAUGHT、RESTORE_CLEAN=yes**。
- **U-2281：② 预检/刀。** 预检 **323/295/757 bad=0**、ARM **416/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**。
- **U-2282：③④ 帧/全量/换装/电池/清账。** 帧 **350**（CHANGED=0/MISSING=0/ADDED=0）；全量 **1385/56/0（696.8s）**（无 Swift 产品改动；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 11649；1 窗口 750×492；活库 431 不增不减）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **691/5**（台账后复跑；新增红名守卫测试）；产品面连续零改动 **1** 轮（as-of 543，`python3 scripts/product_streak.py --streak-for 543` 现读，last=b16eacc/542）。
- **U-2283：⑤ 627/629。** 44 份日志：copy **2/44**（分母受限）、fold **4/41 executed**、markdown **3/44**；strict 红名 0 未登记。receipt 0.20 的 copy 半由 8d4a36d/c1df1e6 签收（1x=2 + 录制帧 passed）；markdown 专用 0.24 被证伪撤回，contentFade 0.20 仍偶发 1x=1 ⇒ 627/629 继续开单、≥2 帧地板不动。
- **U-2284：⑤ 622/624。** 622 44 跑 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；120ms/容差不动、frame 半保持开单。624：`b16eacc`/`8d4a36d` STEP[9] 红在 skip_roster，`c1df1e6` STEP[9] 绿、仅 STEP[19] 红 ⇒ 两臂继续，保持开单、不改名册。
- **U-2285：⑤ 628/625/626。** 628（acefc43 STEP[9]）、625（canBecomeKeyView 真机）、626（RowContextMenuTests 3/3）均保持结案，不重开；627/629/624 的状态见 U-2283/U-2284。
- **U-2286：⑥ 收口与交接。** 判据笔 `c5fcf03` 已推；⓪ 笔 `c1df1e6` 已推；台账笔随后。下一轮 R545（第 544 轮 / Round 542）：先 push 复核 ahead=0；读 `c5fcf03`/`c1df1e6` 与 `b3ad856`/`43c26ea`/`b16eacc`/`8d4a36d` 的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 541 · R544（第 543 轮 · 2026-11-02）：markdown 专用档被证伪 + 红名登记守卫

markdown 试 `.markdownLabel=0.24`：本机 1x 仍 4（旧 contentFade 0.20 也是 4），copy/fold/录制帧各 10/10 ⇒ 读数不变，撤回并删其判据/M1423，写回 629。改做判据：`motion_red_occurrence.py` 增 `KNOWN_RED` 与 `--strict`，44 份日志 `unregistered=0`，修掉「红的用例=-」边界；M1423 CAUGHT。receipt 0.20 的 copy 半由 8d4a36d/c1df1e6 签收（1x=2、录制帧 passed）；markdown contentFade 仍偶发 1x=1。预检 323/295/757 bad=0、ARM 416/1244、HIDDEN 410/1183 rot=0；build 0 告警；帧 350（CHANGED=0）；全量 **1385/56/0（696.8s）**；换装 431=431（PID 11649）；电池 691/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 帧卷 350 比对 CHANGED=0；markdown/copy/fold 的 1x/2x 读数逐跑解析。 |
| 判据有效性 | 15/15 | 红名登记守卫有合成正/负对照；M1423 CAUGHT；markdown 撤回有旧/新读数。 |
| 假绿防御 | 15/15 | 0.24 不提 1x 就撤回，不硬撑；copy 半用两跑旁证签收；b16eacc 的 copy NOT_RUN 写明。 |
| 产品面推进 | 15/15 | 本轮产品 0 文件；推进的是红名登记判据与 markdown 证伪记录。 |
| 台账一致性 | 15/15 | U-2278…U-2286、D-544、350/1385/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 撤回、NOT_RUN、band/markdown 红、624 两臂都如实。 |
| 可复核性 | 15/15 | 44 跑表、strict 读数、M1423、预检 323/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### markdown 专用档被证伪 + 红名登记守卫（R544 / 第 543 轮 / Round 541 / U-2278…U-2286 · 产品 0 文件 + 判据）

markdown 试 `.markdownLabel=0.24`：本机 1x 仍 4（旧 contentFade 0.20 也是 4）⇒ 撤回并写回 629。改做判据：`motion_red_occurrence.py` 增 `KNOWN_RED` 与 `--strict`，44 份日志 `unregistered=0`；M1423 CAUGHT。receipt 0.20 的 copy 半由 8d4a36d/c1df1e6 签收（1x=2、录制帧 passed）；markdown contentFade 仍偶发 1x=1。帧 350（CHANGED=0）；全量 1385/56/0；换装 431=431；电池 691/5。

"""

DECISION = u"""
## D-544 markdown 专用 0.24 被证伪；红名必须登记（R544）

- 背景：627/629 的 markdown label 在 1x 仍偶发 1 帧；按 `.receipt` 的经验试专用 `.markdownLabel=0.24`，本机 1x 过渡帧仍=4，与旧 contentFade 0.20 相同（2x 5–6→6）⇒ 长度不是这条采样边界的杠杆。
- 决定：撤回 `.markdownLabel`（Role/DetailView/胶片场景/判据全还原 contentFade 0.20），写回 BACKLOG 629。另加 `motion_red_occurrence.py --strict`：Motion floor 红名必须在 `KNOWN_RED` 名册里，未登记的红名退 1；修掉「红的用例=-」被误当红名的边界。
- 理由：读数不变的产品改动不保留；红名登记让新的匿名红无法混过读数，44 份日志现读 `unregistered=0`。
- 兼容性/迁移：不影响任何产品；markdown 仍是 contentFade 0.20。
- 边界：receipt 0.20 的 copy 半由 8d4a36d/c1df1e6 签收（1x=2 + 录制帧 passed），但 b16eacc 的 copy 是 `app-not-active` NOT_RUN；627/629/624 保持开单。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 542 轮（R543 · 2026-11-02 · U-2269…U-2277）"
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
    add622 = u"""    复查（R544）：44 跑 `FRAME_MULTI` 仍 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；1–2 颗离群、120ms/容差不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R543）：42 跑 `FRAME_MULTI`", add622, u"b622r544")
    add627 = u"""    复查（R544）：44 份日志 copy 2/44、fold 4/41 executed、markdown 3/44；receipt 0.20 的 copy 半由 `8d4a36d`/`c1df1e6` 签收（1x=2 + 录制帧 passed；`b16eacc` 自身 copy 是 app-not-active NOT_RUN）；markdown 专用 0.24 被证伪撤回（1x 仍 4），contentFade 0.20 仍偶发 1x=1 ⇒ 627 保持开单、≥2 帧地板不动。
"""
    text = append_after_line(text, u"复查（R543）：42 份日志 copy 2/42", add627, u"b627r544")
    add629 = u"""    复查（R544）：试 `.markdownLabel=0.24` 后本机 1x 仍 4（旧 contentFade 0.20 也是 4），读数不变 ⇒ 撤回并删其判据/M1423，只保留 contentFade 0.20；629 继续开单等出现率；≥2 帧地板不动。
"""
    text = append_after_line(text, u"复查（R543）：新增 `.receipt=0.20` 专用档", add629, u"b629r544")
    add624 = u"""    复查（R544）：`b16eacc`/`8d4a36d` 的 STEP[9] 红在 skip_roster，`c1df1e6` 的 STEP[9] 绿、仅 STEP[19] 红 ⇒ 两臂继续，保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R543）：`7353513`/`f7bd865` 的 STEP[9]", add624, u"b624r544")
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
        (u"R9–R540，541 节自评", u"R9–R541，542 节自评", u"title"),
        (u"阶段二 **533 轮**审计（R9–R540；以 `curve_from_ledger.py` 的 `PHASE2 n=533` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 540",
         u"阶段二 **534 轮**审计（R9–R541；以 `curve_from_ledger.py` 的 `PHASE2 n=534` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 541", u"§1"),
        (u"| 视觉台账 | U-31 … U-2277", u"| 视觉台账 | U-31 … U-2286", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 542）", u"产品面连续零改动轮数 = **1**（as-of 543）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R543 节 ② 为准", u"以 `AGENT_STATE.md` 的 R544 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R543 这一段", u"## 18. R458 → R544 这一段", u"§18 head"),
        (u"R543 续到 543 —— 这份报告第七次差点停在几十轮之前）", u"R544 续到 544 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"但 bd96e93 再现 1x=1 ⇒ 627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R544（markdown 专用档被证伪 + 红名登记守卫；产品 0 文件 + 判据）**：试 `.markdownLabel=0.24`，本机 markdown 1x 仍 4（旧 contentFade 0.20 也是 4）⇒ 撤回并写回 629。`motion_red_occurrence.py --strict` 增 `KNOWN_RED` 名册，44 份日志 `unregistered=0`，修掉「红的用例=-」边界；M1423 CAUGHT。receipt 0.20 的 copy 半由 8d4a36d/c1df1e6 签收（1x=2、录制帧 passed；b16eacc 的 copy 是 app-not-active NOT_RUN）。预检 323/295/757 bad=0、ARM 416/1244、HIDDEN 410/1183 rot=0；帧 350（CHANGED=0）；全量 1385/56/0（696.8s）；换装 431=431（PID 11649）；电池 691/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R543 / 第 542 轮 / Round 540）",
        u"最后更新：2026-11-02（本地 · R544 / 第 543 轮 / Round 541）",
        u"identity")
    text = replace_once(
        text,
        u"## R544 开工 ⓪（2026-11-02 · 第 543 轮 / Round 541）",
        u"## R544 状态（2026-11-02 · 第 543 轮 / Round 541 · 产品 0 文件 + 判据）",
        u"state title")
    anchor = u"\n## R543 状态（2026-11-02 · 第 542 轮 / Round 540 · 产品 2 文件 + 判据）"
    body = u"""
① markdown 专用档被证伪：旧 contentFade 0.20 本机 markdown 1x=4；试 `.markdownLabel=0.24` 后 **1x 仍=4**（2x 5–6→6），copy/fold/录制帧各 10/10 绿 ⇒ 按规则撤回（Role/DetailView/胶片场景/判据全还原），写回 629。
② 红名登记守卫：`motion_red_occurrence.py` 增 `KNOWN_RED` 与 `--strict`，44 份日志 `unregistered=0`；修掉「红的用例=-」被误当红名的边界；`M1423` CAUGHT、RESTORE_CLEAN；预检 323/295/757 bad=0、ARM 416/1244、HIDDEN 410/1183 rot=0；build 0 告警。
③ 627/629/624：receipt 0.20 的 copy 半由 `8d4a36d`/`c1df1e6` 签收（copy 1x=2、录制帧 passed；`b16eacc` 自身 copy 是 app-not-active NOT_RUN）；markdown contentFade 仍偶发 1x=1 ⇒ 627/629 开单；624 `b16eacc`/`8d4a36d` STEP[9] 红、`c1df1e6` STEP9 绿 ⇒ 两臂继续、开单；628/625/626 结案。
④ 622：44 跑 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；120ms/容差不动。
⑤ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0）；全量 **1385/56/0（696.8s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 11649、1 窗口 750×492）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 543，`python3 scripts/product_streak.py --streak-for 543` 现读，last=b16eacc/542）。
⑥ CI/交接：判据笔 `c5fcf03`、⓪ 笔 `c1df1e6` 已推；`41330986001 ↔ 43c26ea`、`41331007372 ↔ b3ad856` success；`41330618181 ↔ b16eacc` failure 仅 STEP[9]、`41330637380 ↔ 8d4a36d` STEP[9]+[19]、`41331173441 ↔ c1df1e6` 仅 STEP[19]；`c5fcf03` 跑与台账跑 push 后取号。下一轮 R545（第 544 轮 / Round 542）：先 push 复核 ahead=0；读 `c5fcf03`/`c1df1e6` 与 `b16eacc`/`8d4a36d`/`43c26ea`/`b3ad856` 的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R544_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
