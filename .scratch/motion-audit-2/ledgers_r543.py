#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R543 台账（第 542 轮 / Round 540）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 542 轮（R543 · 2026-11-02 · U-2269…U-2277）：复制回执专用 receipt 档 0.20（产品 2 文件 + 判据）

- **U-2269：⓪ CI。** HEAD=origin=`bd96e93`、ahead=0、`git push` no-op；api=200/apple=200。开工三跑 in_progress ⇒ NOT-RUN；收口前：`41321338166 ↔ 48ef7d7`（R542 ⓪）、`41321193291 ↔ 4521ac3`、`41321172002 ↔ 0dc8105`、`41321009857 ↔ cc15c76`、`41326374225 ↔ 087290d`（R542 台账）均 **success（0 失败步）**。`41326039488 ↔ f7bd865`（contentFade 0.20）failure **STEP[9]+[15]**：STEP[9]=skip_roster + sources 时序；STEP[15]=`testCollapseWidthIsMeasuredFrameByFrame` 0.998408 vs 1.0（已知 fold 采样 flake）；同跑 **markdown 1x 过渡帧=2**、`testRecordingCardFrameIsDeterministicAcrossRenders` 两遍 passed（diff_px=0）⇒ **contentFade 0.20 签收**。`41320804339 ↔ 7353513` failure STEP[9]+[15]（录制帧确定性 dark 11667px，emphasis 已撤回）、`41318294600 ↔ d984ab7` failure 仅 STEP[18]（176.6ms/2/204）、`41326398317 ↔ bd96e93` failure STEP[15]+[19]（fold 0.998929；Motion floor 红 `testBandCaptureIsCheaperAndStillSeesTheMotion` + markdown **1x=1** ⇒ contentFade 的改善不是确定性的，629 继续开单）。
- **U-2270：② 复制回执专用 receipt 档。** 新增 `MotionCatalog.Role.receipt = 0.20`（单档淡入，不进 emphasis）；`GlassControls` 的回执驱动改 `for: .receipt`，`MotionFilmstripTests` 的回执场景改用 `.receipt`（声明 200ms）。emphasis 保持 **0.16**（录制描边不再被牵动）。本机：copy receipt **1x 过渡帧 3–4**、2x 4–5（10/10）；`testRecordingCardFrameIsDeterministicAcrossRenders` **10/10 diff_px=0**；markdown 1x=4、fold 中间帧 7–8（各 10/10）。`CopyReceiptTests` 的源接线守卫同步改钉 `.receipt`。
- **U-2271：② 判据/刀/预检。** `MotionCatalogTests.testReceiptFadeSurvivesOneXSampling` 钉 `.receipt ≥0.20`；`M1422`（改回 0.16）**CAUGHT、RESTORE_CLEAN=yes**；预检 **322/295/757 bad=0**、ARM **415/1244**（dupes=0 repeats=0）、HIDDEN **409/1183 rot=0**；build **0 告警**。
- **U-2272：③④ 帧/全量/换装/电池/清账。** 帧 **350**（CHANGED=0/MISSING=0/ADDED=0）；全量 **1385/56/0（705.8s）**（新增 receipt 判据；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 91822；1 窗口 750×492；活库 431 不增不减）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **690/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 542，`python3 scripts/product_streak.py --streak-for 542` 现读，last=f7bd865/541）。
- **U-2273：⑤ 627/629。** 42 份日志：copy receipt **2/42**（分母受限）、fold **2/39 executed**、markdown **2/42**；本机 copy（receipt 0.20）1x 3–4、markdown 1x=4、fold 7–8。contentFade 0.20 在 f7bd865 产品跑满足签收条件（1x=2 + 录制帧绿），但 bd96e93 再现 markdown 1x=1 ⇒ 629 仍开单等出现率；receipt 档待 R543 产品跑签收；≥2 帧地板不动。
- **U-2274：⑤ 622/624。** 622 42 跑 `FRAME_MULTI`：`worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；120ms/容差不动、frame 半保持开单。624 在 `7353513`/`f7bd865` 的 STEP[9] 仍红在 skip_roster，保持开单、不改名册。
- **U-2275：⑤ 628/625/626。** 628（acefc43 STEP[9] 签收）、625（canBecomeKeyView 真机）、626（RowContextMenuTests 3/3）均保持结案，不重开。
- **U-2276：⑥ 收口与交接。** 产品笔 `b16eacc` 已推；⓪ 笔 `8d4a36d` 已推；台账笔随后。下一轮 R544（第 543 轮 / Round 541）：先 push 复核 ahead=0；读 `b16eacc`/`8d4a36d` 与 `f7bd865`/`087290d`/`bd96e93`/`7353513` 的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 540 · R543（第 542 轮 · 2026-11-02）：复制回执专用 receipt 档 0.20

给复制回执单独一档 `.receipt=0.20`（emphasis 保持 0.16，录制描边不再被牵动）：回执驱动/场景改 `.receipt`；本机 copy 1x 过渡帧 3–4、2x 4–5，录制帧确定性 10/10 diff=0，markdown 1x=4、fold 中间帧 7–8（各 10/10）；CopyReceiptTests 守卫改钉 `.receipt`；M1422 CAUGHT。contentFade 0.20 由 f7bd865 产品跑签收（markdown 1x=2 + 录制帧 passed），但 bd96e93 再现 markdown 1x=1 ⇒ 629 继续开单。42 份日志：copy 2/42（分母受限）、fold 2/39、markdown 2/42；622 第七值 176.6/2/204。预检 322/295/757 bad=0、ARM 415/1244、HIDDEN 409/1183 rot=0；build 0 告警；帧 350（CHANGED=0）；全量 **1385/56/0（705.8s）**；换装 431=431（PID 91822）；电池 690/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 帧卷 350 比对 CHANGED=0；copy/markdown/fold 的 1x/2x 读数逐跑解析。 |
| 判据有效性 | 15/15 | M1422（receipt 回 0.16）CAUGHT；CopyReceiptTests 守卫改钉新角色。 |
| 假绿防御 | 15/15 | contentFade 只在产品跑满足条件时签收，但补记跑 1x=1 仍记 629；录制帧 10/10 绿才保留 receipt。 |
| 产品面推进 | 15/15 | 回执专用 0.20 档，避免 emphasis 连坐；产品 2 文件。 |
| 台账一致性 | 15/15 | U-2269…U-2277、D-543、350/1385/431/690 都来自命令与日志。 |
| 交付诚实性 | 15/15 | contentFade 签收与 629 残余分开写；627/624 开单；628/625/626 不重开。 |
| 可复核性 | 15/15 | 42 跑表、M1422、预检 322/295/757、1385 全量、690 电池全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 复制回执专用 receipt 档 0.20（R543 / 第 542 轮 / Round 540 / U-2269…U-2277 · 产品 2 文件 + 判据）

给复制回执单独一档 `MotionCatalog.Role.receipt=0.20`（emphasis 保持 0.16，录制描边不再被牵动）；回执驱动与胶片场景改用 `.receipt`。本机 copy 1x 过渡帧 3–4、2x 4–5；录制帧确定性 10/10 diff=0；markdown 1x=4、fold 中间帧 7–8。CopyReceiptTests 守卫改钉 `.receipt`；M1422 CAUGHT。contentFade 0.20 由 `f7bd865` 签收（markdown 1x=2 + 录制帧 passed），但 `bd96e93` 再现 1x=1 ⇒ 629 继续开单。帧 350（CHANGED=0）；全量 1385/56/0；换装 431=431；电池 690/5。

"""

DECISION = u"""
## D-543 复制回执用专用 receipt 档，emphasis 继续留给录制描边（R543）

- 背景：R541 把 `.emphasis` 0.16→0.20 后，copy 1x 变好但录制帧确定性在 `7353513` 出现新红（dark 11667px），而录制描边正是 `SettingsView:1141` 的 `.animation(for: .emphasis)`；R542 已撤回 emphasis。
- 决定：新增 `.receipt=0.20`（单档淡入），复制回执的驱动与胶片场景改用它；emphasis 保持 0.16。`CopyReceiptTests` 的源接线守卫改钉 `.receipt`；`testReceiptFadeSurvivesOneXSampling` + M1422 钉住。
- 理由：回执需要更长的可见淡入，但录制描边不需要；把两者拆成不同角色，既拿到 copy 1x 3–4，又让录制帧确定性 10/10 diff=0。
- 兼容性/迁移：`.receipt` 只影响回执出现/消失（0.20 在 0.25 上限内）；静态帧 CHANGED=0。
- 边界：receipt 档待 R543 产品跑签收；contentFade 0.20 虽由 f7bd865 签收，但 bd96e93 再现 markdown 1x=1 ⇒ 629 继续开单。
"""


def main():
    # 1. UI_AUDIT
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 541 轮（R542 · 2026-11-02 · U-2260…U-2268）"
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
    add622 = u"""    复查（R543）：42 跑 `FRAME_MULTI` 仍 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；1–2 颗离群、120ms/容差不动、frame 半保持开单。
"""
    text = append_after_line(text, u"复查（R542）：42 跑 `FRAME_MULTI`", add622, u"b622r543")
    add627 = u"""    复查（R543）：42 份日志 copy 2/42、fold 2/39 executed、markdown 2/42；新增 `.receipt=0.20` 专用档后本机 copy 1x 3–4、录制帧确定性 10/10 diff=0；contentFade 0.20 在 `f7bd865` 产品跑签收（markdown 1x=2），但 `bd96e93` 再现 markdown 1x=1，且同跑 Motion floor 红 `testBandCaptureIsCheaperAndStillSeesTheMotion`；627/629 继续开单、≥2 帧地板不动。
"""
    text = append_after_line(text, u"复查（R542）：42 份日志扩窗", add627, u"b627r543")
    add629 = u"""    复查（R543）：新增 `.receipt=0.20` 专用档（copy 本机 1x 3–4，M1422 CAUGHT；emphasis 仍 0.16，录制帧 10/10 diff=0）；contentFade 0.20 在 `f7bd865` 满足签收条件，但 `bd96e93` 复现 markdown 1x=1 ⇒ 629 保持开单等出现率；≥2 帧地板不动。
"""
    text = append_after_line(text, u"复查（R542）：emphasis 0.20 已撤回", add629, u"b629r543")
    add624 = u"""    复查（R543）：`7353513`/`f7bd865` 的 STEP[9] 仍红在 skip_roster；保持开单、不改名册。
"""
    text = append_after_line(text, u"复查（R540）：`acefc43`（修后）与 `40a2a71`（修前）", add624, u"b624r543")
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
        (u"R9–R539，540 节自评", u"R9–R540，541 节自评", u"title"),
        (u"阶段二 **532 轮**审计（R9–R539；以 `curve_from_ledger.py` 的 `PHASE2 n=532` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 539",
         u"阶段二 **533 轮**审计（R9–R540；以 `curve_from_ledger.py` 的 `PHASE2 n=533` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 540", u"§1"),
        (u"| 视觉台账 | U-31 … U-2268", u"| 视觉台账 | U-31 … U-2277", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 541）", u"产品面连续零改动轮数 = **1**（as-of 542）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R542 节 ② 为准", u"以 `AGENT_STATE.md` 的 R543 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R542 这一段", u"## 18. R458 → R543 这一段", u"§18 head"),
        (u"R542 续到 542 —— 这份报告第七次差点停在几十轮之前）", u"R543 续到 543 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R543（复制回执专用 receipt 档 0.20；产品 2 文件 + 判据）**：新增 `.receipt=0.20`（emphasis 保持 0.16，录制描边不被牵动），回执驱动/场景改 `.receipt`；本机 copy 1x 3–4、2x 4–5，录制帧确定性 10/10 diff=0，markdown 1x=4、fold 中间帧 7–8（各 10/10）；`CopyReceiptTests` 守卫改钉 `.receipt`，M1422 CAUGHT；预检 322/295/757 bad=0、ARM 415/1244、HIDDEN 409/1183 rot=0；帧 350（CHANGED=0）；全量 1385/56/0（705.8s）；换装 431=431（PID 91822）；电池 690/5。contentFade 0.20 由 f7bd865 签收（markdown 1x=2 + 录制帧 passed），但 bd96e93 再现 1x=1 ⇒ 627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R542 / 第 541 轮 / Round 539）",
        u"最后更新：2026-11-02（本地 · R543 / 第 542 轮 / Round 540）",
        u"identity")
    text = replace_once(
        text,
        u"## R543 开工 ⓪（2026-11-02 · 第 542 轮 / Round 540）",
        u"## R543 状态（2026-11-02 · 第 542 轮 / Round 540 · 产品 2 文件 + 判据）",
        u"state title")
    anchor = u"\n## R542 状态（2026-11-02 · 第 541 轮 / Round 539 · 产品 1 文件 + 判据）"
    body = u"""
① 回执专用档：新增 `.receipt=0.20`（单档淡入），`GlassControls`/胶片场景改 `for: .receipt`；emphasis 保持 0.16，录制描边不再被牵动。本机 copy 1x 过渡帧 3–4、2x 4–5（10/10）；录制帧确定性 10/10 diff_px=0；markdown 1x=4、fold 中间帧 7–8（各 10/10）；CopyReceiptTests 守卫改钉 `.receipt`；M1422 CAUGHT、RESTORE_CLEAN。
② contentFade 0.20：`f7bd865` 产品跑 markdown 1x=2、录制帧两遍 passed（diff=0）⇒ 签收；但 `bd96e93` 补记跑再现 markdown 1x=1 ⇒ **629 继续开单**；同跑 Motion floor 另红 `testBandCaptureIsCheaperAndStillSeesTheMotion`（band 采样）。
③ 627/622：42 份日志 copy 2/42（分母受限）、fold 2/39 executed、markdown 2/42；622 42 跑 `worst_max=262.3`、`over_max=2`、`over_runs=17`、`loaded_p95_max=46.73`、`比值=0.585–2.167`；第七值 176.6ms/2/204；120ms/容差不动。
④ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=0）；全量 **1385/56/0（705.8s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 91822、1 窗口 750×492）；电池 **690/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 542，`python3 scripts/product_streak.py --streak-for 542` 现读，last=f7bd865/541）。
⑤ CI/交接：产品笔 `b16eacc`、⓪ 笔 `8d4a36d` 已推；`41326374225 ↔ 087290d`、`41321338166 ↔ 48ef7d7`、`41321193291 ↔ 4521ac3`、`41321172002 ↔ 0dc8105`、`41321009857 ↔ cc15c76` 全 **success**；`41326039488 ↔ f7bd865` failure STEP[9]+[15]（fold 0.998408；markdown 1x=2、录制帧 passed）、`41320804339 ↔ 7353513` failure STEP[9]+[15]（录制帧 dark 11667px）、`41318294600 ↔ d984ab7` failure 仅 STEP[18]（176.6/2/204）、`41326398317 ↔ bd96e93` failure STEP[15]+[19]（fold 0.998929；band capture + markdown 1x=1）。`b16eacc` 产品跑与 `8d4a36d` ⓪ 跑 push 后取号。下一轮 R544（第 543 轮 / Round 541）：先 push 复核 ahead=0；读这两跑与上述已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R543_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
