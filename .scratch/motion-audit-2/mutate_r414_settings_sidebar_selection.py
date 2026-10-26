#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R414 变异对照：设置侧栏选中胶囊必须只有一颗、会滑动、且行内不再叠第二层。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
SETTINGS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

PIXEL = "UICaptureTests/testCaptureKeyViews"
SOURCE = "SettingsSidebarSelectionTests/testSelectionCapsuleIsWiredIntoTheSidebar"

CAPSULE_NEEDLE = "        return SettingsSidebarSelectionPlan.capsuleRect(rowFrame: frame)\n"
CAPSULE_MUTANT = "        return nil\n"
PROGRESS_NEEDLE = "        let t = CGFloat(min(1, max(0, progress)))\n"
PROGRESS_MUTANT = "        let t: CGFloat = 0\n"
ANIM_NEEDLE = """        .animation(MotionCatalog.animation(for: .selection, reduceMotion: shouldReduce),
                   value: selectedCategory)
"""
ANIM_MUTANT = ""
FILL_NEEDLE = "        guard !isSelected else { return 0 }\n"
FILL_MUTANT = "        guard isSelected else { return 0 }\n"

MUTATIONS = [
    ("M1076", "静置/落定胶囊不画（像素判据）", SETTINGS, CAPSULE_NEEDLE, CAPSULE_MUTANT,
     PIXEL, ["静置帧没有读到胶囊底色"]),
    ("M1077", "插值进度恒 0（像素判据）", SETTINGS, PROGRESS_NEEDLE, PROGRESS_MUTANT,
     PIXEL, ["中点没有离开起点"]),
    ("M1078", "胶囊没有驱动（源判据）", SETTINGS, ANIM_NEEDLE, ANIM_MUTANT,
     SOURCE, ["选中胶囊没有驱动"]),
    ("M1079", "行内仍画选中底（源判据）", SETTINGS, FILL_NEEDLE, FILL_MUTANT,
     SOURCE, ["行内还画着选中底"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r414-mut-shots-")
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
    original = read(SETTINGS)
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
                    if "SETTINGS_SIDEBAR_SELECTION_CAPSULE" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(SETTINGS) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R414_SETTINGS_SIDEBAR_SELECTION_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
