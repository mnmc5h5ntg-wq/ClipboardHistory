#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R532 收口后 CI 复读 + R533 ⓪：只写 STATE/BACKLOG，不碰产品。"""
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


def main():
    name = "AGENT_STATE.md"
    text = rd(name)
    anchor = u"\n\n## R532 状态（2026-11-01 · 第 531 轮 / Round 529 · 产品 5 文件 + 判据）"
    body = u"""
## R533 状态（2026-11-01 · 第 532 轮 / Round 530 · 开工 ⓪）

R533 ⓪ 读数（只登记、不轮询）：HEAD=origin=`df43baa`、ahead=0。`41293387308 ↔ 882e30f`（产品）读时 in_progress、`41293578965 ↔ df43baa`（台账）queued ⇒ **NOT-RUN**。
- `41289573776 ↔ 9bfd943` **failure STEP[9]+[15]**：STEP[9]=指针/citations/streak 时序 + skip_roster（`9bfd943` 是判据笔，台账未补）；STEP[15] 唯一失败是 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime`（已知本机会话族，runner 也偶发）⇒ **hover 新见证本身通过**：组合臂 `idleInk=0` 两档、组件臂 light **571/706/38308/1803**、dark **627/671/21456/1437**。
- `41289753591 ↔ adb50c1` **failure STEP[15]+[19]**：STEP[15] 两条运动 flake（`testCollapseWidthIsMeasuredFrameByFrame` 终宽 0.998838 vs 1.0±0.001；`testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1x 只有 1 个过渡帧 <2）；STEP[19] Motion coverage floor 由这两条红计；hover 新见证通过。
- `41289948933 ↔ c788299` **success（整跑无失败）**：与 9bfd943 同一份判据，623 的 runner 签收读数在此：组合臂 light/dark `idleInk=0 hoverInk=0 totalDelta=0` + `TITLE_HOVER_COMPOSED_NOT_RUN=idle-title-band-blank`（floor 200）；组件臂 light **571/706/38308/1803**、dark **627/671/21456/1437**（floor 200/1000/200）⇒ **组合臂容器盲区 + 组件臂绿，623 按规则具名签收**。
- `41290053584 ↔ 6add742` **failure STEP[9]+[15]**：STEP[9]=R532 ⓪ 的指针/streak/citations 时序；STEP[15] 唯一失败又是 SelectionReveal 会话族；无 STEP[17]。
- **624**：skip_roster 在 `9bfd943`（非台账笔）红、在 `adb50c1`/`c788299`（台账笔）绿；观察相关「非台账笔红、台账笔绿」仍不能证明成因（嵌套跑时长/负载），保持开单、不改名册。
- **622**：这四跑都没有 STEP[18]；最近仍是 `9b9cf56` 的 544.1ms/2 颗，本机 4 跑未复现，120ms 与容差不动。
"""
    text = replace_once(text, anchor, body + anchor, u"state ⓪")
    wr(name, text)

    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add623 = u"""**623 结案（R532 收口，`c788299` 跑）**：runner 1x 的 TITLE_HOVER 由旧判据的 0/0 拆成两臂——组合臂 light/dark `idleInk=0` 且 `totalDelta=0`，打 `TITLE_HOVER_COMPOSED_NOT_RUN=idle-title-band-blank`（floor 200）；组件臂 light `571/706/38308/1803`、dark `627/671/21456/1437`（floor 200/1000/200）全过 ⇒ 容器盲区具名 + 有界替代签收。`c788299` 整跑 success。200×scale² 与 1000/200 地板都没降；组合臂若未来能在 runner 画出，会自行按原地板判。
"""
    text = append_after_line(text, u"复查（R532）：`9bfd943`（新见证的签收跑）与 `adb50c1`/`c788299` 读时仍 in_progress", add623, u"backlog623")
    add624 = u"""    复查（R532 收口）：`9bfd943`（非台账笔）STEP[9] 仍红在 skip_roster；`adb50c1`/`c788299`（台账笔）STEP[9] 绿。两臂都记；观察到「非台账笔红、台账笔绿」的相关性，但还不能证明成因（可能是嵌套跑时长/负载）⇒ 保持开单，不改名册、不销单。
"""
    text = append_after_line(text, u"复查（R532）：`9bfd943`/`adb50c1`/`c788299` 仍 in_progress ⇒ 本轮无新两臂读数", add624, u"backlog624")
    wr(name, text)

    sys.stdout.write("R533_OPEN_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
