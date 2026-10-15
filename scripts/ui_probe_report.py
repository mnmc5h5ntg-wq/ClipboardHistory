#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给"在屏探针那一卷被看门狗收掉"这件事**一个名字**（R86 / BACKLOG 92 路 a）。

背景（一句话版）：`.github/workflows/ci.yml` 的 `On-screen interaction probes` 那一步自带 240 秒
看门狗，到点 `kill -9`。R62 之前那一步在"没跑完"这条分支上只留一句解释
（"在屏探针在无头 runner 上不可用"），于是**整卷变成一张免检牌** —— R61 修的侧栏跟随选中
那三条行为判据就住在这卷里，它们的回归在 CI 上一条都没跑，而作业是绿的。
BACKLOG 92 要的就是这一步：**没跑完也要说清是哪一条没跑完**。

为什么这件事可以只读日志、不动判据代码（本轮先量的结论，见
`.scratch/motion-audit-2/r86_spike_partial_output.md`）：`swift test` 会把
`Test Case '-[Module.Class testX]' started.` 逐行打到 stdout，而本机实测（50 秒后 `kill -9`，
退出码 137，与 CI 那个数字同形）**这些行留在了日志里** ——
13 行 started / 12 行有结论，差集正好点名那条正在跑的。
⇒ "started 减去 concluded" 就是挂死的那条，不需要测试自己打点。

输出（每行一条，全大写标记，便于 CI 与台账 grep）：

    UI_PROBE_PROGRESS started=N concluded=M
    UI_PROBE_HUNG=<用例名>            每条"开了口没结论"的用例一行（通常 0 或 1 条）
    UI_PROBE_NO_CASE_STARTED=1        一条用例都没开始（进程死得更早）
    UI_PROBE_ALL_CONCLUDED=1          每条 started 都有结论（这一卷跑完了）
    UI_PROBE_NAMED=0|1                这次停机**有没有名字**（0 = 只可能出现在脚本自己坏了）

退出码：0 = 给出了名字（跑完了、挂在哪条说清了、或一条都没开始也说清了）；
1 = **给不出名字**，只有两种形状会走到这里，而它们都不是"探针坏了"，是"这份日志没资格说这句话"：

  * `UI_PROBE_CONCLUDED_WITHOUT_START` —— 有结论却没有它的 started 行。
    本机与 runner 都见过 stdout 成块丢（R64 / R84 各一次），那时 started 差集会假报一条挂死的用例；
  * `UI_PROBE_NOT_THE_RAW_LOG` —— 喂进来的是 CI 那一步的**汇报片段**而不是 `swift test` 的原始输出。
    这一格是本轮自己踩出来的：拿 `scripts/tests/fixtures/r62_runner_ui.log`（一份真·步骤摘要）
    试脚本时，它 0 条 `Test Case` 行，于是脚本自信地报了"进程在第一条用例开口之前就死了"。
    那句话在**拿错文件**的时候是假话，而它听起来比"我不知道"更像结论。

两种都是宁可红，也不许把"我说不出"当成"没事"。
"""
import argparse
import re
import sys

# XCTest 的两类行。`started` 与 `passed|failed|skipped` 的行名格式一致，只是结尾不同。
CASE = re.compile(r"Test Case '-\[[^\]]*?\b([A-Za-z0-9_]+)\]' (started|passed|failed|skipped)")

# 崩溃/中止的旁证：有这些行时"没结论"是进程级的死法，不是某条用例的死法。
CRASH = ("Fatal error", "Precondition failure", "signal code ", "Killed", "error: Exited with unexpected signal")

# "这份文本是 CI 那一步的**汇报**，不是 `swift test` 的原始日志"的旁证。
# 为什么要有这一格：拿错文件时脚本会自信地报"进程在第一条用例之前就死了"，
# 而那是一句关于产品的假话（真相是我读错了文件）。见 `report()` 里那一格的注释。
ECHO_MARKERS = re.compile(r"ui suite exit:|##\[group\]|没有跑完（看门狗")


def report(text):
    """返回 (行列表, 是否给出了名字)。"""
    if not text.strip():
        # 空文件与"进程一条用例都没开始"在日志里长得一模一样，但成因不同：
        # 前者是**仪器**没把东西写下来（重定向没建成、路径写错、被 truncate 过）。
        # 把仪器故障报成一句关于产品的结论，是这一族最贵的错（R64 那一课）。
        return (["UI_PROBE_LOG_EMPTY=1 日志是空的 ⇒ 这不是『探针没跑』，是『我没有它的输出』"], False)
    started, concluded = [], {}
    for match in CASE.finditer(text):
        name, state = match.group(1), match.group(2)
        if state == "started":
            if name not in started:          # 同一条重复出现（重跑或被两遍并进来）只算一次
                started.append(name)
        else:
            concluded[name] = state

    lines = ["UI_PROBE_PROGRESS started=%d concluded=%d" % (len(started), len(concluded))]
    # 只报"开了口却没有结论"的那些，并保持在日志里的先后顺序
    hung = [n for n in started if n not in concluded]
    for name in hung:
        lines.append("UI_PROBE_HUNG=%s" % name)

    # 反方向的不自洽：有结论却没见过它开始。真日志里这是可能的 —— stdout 成块丢（R64 那一族）
    # 会把 started 行丢掉而留下结论行。那时"挂死在哪条"这句话就没有依据，必须红而不是猜。
    orphans = [n for n in concluded if n not in started]
    for name in orphans:
        lines.append("UI_PROBE_CONCLUDED_WITHOUT_START=%s "
                     "（日志里有它的结论却没有它的 started 行 ⇒ started/concluded 这对差不再可信，"
                     "最可能是 stdout 成块丢；这一格不许被读成『挂死的那条已经点出来了』）" % name)

    crashed = [marker for marker in CRASH if marker in text]
    if crashed:
        lines.append("UI_PROBE_CRASH_MARKERS=%s" % ",".join(crashed))

    if orphans:
        return lines, False
    if hung:
        # 有名字：挂在哪一条说清了（哪怕同时有崩溃旁证，名字仍然要报出来）
        return lines, True
    if started:
        lines.append("UI_PROBE_ALL_CONCLUDED=1")
        return lines, True
    # 一条用例都没开始。但"没有 Test Case 行"有两种完全不同的成因：
    #   ① 进程真的在第一条用例开口之前就死了（这是**关于产品/环境**的结论）；
    #   ② 喂进来的根本不是 `swift test` 的原始日志，而是 CI 那一步自己的汇报片段
    #      （`ui suite exit: 137 …` 那种摘要，里面本来就不会有 `Test Case` 行）。
    # ②会被 ① 读成一句假话："探针在启动阶段就死了" —— 而它只是我拿错了文件。
    # 这一格不是假想：`scripts/tests/fixtures/r62_runner_ui.log` 正是 ② 的形状（run 38603034761
    # 的逐步汇报），本轮第一次把它喂给脚本时，脚本就自信地报了 ①。
    if ECHO_MARKERS.search(text):
        lines.append("UI_PROBE_NOT_THE_RAW_LOG=1 这份日志里有 CI 那一步的汇报行却没有一条 `Test Case` ⇒ "
                     "喂进来的是**步骤摘要**而不是 `swift test` 的原始输出。"
                     "这一格不许被读成『探针在第一条用例之前就死了』—— 那需要原始日志才有资格说")
        return lines, False
    lines.append("UI_PROBE_NO_CASE_STARTED=1 "
                 "（进程在第一条用例开口之前就死了：看门狗收掉的是启动阶段，不是某条判据）")
    return lines, True


def main(argv=None):
    parser = argparse.ArgumentParser(description="给被看门狗收掉的在屏探针卷点出挂死的那条用例")
    parser.add_argument("log", help="`swift test --filter UIInteractionProbeTests` 的日志文件")
    parser.add_argument("--quiet", action="store_true", help="只打结论行，不打进度行")
    args = parser.parse_args(argv)

    try:
        with open(args.log, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except IOError as error:
        # 日志读不到**不是**"没跑完"，是仪器坏了：这里必须红，不能让 CI 那一步安静地绿过去。
        print("UI_PROBE_LOG_UNREADABLE=%s（%s）⇒ 这一格不许被读成『探针没事』" % (args.log, error))
        return 1

    lines, named = report(text)
    for line in lines:
        if args.quiet and line.startswith("UI_PROBE_PROGRESS"):
            continue
        print(line)
    print("UI_PROBE_NAMED=%d" % (1 if named else 0))
    return 0 if named else 1


if __name__ == "__main__":
    sys.exit(main())
