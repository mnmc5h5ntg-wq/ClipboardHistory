# -*- coding: utf-8 -*-
"""R557 补记：⓪ 那四跑到手后的读数、629 的三个 runner 真数、电池两条红其实是同一条。

用法：`python3 addendum_r557.py --check` 只验锚点；不带参数才真写。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STATE = u"""
### R557 补记（2026-11-02 · 第 556 轮 / Round 554 · ⓪ 那四跑到手 + 629 的三个 runner 真数到手）

① ⓪ 挂账四跑 + 本轮两笔的现读（⓪ 时全未读，收口时四跑已 concluded）：
- `41450045802 ↔ 5ba5b2f` conclusion=**failure**；失败步骤 **STEP[9] Release script tests**，STEP[10]–[14] ⇒ skipped。正文 `Ran 695 tests in 108.977s` ⇒ `FAILED (failures=2, skipped=2)`；红名 `test_skip_roster.SkipRosterTests.test_the_roster_matches_what_this_machine_actually_skips`（`None is not true : 内层没有结论行`）与 `test_sources_cell_second_source.SourcesCellSecondSource.test_the_cell_agrees_with_its_own_source`（`0 != 1 : 报告里那一格与 git 派生的不一致（rc=1）`）。该日志 13791/13791 行步骤名全是 `UNKNOWN STEP` ⇒ 按步骤名过滤恒 0 行，正文只能 grep/emit 通道。
- `41450081248 ↔ 680aea3` **failure**；同一形状（STEP[9] 红、10–14 skipped）；`Ran 695 tests in 119.049s` ⇒ `FAILED (failures=3, skipped=2)`，比上一跑多一条 `test_final_report_headline.FinalReportSourcesCellTests.test_the_sources_cell_agrees_with_git`。
- `41450601769 ↔ ccab101` **failure**；同一形状；`Ran 695 tests in 122.714s` ⇒ `FAILED (failures=3, skipped=2)`，同上三条红名。
- `41452722560 ↔ 58851c2` **cancelled**（13:24:36Z→13:39:37Z = 15m01s），失败步骤 0 条、`--log-failed` 0 行 ⇒ **NOT-RUN**：cancelled 既不是绿，也不是产品结论。
- `41455782587 ↔ 598b253` **cancelled**（13:45:52Z→14:00:53Z，同样 15m01s）；对它取正文直接 `log not found: 125311960175` ⇒ 这一跑的正文**一格都取不到**（第四种「读到 0 行」的坏法：作业被取消 ⇒ 日志从未落盘）。
- 本轮自己的两笔 `41464892684 ↔ ce4da8f`、`41465486002 ↔ 5d05578` 均 in_progress ⇒ **NOT-RUN**，R558 必读。
- **读数工具的盲区（本轮新记）**：`ci_read.py steps` 只列 failure/skipped。这三跑的 STEP[15] Swift tests、STEP[16] Motion gate、STEP[17] Capture gate、STEP[18]–[19] coverage floor **全是 success** —— 只有另用 `gh run view --json jobs` 逐条读才看得到。拿 steps 的输出推「后面的步骤没跑」会推出反话。

② **629 那三个 runner 真数到手**（同判据、同 1x，三跑各一条）：

| run ↔ commit | 过渡帧数 | 峰值 | 窗口 | 每格 | 非零的相邻帧差落在 |
| --- | --- | --- | --- | --- | --- |
| `41450045802 ↔ 5ba5b2f` | 2 | 0.0193 | 588ms | 22.6ms | 第 3 格 0.0145、第 9 格 0.0193 |
| `41450081248 ↔ 680aea3` | 2 | 0.0145 | 676ms | 26.0ms | 第 4 格 0.0145、第 9 格 0.0145 |
| `41450601769 ↔ ccab101` | 2 | 0.0193 | 731ms | 28.1ms | 第 3 格 0.0145、第 9 格 0.0193 |

三条结论，都是被读数本身给的，不是猜的：
1. runner 的每格是 **22.6–28.1ms**，不是 R556 推的 ≈44ms（那个数是从别的情景 `窗口=1143ms / 27 格` 借来的 —— 借错了对象）。200ms 的过程在这台机器上跨 7–9 格 ⇒ R556 那条「≥2 帧地板正好压在采样网格边缘」被自己的读数**否掉**。
2. 但 27 帧里只有 **2 格**相邻差非零，其余逐格 `0.0000` ⇒ `过渡帧数=2` 是**零余量**通过。`5a943e7` 那次读 1，就是这两格里的一格掉零。间歇红的形状不是「采样太稀」，是「这条通道本来只在两个离散时刻给出可测差」。
3. 因此 **(A) 加密录制被这三个数否掉**：加密只会多得几格 `0.0000`，不会多得非零格，200s 看门狗那一格也不用动。**(B) 换判据对象**才有对象可换 —— 「相邻差的非零计数」是「有没有插值」的代理量，要判的东西应该读成「过程里有没有一帧严格落在两端之间」（两端夹逼 / 累计差），这条形状 R545 读 settled 进度时用过。

③ 选择已经做完，**落地留给 R558**：本轮台账在数未到之前按 NOT-RUN 闭合，收口之后不重写产品与判据、不重跑验证链。R558 头一格 = 按 (B) 落一条新判据 + 一把刀，`≥2 帧地板`、阈值、声明时长全部不动（地板不许降，是这条出口的硬条件）。

④ **自伤一格（写给下一轮的顺序规矩）**：本轮把产品笔与刀表笔**先推**、台账笔**后推** ⇒ 中间那几跑在 STEP[9] 是**注定红**的：`report_sources_cell` 那一格在「产品已进 git、台账还没写」的窗口里必然与 git 派生值不一致。R556 只修了「派生顺序」（`--write` 挪到产品笔之后），没修「推送顺序」。下一轮按 ⑥ 的字面走：产品/刀先 commit **不 push**，等台账 + `--write` + 电池都过了，**一次性 push**。
另一格是仪器的：`test_skip_roster` 那条「内层没有结论行」**不是 flake** —— `scripts/tests/test_skip_roster.py:36` 的 `SKIPPED_SUMMARY = re.compile(r'OK \\(skipped=(\\d+)\\)')` 只认 OK 汇总行，:184 `assertTrue(ran and skipped)` ⇒ 内层只要有**任何**一条红（本轮就是 sources-cell），汇总行变成 `FAILED (…)`，这格就以「没有结论行」红。同一个成因记成两朵红，而且那句话本身在骗人。已开 **634**。本机 R556 记的那三次「flake」很可能就是当时的 stale-cell 窗口，标签要重审。

⑤ 台账口径不变：本轮 629 仍记 **NOT-RUN**（数是在台账落盘**之后**到手的，不在收口后追改成落地）；632 记「落地 + 剩余具名出口」；禁碰 9 面、4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板一律不动；刀号 **M1446** 起；633 仍等用户人工回执；622/624/627 继续。

"""

BACKLOG_629 = u"""    读数到手（R557 补记，三跑同判据同 1x）：`41450045802↔5ba5b2f` = 过渡帧数 2 / 峰值 0.0193 / 窗口 588ms / 每格 22.6ms；`41450081248↔680aea3` = 2 / 0.0145 / 676ms / 26.0ms；`41450601769↔ccab101` = 2 / 0.0193 / 731ms / 28.1ms。三条非零相邻帧差全部落在同一对位置（第 3–4 格与第 9 格），其余 25 格逐格 `0.0000`。⇒ ① R556 那句「runner 每格 ≈44ms、地板压在网格边缘」被否掉（那个 44ms 是从别的情景借来的读数，借错了对象）；② 零余量通过的形状是「这条通道只在两个离散时刻给出可测差」，`5a943e7` 的 1 帧就是这两格里掉了一格；③ **(A) 加密录制被这三个数否掉**（加密只多得 `0.0000`），**(B) 换判据对象被选中**：把「相邻差非零计数」换成「有没有一帧严格落在两端之间」。**下一轮按 (B) 落地**，`≥2 帧地板`、120ms 阈值、声明时长都不动。

"""

BACKLOG_634 = u"""**634. 电池里两条红其实是同一条：`test_skip_roster` 把内层的红借成自己的「没有结论行」**（R557 补记现读并新开）
    读数：runner 三跑 STEP[9] `Release script tests` 各红 2–3 条，其中 `test_skip_roster.SkipRosterTests.test_the_roster_matches_what_this_machine_actually_skips` **恒红**，正文 `AssertionError: None is not true : 内层没有结论行（Ran / OK (skipped=N)）⇒ 无从对账`；三跑同时红的是 sources-cell 那一族（`test_the_cell_agrees_with_its_own_source`，台账笔之后再加 `test_the_sources_cell_agrees_with_git`）。
    因果（代码直读，不用等下一次红）：`scripts/tests/test_skip_roster.py:36` `SKIPPED_SUMMARY = re.compile(r'OK \\(skipped=(\\d+)\\)')` 只匹配 **OK** 汇总行；:184 `assertTrue(ran and skipped)`。这一格自己起内层 `unittest discover`（:173 那次 subprocess），内层只要有任何一条红，汇总行就是 `FAILED (failures=N, skipped=M)` ⇒ `skipped=None` ⇒ 以「没有结论行」红。**结论行在，只是不是 OK** —— 那句话把「内层有红」说成「内层没跑完」，是两种修法相反的成因。
    为什么算缺陷不是噪音：①同一个成因记成两朵红，真实红数被抬高；②它会在每一次「内层有别的东西红」时替那条红做伪证，等于给红名册加一个会自己繁殖的条目；③本机 R556/R557 记过的三次「内层没有结论行 flake」很可能根本不是 flake，而是当时的 stale-cell 窗口 —— 标签需要重审。
    修法（下一轮，只动这一格观察者，不动被判物、不放宽任何门）：把「有没有汇总行」与「汇总行是 FAILED」拆成两格判据，前者缺 ⇒ 真·无从对账（红），后者 ⇒ 消息里原样带上内层汇总行与内层红名（不许再冒充「没跑完」）；`machine_key` / `machine_class` 的读数一并打出来。
    退场：sources-cell 干净那一跑里这格必须绿；若仍红，正文必须能直接指出内层是哪一条 —— 达不到就说明它还在借红。
    关联：本轮的 stale-cell 窗口由**推送顺序**造成（产品/刀笔先推、台账笔后推，中间窗口里那一格必然与 git 不一致）；规矩见 `AGENT_STATE.md` 的 R557 补记 ④。

"""


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, text):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(text)


def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return text.replace(old, new, 1)


def main():
    check = "--check" in sys.argv

    # 1) STATE：接在本轮状态节末尾（⑤ 那一行的尾巴）
    n = "AGENT_STATE.md"
    t = rd(n)
    anchor = u"2x 8.0pt 与 1x 6.0pt 均不动。\n## R557 ⓪ 开工"
    t = once(t, anchor,
             u"2x 8.0pt 与 1x 6.0pt 均不动。\n" + STATE.strip(u"\n") + u"\n\n## R557 ⓪ 开工",
             u"state tail")
    if not check:
        wr(n, t)

    # 2) BACKLOG 629：把到手读数接在 R557 那句「挂起」之后
    n = "AGENT_BACKLOG.md"
    t = rd(n)
    anchor = u"R558 只要那一跑到手，就按那三个数在 (A)/(B) 里选一条落地。\n"
    t = once(t, anchor, anchor + BACKLOG_629, u"backlog 629")

    # 3) BACKLOG 634：新开单，插在 633 之上
    anchor = u"**633. 桌面授权反复弹：签名身份已固定，剩人工验收一格**（R554 现读并新开）"
    t = once(t, anchor, BACKLOG_634 + u"\n" + anchor, u"backlog 634")
    if not check:
        wr(n, t)

    sys.stdout.write("ADDENDUM_R557_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
