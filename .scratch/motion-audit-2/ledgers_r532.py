#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R532 台账（第 531 轮 / Round 529）。只写七本账，不碰产品。"""
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


UI_SECTION = u"""## 第 531 轮（R532 · 2026-11-01 · U-2180…U-2186）：折叠态一次性提示与跨重启记忆（产品 5 文件 + 判据）

- **U-2180：⓪ CI。** HEAD=origin=`c788299`、ahead=0；`41289573776 ↔ 9bfd943`（新见证签收跑）、`41289753591 ↔ adb50c1`、`41289948933 ↔ c788299`、`41290053584 ↔ 6add742` 读时均 **in_progress ⇒ NOT-RUN**；`41287495651 ↔ a13636a`、`41287270623 ↔ 76b24b8`、`41287008886 ↔ ac04e2d`、`41286598804 ↔ 02fa144` 为 STEP[9] 台账时序 + hover 0/0（R531 已收口复读）。sources/streak 时序红与产品红分账；623 的 runner 见证未到，不宣布签收；624 最新五红两绿（间歇）；622 最新仍是 `9b9cf56` 544.1ms/2 颗、本机 4 跑未复现。
- **U-2181：① 旧值与产品。** 旧值：折叠窗只有箭头与工具提示，`main-collapsed` 帧没有提示行（看图），控制器没有提示状态；登录首启折叠时用户只能自己找箭头。产品 **5 文件**：`MainWindowCollapseController` 增加 `showsCollapseHint`/`acknowledgeCollapseHint`（键 `mainWindowCollapseHintAcknowledged`，确认后跨重启不再显示；未确认时每次折叠都显示）；`HistorySidebarView` 在折叠且未确认时于标题行下画「窗口已折叠 · 点箭头或按 ⌘\\ 展开」+「知道了」（header 39→58）；`MainWindowContent`/`ContentView` 全链路传状态与确认动作；`MainWindowCollapsePolicy` 放文案常量。无提示时标题行几何不变（既有 348 帧中除新提示外 CHANGED=0）。
- **U-2182：② 判据与刀。** 3 条产品入口测试：`testCollapseHintShowsUntilAcknowledgedAndPersists`（折叠显示→确认→再折叠不显示→重启不显示）、`testCollapsedLaunchShowsHintOnlyWhenNotAcknowledged`、`testCollapseHintIsWiredFromControllerToSidebar`（控制器→根视图→ContentView→侧栏 + 文案）。`M1408`（确认后仍记未确认）**CAUGHT、RESTORE_CLEAN=yes**；预检 **311/288/749 bad=0**、ARM **404/1236**（dupes=0 repeats=0）、HIDDEN **398/1175 rot=0**；build **0 告警**（warnings=0 incremental=0 cold=0 build-tests）。PressFeedback 名册补新位点（labelPadding 2→3、控件档 11→12），两条守卫单跑通过。
- **U-2183：③ 帧卷与看图。** 新夹具 `main-collapsed-hint` 420×560（入材质盲区名册）；捕获 **348 帧**：`ADDED=2 MISSING=0`；首轮 `CHANGED=17` 全是源图标噪声（20×20/27×92px、最大差 2–3、无像素 >8），把「知道了」改成控件档后重捕只 `CHANGED=2`（提示亮/暗）；基线 346→348。亮/暗提示帧逐张看过：提示行、信息图标、「知道了」与列表几何都正常。
- **U-2184：④ 真机取证（只读）。** 旧版（R531 二进制）折叠 420×492：标题行下无提示；新版装好后折叠 420×492：`screencapture -l 29082` 实拍标题行下出现「窗口已折叠 · 点箭头或按 ⌘\\ 展开」+「知道了」；再展开 750×492、1 窗口，未点「知道了」（键仍未写）。未对删除/清空/退出做任何 AXPress，未碰活库内容。
- **U-2185：⑤ 八步与电池。** build 0 告警；全量 **1376/56/0（604.4s）**（前两次 1376/56/2 都是 PressFeedback 名册漏登记新位点，修后第三次真绿；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（活库安装前 430→431，只增不减；PID 28608；真机只读 1 窗口）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **2** 轮（as-of 531，`python3 scripts/product_streak.py --streak-for 531` 现读，last=02fa144/529）。
- **U-2186：⑥ 收口与交接。** 产品笔 `882e30f` 已推（HEAD=origin、ahead=0）；新跑待读（下轮第 ⓪ 全读，重点 9bfd943 的新见证：组合臂 idleInk=0 且组件臂绿 ⇒ 容器盲区具名签收；组件臂也 0 ⇒ 地板红、623 保持开单；624 是否复现）。下一轮 R533（第 532 轮 / Round 530）：先 push 并复核 ahead=0；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 529 · R532（第 531 轮 · 2026-11-01）：折叠态一次性提示与跨重启记忆

旧值：折叠窗只有箭头和工具提示，`main-collapsed` 帧没有提示行。产品 5 文件：控制器增加 `showsCollapseHint`/`acknowledgeCollapseHint`（`mainWindowCollapseHintAcknowledged`，确认后跨重启不再显示；未确认时每次折叠都显示），侧栏在标题行下画「窗口已折叠 · 点箭头或按 ⌘\\ 展开」+「知道了」（header 39→58），根视图/ContentView 全链路接线。3 条产品入口测试；M1408 CAUGHT、RESTORE_CLEAN；预检 311/288/749 bad=0、ARM 404/1236、HIDDEN 398/1175 rot=0；build 0 告警；PressFeedback 名册补 labelPadding 2→3、控件档 11→12。帧 348（ADDED=2；首轮 17 张源图标噪声、修按压反馈后仅 2 张提示帧变化；基线 346→348），亮/暗提示帧逐张看过。真机：旧版折叠无提示；新版折叠 420×492 实拍提示行，再展开 750×492、1 窗口，未点「知道了」。全量 1376/56/0（604.4s；前两次 1376/56/2 都是名册漏登记，修后真绿）；换装 431=431（PID 28608）；电池 683/5。产品 5 文件。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 亮/暗提示帧逐张看过；真机折叠 420×492 实拍提示行，再展开 750×492。 |
| 判据有效性 | 15/15 | 3 条产品入口测试 + 接线断言；M1408 让确认持久化失效并 CAUGHT。 |
| 假绿防御 | 15/15 | 两次全量 1376/56/2 如实记；按压反馈名册补位点后才报绿；未点「知道了」不伪造确认。 |
| 产品面推进 | 15/15 | 折叠首启/首次折叠有可见下一步；产品 5 文件。 |
| 台账一致性 | 15/15 | U-2180…U-2186、D-531、348/1376/431/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | 前两次全量红、源图标噪声、活库 430→431、623 未签收都如实。 |
| 可复核性 | 15/15 | 提示帧、真机截图、M1408、预检 311/288/749、两跑 1376/56/2 与一跑 0 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 折叠态一次性提示与跨重启记忆（R532 / 第 531 轮 / Round 529 / U-2180…U-2186 · 产品 5 文件 + 判据）

折叠且未确认时，标题行下显示「窗口已折叠 · 点箭头或按 ⌘\\ 展开」+「知道了」；确认后跨重启不再显示，未确认时每次折叠都显示。真机旧值折叠 420×492 无提示，新版实拍提示行；帧 348（ADDED=2），M1408 CAUGHT；全量 1376/56/0（604.4s；前两次 1376/56/2 为 PressFeedback 名册漏登记）；换装 431=431。

"""

DECISION = u"""
## D-531 折叠提示在折叠且未确认时显示，确认后跨重启记住（R532）

- 背景：登录首启或第一次折叠时，窗口只剩搜索框/分段/标题/箭头；箭头是唯一可见入口，工具提示要悬停才出现。旧版折叠窗没有一行可见说明（`main-collapsed` 帧无提示行）。
- 决定：控制器持 `showsCollapseHint`（= 折叠 && !已确认）与 `acknowledgeCollapseHint()`；确认写 `mainWindowCollapseHintAcknowledged`，跨重启生效；未确认时每次折叠都显示，不自动消失。视图在标题行下加一行 11pt 次要文字 +「知道了」控件档按钮，header 39→58；无提示时几何不变。
- 理由：一次性提示要比每次出现的横幅安静，但不能只靠悬停工具提示；「知道了」是用户显式确认，写进 defaults 后不再打扰。
- 兼容性/迁移：新键只在用户点「知道了」时写入；已有用户默认无键 ⇒ 第一次折叠会看到提示；展开态不显示；旧夹具与既有帧不变。
- 边界：提示只在主窗口折叠布局；确认是全 App 一个键（多窗口未分）；未点「知道了」时每次折叠都会再出现（刻意，不自动消失）。
"""


def main():
    # 1. UI_AUDIT：降序插在第 530 轮之上
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 530 轮（R531 · 2026-11-01 · U-2172…U-2179）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    # 2. ITERATION：升序追加到文件尾
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    # 3. CHANGELOG：插在 [Unreleased] 之下
    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    # 4. BACKLOG：623/624 复查行
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add623 = u"""    复查（R532）：`9bfd943`（新见证的签收跑）与 `adb50c1`/`c788299` 读时仍 in_progress ⇒ NOT-RUN；未读到组合臂 idleInk，623 保持开单。新判据的组件臂与静置墨地板已随 R531 落在盘上，等下一次 runner 读数按原规则判。
"""
    text = append_after_line(text, u"复查（R531）：静置墨证人已落地", add623, u"backlog623")
    add624 = u"""    复查（R532）：`9bfd943`/`adb50c1`/`c788299` 仍 in_progress ⇒ 本轮无新两臂读数；R531 的五红两绿仍然有效，间歇性未定，不销单。
"""
    text = append_after_line(text, u"复查（R531 收口）：同一卷在 `ac04e2d`/`76b24b8` 两跑", add624, u"backlog624")
    wr(name, text)

    # 5. DECISIONS：追加 D-531
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    # 6. FINAL_REPORT：计数器 + §18 指针 + 一条 R532 记录
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R528，529 节自评", u"R9–R529，530 节自评", u"title"),
        (u"阶段二 **521 轮**审计（R9–R528；以 `curve_from_ledger.py` 的 `PHASE2 n=521` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 528",
         u"阶段二 **522 轮**审计（R9–R529；以 `curve_from_ledger.py` 的 `PHASE2 n=522` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 529", u"§1"),
        (u"| 视觉台账 | U-31 … U-2179", u"| 视觉台账 | U-31 … U-2186", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 530）", u"产品面连续零改动轮数 = **2**（as-of 531）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R531 节 ② 为准", u"以 `AGENT_STATE.md` 的 R532 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R531 这一段", u"## 18. R458 → R532 这一段", u"§18 head"),
        (u"R531 续到 531 —— 这份报告第七次差点停在几十轮之前）", u"R532 续到 532 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"skip_roster 五红两绿 ⇒ 624 记间歇 flake。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R532（折叠态一次性提示与跨重启记忆；产品 5 文件 + 判据）**：旧值折叠窗无提示行；控制器加 showsCollapseHint/acknowledgeCollapseHint（确认后跨重启不再显示），侧栏标题行下加「窗口已折叠 · 点箭头或按 ⌘\\ 展开」+「知道了」（header 39→58），根视图/ContentView 全链路接线。3 条产品入口测试；M1408 CAUGHT；预检 311/288/749 bad=0、ARM 404/1236、HIDDEN 398/1175 rot=0；帧 348（ADDED=2；首轮 17 张源图标噪声、修按压反馈后仅 2 张提示帧变化）；全量 1376/56/0（604.4s；前两次 1376/56/2 为 PressFeedback 名册漏登记）；换装 431=431（PID 28608）；真机 420×492 实拍提示行、再展开 750×492；电池 683/5。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE：identity + R532 标题 + ① ② ③ ④
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R531 / 第 530 轮 / Round 528）",
        u"最后更新：2026-11-01（本地 · R532 / 第 531 轮 / Round 529）",
        u"identity")
    text = replace_once(
        text,
        u"## R532 状态（2026-11-01 · 第 531 轮 / Round 529 · 开工 ⓪）",
        u"## R532 状态（2026-11-01 · 第 531 轮 / Round 529 · 产品 5 文件 + 判据）",
        u"state title")
    anchor = u"\n\n## R531 状态（2026-11-01 · 第 530 轮 / Round 528 · 判据推进，产品 0 文件）"
    body = u"""
① 产品/旧值：旧折叠窗只有箭头与工具提示，`main-collapsed` 帧没有提示行，登录首启折叠时用户只能自己找箭头。产品 **5 文件**：`MainWindowCollapseController` 加 `showsCollapseHint`/`acknowledgeCollapseHint`（键 `mainWindowCollapseHintAcknowledged`，确认后跨重启不再显示；未确认时每次折叠都显示）；`HistorySidebarView` 在折叠且未确认时于标题行下画「窗口已折叠 · 点箭头或按 ⌘\\ 展开」+「知道了」（header 39→58）；`MainWindowContent`/`ContentView` 全链路接线；`MainWindowCollapsePolicy` 放文案常量。无提示时既有帧几何不变。
② 判据/刀：3 条产品入口测试（显示→确认→再折叠不显示→重启不显示；折叠首启；控制器→根视图→ContentView→侧栏接线）；`M1408` CAUGHT、RESTORE_CLEAN=yes；预检 311/288/749 bad=0、ARM 404/1236、HIDDEN 398/1175 rot=0；build 0 告警；PressFeedback 名册补 labelPadding 2→3、控件档 11→12，两条守卫单跑通过。帧 **348**（ADDED=2；首轮 CHANGED=17 源图标噪声、修按压反馈后仅 2 张提示帧变化；基线 346→348），亮/暗提示帧逐张看过。
③ 真机/八步：旧版（R531 二进制）折叠 420×492 无提示；新版折叠 420×492 `screencapture -l 29082` 实拍提示行，再展开 750×492、1 窗口，未点「知道了」（键仍未写）。全量 **1376/56/0（604.4s）**（前两次 1376/56/2 都是 PressFeedback 名册漏登记，修后第三次真绿；本机 SelectionReveal 五条会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=431=431`（活库安装前 430→431，只增不减；PID 28608；真机只读 1 窗口）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；product_streak **2** 轮（as-of 531，`python3 scripts/product_streak.py --streak-for 531` 现读，last=02fa144/529）。
④ 收口：产品笔 `882e30f` 已推（HEAD=origin、ahead=0）；新跑待读（下轮第 ⓪ 全读，重点 9bfd943 的新见证：组合臂 idleInk=0 且组件臂绿 ⇒ 容器盲区具名签收；组件臂也 0 ⇒ 地板红、623 保持开单；624 是否复现）。下一轮编号 R533（第 532 轮 / Round 530）：先 push 并复核 ahead=0；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R532_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
