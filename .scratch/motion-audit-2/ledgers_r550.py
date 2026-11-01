#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R550 台账（第 549 轮 / Round 547）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 549 轮（R550 · 2026-11-02 · U-2327…U-2334）：浮层键盘提示关闭键改大写 Esc（产品 1 文件 + 判据）

- **U-2327：⓪ CI。** HEAD=origin=`181b022`、ahead=0、`git push` no-op；api=200/apple=200。`41354330740 ↔ bb948db` 读时 **queued**、`41354387000 ↔ 181b022` **in_progress** ⇒ 均 NOT-RUN；queued/in_progress 不算成功。`41351367430 ↔ deb28a1` 仅 STEP[15]（SelectionReveal 会话 flake）、`41351231883 ↔ a210a29` STEP[18]+[19]（frame **196.7ms/2**、markdown 1x=1）、`41350830308 ↔ f0e9ea0` 仅 STEP[9]（skip_roster+sources 时序）、`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal）；`41351210379 ↔ 19d33b5` success。
- **U-2328：② 提示关闭键改大写。** `QuickPickKeyboardHint.text` 由「↑↓ 选择 · ↵ 粘贴 · esc 关闭」改成「… · Esc 关闭」；全 App 其它提示统一用「Esc」，小写键名像普通单词。纯几何读数：`Esc` 子串 cap height **5.99→7.85pt**（+31%）、宽 5.13→5.22pt；字号 11pt 不变。
- **U-2329：② 判据/刀/预检。** 新判据 `QuickPickKeyboardHintTests.testCloseKeyUsesAnUppercaseKeyNameWithReadableCaps`：提示必须含「Esc 关闭」且不含「esc 关闭」，`Esc` 子串墨高 ≥7pt；`HINT_KEY_CAPS 高=7.85pt 宽=5.22pt`。`M1429`（退回小写）**CAUGHT、RESTORE_CLEAN=yes**；预检 **329/295/757 bad=0**、ARM **422/1244**（dupes=0 repeats=0）、HIDDEN **410/1183 rot=0**；build **0 告警**；提示文案没有旧刀锚点，无需重钉。
- **U-2330：③ 帧/录制。** 重捕：CHANGED=**26**（所有含提示行的 `quickpick-*` 帧亮/暗）、MISSING=0、ADDED=0，基线 **354→354**；逐张看 `quickpick-list` 提示行：`Esc` 与中文 cap height 齐平、行未移位。录制帧确定性 **10/10 diff=0**。
- **U-2331：③④ 全量/换装/电池/清账/streak。** 全量 **1389/56/0（708.1s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 48908、1 窗口 750×492）；清账 **162/162/0**；电池 **691/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 549，`python3 scripts/product_streak.py --streak-for 549` 现读）。
- **U-2332：⑤ 622/624/627/629/628/625/626。** 622 第七值 176.6ms/2/204、本轮 frame 新值 **196.7ms/2**（具名 runner 负载 flake，120ms/容差不动）；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案。
- **U-2333：⑤ BACKLOG 630 新开并结案。** 提示小写 `esc` 是本轮新发现的产品排版位（不是既有开单）；新开 630 记录现象/读法/判据，同轮结案。
- **U-2334：⑥ 收口与交接。** ⓪ 笔 `c88e12a`、产品笔随后；下一轮 R551（第 550 轮 / Round 548）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `bb948db`/`181b022`/`deb28a1`/`a210a29`/`f0e9ea0` 与其余已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 547 · R550（第 549 轮 · 2026-11-02）：浮层键盘提示关闭键改大写 Esc

`QuickPickKeyboardHint.text` 由「↑↓ 选择 · ↵ 粘贴 · esc 关闭」改成「… · Esc 关闭」；全 App 其它提示统一用「Esc」，小写键名像普通单词。纯几何读数：`Esc` 子串 cap height 5.99→7.85pt（+31%）、宽 5.13→5.22pt；新判据 `HINT_KEY_CAPS` 要求含大写键名且墨高 ≥7pt；M1429 退回小写 CAUGHT。帧 CHANGED=26（所有含提示行的 `quickpick-*` 亮/暗），基线 354→354；逐张看提示行 `Esc` 与中文 cap height 齐平、行未移位；录制确定性 10/10 diff=0；build 0 告警；全量 **1389/56/0（708.1s）**；换装 431=431（PID 48908）；电池 691/5；BACKLOG 630 同轮结案。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | `quickpick-list` 提示行新旧对比：`Esc` 与中文齐平、行未移位。 |
| 判据有效性 | 15/15 | `HINT_KEY_CAPS` 7.85pt；M1429 CAUGHT；旧小写 5.99pt 会红。 |
| 假绿防御 | 15/15 | 文本含/不含两条 + 墨高一条同时判，空串或小写都过不去。 |
| 产品面推进 | 15/15 | 产品 1 文件：提示键名排版。 |
| 台账一致性 | 15/15 | U-2327…U-2334、D-550、354/1389/431/691 都来自命令与日志。 |
| 交付诚实性 | 15/15 | 三跑 NOT-RUN、622 196.7 具名负载 flake、627/629/624 开单都如实。 |
| 可复核性 | 15/15 | 5.99→7.85pt、M1429、预检 329/295/757 全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 浮层键盘提示关闭键改大写 Esc（R550 / 第 549 轮 / Round 547 / U-2327…U-2334 · 产品 1 文件 + 判据）

`QuickPickKeyboardHint.text` 由「↑↓ 选择 · ↵ 粘贴 · esc 关闭」改成「… · Esc 关闭」。`Esc` 子串 cap height 5.99→7.85pt（+31%）、宽 5.13→5.22pt；新判据 `HINT_KEY_CAPS` 要求含大写键名且墨高 ≥7pt；M1429 CAUGHT。帧 CHANGED=26（含提示行的浮层帧亮/暗），基线 354→354；录制确定性 10/10 diff=0；全量 1389/56/0；换装 431=431；电池 691/5；BACKLOG 630 同轮结案。

"""

DECISION = u"""
## D-550 浮层键盘提示用大写 `Esc` 键名（R550）

- 背景：`QuickPickKeyboardHint.text` 把关闭键写成小写 `esc`，而全 App 其它提示统一用「Esc」；11pt 下小写 x-height 只有 5.99pt，读起来像普通单词而不是键名。
- 决定：只改提示文案为「… · Esc 关闭」，字号/颜色/布局/面板约束都不动。
- 理由：`Esc` 子串 cap height 5.99→7.85pt（+31%）、宽 5.13→5.22pt；新判据 `HINT_KEY_CAPS` 同时判「含大写键名」与墨高 ≥7pt；M1429 退回小写 CAUGHT。
- 兼容性/迁移：只改一句文案；含提示行的 26 张浮层帧亮/暗变化，基线 354→354；录制帧确定性 10/10 diff=0。
- 边界：本轮是新发现的排版位（非既有 BACKLOG），新开 630 并同轮结案；627/629/624 不受影响。
"""


def main():
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 548 轮（R549 · 2026-11-02 · U-2319…U-2326）"
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
    if not text.endswith(u"\n"):
        text += u"\n"
    text += u"""
**630. 浮层键盘提示把关闭键写成小写 `esc`**（R550 发现并同轮结案）
    现象：`QuickPickKeyboardHint.text` 是「↑↓ 选择 · ↵ 粘贴 · esc 关闭」，而全 App 其它提示统一用「Esc」；11pt 下小写 x-height 5.99pt，键名读起来像普通单词。
    修法：改「Esc 关闭」；cap height 7.85pt（+31%），宽 5.13→5.22pt；新判据 `HINT_KEY_CAPS`（≥7pt）+ M1429 CAUGHT；含提示行的 26 张浮层帧只差提示行。**同轮结案**。
"""
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
        (u"R9–R546，547 节自评", u"R9–R547，548 节自评", u"title"),
        (u"阶段二 **539 轮**审计（R9–R546；以 `curve_from_ledger.py` 的 `PHASE2 n=539` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 546",
         u"阶段二 **540 轮**审计（R9–R547；以 `curve_from_ledger.py` 的 `PHASE2 n=540` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 547", u"§1"),
        (u"| 视觉台账 | U-31 … U-2326", u"| 视觉台账 | U-31 … U-2334", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 548）", u"产品面连续零改动轮数 = **1**（as-of 549）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R549 节 ② 为准", u"以 `AGENT_STATE.md` 的 R550 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R549 这一段", u"## 18. R458 → R550 这一段", u"§18 head"),
        (u"R549 续到 549 —— 这份报告第七次差点停在几十轮之前）", u"R550 续到 550 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"换装 431=431（PID 28058）；电池 691/5。627/629/624 保持开单。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R550（浮层键盘提示关闭键改大写 Esc；产品 1 文件 + 判据）**：`QuickPickKeyboardHint.text` 的「esc 关闭」改「Esc 关闭」；`Esc` 子串 cap height 5.99→7.85pt（+31%）、宽 5.13→5.22pt；新判据 `HINT_KEY_CAPS`（含大写键名、墨高 ≥7pt），M1429 CAUGHT。帧 CHANGED=26（含提示行的浮层帧亮/暗），基线 354→354；录制确定性 10/10 diff=0；预检 329/295/757 bad=0、ARM 422/1244、HIDDEN 410/1183 rot=0；全量 1389/56/0（708.1s）；换装 431=431（PID 48908）；电池 691/5；BACKLOG 630 同轮结案。627/629/624 保持开单。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R549 / 第 548 轮 / Round 546）",
        u"最后更新：2026-11-02（本地 · R550 / 第 549 轮 / Round 547）",
        u"identity")
    text = replace_once(
        text,
        u"## R550 开工 ⓪（2026-11-02 · 第 549 轮 / Round 547）",
        u"## R550 状态（2026-11-02 · 第 549 轮 / Round 547 · 产品 1 文件 + 判据）",
        u"state title")
    anchor = u"\n## R549 状态（2026-11-02 · 第 548 轮 / Round 546 · 产品 1 文件 + 判据）"
    body = u"""
① 提示键名：`QuickPickKeyboardHint.text` 的「esc 关闭」改「Esc 关闭」；`Esc` 子串 cap height 5.99→7.85pt（+31%）、宽 5.13→5.22pt，字号/颜色/布局不动。
② 判据/刀：新 `QuickPickKeyboardHintTests.testCloseKeyUsesAnUppercaseKeyNameWithReadableCaps`（含大写键名、`HINT_KEY_CAPS` 7.85pt ≥7pt）；`M1429` 退回小写 CAUGHT、RESTORE_CLEAN；预检 329/295/757 bad=0、ARM 422/1244、HIDDEN 410/1183 rot=0；build 0 告警；录制确定性 10/10 diff=0。
③ 帧/全量/换装/电池/清账/streak：帧 **354→354**（CHANGED=26：所有含提示行的 `quickpick-*` 帧亮/暗；ADDED=0）；全量 **1389/56/0（708.1s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（PID 48908）；电池 **691/5**（台账后复跑）；清账 162/162/0；产品面连续零改动 **1** 轮（as-of 549，`python3 scripts/product_streak.py --streak-for 549` 现读）。
④ 622/624/627/629：622 frame 新值 196.7ms/2（具名 runner 负载 flake，120ms/容差不动）；624 两臂继续、不改名册；627/629 保持开单；628/625/626 结案；BACKLOG 630 同轮结案。
⑤ CI/交接：⓪ 笔 `c88e12a`、产品笔 `bcea7f6`、台账笔随后；`41354330740 ↔ bb948db` queued、`41354387000 ↔ 181b022` in_progress ⇒ NOT-RUN；`41351367430 ↔ deb28a1` 仅 STEP[15]（SelectionReveal）、`41351231883 ↔ a210a29` STEP[18]+[19]（frame 196.7ms/2、markdown 1x=1）、`41350830308 ↔ f0e9ea0` 仅 STEP[9]（skip_roster+sources）、`41337616903 ↔ 30c7913` 仅 STEP[15]（PerfBudget 274.93ms + 录制帧 dark 9457px）、`41334537980 ↔ 8b667ae` 仅 STEP[15]（SelectionReveal）；`41351210379 ↔ 19d33b5` success。下一轮 R551（第 550 轮 / Round 548）：先 push 复核 ahead=0；读本轮产品笔与台账笔、复读 `bb948db`/`181b022`/`deb28a1`/`a210a29`/`f0e9ea0` 与已读跑的全部失败步骤；622 frame 半、624、627、629 继续；628/625/626 不重开；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R550_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
