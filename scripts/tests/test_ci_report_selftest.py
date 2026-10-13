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
import signal
import subprocess
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
        (r"CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci \\\n\s*"
         r"swift test --filter UIInteractionProbeTests > /tmp/ui\.log 2>&1 &",
         "cp FAKE_LOG /tmp/ui.log &"),
    ],
    "motion": [
        (r"CLIPBOARD_HISTORY_UI_MOTION=1 CLIPBOARD_HISTORY_MOTION_OUT=/tmp/motion-ci \\\n\s*"
         r"swift test --filter MotionFilmstripTests > /tmp/motion\.log 2>&1 &",
         "cp FAKE_LOG /tmp/motion.log &"),
    ],
    # 这一步没有"被测命令"：它读上一步留下的 /tmp/motion.log。
    # 所以夹具挂在它的**第一行抽取**上 —— 先落一份日志再去读它，
    # 这样测的仍然是 ci.yml 里那段判定逻辑本身，不是另抄一份。
    "motion_floor": [
        (r"resolve=\$\(grep -m1 'MOTION_RESOLVE_SUMMARY' /tmp/motion\.log",
         "cp FAKE_LOG /tmp/motion.log; resolve=$(grep -m1 'MOTION_RESOLVE_SUMMARY' /tmp/motion.log"),
    ],
    # R36 的硬门：它没有"被测命令"，只有"读上一步留下的日志再判"。
    # 所以夹具挂在 `cp` 上，脚本路径换成绝对路径（自检的 cwd 不一定是仓库根）。
    "capture_gate": [
        (r"python3 scripts/ci_capture_gate\.py /tmp/frames\.log",
         "cp FAKE_LOG /tmp/frames.log; python3 " + os.path.join(ROOT, "scripts", "ci_capture_gate.py")
         + " /tmp/frames.log"),
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
    ("onscreen", "singular_summary"): (SINGULAR, ["ui suite exit:"], 0, []),
    # 看门狗收掉进程就是这个形状：旧脚本在这里中止，"没有跑完"那条分支永远走不到
    ("onscreen", "truncated_log"): (TRUNCATED, ["ui suite exit:", "没有跑完"], 0, []),
    ("onscreen", "normal"): (NORMAL, ["ui suite exit:"], 0, []),
    ("onscreen", "watchdog_already_exited"): (
        TRUNCATED, ["ui suite exit:", "没有跑完"], 0,
        [(r"\( sleep 240; kill -9 \"\$pid\" 2>/dev/null \) &", "( exit ) &"),
         (r"cp \S+ /tmp/ui\.log &", "( cp FAKE_LOG /tmp/ui.log; sleep 1 ) &")]),
    ("motion", "normal"): (MOTION_NORMAL, ["motion suite exit:", "MOTION_SUMMARY",
                                           "MOTION_RESOLVE_SUMMARY"], 0, []),
    # 看门狗收掉进程 ⇒ 必须走 "MOTION_NOT_RUN" 那一支并且退出码 0（报告型不挡发布）
    ("motion", "truncated_log"): (TRUNCATED, ["motion suite exit:", "MOTION_NOT_RUN"], 0, []),
    ("motion", "watchdog_already_exited"): (
        TRUNCATED, ["motion suite exit:", "MOTION_NOT_RUN"], 0,
        [(r"\( sleep 200; kill -9 \"\$pid\" 2>/dev/null \) &", "( exit ) &"),
         (r"cp \S+ /tmp/motion\.log &", "( cp FAKE_LOG /tmp/motion.log; sleep 1 ) &")]),
    # 结论行丢了 MOTION_SUMMARY 时（比如抽取失手）这一格要红：它保证"跑过"和"读出内容"是两件事
    ("motion", "summary_missing_from_log"): (NORMAL, ["motion suite exit:", "无 MOTION_SUMMARY"], 0, []),
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
    # ---- R7：覆盖率下限那一步。三条形状各钉一件事：够 ⇒ 0；不够 ⇒ **必须 1**；
    #      没跑完 ⇒ 0（不能把探针故障算成产品缺陷）。少了第二格，这道闸就是一句 echo。
    ("motion_floor", "enough_coverage"): (
        MOTION_NORMAL, ["motion floor:", "MOTION_FLOOR_OK=3/3"], 0, []),
    ("motion_floor", "under_covered"): (
        NORMAL + "MOTION_SUMMARY notice-banner=3 detail-kind-change=3 empty-state=2\n"
        + "MOTION_RESOLVE_SUMMARY judged=1/3 not-run=notice-banner,detail-kind-change\n",
        ["MOTION_UNDERCOVERED=1/3"], 1, []),
    ("motion_floor", "suite_did_not_finish"): (
        TRUNCATED, ["MOTION_FLOOR_SKIPPED=suite-did-not-finish"], 0, []),
    ("motion_floor", "no_resolve_line"): (
        NORMAL + "MOTION_SUMMARY notice-banner=3 detail-kind-change=3 empty-state=4\n",
        ["MOTION_FLOOR_SKIPPED=no-resolve-line"], 0, []),
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


def run_bash(script, shots_dir):
    """跑一步的脚本正文，返回 (退出码, 输出)。

    输出走**文件**而不是管道：脚本里的看门狗是 `( sleep 240; kill ... ) &`，
    `kill "$killer"` 只收掉子 shell，那个 `sleep` 会变成孤儿并**继续持有继承来的 stdout 管道**，
    于是 `communicate()` 一直等 EOF —— 实测这个自检自己被吊死在 300 秒超时上。
    真实 runner 不挂是因为它一直在读管道。顺手用独立会话把整组进程收干净，别攒孤儿 sleep。
    """
    prepared = script.replace("/tmp/shots-ci", shots_dir)
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

    shots = os.path.join(os.environ.get("TMPDIR", "/tmp"), "ci_selftest_shots")
    os.makedirs(shots, exist_ok=True)
    for i in range(61):                     # 让 `test frames -ge 60` 这一闸真被跨过
        open(os.path.join(shots, "f%02d.png" % i), "wb").close()

    failures = []
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
    return failures


class CIReportSelfTest(unittest.TestCase):
    """CI 的 `Release script tests` 步骤用 unittest discover 收 scripts/tests，
    所以这条守卫要在那里被真的执行 —— 否则它只是我本地跑过一次的脚本。"""

    def test_report_only_steps_always_print_their_numbers(self):
        for failure in check(CI_DEFAULT):
            self.fail(failure)


def main():
    ci_path = sys.argv[1] if len(sys.argv) > 1 else CI_DEFAULT
    failures = check(ci_path)
    print("\n合计 %d 个形状，失败 %d 个" % (len(EXPECT), len(failures)))
    for line in failures:
        print("  ✗ " + line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
