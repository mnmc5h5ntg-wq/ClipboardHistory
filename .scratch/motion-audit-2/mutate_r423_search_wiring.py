#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R423 变异对照：侧栏无结果态必须走 SearchNoResultsPresentation，不许硬编码。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SIDEBAR = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
SOURCE = "SearchNoResultsPresentationTests/testSidebarUsesThePolicyInsteadOfHardcodedText"

NEEDLE = """                    systemName: SearchNoResultsPresentation.iconName(
                        entriesEmpty: historyStore.entries.isEmpty,
                        isFavoritesFilter: historyStore.filter == .favorites,
                        favoriteCount: historyStore.favoriteCount,
                        searchText: historyStore.searchText),
"""
MUTANT = "                    systemName: \"clipboard\",\n"

MUTATIONS = [
    ("M1118", "侧栏图标硬编码回剪贴板（源判据）", SIDEBAR, NEEDLE, MUTANT,
     SOURCE, ["侧栏没有用 policy 的图标"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r423-mut2-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    out = proc.stdout + proc.stderr
    verdicts = [line for line in out.splitlines()
                if "Test Case" in line and ("passed" in line or " failed" in line)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in line for line in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [line.split("]")[0].replace("Test Case '-[", "")
              for line in verdicts if " failed" in line]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def main():
    original = read(SIDEBAR)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        count = read(path).count(old)
        if count != 1:
            raise SystemExit("预检中止：%s 的针在 %s 命中 %d 次" % (mid, path, count))
    code, out, _ = run(SOURCE)
    if code != "ESCAPED":
        raise SystemExit("预检失败 %s %s\n%s" % (SOURCE, code, out[-2000:]))
    print("预检 OK " + SOURCE)

    caught = wrong = 0
    for mid, desc, path, old, new, filter_name, needles in MUTATIONS:
        stamp = time.time() + 2
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original.replace(old, new, 1))
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and (new in read(path) or new == "")
        try:
            code, out, failed = run(filter_name)
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original)
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(needle in out for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))

    clean = read(SIDEBAR) == original
    code, _, _ = run(SOURCE)
    print("还原后复跑：%s=%s" % (SOURCE, code))
    print("R423_SEARCH_WIRING_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
