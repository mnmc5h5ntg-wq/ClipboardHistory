#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R412 变异对照：设置快捷键行的「正在录制」行级描边必须真的从按钮接到行上。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HOTKEY = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/HotKeyRecorderView.swift")
SETTINGS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

SRC_FILTER = "SettingsRowRecordingTests/testRecordingRowIsWiredFromButtonToOutline"
PIXEL_FILTER = "SettingsRowRecordingTests/testRecordingOutlineAppearsOnTheRealRow"

CALL_NEEDLE = "                                onRecordingChange(recording)\n"
CALL_MUTANT = ""
WIRE_NEEDLE = "                    onRecordingChange: { isRecording = $0 }\n"
WIRE_MUTANT = "                    onRecordingChange: { _ in }\n"
OPACITY_NEEDLE = "        isRecording ? 0.9 : 0\n"
OPACITY_MUTANT = "        0\n"
FAINT_MUTANT = "        isRecording ? 0.02 : 0\n"
ANIM_NEEDLE = "            .animation(MotionCatalog.animation(for: .emphasis), value: isRecording)\n"
ANIM_MUTANT = ""

MUTATIONS = [
    ("M1065", "录制器不再把状态报给行（源判据）", HOTKEY, CALL_NEEDLE, CALL_MUTANT,
     SRC_FILTER, ["录制器自己翻了状态却没有调用出口"]),
    ("M1066", "设置行不接录制回调（源判据）", SETTINGS, WIRE_NEEDLE, WIRE_MUTANT,
     SRC_FILTER, ["设置行没接录制回调"]),
    ("M1067", "行描边恒不透明确（像素判据）", SETTINGS, OPACITY_NEEDLE, OPACITY_MUTANT,
     PIXEL_FILTER, ["录制行带里只有"]),
    ("M1068", "行描边淡到读不出（像素判据）", SETTINGS, OPACITY_NEEDLE, FAINT_MUTANT,
     PIXEL_FILTER, ["录制行带里只有"]),
    ("M1069", "行描边没有驱动（源判据）", SETTINGS, ANIM_NEEDLE, ANIM_MUTANT,
     SRC_FILTER, ["行级描边没有驱动"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r412-mut-shots-")
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
    originals = {HOTKEY: read(HOTKEY), SETTINGS: read(SETTINGS)}
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
        mutated = originals[path].replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(mutated)
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and (new in read(path) or new == "")
        try:
            code, out, failed = run(filter_name)
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(originals[path])
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(needle in out for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        readings = [line for line in out.splitlines() if "RECORDER_ROW_EDGE" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == originals[path]))

    clean = all(read(path) == original for path, original in originals.items())
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R412_SETTINGS_RECORDING_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
