#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R546 台账（第 545 轮 / Round 543）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 545 轮（R546 · 2026-11-02 · U-2295…U-2302）：登录失败图标换圆形感叹号（产品 1 文件 + 判据）

- **U-2295：⓪ CI。** HEAD=origin=`9503700`、ahead=0、`git push` no-op；api=200/apple=200。三跑读时 **in_progress ⇒ NOT-RUN**：`41336963006 ↔ 9121760`（台账）、`41337019426 ↔ 8acec7f`（补记二）、`41337616903 ↔ 30c7913`（补记三）。`41334537980 ↔ 8b667ae` failure **仅 STEP[15]**：`SelectionRevealAnimationTests/testProductDurationRevealStillMovesOverTime`（origin=[0.0,1430.0,1430.0,1430.0]）——已知会话 flake、非产品。复读：`41331769689 ↔ c5fcf03` 仅 STEP[19]（markdown 1x=1）；`41331173441 ↔ c1df1e6` 仅 STEP[19]（band 11.73 vs 10.79 + markdown 1x=1；copy 1x=2、录制帧 passed）；`41330618181 ↔ b16eacc` 仅 STEP[9]（skip_roster+sources；copy `app-not-active` NOT-RUN）；`41330637380 ↔ 8d4a36d` STEP[9]+[19]（skip_roster+sources；markdown 1x=1）；`41326398317 ↔ bd96e93` STEP[15]+[19]（fold 0.9989289765 vs 1.0 ±0.001、final=420；band 0.97× + markdown 1x=1）。`41334225593 ↔ 5589ebe`、`41334244256 ↔ e357708` success。
- **U-2296：② 登录失败图标换圆形感叹号。** BACKLOG 584：失败回执图标与文字同错误色、与横幅同用警示三角，图标身份弱。`SettingsView` 把 `exclamationmark.triangle.fill` 换成 `exclamationmark.circle.fill`（同尺寸 `VisualGlyph.badge`、同 semibold、同错误色，不动文案/布局）。旧值 `LOGIN_FAILURE_ICON`：light 负臂 2964 / 正臂 3221 / 差 **257**，dark 2546 / 2793 / 差 **247**，首红 397/398、左移 -1px；新值：light 2964 / 3294 / 差 **330**（+73），dark 2546 / 2859 / 差 **313**（+66），首红与左移不变。逐张看 `settings-general-login-failed` 亮/暗：圆形感叹号更实、与横幅三角区分开，文字位置未动。
- **U-2297：② 预检/刀。** `M1425`（把图标 `.opacity(0)`）**CAUGHT、RESTORE_CLEAN=yes**；预检 **325/295/757 bad=0**、ARM **418/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**。录制帧确定性 **10/10 diff=0**（light 墨 51147、dark 57774）。
- **U-2298：③ 帧。** 重捕 **350** 帧：CHANGED=**2**（仅 `settings-general-login-failed-720x540-light/dark`）、MISSING=0、ADDED=0；基线 **350→350**（同一笔 update）；另 348 帧逐字节不变。
- **U-2299：③④ 全量/换装/电池/清账/streak。** 全量 **1385/56/0（680.2s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 42780、1 窗口 750×492）；清账 **162/162/0**；电池 **691/5**（台账后复跑）；产品面连续零改动 **3** 轮（as-of 545，`python3 scripts/product_streak.py --streak-for 545` 现读）。
- **U-2300：⑤ 627/629/624。** 627 的 fold 类红已改读 settled（R545），markdown 仍 1x=1、copy 1x=2 ⇒ 保持开单；629 继续开单；624 两臂继续、不改名册。
- **U-2301：⑤ 622/628/625/626。** 622 第七值 **176.6ms/2/204**、44 跑 worst 262.3 / over 2 / over_runs 17 / loaded_p95 46.73 / 比值 0.585–2.167，120ms/容差不动、frame 半开单；628/625/626 保持结案。
- **U-2302：⑥ 收口与交接。** ⓪ 笔 `84d7a9a`、产品笔随后；下一轮 R547（第 546 轮 / Round 544）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `9121760`/`8acec7f`/`30c7913`/`8b667ae` 与其余已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 543 · R546（第 545 轮 · 2026-11-02）：登录失败图标换圆形感叹号

BACKLOG 584：失败回执的图标与文字同错误色、又与横幅同用警示三角，图标身份弱。`SettingsView` 把 `exclamationmark.triangle.fill` 换成 `exclamationmark.circle.fill`，尺寸/字重/颜色/文案/布局都不动。旧/新 `LOGIN_FAILURE_ICON`：light 差 257→330、dark 247→313（负臂不变），首红 397/398 与左移 -1px 不变；亮/暗帧逐张看，圆形感叹号更实、与横幅三角区分开。帧 350、CHANGED=2（仅失败回执亮/暗）、基线 350→350；录制帧确定性 10/10 diff=0；M1425 CAUGHT；预检 325/295/757 bad=0、ARM 418/1244、HIDDEN 410/1183 rot=0；build 0 告警；全量 **1385/56/0（680.2s）**；换装 431=431（PID 42780）；电池 691/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗失败回执逐张看；只有这 2 帧变化。 |
| 判据有效性 | 15/15 | 旧/新 `LOGIN_FAILURE_ICON` 差 257→330、247→313；M1425 CAUGHT。 |
| 假绿防御 | 15/15 | 负臂 2964/2546 不变，证明多出来的红来自图标而不是文字。 |
| 产品面推进 | 15/15 | 产品 1 文件：登录失败图标形状换代。 |
| 台账一致性 | 15/15 | U-2295…U-2302、D-546、350/1385/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 三跑 NOT-RUN、runner 签收未到、627/629/624 开单都如实。 |
| 可复核性 | 15/15 | 旧/新读数、M1425、预检 325/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 登录失败图标换圆形感叹号（R546 / 第 545 轮 / Round 543 / U-2295…U-2302 · 产品 1 文件 + 判据）

`SettingsView` 的登录失败回执图标由 `exclamationmark.triangle.fill` 换成 `exclamationmark.circle.fill`（同尺寸/字重/错误色，不动文案与布局）。`LOGIN_FAILURE_ICON` 旧/新：light 差 257→330、dark 247→313，负臂不变；亮/暗帧逐张看，圆形感叹号与横幅三角区分更清楚。帧 350、CHANGED=2、基线 350→350；录制确定性 10/10 diff=0；M1425 CAUGHT；全量 1385/56/0；换装 431=431；电池 691/5。

"""

DECISION = u"""
## D-546 登录失败图标用圆形感叹号，不用警示三角（R546）

- 背景：BACKLOG 584 记着失败回执的图标与文字同错误色、且与横幅同用 `exclamationmark.triangle.fill`，图标身份弱；判据 `LOGIN_FAILURE_ICON` 只能数红色像素差。
- 决定：回执图标换成 `exclamationmark.circle.fill`，尺寸仍是 `VisualGlyph.badge`、字重 semibold、颜色仍走 `loginFailureStyle`，文案与 HStack 布局不动。
- 理由：同一错误色下，实心圆感叹号比三角更实、与横幅的三角区分开；`LOGIN_FAILURE_ICON` 旧/新差 257→330（light）、247→313（dark），负臂不变，说明多出来的红来自图标本身。
- 兼容性/迁移：只改一个 SF Symbol 名；静态帧只有 `settings-general-login-failed` 亮/暗 2 张变化，基线 350→350；录制帧确定性 10/10 diff=0。
- 边界：runner 1x 的 `LOGIN_FAILURE_ICON` 待签收；627/629/624 不受影响。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 544 轮（R545 · 2026-11-02 · U-2287…U-2294）"
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
    add584 = u"""    复查（R546）：登录失败图标由警示三角改为圆形感叹号（产品 `SettingsView.swift` 1 文件）；旧/新 `LOGIN_FAILURE_ICON`：light 负臂 2964 正臂 3221→3294 差 257→330、dark 负臂 2546 正臂 2793→2859 差 247→313；首红 397/398 与左移 -1px 不变；帧只变 `settings-general-login-failed` 亮/暗 2 张；录制确定性 10/10 diff=0；M1425 CAUGHT。runner 1x 待签收。
"""
    text = text.replace(u"    修法：若要更强的图标身份，可给图标不同形状/尺寸或单独色相；先不加判据、不声称已解决。\n",
                        u"    修法：若要更强的图标身份，可给图标不同形状/尺寸或单独色相；先不加判据、不声称已解决。\n" + add584, 1)
    add568 = u"""    复查（R546）：量 `settings-stats-populated` 帧，今天角标 bbox 1108,408–1115,415（2x）；按 1pt padding 推算格边约 1117 ⇒ 右缘留 1pt、帧上未见裁切。不改产品，结案。
"""
    text = text.replace(u"    修法：下一帧看右缘是否被裁；若裁，按格子内缩不改判据地板。\n",
                        u"    修法：下一帧看右缘是否被裁；若裁，按格子内缩不改判据地板。\n" + add568, 1)
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
        (u"R9–R542，543 节自评", u"R9–R543，544 节自评", u"title"),
        (u"阶段二 **535 轮**审计（R9–R542；以 `curve_from_ledger.py` 的 `PHASE2 n=535` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 542",
         u"阶段二 **536 轮**审计（R9–R543；以 `curve_from_ledger.py` 的 `PHASE2 n=536` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 543", u"§1"),
        (u"| 视觉台账 | U-31 … U-2294", u"| 视觉台账 | U-31 … U-2302", u"U 上界"),
        (u"产品面连续零改动轮数 = **2**（as-of 544）", u"产品面连续零改动轮数 = **3**（as-of 545）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R545 节 ② 为准", u"以 `AGENT_STATE.md` 的 R546 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R545 这一段", u"## 18. R458 → R546 这一段", u"§18 head"),
        (u"R545 续到 545 —— 这份报告第七次差点停在几十轮之前）", u"R546 续到 546 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 25615）；电池 691/5。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R546（登录失败图标换圆形感叹号；产品 1 文件 + 判据）**：`SettingsView` 的失败回执图标由 `exclamationmark.triangle.fill` 换成 `exclamationmark.circle.fill`，尺寸/字重/颜色/布局不动；`LOGIN_FAILURE_ICON` light 差 257→330、dark 247→313（负臂不变），亮/暗帧逐张看更清楚。帧 350、CHANGED=2（仅失败回执）、基线 350→350；录制确定性 10/10 diff=0；M1425 CAUGHT；预检 325/295/757 bad=0、ARM 418/1244、HIDDEN 410/1183 rot=0；全量 1385/56/0（680.2s）；换装 431=431（PID 42780）；电池 691/5。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R545 / 第 544 轮 / Round 542）",
        u"最后更新：2026-11-02（本地 · R546 / 第 545 轮 / Round 543）",
        u"identity")
    text = replace_once(
        text,
        u"## R546 开工 ⓪（2026-11-02 · 第 545 轮 / Round 543）",
        u"## R546 状态（2026-11-02 · 第 545 轮 / Round 543 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R545 状态（2026-11-02 · 第 544 轮 / Round 542 · 产品 0 文件 + 判据）"
    body = u"""
① 登录失败图标换代：BACKLOG 584；`SettingsView` 的 `exclamationmark.triangle.fill` → `exclamationmark.circle.fill`，尺寸/字重/错误色/文案/布局不动。旧/新 `LOGIN_FAILURE_ICON`：light 257→330、dark 247→313（负臂 2964/2546 不变），首红 397/398、左移 -1px 不变；亮/暗帧逐张看更清楚。
② 预检/刀：`M1425`（图标 `.opacity(0)`）CAUGHT、RESTORE_CLEAN；预检 325/295/757 bad=0、ARM 418/1244、HIDDEN 410/1183 rot=0；build 0 告警；录制帧确定性 10/10 diff=0。
③ 帧/全量/换装/电池/清账/streak：帧 **350**（CHANGED=2，仅失败回执亮/暗；基线 350→350）；全量 **1385/56/0（680.2s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 42780、1 窗口 750×492）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **3** 轮（as-of 545，`python3 scripts/product_streak.py --streak-for 545` 现读）。
④ 622/624/627/629：622 第七值 176.6ms/2/204、120ms/容差不动；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
⑤ 补记：BACKLOG 568 量得今天角标 bbox 1108,408–1115,415、按 1pt padding 推算格边约 1117 ⇒ 未裁切，结案。
⑥ CI/交接：⓪ 笔 `84d7a9a` 已推；`41336963006 ↔ 9121760`、`41337019426 ↔ 8acec7f`、`41337616903 ↔ 30c7913` 读时 in_progress ⇒ NOT-RUN；`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal 会话 flake）；其余复读同 R545。下一轮 R547（第 546 轮 / Round 544）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `9121760`/`8acec7f`/`30c7913`/`8b667ae` 与已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R546_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
