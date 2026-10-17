#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R115 的变异表：侧栏逐行图标那把尺的四格牙（M606–M609）。

本轮做的事：把 167 撤回用的量法搬进 `UICaptureHarness` 那颗尺真身 —— 行带从**已布局的视图树**
里取（`_FocusRingView`），图标墨的横向范围由帧自己报（`iconInkSpan`），行数与产品那个枚举钉死。
顺带修掉 BACKLOG 168：脚本电池的样张把生产标记 `*_GATE_*` 打进真实 stdout，
CI 日志里 runner 的判词与夹具的读数同形。

四刀各钉一句：
  M606 行容器的尺寸闸门放宽到 20pt ⇒ 32pt 的行被滤掉 ⇒ 数到 0 行 ⇒ **CAUGHT**
       （钉在"行带是量出来的"，不是"我算出来的"）。
  M607 把容器名从 `FocusRingView` 换成 `ImageView` ⇒ 数到 0 行 ⇒ **CAUGHT**
       （钉在这个容器名是承重墙；R115 实测侧栏里根本没有 NSImageView）。
  M608 期望行数改成"枚举数 − 1" ⇒ **CAUGHT**（钉住"行数由产品决定"这条绑定）。
  M609 让 `_run` 把结论行重新写回真实 stdout ⇒ 归属守卫 **CAUGHT**
       （168 的修复不是文档，是有牙的：样张一漏字就被抓）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r115.py [M606 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import subprocess
import sys

SWIFT_ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
REPO = "/Users/wangziyi/Codex_Project0"
HARNESS = os.path.join(SWIFT_ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
GATE_TESTS = os.path.join(REPO, "scripts/tests/test_ci_capture_gate.py")
ICON_TEST = "UICaptureTests/testSettingsSidebarIconsAreMeasuredRowByRow"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M606", "行容器尺寸闸门 60→20 ⇒ 32pt 的行全被滤掉", HARNESS,
     "r.height > 8, r.height < 60", "r.height > 8, r.height < 20", "swift", "CAUGHT"),
    ("M607", "行容器名换成 ImageView ⇒ 视图树里根本没有那种东西", HARNESS,
     '.contains("FocusRingView")', '.contains("ImageView")', "swift", "CAUGHT"),
    ("M608", "期望行数改成枚举数 − 1 ⇒ 行数不再由产品决定", HARNESS,
     "let expectedRows = SettingsCategory.allCases.count",
     "let expectedRows = SettingsCategory.allCases.count - 1", "swift", "CAUGHT"),
    ("M609", "样张把结论行写回真实 stdout ⇒ 生产标记与夹具再次同形", GATE_TESTS,
     "        self.last_output = buf.getvalue()",
     '        print(buf.getvalue(), end="")', "pytest", "CAUGHT"),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def run(kind):
    if kind == "swift":
        cmd = ["swift", "test", "--filter", ICON_TEST]
        cwd, env = SWIFT_ROOT, ENV
    else:
        cmd = ["python3", "-m", "pytest",
               "scripts/tests/test_gate_marker_hygiene.py",
               "scripts/tests/test_ci_capture_gate.py", "-q"]
        cwd, env = REPO, {k: v for k, v in os.environ.items() if k != "SDKROOT"}
    proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if "no tests were executed" in out or "error: " in out and "cannot find" in out:
        return "DID-NOT-RUN", out
    if proc.returncode == 0:
        return "SURVIVED", out
    for line in out.splitlines():
        if "error:" in line and "XCTAssert" in line:
            return "CAUGHT", out
        if "AssertionError" in line or "FAILED" in line:
            return "CAUGHT", out
    return "CAUGHT", out


def main():
    wanted = set(sys.argv[1:])
    originals = {}
    for _, _, path, _, _, _, _ in ARMS:
        if path not in originals:
            originals[path] = read(path)
    results, tally = [], {}
    mismatch = not_run = 0
    for name, note, path, needle, replacement, kind, expect in ARMS:
        if wanted and name not in wanted:
            continue
        hits = originals[path].count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            tally["DID-NOT-RUN"] = tally.get("DID-NOT-RUN", 0) + 1
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        write(path, originals[path].replace(needle, replacement, 1))
        verdict, out = run(kind)
        write(path, originals[path])
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = (verdict == expect)
        if not ok:
            mismatch += 1
        if verdict == "DID-NOT-RUN":
            not_run += 1
        snippet = ""
        for line in out.splitlines():
            if "XCTAssert" in line or "AssertionError" in line:
                snippet = line.strip()[:170]
                break
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s" % (name, verdict, note))
    dirty = [path for path in originals if read(path) != originals[path]]
    for path in dirty:
        write(path, originals[path])
    restored = "yes" if not dirty else "二次还原仍不干净：" + ",".join(dirty)
    print("\n=== R115 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and len(results) > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
