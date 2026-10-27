#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R417 变异对照：暂停采集横幅必须接在 ContentView 的签名/过渡/动作与同一把钥匙上。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
CONTENT = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/ContentView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PIXEL = "UICaptureTests/testPauseBannerAppearsOnlyWhenCaptureIsPaused"
DEFAULTS = "UICaptureTests/testPauseBannerReadsTheDefaultsKeyCaptureReads"
SOURCE = "PauseBannerTests/testPausedBannerIsWiredIntoTheContentView"
FILM = "MotionFilmstripTests/testPauseBannerAppearsAndDismissesWithAVisibleProcess"

BRANCH_NEEDLE = """        if isPausedForDrawing {
            NoticeBanner(message: "已暂停记录剪贴板"""
BRANCH_MUTANT = """        if !isPausedForDrawing {
            NoticeBanner(message: "已暂停记录剪贴板"""
TRANSITION_NEEDLE = """            }
            .transition(MotionCatalog.asymmetricTransition(insertion: .bannerIn, removal: .bannerOut))
        }
        if let recovery = historyStore.historyRecoveryNotice {
"""
TRANSITION_MUTANT = """            }
        }
        if let recovery = historyStore.historyRecoveryNotice {
"""
ACTION_NEEDLE = "                recordingPaused = false\n"
ACTION_MUTANT = "                recordingPaused = true\n"
KEY_NEEDLE = "    @AppStorage(\"recordingPaused\") private var recordingPaused = false\n"
KEY_MUTANT = "    @AppStorage(\"recordingPausedTypo\") private var recordingPaused = false\n"
SIGNATURE_NEEDLE = "        if isPausedForDrawing { bits |= 32 }\n"
SIGNATURE_MUTANT = ""

MUTATIONS = [
    ("M1088", "暂停分支的极性反了（像素判据）", CONTENT, BRANCH_NEEDLE, BRANCH_MUTANT,
     PIXEL, ["未暂停时横幅带已有"]),
    ("M1089", "暂停横幅没有进出过渡（源判据）", CONTENT, TRANSITION_NEEDLE, TRANSITION_MUTANT,
     SOURCE, ["暂停横幅没有进出过渡"]),
    ("M1090", "「继续记录」没有把开关关回去（源判据）", CONTENT, ACTION_NEEDLE, ACTION_MUTANT,
     SOURCE, ["没有把开关关回去"]),
    ("M1091", "AppStorage 读错钥匙（产品入口判据）", CONTENT, KEY_NEEDLE, KEY_MUTANT,
     DEFAULTS, ["横幅没读这把钥匙"]),
    ("M1092", "签名没有暂停这一位（胶片判据）", CONTENT, SIGNATURE_NEEDLE, SIGNATURE_MUTANT,
     FILM, ["暂停横幅是硬切"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r417-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    motion_out = None
    if "MotionFilmstripTests" in filter_name:
        motion_out = tempfile.mkdtemp(prefix="r417-mut-motion-")
        env["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
        env["CLIPBOARD_HISTORY_MOTION_OUT"] = motion_out
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    finally:
        shutil.rmtree(shots, ignore_errors=True)
        if motion_out:
            shutil.rmtree(motion_out, ignore_errors=True)
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
    original = read(CONTENT)
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
                    if "PAUSE_BANNER" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(CONTENT) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R417_PAUSE_BANNER_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
