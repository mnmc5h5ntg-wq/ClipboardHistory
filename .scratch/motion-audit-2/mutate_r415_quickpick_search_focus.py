#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R415 变异对照：QuickPick 搜索框焦点边界必须从 first responder 接到 backdrop。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
CONTROLLER = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PIXEL = "UICaptureTests/testQuickPickSearchFieldFocusLiftsItsChrome"
SOURCE = "QuickPickSearchFocusTests/testFocusStateIsWiredIntoTheSearchBackdrop"

GUARD_NEEDLE = "        guard (focusedForCapture ?? focused) || (hoveredForCapture ?? hovered) else { return }\n"
GUARD_MUTANT = "        guard (hoveredForCapture ?? hovered) else { return }\n"
WIRE_NEEDLE = """        field.onFocusChange = { [weak backdrop] focused in
            backdrop?.focused = focused
        }
"""
WIRE_MUTANT = ""
SHOW_NEEDLE = "            searchBackdrop?.focused = true\n"
SHOW_MUTANT = ""
HIDE_NEEDLE = "        searchBackdrop?.focused = false\n"
HIDE_MUTANT = ""

MUTATIONS = [
    ("M1080", "焦点不参与 backdrop 绘制（像素判据）", CONTROLLER, GUARD_NEEDLE, GUARD_MUTANT,
     PIXEL, ["焦点没有抬边界"]),
    ("M1081", "字段焦点出口没有接到 backdrop（源判据）", CONTROLLER, WIRE_NEEDLE, WIRE_MUTANT,
     SOURCE, ["字段的焦点出口没有接到 backdrop"]),
    ("M1082", "show 不点亮焦点（源判据）", CONTROLLER, SHOW_NEEDLE, SHOW_MUTANT,
     SOURCE, ["show() 没有点亮焦点"]),
    ("M1083", "hide 不收回焦点（源判据）", CONTROLLER, HIDE_NEEDLE, HIDE_MUTANT,
     SOURCE, ["hide() 没有收回焦点"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r415-mut-shots-")
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
    original = read(CONTROLLER)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        count = read(path).count(old)
        if count != 1:
            raise SystemExit("预检中止：%s 的针在 %s 命中 %d 次" % (mid, path, count))
    filters = []
    for row in MUTATIONS:
        if row[5] not in filters:
            filters.append(row[5])
    for filter_name in filters:
        code, out, _ = run(filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检失败 %s %s\n%s" % (filter_name, code, out[-2000:]))
    print("预检 OK " + ",".join(filters))

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
        readings = [line for line in out.splitlines()
                    if "QUICKPICK_SEARCH_FOCUS" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(CONTROLLER) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R415_QUICKPICK_SEARCH_FOCUS_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
