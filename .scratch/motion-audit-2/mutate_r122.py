#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R122 的变异表：侧栏图标"反侧"那一格升成会红之后，它到底有没有牙（M620–M621）。

本轮做的事：`SettingsView` 侧栏那六枚符号里 `wand.and.stars`（推荐）与 `chart.bar`（统计）
是仅有的两枚**多色符号**，在 `.hierarchical` 下它们带自己的调色板，于是暗档有 22 行图标的墨
落在背景那一边（黑底黑图标）。把渲染模式换成 `.monochrome` 之后实测
`dark 期望 56→78、反侧 22→0`；同时 `light 期望 35→13、无墨 43→65`（那是离屏通道对
`.primary` 的解析盲区，不是本轮改坏的东西 —— 两档要的解析方向相反，所以亮档那一半只登记不判产品）。
判据跟着从"只报数"升成会红（`SIDEBAR_ICON_INVERTED`，闸门与判据同源 D-166）。

两刀（都期望 CAUGHT）：
  M620 产品：把渲染模式换回 `.hierarchical` ⇒ 暗档 22 行反侧，红必须抓到（这一刀钉的是"改动别悄悄回去"）
  M621 判据：把那条红从比 `inverted` 改成比 `blank` ⇒ 亮档 65 行无墨会把它踩红
       —— 这一刀证明那条红认的是**反侧**那一格，不是"有没有墨"那一格（两种病的修法相反）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r122.py [M620 ...]
退出码：0 = 每一臂都拿到自己的期望，且两个文件都还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
PRODUCT = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
TEST = "testSettingsSidebarIconsAreMeasuredRowByRow"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M620", "产品换回 .hierarchical ⇒ 暗档 22 行反侧必须被新的红抓到", PRODUCT,
     "                .symbolRenderingMode(.monochrome)",
     "                .symbolRenderingMode(.hierarchical)",
     "CAUGHT"),
    ("M621", "把那条红从比反侧改成比无墨 ⇒ 亮档 65 行无墨会踩红（证明它认的是反侧）", HARNESS,
     "                XCTAssertEqual(inverted[tag] ?? 0, 0,",
     "                XCTAssertEqual(blank[tag] ?? 0, 0,",
     "CAUGHT"),
]


def read(path):
    with io_open(path, encoding="utf-8") as handle:
        return handle.read()


def save(path, text):
    with io_open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def run():
    proc = subprocess.run(["swift", "test", "--filter", "UICaptureTests/" + TEST],
                          cwd=ROOT, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    verdicts = re.findall(r"Test Case '-\[[^\]]*\b%s\]' (passed|failed|skipped)" % TEST, out)
    if not verdicts:
        return ("COMPILE-ERROR" if "error:" in out else "DID-NOT-RUN"), out
    return ("CAUGHT" if verdicts[-1] == "failed" else verdicts[-1].upper()), out


def snippet(out):
    for line in out.splitlines():
        if "SIDEBAR_ICON_COVERAGE" in line or "SIDEBAR_ICON_INVERTED" in line:
            return line.strip()[:200]
    return ""


import io as io_open  # noqa: E402  (kept last so the header stays readable)
io_open = io_open.open  # type: ignore


def main():
    wanted = set(sys.argv[1:])
    originals = {path: read(path) for path in (HARNESS, PRODUCT)}
    results, tally, mismatch, not_run = [], {}, 0, 0
    for name, note, path, needle, replacement, expect in ARMS:
        if wanted and name not in wanted:
            continue
        text = originals[path]
        hits = text.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        save(path, text.replace(needle, replacement, 1))
        verdict, out = run()
        save(path, text)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = verdict == expect
        mismatch += 0 if ok else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        results.append((name, expect, verdict, note,
                        ("对 期望 %s｜%s" % (expect, snippet(out))) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet(out)))))
        print("%s: %s %s" % (name, verdict, note))
    dirty = [p for p in originals if read(p) != originals[p]]
    restored = "yes" if not dirty else ("仍不干净:" + ",".join(os.path.basename(p) for p in dirty))
    print("\n=== R122 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        print("  %s  exp=%-8s got=%-12s %s %s  %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and not dirty and results) else 1


if __name__ == "__main__":
    sys.exit(main())
