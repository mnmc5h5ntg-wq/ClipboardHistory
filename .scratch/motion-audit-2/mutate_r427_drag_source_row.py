#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R427 变异对照：行是否消费拖拽源状态、是否用正的 entry ID 登记。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
ROW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "DragSourceFeedbackTests|testDragSourceRowDimsOnlyWhileDragging"

OPACITY_NEEDLE = "        .opacity(isDraggingForDrawing ? DragSourceFeedback.dimOpacity : 1)\n"
OPACITY_MUTANT = "        .opacity(1)\n"
ENV_NEEDLE = "        dragSourceFeedback.state.isDragging(entry.id) || draggingEntryIDForCapture == entry.id\n"
ENV_MUTANT = "        dragSourceFeedback.state.isDragging(entry.id)\n"
ID_NEEDLE = "        .modifier(EntryDragModifier(entryID: entry.id, content: entry.content))\n"
ID_MUTANT = "        .modifier(EntryDragModifier(entryID: UUID(), content: entry.content))\n"

MUTATIONS = [
    ("M1157", "行不降透明度（拖拽源没有反馈）", ROW, OPACITY_NEEDLE, OPACITY_MUTANT,
     FILTER, ["testDragSourceRowDimsOnlyWhileDragging"]),
    ("M1158", "只认产品状态、不读取证键（帧画不出拖拽源）", ROW, ENV_NEEDLE, ENV_MUTANT,
     FILTER, ["testDragSourceRowDimsOnlyWhileDragging"]),
    ("M1159", "行交给拖拽的 ID 是随机新值", ROW, ID_NEEDLE, ID_MUTANT,
     FILTER, ["testOnDragRegistersTheSourceAndTheRowConsumesIt"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r427-mut-shots-")
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
    original = read(ROW)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        count = read(path).count(old)
        if count != 1:
            raise SystemExit("预检中止：%s 的针在 %s 命中 %d 次" % (mid, path, count))
    code, out, _ = run(FILTER)
    if code != "ESCAPED":
        raise SystemExit("预检失败 %s %s\n%s" % (FILTER, code, out[-2000:]))
    print("预检 OK " + FILTER)

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

    clean = read(ROW) == original
    code, _, _ = run(FILTER)
    print("还原后复跑：%s=%s" % (FILTER, code))
    print("R427_DRAG_SOURCE_ROW_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
