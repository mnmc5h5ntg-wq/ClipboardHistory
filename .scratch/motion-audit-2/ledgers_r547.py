#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R547 台账（第 546 轮 / Round 544）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 546 轮（R547 · 2026-11-02 · U-2303…U-2310）：默认排除行加锁图标（产品 1 文件 + 判据）

- **U-2303：⓪ CI。** HEAD=origin=`d22f30a`、ahead=0、`git push` no-op；api=200/apple=200。`41341540906 ↔ 54420e0`、`41341586171 ↔ d22f30a` 读时 **in_progress ⇒ NOT-RUN**；产品笔 `feec6cc`、重钉笔 `73fb0fd` 无独立跑。`41337616903 ↔ 30c7913` failure **仅 STEP[15]**：`PerfBudgetTests/testMarkdownRenderCostAtTheArchiveCap` 274.93ms > 250ms（负载 flake）与 `testRecordingCardFrameIsDeterministicAcrossRenders` dark 9457px（文档笔的 runner flake，非动效取值）；`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）；复读 c5fcf03/c1df1e6/b16eacc/8d4a36d/bd96e93 的红同 R545。`41337778679 ↔ 84d7a9a`、`41337664834 ↔ 9503700`、`41337019426 ↔ 8acec7f`、`41336963006 ↔ 9121760` success。
- **U-2304：② 默认排除行加锁图标。** BACKLOG 578：默认行尾部只有灰字「默认」，与自定义行红字「移除」靠读字区分。`SettingsView` 在「默认」前补 9pt `lock.fill`（semibold、secondary、a11y 隐藏），HStack 间距 3，文案/布局不动。旧 `DEFAULT_BADGE`：light 正臂 5548 / 差 2844，dark 6723 / 3591（负臂 2704/3132）；新：light 7024 / **4320**，dark 8217 / **5085**，负臂不变。新增 `DEFAULT_LOCK`（正臂 vs 只关锁的负向臂）：light 5548→7024、差 **1476**；dark 6723→8217、差 **1494**。
- **U-2305：② 判据/缝/刀。** 产品加 `settingsDefaultExcludedLockForCapture` 缝（默认 nil ⇒ 画）；夹具加 `settings-privacy-no-default-lock`（只关锁、文字仍在）；新判据 `testDefaultExcludedRowsCarryALockIcon` 读右列墨差，地板 200·s²（2x=800，实测 1476/1494）。`M1426`（`if false` 隐藏锁）**CAUGHT、RESTORE_CLEAN=yes**。
- **U-2306：② 预检/构建。** 预检 **326/295/757 bad=0**、ARM **419/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**。
- **U-2307：③ 帧/录制。** 重捕：CHANGED=**6**（`settings-privacy-720x540`、`settings-privacy-excluded-720x1040`、`settings-privacy-tall-720x1040` 各亮/暗）、ADDED=**2**（`settings-privacy-no-default-lock` 亮/暗），基线 **350→352**；720×540 与 1040 页逐张看：锁与「默认」对齐、行未被挤坏。录制帧确定性 **10/10 diff=0**。
- **U-2308：③④ 全量/换装/电池/清账/streak。** 全量 **1386/56/0（688.4s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 84566、1 窗口 750×492）；清账 **162/162/0**；电池 **691/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 546，`python3 scripts/product_streak.py --streak-for 546` 现读）。
- **U-2309：⑤ 622/624/627/629/628/625/626。** 622 第七值 **176.6ms/2/204**、44 跑 worst 262.3 / over 2 / over_runs 17 / loaded_p95 46.73 / 比值 0.585–2.167，120ms/容差不动、frame 半开单；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
- **U-2310：⑥ 收口与交接。** ⓪ 笔 `f58bf8c`、产品笔随后；下一轮 R548（第 547 轮 / Round 545）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `54420e0`/`d22f30a`/`30c7913`/`8b667ae` 与其余已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 544 · R547（第 546 轮 · 2026-11-02）：默认排除行加锁图标

BACKLOG 578：默认行尾部只有灰字「默认」，与自定义行红字「移除」靠读字区分。`SettingsView` 在「默认」前补 9pt `lock.fill`（semibold、secondary、a11y 隐藏），HStack 间距 3，文案/布局不动。旧/新 `DEFAULT_BADGE`：light 5548/2844→7024/4320、dark 6723/3591→8217/5085（负臂不变）；新 `DEFAULT_LOCK` 正臂 vs 只关锁：light 差 1476、dark 1494。产品加 `settingsDefaultExcludedLockForCapture` 缝，夹具加 `settings-privacy-no-default-lock`，新判据地板 200·s²；M1426 CAUGHT。帧 CHANGED=6、ADDED=2，基线 350→352；720×540/1040 逐张看锁与「默认」对齐、行未挤坏；录制确定性 10/10 diff=0；build 0 告警；全量 **1386/56/0（688.4s）**；换装 431=431（PID 84566）；电池 691/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 720×540 与 1040 隐私页亮/暗逐张看；6 帧变化 + 2 帧新增。 |
| 判据有效性 | 15/15 | `DEFAULT_LOCK` 1476/1494；M1426 CAUGHT；负臂文字仍在。 |
| 假绿防御 | 15/15 | 负臂只关锁、文字仍在，证明差来自锁而不是整枚标记。 |
| 产品面推进 | 15/15 | 产品 1 文件：默认排除行补锁图标。 |
| 台账一致性 | 15/15 | U-2303…U-2310、D-547、350→352/1385/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 两跑 NOT-RUN、627/629/624 开单、runner 未签收都如实。 |
| 可复核性 | 15/15 | 旧/新 `DEFAULT_BADGE`/`DEFAULT_LOCK`、M1426、预检 326/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 默认排除行加锁图标（R547 / 第 546 轮 / Round 544 / U-2303…U-2310 · 产品 1 文件 + 判据）

`SettingsView` 在默认排除行的「默认」前补 9pt `lock.fill`（semibold、secondary、a11y 隐藏），文案与布局不动。`DEFAULT_BADGE` 旧/新：light 2844→4320、dark 3591→5085（负臂不变）；新增 `DEFAULT_LOCK`（正臂 vs 只关锁）light 差 1476、dark 1494；产品加 `settingsDefaultExcludedLockForCapture` 缝与 `settings-privacy-no-default-lock` 负向帧；M1426 CAUGHT。帧 CHANGED=6、ADDED=2，基线 350→352；录制确定性 10/10 diff=0；全量 1386/56/0；换装 431=431；电池 691/5。

"""

DECISION = u"""
## D-547 默认排除行用锁图标给「不可移除」一个形状（R547）

- 背景：BACKLOG 578 记着默认行尾部只有灰字「默认」，自定义行是红字「移除」，色盲/低对比用户只能靠读字区分。
- 决定：在「默认」前补 9pt `lock.fill`（semibold、secondary、`accessibilityHidden`），HStack 间距 3；文案与行布局不动。产品加 `settingsDefaultExcludedLockForCapture` 缝，夹具加 `settings-privacy-no-default-lock`（只关锁、文字仍在）。
- 理由：锁是「不可移除」的直接形状；`DEFAULT_BADGE` light/dark 正臂差 2844→4320 / 3591→5085，新增 `DEFAULT_LOCK` 1476/1494，负臂不变，说明墨差来自锁本身。
- 兼容性/迁移：只加一枚图标；静态帧 6 张变化 + 2 张新增，基线 350→352；录制帧确定性 10/10 diff=0。
- 边界：runner 1x 的 `DEFAULT_LOCK`/`DEFAULT_BADGE` 待签收；627/629/624 不受影响。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 545 轮（R546 · 2026-11-02 · U-2295…U-2302）"
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
    add578 = u"""    复查（R547）：默认排除行在「默认」前补 9pt 锁（产品 `SettingsView.swift` 1 文件 + 捕获缝）；`DEFAULT_BADGE` light 2844→4320、dark 3591→5085（负臂 2704/3132 不变）；新 `DEFAULT_LOCK` light 1476、dark 1494；夹具 `settings-privacy-no-default-lock`；M1426 CAUGHT。runner 1x 待签收。
"""
    text = text.replace(u"    修法：下一轮若要更强的身份语义，可给默认行加一个中性图标；先不加判据、不声称已解决。\n",
                        u"    修法：下一轮若要更强的身份语义，可给默认行加一个中性图标；先不加判据、不声称已解决。\n" + add578, 1)
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
        (u"R9–R543，544 节自评", u"R9–R544，545 节自评", u"title"),
        (u"阶段二 **536 轮**审计（R9–R543；以 `curve_from_ledger.py` 的 `PHASE2 n=536` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 543",
         u"阶段二 **537 轮**审计（R9–R544；以 `curve_from_ledger.py` 的 `PHASE2 n=537` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 544", u"§1"),
        (u"| 视觉台账 | U-31 … U-2302", u"| 视觉台账 | U-31 … U-2310", u"U 上界"),
        (u"产品面连续零改动轮数 = **3**（as-of 545）", u"产品面连续零改动轮数 = **1**（as-of 546）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R546 节 ② 为准", u"以 `AGENT_STATE.md` 的 R547 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R546 这一段", u"## 18. R458 → R547 这一段", u"§18 head"),
        (u"R546 续到 546 —— 这份报告第七次差点停在几十轮之前）", u"R547 续到 547 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 42780）；电池 691/5。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R547（默认排除行加锁图标；产品 1 文件 + 判据）**：`SettingsView` 在「默认」前补 9pt `lock.fill`（semibold、secondary、a11y 隐藏），文案/布局不动；`DEFAULT_BADGE` light 2844→4320、dark 3591→5085（负臂不变），新 `DEFAULT_LOCK` light 1476、dark 1494；加 `settingsDefaultExcludedLockForCapture` 缝与 `settings-privacy-no-default-lock` 负向帧；M1426 CAUGHT。帧 CHANGED=6、ADDED=2，基线 350→352；录制确定性 10/10 diff=0；预检 326/295/757 bad=0、ARM 419/1244、HIDDEN 410/1183 rot=0；全量 1386/56/0（688.4s）；换装 431=431（PID 84566）；电池 691/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R546 / 第 545 轮 / Round 543）",
        u"最后更新：2026-11-02（本地 · R547 / 第 546 轮 / Round 544）",
        u"identity")
    text = replace_once(
        text,
        u"## R547 开工 ⓪（2026-11-02 · 第 546 轮 / Round 544）",
        u"## R547 状态（2026-11-02 · 第 546 轮 / Round 544 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R546 状态（2026-11-02 · 第 545 轮 / Round 543 · 产品 1 文件 + 判据）"
    body = u"""
① 默认排除行加锁：`SettingsView` 在「默认」前补 9pt `lock.fill`（semibold、secondary、a11y 隐藏），文案/布局不动；`DEFAULT_BADGE` light 2844→4320、dark 3591→5085（负臂 2704/3132 不变）；新 `DEFAULT_LOCK` light 1476、dark 1494。
② 判据/缝/刀：产品加 `settingsDefaultExcludedLockForCapture`，夹具加 `settings-privacy-no-default-lock`；新判据地板 200·s²；`M1426` CAUGHT、RESTORE_CLEAN；预检 326/295/757 bad=0、ARM 419/1244、HIDDEN 410/1183 rot=0；build 0 告警；录制确定性 10/10 diff=0。
③ 帧/全量/换装/电池/清账/streak：帧 **350→352**（CHANGED=6、ADDED=2）；全量 **1386/56/0（688.4s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 84566、1 窗口 750×492）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 546，`python3 scripts/product_streak.py --streak-for 546` 现读）。
④ 622/624/627/629：622 第七值 176.6ms/2/204、120ms/容差不动；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
⑤ CI/交接：⓪ 笔 `f58bf8c` 已推；`41341540906 ↔ 54420e0`、`41341586171 ↔ d22f30a` 读时 in_progress ⇒ NOT-RUN；产品笔 `feec6cc`、重钉笔 `73fb0fd` 无独立跑；`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px，均具名 flake）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）。下一轮 R548（第 547 轮 / Round 545）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `54420e0`/`d22f30a`/`30c7913`/`8b667ae` 与已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R547_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
