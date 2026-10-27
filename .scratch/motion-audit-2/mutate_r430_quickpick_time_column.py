#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R430 变异对照：浮层右侧时间列（产品文件 QuickPickController.swift 一张表五把刀）。"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = ("testRowTimeSurvivesTheLongestTitle"
          "|testSourceOnlyMatchNamesItsReasonWhileOtherMatchesStayBare"
          "|testQuickPickRowsEndOnOneTimeColumn"
          "|testQuickPickSourceMatchReasonExtendsTheTypedRow"
          "|testQuickPickSourceOnlyMatchCarriesItsReason")

CONSTRAINTS_NEEDLE = """                text.leadingAnchor.constraint(equalTo: symbol.trailingAnchor, constant: 6),
                text.trailingAnchor.constraint(equalTo: time.leadingAnchor,
                                               constant: -QuickPickController.timeGap),
                text.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
                time.trailingAnchor.constraint(equalTo: cell.trailingAnchor,
                                               constant: -QuickPickController.timeTrailingInset),
"""
CONSTRAINTS_MUTANT = """                text.leadingAnchor.constraint(equalTo: symbol.trailingAnchor, constant: 6),
                text.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
                time.leadingAnchor.constraint(equalTo: text.trailingAnchor,
                                              constant: QuickPickController.timeGap),
                time.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
"""

REASON_NEEDLE = """        if let reason = QuickPickModel.sourceMatchReason(for: entry, query: query) {
            pieces.append("来自 \\(reason)")
        }
"""
REASON_MUTANT = """        if let reason = QuickPickModel.sourceMatchReason(for: entry, query: query) {
            _ = reason
        }
"""

ROW_TIME_NEEDLE = """    static func rowTime(for entry: HistoryStore.Entry) -> String {
        ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp)
    }
"""
ROW_TIME_MUTANT = """    static func rowTime(for entry: HistoryStore.Entry) -> String {
        ""
    }
"""

MUTATIONS = [
    ("M1174", "时间列永远空字符串", FILE,
     "        cell.timeField?.stringValue = Self.rowTime(for: entry)\n",
     "        cell.timeField?.stringValue = \"\"\n",
     ["testQuickPickRowsEndOnOneTimeColumn"]),
    ("M1175", "时间列不再钉在右沿、改为跟着标题走", FILE,
     CONSTRAINTS_NEEDLE, CONSTRAINTS_MUTANT,
     ["testQuickPickRowsEndOnOneTimeColumn"]),
    ("M1176", "时间又拼回可截断的标题串", FILE,
     """        if let reason = QuickPickModel.sourceMatchReason(for: entry, query: query) {
            pieces.append("来自 \\(reason)")
        }
        return pieces.joined(separator: "  ·  ")
""",
     """        if let reason = QuickPickModel.sourceMatchReason(for: entry, query: query) {
            pieces.append("来自 \\(reason)")
        }
        pieces.append(ClipboardDateFormatters.sidebarTime.string(from: entry.timestamp))
        return pieces.joined(separator: "  ·  ")
""",
     ["testRowTimeSurvivesTheLongestTitle"]),
    ("M1177", "rowTime 返回空串", FILE, ROW_TIME_NEEDLE, ROW_TIME_MUTANT,
     ["testRowTimeSurvivesTheLongestTitle", "testQuickPickRowsEndOnOneTimeColumn"]),
    ("M1178", "来源命中理由不再写进标题", FILE, REASON_NEEDLE, REASON_MUTANT,
     ["testSourceOnlyMatchNamesItsReasonWhileOtherMatchesStayBare",
      "testQuickPickSourceMatchReasonExtendsTheTypedRow"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r430-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
        out = proc.stdout + proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        returncode = -1
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    verdicts = [line for line in out.splitlines()
                if "Test Case" in line and ("passed" in line or " failed" in line)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in line for line in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [line.split("]")[0].replace("Test Case '-[", "")
              for line in verdicts if " failed" in line]
    return ("CAUGHT" if returncode != 0 else "ESCAPED"), out, failed


def main():
    original = read(FILE)
    for mid, _desc, path, old, _new, _needles in MUTATIONS:
        count = read(path).count(old)
        if count != 1:
            raise SystemExit("预检中止：%s 的针在 %s 命中 %d 次" % (mid, path, count))
    code, out, _ = run(FILTER)
    if code != "ESCAPED":
        raise SystemExit("预检失败 %s %s\n%s" % (FILTER, code, out[-2000:]))
    print("预检 OK " + FILTER)
    caught = wrong = 0
    for mid, desc, path, old, new, needles in MUTATIONS:
        stamp = time.time() + 2
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original.replace(old, new, 1))
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and new in read(path)
        try:
            code, out, failed = run(FILTER)
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original)
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(any(needle in name for name in failed) for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))
    clean = read(FILE) == original
    code, _, _ = run(FILTER)
    print("还原后复跑：%s=%s" % (FILTER, code))
    print("R430_QUICKPICK_TIME_COLUMN_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
