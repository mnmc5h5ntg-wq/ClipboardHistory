#!/usr/bin/env python3
"""CI 汇报行自检：把 ci.yml 里几步的 run 脚本**原文**抽出来，
只把"被测命令"换成夹具，然后喂几种日志形状，断言**结论行必然打出来**。

R36 起它多了一类客户：`Capture gate` 那一步是**硬门**（没有 continue-on-error），
四个形状各钉一种骗人方式 —— 真红被吞 / 已知盲区被当成红 / 整批退回 skip / 干脆没跑到用例。
其中"真红"那一格喂的是 run 38473962277 的**逐字日志**（`fixtures/r36_runner_capture.log`），
所以这里测的是"那道门会不会红在它该红的地方"，不是"它会不会红"。
顺带：这一步第一次以"作者自己改坏了"的方式证明自己在岗 —— R36 改了捕获步骤的名字，
`STEPS[...]` 那个 marker 立刻 `ValueError: substring not found`（改名要同时改这里，钉得住）。

为什么要有这个文件（实测 run 38062956819）：那两步在 `bash -e` + `set -o pipefail` 下，
**汇报行自己的** `grep -oE 'Executed [0-9]+ tests'` 失手了 —— runner 只打单数
"Executed 1 test"，grep 返回 1，赋值语句非零 ⇒ 脚本当场中止 ⇒ 又退回"红了但没有数字"，
而"报告型"存在的唯一理由就是留数字。（被测命令那层的 `|| true` 挡不住这一层。）

规矩落在代码里：抽取行必须自带 `|| true`，且要能匹配单数。
跑法：python3 scripts/tests/test_ci_report_selftest.py [ci.yml 路径]
（文件名按 scripts/tests 的 `test_*.py` 约定，才能被 CI 的 `unittest discover` 收到。）
对旧版 ci.yml 跑它会报"结论行缺失"（已实测），这就是这条守卫不是装饰的证据。
退出码 0 = 全部形状合格。
"""

import os
import re
import shutil
import signal
import subprocess
import tempfile
import sys
import textwrap
import unittest
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CI_DEFAULT = os.path.join(ROOT, ".github", "workflows", "ci.yml")

STEPS = {
    "offscreen": "Offscreen frame capture (report-only, gated below)",
    "onscreen": "On-screen interaction probes (report-only)",
    "motion": "Motion filmstrip (report-only)",
    "motion_floor": "Motion coverage floor",
    # R36：这一步是**硬门**（没有 continue-on-error）。它读上一步留下的 /tmp/frames.log，
    # 所以要和 motion_floor 一样把夹具挂在"第一行抽取"上 —— 测的仍然是 ci.yml 里那一句本身。
    "capture_gate": "Capture gate (unregistered reds must be zero)",
}

GATE_FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "fixtures", "r36_runner_capture.log")
with open(GATE_FIXTURE, encoding="utf-8") as _handle:
    REAL_RUNNER_LOG = _handle.read()


def _passed_lines(n):
    return "".join("Test Case '-[ClipboardHistoryAppTests.UICaptureTests test%02d]' passed (0.001 seconds).\n"
                   % i for i in range(n))


def _skipped_lines(n):
    return "".join("Test Case '-[ClipboardHistoryAppTests.UICaptureTests test%02d]' skipped (0.001 seconds).\n"
                   % i for i in range(n))

# 被测命令 → 夹具。命中次数必须恰好 1，否则说明 ci.yml 改了写法、夹具已经失效。
SUBSTITUTIONS = {
    "offscreen": [
        # 被测命令现在多了一段真过滤器（`| sed '/Unrecognized colorspace number/d' | tee frames.log`）。
        # 夹具因此只替到 **raw 那一层**：让 ci.yml 里那段 sed 真的跑起来，
        # 否则改了过滤器而自检还在测旧形状，噪声回归时没人会红。
        (r"CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci \\\n\s*"
         r"swift test --filter UICaptureTests 2>&1 \| tee /tmp/frames-raw\.log"
         r" \| sed '/colorspace/d' \| tee /tmp/frames\.log",
         # 整段管道一起替掉，但**把那段 sed 原样搬进夹具**：只替前半截会让
         # /tmp/frames.log 根本不生成（实测第一次就是这么红的），而"过滤器仍在链上"
         # 正是这次改动唯一需要被证明的事。
         "cp FAKE_LOG /tmp/frames-raw.log"
         "; sed '/colorspace/d' /tmp/frames-raw.log | tee /tmp/frames.log"),
    ],
    "onscreen": [
        # 环境变量那一串允许**任意多行续行**：R90 加了 `CLIPBOARD_HISTORY_PROBE_PULSE=/tmp`，
        # 而上一版这里写死了"env 行紧跟 swift test"⇒ 自检当场红在锚点上（这正是它存在的意义：
        # 步骤正文一改，夹具替换没落地就会红，而不是静默地"没执行到真命令"）。
        (r"CLIPBOARD_HISTORY_UI_INTERACTION=1[^\n]*\n"
         r"(?:\s*[A-Z_]+=\S*[^\n]*\\\n)*"
         r"\s*swift test --filter UIInteractionProbeTests > /tmp/ui\.log 2>&1 &",
         "cp FAKE_LOG /tmp/ui.log &"),
    ],
    # R59：告警闸门那一步的夹具（真命令要在自检里被替成 cp 假日志）。
    "build": [],
    "motion": [
        (r"CLIPBOARD_HISTORY_UI_MOTION=1 CLIPBOARD_HISTORY_MOTION_OUT=/tmp/motion-ci \\\n\s*"
         r"swift test --filter MotionFilmstripTests > /tmp/motion\.log 2>&1 &",
         "cp FAKE_LOG /tmp/motion.log &"),
        # R56 / BACKLOG 79：补读那一段找的是**真实 CI 的输出目录**。自检必须把它换到自己的
        # 临时目录（R92 起 `run_bash` 把**所有** `/tmp…` 都换掉，不再只换 `/tmp/shots-ci`），
        # 否则它读的是开发机上恰好存在的
        # 一份旧读数 —— 那种夹具会在"本机跑过 motion suite"之后凭空变绿或变红。
        (r"readings=/tmp/motion-ci/motion-readings\.log",
         # `rm -f` 不是多余：这个临时目录在**同一遍里跨格复用**（R92 / M514 之后每遍一个新目录，
         # 但同一遍里上一格留下的读数文件仍然会让
         # "两条通道都空"那一格读到东西而凭空变绿（实测第一次就是这么红的）。
         "rm -f /tmp/shots-ci/motion-readings.log; readings=/tmp/shots-ci/motion-readings.log"),
    ],
    # 这一步没有"被测命令"：它读上一步留下的 /tmp/motion.log。
    # R46（BACKLOG 66）之后那一步是一句 `python3 scripts/motion_floor_gate.py …`，
    # 所以夹具挂在它身上：先落一份日志，再用**绝对路径**跑脚本
    # （自检的 cwd 不一定是仓库根，两个相对参数都得换掉 —— `capture_gate` 那一条就是这么做的）。
    "motion_floor": [
        (r"python3 scripts/motion_floor_gate\.py /tmp/motion\.log",
         "cp FAKE_LOG /tmp/motion.log; python3 " + os.path.join(ROOT, "scripts", "motion_floor_gate.py")
         + " /tmp/motion.log"),
        (r"--expectations scripts/motion_floor_expectations\.json",
         "--expectations " + os.path.join(ROOT, "scripts", "motion_floor_expectations.json")),
    ],
    # R36 的硬门：它没有"被测命令"，只有"读上一步留下的日志再判"。
    # 所以夹具挂在 `cp` 上，脚本路径换成绝对路径（自检的 cwd 不一定是仓库根）。
    "capture_gate": [
        (r"python3 scripts/ci_capture_gate\.py /tmp/frames\.log",
         # R64 / BACKLOG 96：这道门现在**要求**第二条读数通道，所以自检必须自己造一份，
         # 而且要先把上一格留下的删掉 —— 这个临时目录跨格复用，残留的读数文件会让
         # "通道缺文件"那一格凭空变绿（R56 的 motion 那一格是同一个坑，见上面那条 `rm -f`）。
         # 造的内容就是从同一份假日志里抄读数行 ⇒ "并集补回 0 行"是这里的默认形状，
         # 而"补回 k>0"与"缺文件必须红"由 scripts/tests/test_ci_capture_gate.py 逐条判。
         "cp FAKE_LOG /tmp/frames.log; "
         "mkdir -p /tmp/shots-ci; rm -f /tmp/shots-ci/capture-readings.log; "
         "grep -E '^(CAPTURE_|MATERIAL_BLIND|SPARSE_|TEXT_SIDE|INK_SIDE|DISABLED_STATE|PROBE_DOMAIN"
         "|DISCRIMINATOR_ARM)' /tmp/frames.log > /tmp/shots-ci/capture-readings.log || true; "
         "python3 " + os.path.join(ROOT, "scripts", "ci_capture_gate.py") + " /tmp/frames.log"),
        # 这一条替换是**接线断言**：命中不了 ⇒ ci.yml 里那道门不再带 `--readings`，
        # 也就是 BACKLOG 96 的修法被悄悄撤掉了 —— 那种撤掉不会让上面任何一格变红，
        # 只会让"这次只剩一条腿"重新变成看不出来的事。
        (r"--readings /tmp/shots-ci/capture-readings\.log",
         "--readings /tmp/shots-ci/capture-readings.log"),
    ],
}

SINGULAR = ("Test Suite 'UICaptureTests' failed\n"
            "\t Executed 1 test, with 2 failures (0 unexpected) in 11.218 (11.218) seconds\n")
TRUNCATED = "Test Case '-[p probeA]' started.\n"
NORMAL = ("Test Suite 'All tests' passed\n"
          "\t Executed 12 tests, with 3 tests skipped and 0 failures (0 unexpected) in 4.0 (4.1) seconds\n")

# 动效那一步的结论行必须带上 MOTION_SUMMARY 本体（报告 MC-8 的要点：正文要能被读出来），
# 所以夹具里给它一份"跑完了并且报了三个数"的日志。
MOTION_NORMAL = (NORMAL
                 + "MOTION_SUMMARY notice-banner=3 detail-kind-change=3 empty-state=4\n"
                 + "MOTION_RESOLVE_SUMMARY judged=3/3 not-run=-\n")

# R46：地板现在按**登记表**判，而表里是今天 `Scenario.all()` 的四臂。
# 上面那份三臂日志留给"报告型那一步"用（它只 echo 读数，不查形状），
# 地板那六格必须用这一份 —— 否则每一格都会先红在 MISSING_KEY 上，测的就不是它想测的事了。
# R85 / BACKLOG 118：地板那一层的"一次完整运行"现在包含常驻循环的两行状态。
# 挂在 FLOOR_SUMMARY 上而不是逐格改七个场景，是因为这七格测的都是"臂一级的形状"，
# 循环那一族对它们全是背景条件 —— 背景条件缺了会让每一格多两朵 LOOP_SILENT 红，
# 而"缺席要红"这件事由 scripts/tests/test_motion_floor_gate.py 的
# `testLoopStateLinesAreCountedNotGuessed` 专门判（一处判一件事）。
FLOOR_SUMMARY = ("MOTION_SHIMMER_STATE 判定=ok 原因=-\n"
                 "MOTION_SHIMMER_BAND_STATE 判定=ok 原因=-\n"
                 "MOTION_SUMMARY notice-banner=3 notice-banner-dismiss=3 "
                 "detail-kind-change=3 empty-state=4 settings-reset-fade=2")

# (步骤, 形状) → (日志正文, 必须出现的结论片段, 期望退出码, 额外替换)
#
# 第四项是给"看门狗自己先退出"那个形状用的：实测 run 38064293655 里在屏步骤**仍然没有结论行**，
# 但根因换了 —— 不是抽取失手，是 `kill "$killer" 2>/dev/null`：看门狗执行完 kill 就退出，
# 父脚本再 kill 它得到 "No such process"（返回 1），`bash -e` 在这行中止，下面的 echo 一行都轮不到。
# 本地前三形状测不到它，因为夹具里的被测命令瞬间就成功了，killer 还活着。
# 所以这一格把 watchdog 换成 `( exit ) &`、把被测命令换成慢作业，让 `kill "$killer"` 必然落到已退出的进程上。
EXPECT = {
    ("offscreen", "singular_summary"): (SINGULAR, ["captured frames:"], 0, []),
    # 抽取落空时 offscreen 的 `test executed -ge 1` 应当给 1，但**结论行必须先打出来**
    ("offscreen", "truncated_log"): (TRUNCATED, ["captured frames:"], 1, []),
    ("offscreen", "normal"): (NORMAL, ["captured frames:"], 0, []),
    # 兜不住 find 的那格：目录不存在时 `find | wc | tr` 在 pipefail 下也是非零
    ("offscreen", "missing_shots_dir"): (NORMAL, ["captured frames:"], None,
                                         [(r"/tmp/shots-ci", "/tmp/definitely-not-here-xyz")]),
    # R88 起还要看到那两行新读数：它们是本轮唯一能分开"没开始"与"日志丢了"的东西。
    ("onscreen", "singular_summary"): (SINGULAR, ["ui suite exit:",
                                              "UI_PROBE_ORPHAN_XCTEST=",
                                              "UI_PROBE_RUNNER_ALIVE="], 0, []),
    # 看门狗收掉进程就是这个形状：旧脚本在这里中止，"没有跑完"那条分支永远走不到
    ("onscreen", "truncated_log"): (TRUNCATED, ["ui suite exit:", "没有跑完",
                                          "UI_PROBE_ORPHAN_XCTEST=0"], 0, []),
    ("onscreen", "normal"): (NORMAL, ["ui suite exit:"], 0, []),
    ("onscreen", "watchdog_already_exited"): (
        TRUNCATED, ["ui suite exit:", "没有跑完"], 0,
        # R88：看门狗从一行变成了一段（收掉之前先量进程表 + 改成杀进程组）。
        # 夹具的锚点跟着改成"整段子壳"，并且**必须命中**：命中 0 次就是 ci.yml 又改了写法。
        [(r"\( sleep 240[\s\S]*?\) &", "( exit ) &"),
         (r"cp \S+ /tmp/ui\.log &", "( cp FAKE_LOG /tmp/ui.log; sleep 1 ) &")]),
    ("motion", "normal"): (MOTION_NORMAL, ["motion suite exit:", "MOTION_SUMMARY",
                                           "MOTION_RESOLVE_SUMMARY"], 0, []),
    # R59 / BACKLOG 86：红的那一支必须把**那一句为什么**一起打出来。
    # 现场：run 38576482491 里 `testTransitionsAreActuallyRunning` 红了 7.4s（`motion suite exit: 1`），
    # 而整步日志只有名字 —— XCTAssert 那句在 /tmp/motion.log 里，那个文件不上传。
    # "runner 上为什么红"只能靠猜，而这一族猜错过一次（R51 那条红得不正确的判据）。
    # 这一格同时是那条 grep 的正对照：把 `error: -[` 那两行删掉，"一帧跳变"就不会出现在输出里。
    ("motion", "red_test_prints_its_reason"): (
        MOTION_NORMAL
        + "Test Case '-[ClipboardHistoryAppTests.MotionFilmstripTests "
          "testTransitionsAreActuallyRunning]' failed (7.443 seconds).\n"
        + 'error: -[ClipboardHistoryAppTests.MotionFilmstripTests '
          "testTransitionsAreActuallyRunning] : XCTAssertLessThanOrEqual failed: "
          '(260) is greater than (75) - 这是一帧跳变，不是过渡\n',
        ["testTransitionsAreActuallyRunning", "一帧跳变"], 0, []),
    # R58 / BACKLOG 83：**没有任何白名单提到过的读数族**也必须出现在 CI 日志里。
    # 这一格的理由很具体：R55 加了 MOTION_GRAB、R57 加了 MOTION_BAND，而那一步的摘录
    # 用的是一份写死的前缀列表 ⇒ "runner 上带捕获到底成没成功"在 run 38570965657 的日志里查不到
    # （只有 `judged=4/4`，而带捕获之前的 R56 也是 4/4 ⇒ 两个形状分不开）。
    # 它同时是那条改动的**正对照**：把 grep 改回白名单，这一格立刻红。
    ("motion", "family_not_in_any_list"): (
        MOTION_NORMAL + "MOTION_BAND dismiss 带：位置同一性 带vs整窗头=0.000\n",
        ["motion suite exit:", "MOTION_BAND", "MOTION_LINES=3"], 0, []),
    # 看门狗收掉进程 ⇒ 必须走 "MOTION_NOT_RUN" 那一支并且退出码 0（报告型不挡发布）
    ("motion", "truncated_log"): (TRUNCATED, ["motion suite exit:", "MOTION_NOT_RUN"], 0, []),
    ("motion", "watchdog_already_exited"): (
        TRUNCATED, ["motion suite exit:", "MOTION_NOT_RUN"], 0,
        [(r"\( sleep 200; kill -9 \"\$pid\" 2>/dev/null \) &", "( exit ) &"),
         (r"cp \S+ /tmp/motion\.log &", "( cp FAKE_LOG /tmp/motion.log; sleep 1 ) &")]),
    # 结论行丢了 MOTION_SUMMARY 时（比如抽取失手）这一格要红：它保证"跑过"和"读出内容"是两件事
    ("motion", "summary_missing_from_log"): (NORMAL, ["motion suite exit:", "无 MOTION_SUMMARY"], 0, []),
    # R56 / BACKLOG 79 的正对照：**stdout 一条读数都没有，而文件通道有**。
    # 这一步必须自己喊出 `MOTION_STDOUT_LOST=1` 并把结论行并进日志 ——
    # 少了这一格，"补读"这段脚本就只是我声称存在的东西（它挡的是下一次 38543090198）。
    ("motion", "stdout_lost_but_file_channel_recovers"): (
        NORMAL,
        ["motion suite exit:", "MOTION_CHANNEL_UNIONED=1", "MOTION_RESOLVE_SUMMARY judged=4/4"], 0,
        [(r"readings=/tmp/shots-ci/motion-readings\.log",
          "mkdir -p /tmp/shots-ci; printf 'MOTION_SUMMARY notice-banner=3 notice-banner-dismiss=3 "
          "detail-kind-change=3 empty-state=4\\nMOTION_RESOLVE_SUMMARY judged=4/4 not-run=-\\n' "
          "> /tmp/shots-ci/motion-readings.log; readings=/tmp/shots-ci/motion-readings.log")]),
    # 两条通道都空 ⇒ 不许静默：必须打出 `MOTION_READINGS_FILE_ABSENT=1`。
    # 上面两格合起来钉的是**并集**这件事：
    # `stdout_lost…` 那格是"整片丢"（stdout 0 行、文件 2 行），
    # `partial…` 这格是"半丢"（stdout 只剩 SUMMARY，结论行只在文件里）——
    # 真实观测到的正是第二种：结论行活着、理由行死了。
    # 如果实现写成"文件覆盖 stdout"，这一格的 MOTION_SUMMARY 会被扔掉，
    # 地板就会红在 MISSING_KEY 上 —— 那是把**修通道**做成**造新红**。
    ("motion", "partial_stdout_loss_recovers_resolve"): (
        NORMAL + "MOTION_SUMMARY notice-banner=3 notice-banner-dismiss=3 "
                 "detail-kind-change=3 empty-state=4\n",
        # 三条都要：`MOTION_SUMMARY` 必须**仍然在**（它只来自 stdout 那一半）。
        # 只断言"结论行被补回来了"的话，把并集写成"文件覆盖 stdout"也能通过，
        ["MOTION_CHANNEL_UNIONED=1 stdout=1 文件=1", "MOTION_RESOLVE_SUMMARY judged=4/4",
         "MOTION_SUMMARY notice-banner=3"], 0,
        [(r"readings=/tmp/shots-ci/motion-readings\.log",
          "mkdir -p /tmp/shots-ci; printf 'MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-\\n' "
          "> /tmp/shots-ci/motion-readings.log; readings=/tmp/shots-ci/motion-readings.log")]),
    # 两条通道都空 ⇒ 不许静默：必须打出 `MOTION_READINGS_FILE_ABSENT=1`，
    # 让下一步的 NO_RESOLVE 红有一个**前因**可查（R36 那条"红必须有名字"）。
    ("motion", "both_channels_empty_is_named"): (
        NORMAL, ["MOTION_READINGS_FILE_ABSENT=1", "无 MOTION_RESOLVE_SUMMARY"], 0, []),
    # R2 新增的形状：有 MOTION_SUMMARY 但没有"今天判了几条" ⇒ 结论行必须自己喊出来。
    # 少这一格，"判据悄悄退化成只判一条"在 CI 上是看不见的。
    ("motion", "resolve_missing_from_log"): (
        NORMAL + "MOTION_SUMMARY notice-banner=3 detail-kind-change=3 empty-state=4\n",
        ["motion suite exit:", "MOTION_SUMMARY", "无 MOTION_RESOLVE_SUMMARY"], 0, []),
    # 红必须可解释：只有 "exit 1" 的一步等于没有这一步（本轮 run 38256846956 就是这个形状）。
    # 所以给它一份"有一条判据红了 + 各条读数都在"的日志，要求两样都出现在结论里。
    ("motion", "failing_test_names"): (
        MOTION_NORMAL
        + "MOTION_NATIVE row-insert 开 帧数=11 峰值=0.042 采样≈9ms\n"
        + "Test Case '-[ClipboardHistoryAppTests.MotionFilmstripTests testSkeletonSweepActuallySweeps]'"
          " failed (0.123 seconds).\n",
        ["motion suite exit:", "MOTION_NATIVE", "testSkeletonSweepActuallySweeps"], 0, []),
    # ---- R7 开的首版地板（`judged<2`）只管"判够没判够"；R46（BACKLOG 66）之后这一步交给
    #      `scripts/motion_floor_gate.py`，形状从"一个数"变成"谁在、谁不在、不在的理由登记过没有"。
    #      下面六格各钉一种骗人方式，缺任何一格，那一族就能从闸门里漏过去。
    #      注意这些日志都是**四臂形状**（今天的 `Scenario.all()`），
    #      而 `MOTION_NORMAL` 是三条判据那一辈的 —— 拿它喂新的地板会红在 MISSING_KEY，
    #      那不是这一格要判的事，所以这里各写各的。
    ("motion_floor", "enough_coverage"): (
        NORMAL + FLOOR_SUMMARY + "\nMOTION_RESOLVE_SUMMARY judged=5/5 not-run=-\n",
        ["MOTION_FLOOR_FACTS", "MOTION_FLOOR_OK=5/5"], 0, []),
    # R44 的真实形状：掉了一臂，但理由登记过 ⇒ 放行，**且必须把这条打印出来**。
    # 旧版这一步在这里连"掉了谁"都不说，所以我是靠人肉对比 run 日志发现的。
    # 这一格跟着清单改过两次期望：R57 收紧到四臂必须判到 ⇒ 同一条日志是红；
    # R75 按实测把 `notice-banner` 一臂放回放行（地板 4⇒3）⇒ **仍要求判到的那三臂少一条还是红**，
    # 所以这里换成"掉的是 dismiss 且 judged 掉到地板以下"，红仍然只可能来自地板。
    # 留着这一格的意义正在这里：清单变严/变松时，它会逼着有人回来改期望，
    # 而不是让"闸门今天到底要求几条"这件事只活在 JSON 里。
    ("motion_floor", "drift_on_a_required_arm_is_red_while_floor_is_three"): (
        NORMAL + FLOOR_SUMMARY + "\n"
        + "MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：事件段最粗 101ms\n"
        + "MOTION_RESOLVE_SUMMARY judged=2/4 not-run=notice-banner-dismiss\n",
        ["MOTION_FLOOR_FACTS judged=2/4", "not-run=notice-banner-dismiss",
         "MOTION_FLOOR_UNDERCOVERED", "MOTION_FLOOR_REDS=1"], 1, []),
    # R75 的新形状：`notice-banner` 判不到，理由是"证人合格且自己也 snap" ⇒ **不挡发布，但要点名**。
    # 这一格钉的是这次放宽的两半：只放行不点名，就是 BACKLOG 49 说的免检牌；
    # 只点名不放行，runner 那一臂就会变成恒红（R39 那一族：恒红的守卫最后被人删掉）。
    ("motion_floor", "witness_snaps_here_is_named_uncoverage"): (
        NORMAL + FLOOR_SUMMARY + "\n"
        + "MOTION_NOT_RUN=witness-snaps-here notice-banner：证人采样≈32ms 可分数段=4 合格=是 判定=拍成跳变\n"
        + "MOTION_RESOLVE_SUMMARY judged=4/5 not-run=notice-banner\n",
        ["MOTION_FLOOR_FACTS judged=4/5", "not-run=notice-banner",
         "MOTION_FLOOR_OK=4/5", "MOTION_FLOOR_REDS=0"], 0, []),
    # 掉了同一臂，但这次没人说为什么 ⇒ 红。"没测到"可以接受，"没测到且说不清"不行。
    ("motion_floor", "drift_without_reason"): (
        NORMAL + FLOOR_SUMMARY + "\n"
        + "MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss\n",
        ["MOTION_FLOOR_REASONLESS"], 1, []),
    # 地板本身。**R52 改过这一格的形状**，理由要写清楚：
    # R52 之前清单里 `notice-banner` 是 must_judge（地板=3），所以"judged=2 且掉的是 detail-kind-change"
    # 这一格能红在地板上。R52 把 notice-banner 改成放行之后地板降到 2，于是任何 must_judge 臂缺席
    # 都会**先**撞 BAD_REASON（它没登记理由）⇒ 地板再也无法单独红。
    # 这一格因此换成一个仍然只有地板能抓的形状：`judged=1` 却只登记了两条横幅臂缺席 ⇒
    # detail-kind-change 与 empty-state 都该判到，结论行却说自己只判了 1 条 ——
    # **judged 与 not-run 名单不自洽**（判据说谎）。R38 那条"锁要写成恒等式"说的就是这种红。
    ("motion_floor", "under_covered"): (
        NORMAL + FLOOR_SUMMARY + "\n"
        + "MOTION_NOT_RUN=premise-not-visible notice-banner：首尾相同\n"
        + "MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：事件段最粗 101ms\n"
        + "MOTION_RESOLVE_SUMMARY judged=1/4 not-run=notice-banner,notice-banner-dismiss\n",
        ["MOTION_FLOOR_UNDERCOVERED", "MOTION_FLOOR_REDS=1"], 1, []),
    # 探针自己没跑完 ⇒ 不红（不能把探针故障算成产品缺陷），但必须打印。
    ("motion_floor", "suite_did_not_finish"): (
        TRUNCATED, ["MOTION_FLOOR_SKIPPED=suite-did-not-finish"], 0, []),
    # R46 把这一格从 0 改成 1：旧版在这里 `exit 0`（"旧版判据没有这一行，由上一步负责喊"），
    # 而本仓库每条判据都会打这一行 —— 缺了就是坏了，留成绿是一张免检牌。
    ("motion_floor", "no_resolve_line"): (
        NORMAL + FLOOR_SUMMARY + "\n",
        ["MOTION_FLOOR_NO_RESOLVE"], 1, []),
    # ---- R36：帧捕获那道硬门的四个形状。四个都要，因为这道门挡的是**四种不同的骗人方式**：
    #      真红被吞 / 已知盲区被当成红 / 整批退回 skip / 干脆没跑到用例。
    ("capture_gate", "real_runner_log"): (
        REAL_RUNNER_LOG,
        ["CAPTURE_GATE_RESULT=fail", "testCaptureKeyViews", "处置只有两种"], 1, []),
    ("capture_gate", "registered_not_run_only"): (
        _passed_lines(16) + "CAPTURE_NOT_RUN settings-x 95% 未绘制\n"
        + "MATERIAL_BLIND_NOT_RUN 这一台一处黑带都没有\n",
        ["CAPTURE_GATE_RESULT=ok", "CAPTURE_NOT_RUN"], 0, []),
    ("capture_gate", "all_judgements_became_skips"): (
        _skipped_lines(20) + "MATERIAL_BLIND_NOT_RUN 略\n",
        ["skip 不是通过"], 1, []),
    ("capture_gate", "log_without_any_case"): (
        "Building for debugging...\nBuild complete! (0.09s)\n",
        ["没跑不算通过"], 1, []),
}


def extract_run_block(text, step_name):
    """取步骤 `run: |` 之后的脚本正文，逐字保留（不复制一份来测，测的就是 ci.yml 里那段）。"""
    marker = "- name: " + step_name + "\n"
    start = text.index(marker) + len(marker)
    run_at = text.index("run: |\n", start) + len("run: |\n")
    lines = []
    for line in text[run_at:].splitlines():
        if line.startswith("          "):
            lines.append(line[10:])
        elif line.strip() == "":
            lines.append("")
        else:
            break
    return textwrap.dedent("\n".join(lines)).strip("\n")


def build_script(block, fake_log, key, extra_subs=()):
    script = block
    for pattern, replacement in list(SUBSTITUTIONS[key]) + list(extra_subs):
        script, count = re.subn(
            pattern, lambda _m, r=replacement: r.replace("FAKE_LOG", fake_log), script)
        # 额外替换允许命中 0 次的情形不存在：命中不了就是 ci.yml 改了写法，夹具已经失效
        if count < 1:
            raise AssertionError("夹具替换没有落地（命中 %d 次）：%s" % (count, pattern))
    return script


# ── R92 / BACKLOG 128：夹具**一律**不许往共享的 /tmp 里写 ─────────────────────────
# 现场（run 38838819089 与 38846896495，2/2 复现，不是骰子）：`a68a08f`（R89）为了"闸门一红
# 就吃掉后面七步的证据"，把 `Capture gate` 与 `On-screen probe coverage floor` 挪到作业末尾
# 加 `if: always()`。位置本身是对的，错的是这里以前只把 **`/tmp/shots-ci`** 换进临时目录：
#   SUBSTITUTIONS 造出来的命令是字面量 `cp FAKE_LOG /tmp/frames.log`、`/tmp/ui.log`、
#   `/tmp/motion.log` ⇒ 它们写进了**这个作业自己的 /tmp**，把闸门要读的三份真日志覆盖了。
# 于是 `CAPTURE_GATE_RESULT=fail …这一步没跑到用例` 与 `UI_PROBE_CHANNELS … started=probeA`
# 读的都是最后一格的假日志（`probeA` 就是 `TRUNCATED` 夹具里的用例名），而同一次 run 里
# 捕获那一步自己打的是 `Executed 47 tests … 0 failures`、在屏那一步打的是 `exit: 137`。
# 本机实测：先往 /tmp/frames.log 写 `REAL-MARKER`，跑一遍自检，文件变成
# `Test Case '-[p probeA]' started.`，marker 一行不剩。
# 为什么这里用**通配**而不是补一份路径清单：清单正是这次的成因 —— 加一条新的 `/tmp/x.log`
# 不需要改这个自检，于是"漏一条"是默认结局，而通配只在路径形状整个换掉时才会漏。
# 两道边界都必需（**R92 自己踩出来的**）：
#   · 后顾 `(?![A-Za-z0-9_.+-])`：少了它，`tempfile` 给的
#     `/var/folders/…/T/tmpab1x/fake.log` 会被当成 `/tmp` 换掉一段，实测变成
#     `cp: <shots>/_sdnt8zy/fake-干净.log: No such file or directory`；
#   · 前瞻 `(?<![A-Za-z0-9_./-])`：`/private/tmp/x` 这种"前缀还有东西"的路径**不换**，
#     因为只换后半截会把一条真路径改坏。它由上面那条静态扫描兜住 —— 那一步会红着说
#     "有一条 /tmp 路径我没敢动"，而不是静默地留着共享写入。
TMP_PATH = re.compile(r"(?<![A-Za-z0-9_.\-/])/tmp(?:/[A-Za-z0-9_.+:\-]+)*(?![A-Za-z0-9_.\-])")


def sandbox_path(path, shots_dir):
    """把一个 ci.yml 里的绝对 `/tmp/…` 路径映射到这一格的临时目录。

    `/tmp/shots-ci/capture-readings.log` → `<shots>/shots-ci_capture-readings.log`：
    嵌套的那一层压平进文件名，是为了让**同一个临时目录**同时装下目录类与文件类路径，
    而不用给每条路径再造子目录（`find <shots>/shots-ci -name '*.png'` 那一路仍然成立，
    因为 `/tmp/shots-ci` 本身映射成一个真子目录）。
    """
    if path == "/tmp":
        return shots_dir
    if not path.startswith("/tmp/"):
        raise AssertionError("sandbox_path 只处理 /tmp 下面的路径：%s" % path)
    return os.path.join(shots_dir, path[len("/tmp/"):].replace("/", "_"))


def prepare(script, shots_dir):
    """把整段脚本里所有 `/tmp…` 换成这一格的临时目录（`run_bash` 唯一的入口）。"""
    return TMP_PATH.sub(lambda match: sandbox_path(match.group(0), shots_dir), script)


def run_bash(script, shots_dir):
    """跑一步的脚本正文，返回 (退出码, 输出)。

    输出走**文件**而不是管道：脚本里的看门狗是 `( sleep 240; kill ... ) &`，
    `kill "$killer"` 只收掉子 shell，那个 `sleep` 会变成孤儿并**继续持有继承来的 stdout 管道**，
    于是 `communicate()` 一直等 EOF —— 实测这个自检自己被吊死在 300 秒超时上。
    真实 runner 不挂是因为它一直在读管道。顺手用独立会话把整组进程收干净，别攒孤儿 sleep。
    """
    prepared = prepare(script, shots_dir)
    out_path = os.path.join(shots_dir, "bash_out.txt")
    with open(out_path, "w", encoding="utf-8") as handle:
        proc = subprocess.Popen(["bash", "-e", "-c", prepared],
                                stdout=handle, stderr=subprocess.STDOUT,
                                start_new_session=True, text=True)
        try:
            code = proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
            code = -1
    try:
        # start_new_session 让子进程的 pgid == 它的 pid；直接按 pgid 收，
        # 不要用 getpgid()（leader 一死就 ProcessLookupError，孤儿 sleep 反而活下来）。
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    with open(out_path, encoding="utf-8") as handle:
        return code, handle.read()


def check(ci_path):
    """返回失败清单（空 = 全部形状合格）。同时把每个形状打到 stdout。"""
    with open(ci_path, encoding="utf-8") as handle:
        text = handle.read()

    # R92 / M514 量出来的第二件事：这个目录以前是 `$TMPDIR/ci_selftest_shots` 且**跨次运行复用**，
    # 于是上一遍留下的 61 张 PNG 会替这一遍作证 —— 把落点改回临时目录根（`frames_dir = shots`）
    # 那一刀本来应当红在 `test frames -ge 60` 上，实际却整批绿，因为
    # `find <shots>/shots-ci` 数到的是**上一次**跑留在那儿的那些png。
    # 现在每遍一个空目录、跑完删掉；同一遍里各格仍然共用它（下面两格靠的就是这个）。
    shots = tempfile.mkdtemp(prefix="ci_selftest_shots-")
    frames_dir = sandbox_path("/tmp/shots-ci", shots)
    os.makedirs(frames_dir, exist_ok=True)
    for i in range(61):                     # 让 `test frames -ge 60` 这一闸真被跨过
        open(os.path.join(frames_dir, "f%02d.png" % i), "wb").close()

    failures = []
    try:
        for (key, case), (log_body, snippets, expected_code, extra_subs) in sorted(EXPECT.items()):
            fake = os.path.join(shots, "log_%s_%s.txt" % (key, case))
            with open(fake, "w", encoding="utf-8") as handle:
                handle.write(log_body)
            script = build_script(extract_run_block(text, STEPS[key]), fake, key, extra_subs)
            try:
                code, out = run_bash(script, shots)
            except subprocess.TimeoutExpired:
                failures.append("%s/%s 超时" % (key, case))
                continue
            missing = [s for s in snippets if s not in out]
            bad_code = expected_code is not None and code != expected_code
            print("%-9s %-17s exit=%-3s %s" % (key, case, code,
                                               "FAIL" if missing or bad_code else "OK"))
            if missing:
                failures.append("%s/%s: 结论行缺失 %s（退出码 %s）" % (key, case, missing, code))
                print("---- 实际输出尾部 ----\n" + out.strip()[-500:])
            if bad_code:
                failures.append("%s/%s: 期望退出码 %d，实际 %d" % (key, case, expected_code, code))
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    return failures


class CIReportSelfTest(unittest.TestCase):
    """CI 的 `Release script tests` 步骤用 unittest discover 收 scripts/tests，
    所以这条守卫要在那里被真的执行 —— 否则它只是我本地跑过一次的脚本。"""

    def test_report_only_steps_always_print_their_numbers(self):
        for failure in check(CI_DEFAULT):
            self.fail(failure)

    # ---- R92 / BACKLOG 128：夹具不许覆盖共享 /tmp（那两道最终闸门读的就是它）--------
    SHARED_LOGS = ("/tmp/frames.log", "/tmp/ui.log", "/tmp/motion.log", "/tmp/build.log")

    def test_sandbox_path_maps_every_tmp_shape_this_job_uses(self):
        """真值表：`ci.yml` 里现在出现的每一种 `/tmp` 形状，映射结果逐条钉住。

        为什么单独一条而不是只测 `prepare`：`prepare` 的正则是"通配"的，
        通配最容易悄悄漏掉的就是**它自己没见过的形状**（裸 `/tmp`、嵌套两层的目录、
        带连字符的名字）。这一格是把形状列出来，漏一种就红在名字上。
        """
        self.assertEqual(sandbox_path("/tmp", "S"), "S")
        self.assertEqual(sandbox_path("/tmp/shots-ci", "S"), os.path.join("S", "shots-ci"))
        self.assertEqual(sandbox_path("/tmp/frames.log", "S"), os.path.join("S", "frames.log"))
        self.assertEqual(sandbox_path("/tmp/shots-ci/capture-readings.log", "S"),
                         os.path.join("S", "shots-ci_capture-readings.log"))
        # 一句话里两处：都要换，且不能互相吞
        self.assertEqual(prepare("a /tmp/ui.log b /tmp/shots-ci/x.log", "S"),
                         "a " + os.path.join("S", "ui.log") + " b " + os.path.join("S", "shots-ci_x.log"))
        # 环境变量那一行是**裸** /tmp（R90 的心跳目录就是这么给的）
        self.assertEqual(prepare("CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \\", "S"),
                         "CLIPBOARD_HISTORY_PROBE_PULSE=" + "S" + " \\")
        # 这两条是 R92 当场踩出来的两个边界：`tempfile` 的目录名以 `tmp` 开头，
        # 早先那版正则会把它的前半截换掉，实测变成
        # `cp: <shots>/_sdnt8zy/fake-干净.log: No such file or directory`（0 告警那一格凭空变红）。
        self.assertEqual(prepare("cp /var/folders/47/T/tmpab1x/fake-干净.log /tmp/frames.log", "S"),
                         "cp /var/folders/47/T/tmpab1x/fake-干净.log " + os.path.join("S", "frames.log"))
        # 尾部那一半：一个**以 tmp 开头**的名字（`/tmpbackup/x`）不是 `/tmp` 下面的一条路径。
        # 这条不是装饰 —— M511 那把刀（去掉尾部边界）在只有上一条时**逃掉了**，
        # 因为 `/T/tmpab1x` 已经被前向边界挡住了，尾部边界管的是"前面没有斜杠"那一类。
        self.assertEqual(prepare("cp /tmpbackup/x /tmp/frames.log", "S"),
                         "cp /tmpbackup/x " + os.path.join("S", "frames.log"))
        self.assertEqual(prepare("OUT=/tmpwork; echo hi", "S"), "OUT=/tmpwork; echo hi")
        # 前缀还有东西的路径**不换**（只换后半截会把一条真路径改坏）；
        # 它由 test_cell_commands_never_address_the_shared_tmp 那条扫描负责喊红。
        self.assertEqual(prepare("cat /private/tmp/frames.log", "S"), "cat /private/tmp/frames.log")
        with self.assertRaises(AssertionError):
            sandbox_path("/var/tmp/x", "S")

    def test_cell_commands_never_address_the_shared_tmp(self):
        """接线断言：每一格**真正交给 bash 的那段脚本**里不许还剩 `/tmp`。

        只测 `prepare` 本身不够 —— 这次坏的是"忘了调它"那一层。所以这里从 ci.yml 重新
        走一遍 `build_script` + `prepare`，逐格扫。注释行放过（它们是给人读的路径名，
        不会被 bash 执行）；非注释行里出现 `/tmp` 就是又一处共享写入。
        """
        with open(CI_DEFAULT, encoding="utf-8") as handle:
            text = handle.read()
        offenders = []
        cells = [(key, case, extra) for (key, case), (_b, _s, _c, extra) in EXPECT.items()]
        cells.append(("build", "gates_tests", [(r"swift build --build-tests 2>&1 \| tee /tmp/build\.log",
                                                "cp FAKE_LOG /tmp/build.log")]))
        for (key, case, extra) in cells:
            block = extract_run_block(text, STEPS.get(key, "Build (must be warning-free)"))
            prepared = prepare(build_script(block, "/sandbox/fake.log", key, extra), "/sandbox")
            for line in prepared.splitlines():
                if line.lstrip().startswith("#") or "/tmp" not in line:
                    continue
                offenders.append("%s/%s：%s" % (key, case, line.strip()[:120]))
        self.assertFalse(offenders, "夹具命令还在往共享 /tmp 写（闸门会读到假日志）：\n" + "\n".join(offenders[:6]))

    def test_selftest_does_not_clobber_the_logs_the_final_gates_read(self):
        """行为证人（这条才是 R92 的**正对照**）：跑一格真夹具，共享 /tmp 里那四份日志
        的 mtime/大小必须一模一样，而沙箱里必须**确实**多了那一份假日志。

        为什么不能只用上面那条静态扫描：把 `run_bash` 改回
        `script.replace("/tmp/shots-ci", shots_dir)` 时，静态扫描仍然绿 ——
        因为它测的是 `prepare`，而那正是被绕开的那一步。这一半测的是"它到底有没有被调到"。
        成对写：只断言"真文件没动"会有一种假绿（命令根本没写成，哪儿都没有），
        所以必须同时断言沙箱里出现了 `frames.log`。
        """
        with open(CI_DEFAULT, encoding="utf-8") as handle:
            text = handle.read()
        before = {}
        for path in self.SHARED_LOGS:
            try:
                handle_stat = os.stat(path)
                before[path] = (handle_stat.st_mtime_ns, handle_stat.st_size)
            except OSError:
                before[path] = None
        block = extract_run_block(text, STEPS["capture_gate"])
        with tempfile.TemporaryDirectory() as shots:
            # 夹具本体必须是真的能 `cp` 到的文件：早先这里传了一个不存在的假路径，
            # `bash -e` 在第一步 `cp` 就中止 ⇒ 沙箱里什么都没写 ⇒ 下面那句"真文件没被动过"
            # 变成空话。这条测试存在的意义正是拒绝那种假绿，所以它自己先得不是假绿。
            fake = os.path.join(shots, "fake-capture.log")
            with open(fake, "w", encoding="utf-8") as handle:
                handle.write("Building for debugging...\n")
            script = build_script(block, fake, "capture_gate", [])
            run_bash(script, shots)
            self.assertTrue(os.path.exists(os.path.join(shots, "frames.log")),
                            "沙箱里没有 frames.log ⇒ 这一格压根没执行写入，"
                            "下面那句『共享 /tmp 没被动过』是空话（假绿）")
        after = {}
        for path in self.SHARED_LOGS:
            try:
                handle_stat = os.stat(path)
                after[path] = (handle_stat.st_mtime_ns, handle_stat.st_size)
            except OSError:
                after[path] = None
        moved = [p for p in self.SHARED_LOGS if before[p] != after[p]]
        self.assertFalse(moved,
                         "自检把作业共享 /tmp 里的日志覆盖了：%s ⇒ 挪到末尾的那两道闸门读的是假日志"
                         % moved)

    def test_build_step_gates_the_test_target_too(self):
        """R59 / BACKLOG 87：那条"构建 0 告警"以前只编译 `Sources/`。

        现场：R58 提交的测试文件里有一条 `variable 'a' was never mutated`，
        它在 `swift test` 的输出里明明白白，两次 CI 都是绿的 ——
        因为那一步跑的是不带 `--build-tests` 的 `swift build`。
        这条守卫同时钉三件事：① 命令编译测试目标；② 有告警必须打红；
        ③ 打红时日志里能读到**是哪一条**（只报一个数字的话，下一次还得重跑构建才知道）。
        """
        with open(CI_DEFAULT, encoding="utf-8") as handle:
            text = handle.read()
        block = extract_run_block(text, "Build (must be warning-free)")
        self.assertIn("swift build --build-tests", block,
                      "告警闸门又退回成只编译 Sources/ 了 ⇒ 测试目标里的告警没人看（BACKLOG 87）")
        subs = [(r"swift build --build-tests 2>&1 \| tee /tmp/build\.log",
                 "cp FAKE_LOG /tmp/build.log")]
        with tempfile.TemporaryDirectory() as shots:
            for name, body, want_red in (
                    ("干净", "Build complete! (9.9s)\n", False),
                    ("有一条告警",
                     "warning: variable 'a' was never mutated; consider changing to 'let' constant\n",
                     True)):
                fake = os.path.join(shots, "fake-%s.log" % name)
                with open(fake, "w", encoding="utf-8") as handle:
                    handle.write(body)
                script = build_script(block, fake, "build", extra_subs=subs)
                code, out = run_bash(script, shots)
                if want_red:
                    self.assertNotEqual(code, 0, "有告警必须把这一步打红：%s" % out)
                    self.assertIn("never mutated", out,
                                  "红了要能读是哪一条告警，不许只留一个数字：%s" % out)
                else:
                    self.assertEqual(code, 0, "0 告警不该红：%s" % out)


def main():
    ci_path = sys.argv[1] if len(sys.argv) > 1 else CI_DEFAULT
    failures = check(ci_path)
    print("\n合计 %d 个形状，失败 %d 个" % (len(EXPECT), len(failures)))
    for line in failures:
        print("  ✗ " + line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
