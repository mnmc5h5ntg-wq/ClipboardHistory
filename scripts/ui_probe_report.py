#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给"在屏探针那一卷被看门狗收掉"这件事**一个名字**（R86 / BACKLOG 92 路 a）。

背景（一句话版）：`.github/workflows/ci.yml` 的 `On-screen interaction probes` 那一步自带 240 秒
看门狗，到点 `kill -9`。R62 之前那一步在"没跑完"这条分支上只留一句解释
（"在屏探针在无头 runner 上不可用"），于是**整卷变成一张免检牌** —— R61 修的侧栏跟随选中
那三条行为判据就住在这卷里，它们的回归在 CI 上一条都没跑，而作业是绿的。
BACKLOG 92 要的就是这一步：**没跑完也要说清是哪一条没跑完**。

为什么这件事可以只读日志、不动判据代码（R86 当时的结论，见
`.scratch/motion-audit-2/r86_spike_partial_output.md`）：`swift test` 会把
`Test Case '-[Module.Class testX]' started.` 逐行打到 stdout，而本机一次实测（50 秒后 `kill -9`，
退出码 137）里这些行留在了日志里 ⇒ "started 减去 concluded" 就是挂死的那条。

**R88 把那句"留在日志里"判成了不成立**（`.scratch/motion-audit-2/r88_spike_partial_channel.md`）：
按 CI 的原样重跑，`kill -9` 收掉的是 `swift-test` 驱动进程，真正跑用例的 `xctest` 子进程
被 reparent 之后继续活着（一次活了 5 分钟并占着 `.build` 锁），而日志停在 119 字节、`started=0`。
⇒ 日志的沉默**不能**单独推出"用例没开始"。所以本脚本多了一个入参 `--runner-alive`：
成因由 CI 在收掉那一刻量的进程表决定，而不是由日志的缺席决定。

输出（每行一条，全大写标记，便于 CI 与台账 grep）。**这份清单是契约**：新增一格就要写进来，
而写进来就要有自己的测试格与自己的变异刀 —— 上一版这里停在 R88 的三格，R90 新加的那五格
如果不补进来，"注释里的那份输出格式"就又是一份替事实背书的旧账。

    UI_PROBE_PROGRESS started=N concluded=M
    UI_PROBE_HUNG=<用例名>              每条"开了口没结论"的用例一行（通常 0 或 1 条）
    UI_PROBE_ALL_CONCLUDED=1            每条 started 都有结论（这一卷跑完了）
    UI_PROBE_START_LINES_LOST=1         started 行整块丢了（runner 活着 ⇒ 用例在跑）
    UI_PROBE_NO_CASE_STARTED=1          连 xctest 都没起来 ⇒ 真死在启动阶段
    UI_PROBE_NO_START_LINE=1            只报观察：日志里没有 started 行，而今天没量到进程表
    UI_PROBE_NAMED=0|1                  这次停机**有没有名字**（0 = 只可能出现在脚本自己坏了）

R90 / BACKLOG 122 加的第二条通道（每条用例在 `setUpWithError()` 里写到自己文件上的一行心跳）：

    UI_PROBE_CHANNELS pulse=P started=N concluded=M     两条通道各给了多少证据
    UI_PROBE_HUNG_CHANNEL=pulse|started                 点出来的名字是哪条通道给的
    UI_PROBE_CHANNELS_AGREE=1                           两条点的是同一批（心跳不是孤证）
    UI_PROBE_CHANNELS_CONTRADICT pulse=… started=…      各点一条不同的 ⇒ 红，不许挑一个信
    UI_PROBE_PULSE_EMPTY=1                              接了通道、进程又活着，却一条都没有 ⇒ 通道坏了
    UI_PROBE_PULSE_UNREADABLE=<路径>                    --pulse 指错了文件（与"没有心跳"分开记）
    UI_PROBE_HUNG_LOG=<用例名>                          矛盾时把日志那条也打出来，换个标记

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

# R90 / BACKLOG 122 · 每条用例在 `setUpWithError()` 里写到自己文件上的心跳。
# 名字与 `CASE` 同一个命名空间（都是 `-[Module.Class testName]` 里抠出来的 `testName`），
# 所以两条通道可以对账；对不上时 `UI_PROBE_CHANNELS_CONTRADICT` 会红，而不是挑一个信。
PULSE = re.compile(r"^PROBE_PULSE ([A-Za-z0-9_]+)[ \t]*$", re.M)

# 崩溃/中止的旁证：有这些行时"没结论"是进程级的死法，不是某条用例的死法。
CRASH = ("Fatal error", "Precondition failure", "signal code ", "Killed", "error: Exited with unexpected signal")

# "这份文本是 CI 那一步的**汇报**，不是 `swift test` 的原始日志"的旁证。
# 为什么要有这一格：拿错文件时脚本会自信地报"进程在第一条用例之前就死了"，
# 而那是一句关于产品的假话（真相是我读错了文件）。见 `report()` 里那一格的注释。
ECHO_MARKERS = re.compile(r"ui suite exit:|##\[group\]|没有跑完（看门狗")


def report(text, runner_alive=None, pulse_text=None):
    """返回 (行列表, 是否给出了名字)。

    `runner_alive`：CI 那一步在**收掉进程的那一刻**量到的"跑用例的 xctest 还在不在"
    （1 / 0 / None=今天没量）。这一格是 R88 加进来的，因为它把 93 那两种成因分开了：

      * 1 ⇒ 用例确实开了口，日志里没有 started 行是**通道丢了**（SIGKILL 不 flush 块缓冲）；
      * 0 ⇒ 连 xctest 都没起来 ⇒ "死在启动阶段"这句话**才有资格说**；
      * None ⇒ 不知道 ⇒ 只报观察，不报成因。

    为什么不能只靠日志：R86 那句"本机实测 kill -9 之后 started 行留在日志里"是**一次**观察，
    而 R88 按 CI 原样重跑（`.scratch/motion-audit-2/spike_r88_ci_shape.sh`）读到的是
    `log_bytes=119 started=0` 而 xctest 活着 ⇒ 那句话不成立，它是第②种成因。
    """
    # R90 / BACKLOG 122 · 第二条通道：每条用例在 `setUpWithError()` 里往**自己的文件**写一行心跳。
    # 为什么不用 stderr（R89 我以为是）：`swift test … > ui.log 2>&1` 里 fd2 指向的是 SwiftPM 驱动的
    # 管道，驱动被 SIGKILL 时它那块缓冲一起丢 —— 本机实测：进程活着、已跑进第二条用例的方法体，
    # `ui.log` 仍是 119 字节（`.scratch/motion-audit-2/r90_findings_drag_hang_and_channel.md`）。
    # 放在最前面算：日志整块丢的时候（R88 的形状）它是**唯一**还有内容的通道，
    # 那时连"日志是空的"这一句都要让位给心跳点出来的名字。
    pulse = []
    if pulse_text:
        for match in PULSE.finditer(pulse_text):
            if match.group(1) not in pulse:
                pulse.append(match.group(1))
    if not text.strip():
        if pulse:
            # 日志一个字没有，而心跳有 ⇒ 通道丢了但用例确实开了口，而且知道是哪一条。
            # 这一格不许再报 `LOG_EMPTY` 那种"我没有它的输出"：我现在有它的输出，只是不在那份文件里。
            lines = ["UI_PROBE_PROGRESS started=0 concluded=0",
                     "UI_PROBE_CHANNELS pulse=%d started=0 concluded=0" % len(pulse),
                     "UI_PROBE_LOG_EMPTY=1 日志是空的（驱动那层被 SIGKILL，块缓冲整块丢）"]
            for name in pulse:
                lines.append("UI_PROBE_HUNG=%s" % name)
            lines.append("UI_PROBE_HUNG_CHANNEL=pulse")
            lines.append("UI_PROBE_START_LINES_LOST=1 "
                         "（日志空而心跳有 ⇒ 成因是通道丢，不是『一条用例都没开始』）")
            return lines, True
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
    pulse_hung = [n for n in pulse if n not in concluded]
    lines.append("UI_PROBE_CHANNELS pulse=%d started=%d concluded=%d"
                 % (len(pulse), len(started), len(concluded)))

    # 两条通道各点一条不同的"没结论" ⇒ 至少一条在说谎。这一格不许挑一个信：
    # 心跳在 setUp 第一行、started 在 XCTest 自己那里，两者对不上说明**其中一条通道被截断或串行**，
    # 而那正是这一族最贵的错（把仪器的不一致当成产品的答案）。
    if pulse_hung and hung and set(pulse_hung) != set(hung):
        lines.append("UI_PROBE_CHANNELS_CONTRADICT pulse=%s started=%s "
                     "（两条通道各自点出不同的那条 ⇒ 至少一条不可信，这一格不许挑一个信）"
                     % (",".join(pulse_hung), ",".join(hung)))
        for name in pulse_hung:
            lines.append("UI_PROBE_HUNG=%s" % name)
        for name in hung:
            lines.append("UI_PROBE_HUNG_LOG=%s" % name)
        return lines, False

    # 优先用心跳那条：它是**产品自己写的行**，而 started 那行要经过驱动的管道（会被整块带走）。
    names, channel = (pulse_hung, "pulse") if pulse_hung else (hung, "started")
    for name in names:
        lines.append("UI_PROBE_HUNG=%s" % name)
    if names:
        lines.append("UI_PROBE_HUNG_CHANNEL=%s" % channel)
    if pulse_hung and hung and set(pulse_hung) == set(hung):
        lines.append("UI_PROBE_CHANNELS_AGREE=1 （两条通道点的是同一批 ⇒ 心跳那条不是孤证）")
    # 接了心跳通道却一条都没有，而进程收掉时还活着 ⇒ 不是"用例没开始"，是**这条通道自己坏了**。
    # 这一格必须红：否则"我加了心跳"会变成一条没人验过的装饰（R88 那一族的反面）。
    if pulse_text is not None and not pulse and runner_alive == 1:
        lines.append("UI_PROBE_PULSE_EMPTY=1 心跳文件在、收掉那一刻 xctest 还活着，却一条心跳都没有 ⇒ "
                     "通道坏了（路径没对上、写盘失败、或 setUp 之前就没跑起来）。"
                     "这一格不许被读成『用例一条都没开始』，也不许退回 started 那条通道当结论")
        return lines, False

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
        # R143 审查轮（#26 的兄弟）：`ALL_CONCLUDED` 原来只看"每条 started 都有结论行"，
        # 而 `failed` 也是结论 ⇒ 一份"六条全红"的日志会被报成"这一卷跑完了"。
        # 红的那几条必须点名，且这一格的退出码要跟着红。
        red = sorted({name for name, verdict in CASE.findall(text) if verdict == "failed"})
        lines.append("UI_PROBE_CONCLUDED_RED=%d%s"
                     % (len(red), (" " + ",".join(red[:8])) if red else ""))
        lines.append("UI_PROBE_ALL_CONCLUDED=%d" % (0 if red else 1))
        return lines, not red
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
    # R88：到这里只剩"原始日志、零条 started 行"这一种形状，而它有两种成因。
    # 日志自己分不开 ⇒ 用 CI 在收掉那一刻量到的 `runner_alive` 分开（见 report 的 docstring）。
    if runner_alive == 1:
        # R90：这条通道接上之后，"没名字"这一句多半不再成立 —— 但它不许被删掉，
        # 因为心跳没接上的机器（本地手跑、老日志）仍然会走到这里，那时它就是实话。
        tail = ("『挂在哪一条』由心跳那条通道点出来了（上面的 UI_PROBE_HUNG / UI_PROBE_HUNG_CHANNEL=pulse）"
                if pulse_hung else
                "『挂在哪一条』仍然没有名字 —— 那需要每条用例自己写一行（BACKLOG 122，"
                "而它**不**能走 stderr：见 report() 里 R90 那段）")
        lines.append("UI_PROBE_START_LINES_LOST=1 "
                     "（收掉的那一刻 xctest 还活着 ⇒ 用例确实开了口，是驱动那层的缓冲被 SIGKILL 整块带走。"
                     "这一格取代 R86–R87 那句 `NO_CASE_STARTED`：那句当时是假话。%s）" % tail)
        return lines, True
    if runner_alive == 0:
        lines.append("UI_PROBE_NO_CASE_STARTED=1 "
                     "（收掉的那一刻连 xctest 都没起来 ⇒ 进程确实死在第一条用例开口之前。"
                     "这一句现在才有资格说，因为它的依据是那一瞬间的进程表，不是日志的沉默）")
        return lines, True
    lines.append("UI_PROBE_NO_START_LINE=1 "
                 "（日志里一条 `Test Case … started` 都没有。这一格**只报观察**："
                 "它不等于『进程死在第一条用例之前』—— 那需要 --runner-alive，今天没量到）")
    return lines, True


# ---------------------------------------------------------------------------
# R95 / BACKLOG 132：把"它是挂住还是只是慢"从一句话变成一份栈
# ---------------------------------------------------------------------------
# `sample <pid>` 的真实形状是**本机实测来的**（`/tmp/sample_probe_shape.txt`，
# 拿 `sleep` 当靶子）：`Call graph:` 下面是嵌套的调用树，每个节点前面是"落在这条路径上的采样数"，
# 线程行的形状是 `    534 Thread_21774250   DispatchQueue_1: com.apple.main-thread  (serial)`；
# 末尾那段 `Sort by top of stack, same collapsed (when >= 5):` **不拿来用**：它是跨线程汇总，
# 拿它算占比会把"只有主线程挂住"读成"散开"（见 `_dominant_path` 的文档串）。
# 为什么判"挂 vs 慢"要看**占比**而不是看有没有栈：一份 2 秒的栈里，如果 100% 的采样都落在同一个
# 等待帧上，那是挂；如果栈顶散在几处，那它是在往前走，只是慢 —— 这两种的处置完全不同
# （前者要修探针，后者要把看门狗调大并去量慢在哪一段）。
BLOCKING = (
    ("coredrag", ("_tryCatchDragUntilMouseUp", "CoreDragStartDraggingAsync",
                  "_BlockUntilNextEventMatchingListInMode")),
    ("menu-tracking", ("TrackMouse", "popUpContextMenu", "-[NSMenu", "menuNeedsUpdate")),
    ("runloop-wait", ("_BlockUntilNextEventMatchingListInMode", "CFRunLoopRunSpecific",
                      "mach_msg2_trap", "kevent")),
    ("sleep-wait", ("__semwait_signal", "__psynch_", "nanosleep", "wait4", "__workq_kernreturn")),
)
THREADED = re.compile(r"^\s*(\d+)\s+Thread_\d+.*main-thread", re.M)
NODE = re.compile(r"^(\s+)(\d+)\s+(.*)$", re.M)   # ← 少了 re.M 时 `^` 只认字符串开头：
# 第一版就是这样，于是"最深帧"永远读不到、族永远是 unknown，而**占比那一格仍然对**
# —— 一把一半坏一半好的尺最容易骗过人（它给的那个数看着是合理的）。
# 教训同 R90：新尺先在真产物上跑一遍，再拿合成件补它跑不到的形状。


def blocking_family(sym):
    """这一帧自己属不属于"停着不动"的那几族。不属于就 `unknown`（= 它在干活）。"""
    for name, toks in BLOCKING:
        if any(t in sym for t in toks):
            return name
    return "unknown"


def _dominant_path(nodes):
    """nodes = [(缩进, 采样数, 帧名)]（同一线程块内，按文件顺序）。返回 (叶子帧, 叶子采样数)。

    沿"每层采样数最大的那个孩子"一路走到底。为什么不能"取最后一个 count==total 的节点"
    （第一版的写法）：栈散开恰恰表现为**某一层的孩子各拿一部分**，那种时候没有任何孩子的
    count 等于 total，第一版就会退回"最后一个节点"并仍然报 100% —— 把**慢**读成**挂**。
    第一版还有个方向相反的错误：占比拿 `Sort by top of stack` 那段算，而那是**跨线程**汇总，
    一条只有主线程挂住的栈会因为别的线程也停在 mach_msg 上被判成"散开"。

    R96 起它只负责"主导路径占比"那一格**展示**；判定不再走它（走 `_waiting_leaves`）。
    原因见那里的文档串：并列的时候"挑一条最深路径"本身就是替栈做决定。
    """
    if not nodes:
        return "", 0
    leaf, count = nodes[0][2], nodes[0][1]
    while nodes:
        indent = nodes[0][0]
        level = [(i, n) for i, n in enumerate(nodes) if n[0] == indent]
        if not level:
            break
        best_i, best = max(level, key=lambda kv: kv[1][1])
        leaf, count = best[2], best[1]
        sub = []
        for n in nodes[best_i + 1:]:
            if n[0] <= indent:
                break
            sub.append(n)
        if not sub:
            break
        nodes = sub
    return leaf, count


def _waiting_leaves(nodes):
    """返回 [(等待终端帧, 采样数)]：主线程里"停在等待帧上、且下面再没有等待帧"的那些终端。

    为什么不是"最外层那个等待帧的子树整体算一份"（我第一反应就是这么写的）：等待帧常常**套着**
    别的等待帧（`_BlockUntilNextEventMatchingListInMode` 里是 `ReceiveEvents`，再里面是
    `_tryCatchDragUntilMouseUp`），套几层就把同一批采样数几遍；而反过来只取最外层，
    在**并列**的时候就会替栈挑一个答案 —— 600 个采样里 300 停在菜单跟踪、300 停在 `mach_msg2_trap`，
    最外层只有一个 `_CFRunLoopRunSpecific`，只报它就是"挂在菜单上"这句没有依据的话
    （BACKLOG 137 点名的正是这一格：变异 M527 把"取最后一个孩子"改成"取第一个"，
    旧尺子照样绿，因为它只打印一条路径，而那条路径本来就是被挑出来的）。

    终端的定义是递归的：一个等待帧，如果它的子树里还有等待帧，就不算终端（那些更深的算）。
    这样每个采样恰好落在一个终端上，`sum(count)` 就是"停在等待上的采样数"。
    """
    out = []
    n = len(nodes)

    def walk(i):
        indent, count, sym = nodes[i]
        k = i + 1
        inner = []
        while k < n and nodes[k][0] > indent:
            k, got = walk(k)
            inner.extend(got)
        if blocking_family(sym) != "unknown" and not inner:
            return k, [(sym, count)]
        return k, inner

    i = 0
    while i < n:
        i, got = walk(i)
        out.extend(got)
    return out


def analyse_sample(text):
    """返回 (读数行, 判定)。判定 ∈ {blocked@<族>, blocked@ambiguous, progressing, 未量到}。"""
    if not text or "Call graph:" not in text:
        return (["UI_PROBE_SAMPLE_UNAVAILABLE=1 这份 sample 里没有 `Call graph:` ⇒ "
                 "132 那句「它到底是挂还是慢」今天仍**没有依据**，不许被读成「它只是慢」"]), "未量到"
    m = THREADED.search(text)
    if not m:
        return (["UI_PROBE_SAMPLE_NO_MAIN_THREAD=1 有 `Call graph:` 却找不到主线程那一行 ⇒ "
                 "这份栈不是我们要的那份（靶子换了？），不判"]), "未量到"
    total = int(m.group(1))
    block = text[m.end():]
    stop = re.search(r"^\s*\d+\s+Thread_\d+", block, re.M)
    block = block[:stop.start()] if stop else block
    nodes = [(len(n.group(1)), int(n.group(2)), n.group(3)) for n in NODE.finditer(block)]
    if not nodes:
        # R96 在 runner 上真的撞到了这一格：`sample` 退出码 0、有 `Call graph:`、
        # 主线程那一行也读到了 306 个采样，**但那一段里一个节点都没匹配上**。
        # 旧写法在这里会把占比兜底成 1.0 ⇒ 打出 `blocked@unknown`，
        # 而"unknown + 100%"读起来像"它挂在某个我们不认识的帧上"——
        # 那句话没有任何依据：真实情况是我读不懂这份文件。
        # 所以：不判，并且把**形状**打出来（缩进宽度、有没有以数字开头、NODE 是否命中）。
        # 只打形状不打内容，是因为台账有一条硬规矩：日志里不许出现用户的剪贴板内容，
        # 而栈帧名理论上会带上被处理的字符串——诊断"我的正则读不到什么"不需要看帧名。
        shape = []
        for line in block.splitlines()[:8]:
            if not line.strip():
                continue
            stripped = line.lstrip(' ')
            shape.append('缩进%d 数字开头=%s 长度=%d' % (
                len(line) - len(stripped), 'yes' if re.match(r'^\d+\s', stripped) else 'no',
                len(line)))
        return (["UI_PROBE_SAMPLE_UNPARSED=1 主线程采样=%d 但那一段里 NODE 命中 0 个 ⇒ "
                 "132 那句「它到底是挂还是慢」今天仍**没有依据**（读不懂文件 ≠ 它挂在未知帧上）"
                 % total,
                 "UI_PROBE_SAMPLE_SHAPE 前若干行=%s"
                 % (' | '.join(shape) or '整段为空')], "未量到")
    leaf, leaf_count = _dominant_path(nodes)
    dom_share = (float(leaf_count) / total) if total else 0.0
    terminals = _waiting_leaves(nodes)
    waited = sum(c for _, c in terminals)
    wait_share = (float(waited) / total) if total else 0.0
    fams = sorted(set(blocking_family(sym) for sym, _ in terminals))

    # 判定走**等待占比**，不走主导路径占比。这两格在"一条链挂到底"的栈里是同一个数，
    # 分岔的时候才分开：主导路径占比会因为"孩子各拿一部分"掉到 50%，
    # 而那些孩子**全都是等待帧** —— 那仍然是挂，只是这份栈说不清挂在哪一件事上。
    # 用旧的那一格判，就会把"挂在两件事上"读成"它在往前走"（方向反了的第二种形状）。
    lines = ["UI_PROBE_SAMPLE 主线程采样=%d 等待帧占比=%.0f%% 主导路径占比=%.0f%% 等待终端=%d 个"
             % (total, wait_share * 100.0, dom_share * 100.0, len(terminals))]
    if terminals:
        lines.append("UI_PROBE_SAMPLE_WAITING=" + " ‖ ".join(
            "%s(%d)" % (sym[:70], count) for sym, count in terminals))
    if wait_share >= 0.9 and len(fams) == 1:
        verdict = "blocked@%s" % fams[0]
        lines.append("UI_PROBE_HUNG_KIND=%s ⇒ %.0f%% 的采样都停在同一族的等待帧上（132 分诊：挂）"
                     % (verdict, wait_share * 100.0))
    elif wait_share >= 0.9:
        verdict = "blocked@ambiguous"
        lines.append("UI_PROBE_SAMPLE_TIED=%d 个族分不开：%s ⇒ **挂**是判出来了，"
                     "挂在**哪一件**上这份栈没给答案。不许只挑其中一个写成结论（137）"
                     % (len(fams), "、".join("%s=%d" % (f, sum(c for sym, c in terminals
                                                            if blocking_family(sym) == f))
                                             for f in fams)))
        lines.append("UI_PROBE_HUNG_KIND=%s ⇒ 132 分诊：挂，但族未定" % verdict)
    else:
        verdict = "progressing"
        lines.append("UI_PROBE_HUNG_KIND=progressing ⇒ 只有 %.0f%% 的采样停在等待帧上，"
                     "其余在干活：**不是挂死，是慢**（132 要修的是看门狗与耗时归因，不是探针）"
                     % (wait_share * 100.0))
    return lines, verdict


def main(argv=None):
    parser = argparse.ArgumentParser(description="给被看门狗收掉的在屏探针卷点出挂死的那条用例")
    parser.add_argument("log", help="`swift test --filter UIInteractionProbeTests` 的日志文件")
    parser.add_argument("--quiet", action="store_true", help="只打结论行，不打进度行")
    parser.add_argument("--runner-alive", default=None,
                        help="收掉进程那一刻 xctest 的数量（CI 量的：1=用例在跑⇒日志丢了；"
                             "0=没起来⇒真没开始；不传=只报观察不报成因）")
    parser.add_argument("--pulse", default=None,
                        help="每条用例在 setUpWithError 里写的心跳文件（BACKLOG 122）。"
                             "不传=这条通道没接线；传了而文件读不到=按空内容处理，"
                             "由 `--runner-alive` 决定那是不是通道坏了")
    parser.add_argument("--sample", default=None,
                        help="R95 / BACKLOG 132：看门狗收掉之前对那条 xctest 做的 `sample` 文本。"
                             "不传=这条通道没接线；传了而文件读不到/没有 `Call graph:`=报"
                             "『未量到』，不许把 132 那句「挂还是慢」读成任何一种")
    args = parser.parse_args(argv)

    alive = None
    if args.runner_alive not in (None, "", "?"):
        try:
            alive = 1 if int(args.runner_alive) > 0 else 0
        except ValueError:
            # 传进来的不是数字（CI 那一步自己坏了）⇒ 不许猜，回到"只报观察"那一格。
            print("UI_PROBE_RUNNER_ALIVE_UNPARSED=%s ⇒ 这一格不许被读成『已分出成因』" % args.runner_alive)
            alive = None

    try:
        with open(args.log, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except IOError as error:
        # 日志读不到**不是**"没跑完"，是仪器坏了：这里必须红，不能让 CI 那一步安静地绿过去。
        print("UI_PROBE_LOG_UNREADABLE=%s（%s）⇒ 这一格不许被读成『探针没事』" % (args.log, error))
        return 1

    pulse_text = None
    if args.pulse is not None:
        try:
            with open(args.pulse, encoding="utf-8", errors="replace") as handle:
                pulse_text = handle.read()
        except IOError as error:
            # 心跳文件读不到**不是**"没有心跳"：路径没对上与 setUp 没跑到长得一样，
            # 但只有后者是关于产品的。这里按空内容走，让 PULSE_EMPTY 那一格去判，
            # 同时把"我读不到"这件事本身打出来（它不许被静默吞掉）。
            print("UI_PROBE_PULSE_UNREADABLE=%s（%s）⇒ 这一格不许被读成『心跳通道正常』"
                  % (args.pulse, error))
            pulse_text = ""

    lines, named = report(text, alive, pulse_text)
    for line in lines:
        if args.quiet and line.startswith("UI_PROBE_PROGRESS"):
            continue
        print(line)
    if args.sample is not None:
        sample_text = None
        try:
            with open(args.sample, encoding="utf-8", errors="replace") as handle:
                sample_text = handle.read()
        except IOError as error:
            print("UI_PROBE_SAMPLE_UNREADABLE=%s（%s）⇒ 这一格不许被读成『采样通道正常』"
                  % (args.sample, error))
            sample_text = ""
        for line in analyse_sample(sample_text)[0]:
            print(line)
    # R143 / BACKLOG 176：把帧间隔的三臂读数**转发**进 CI 日志。
    # 为什么要在这一层转发：探针那三行原来走 `print`（块缓冲，进程被看门狗收掉就没了），
    # 改成 `emit` 之后它们进了 /tmp/ui.log —— 但那份日志不上传，CI 里还是看不见，
    # 于是"收紧预算"这件事依旧没有依据。缺席必须自己报一行，不许静默。
    fps = [line.strip()[:240] for line in text.splitlines() if "PROBE_FPS" in line]
    if fps:
        for line in fps[-4:]:
            print("FORWARDED " + line)
    else:
        print("UI_PROBE_FPS_ABSENT=1 这一卷的日志里没有 PROBE_FPS 行 ⇒ 那条用例没跑完，"
              "或者读数没走 emit ⇒ BACKLOG 176 的收紧仍然没有 runner 依据（不许读成「没有回归」）")

    print("UI_PROBE_NAMED=%d" % (1 if named else 0))
    return 0 if named else 1


if __name__ == "__main__":
    sys.exit(main())
