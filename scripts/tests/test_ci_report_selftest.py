#!/usr/bin/env python3
"""CI 汇报行自检：把 ci.yml 里两个 report-only 步骤的 run 脚本**原文**抽出来，
只把"被测命令"换成夹具，然后喂三种日志形状，断言**结论行必然打出来**。

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
    "offscreen": "Offscreen frame capture (report-only)",
    "onscreen": "On-screen interaction probes (report-only)",
}

# 被测命令 → 夹具。命中次数必须恰好 1，否则说明 ci.yml 改了写法、夹具已经失效。
SUBSTITUTIONS = {
    "offscreen": [
        (r"CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci \\\n\s*"
         r"swift test --filter UICaptureTests 2>&1 \| tee /tmp/frames\.log \|\| true",
         "cp FAKE_LOG /tmp/frames.log || true"),
    ],
    "onscreen": [
        (r"CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci \\\n\s*"
         r"swift test --filter UIInteractionProbeTests > /tmp/ui\.log 2>&1 &",
         "cp FAKE_LOG /tmp/ui.log &"),
    ],
}

SINGULAR = ("Test Suite 'UICaptureTests' failed\n"
            "\t Executed 1 test, with 2 failures (0 unexpected) in 11.218 (11.218) seconds\n")
TRUNCATED = "Test Case '-[p probeA]' started.\n"
NORMAL = ("Test Suite 'All tests' passed\n"
          "\t Executed 12 tests, with 3 tests skipped and 0 failures (0 unexpected) in 4.0 (4.1) seconds\n")

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
