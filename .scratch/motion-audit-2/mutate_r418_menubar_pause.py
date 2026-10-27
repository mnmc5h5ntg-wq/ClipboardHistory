#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R418 变异对照：菜单栏暂停记号必须由图标工厂/标签/12 的刷新链各自供电。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
CONTROLLER = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
IMAGE = "MenuBarPopulationTests/testPausedStatusImageAddsTheSlashAndKeepsTheGlyph"
PIXEL = "UICaptureTests/testMenuBarPauseMarkAppearsOnlyWhenPaused"
SOURCE = "MenuBarPopulationTests/testMenuBarPauseLabelIsWiredToTheSharedKey"

SLASH_NEEDLE = "        return paused ? Self.imageAddingPauseSlash(to: base) : base\n"
SLASH_MUTANT = "        return base\n"
LABEL_NEEDLE = """            .overlay {
                if paused {
"""
LABEL_MUTANT = """            .overlay {
                if false {
"""
KEY_NEEDLE = "    @AppStorage(\"recordingPaused\") private var recordingPaused = false\n"
KEY_MUTANT = "    @AppStorage(\"recordingPausedTypo\") private var recordingPaused = false\n"
REFRESH_NEEDLE = """        guard let statusItem else { return }
        let paused = historyStore?.isRecordingPaused ?? false
"""
REFRESH_MUTANT = """        guard let statusItem else { return }
        let paused = false
"""
ATTACH_NEEDLE = "        attachPauseBridgeIfNeeded()\n"
ATTACH_MUTANT = ""
NOTIFY_NEEDLE = "        pauseBridge = NotificationCenter.default.publisher(for: UserDefaults.didChangeNotification)\n"
NOTIFY_MUTANT = "        pauseBridge = NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)\n"

MUTATIONS = [
    ("M1096", "暂停图没有画斜杠（图像判据）", CONTROLLER, SLASH_NEEDLE, SLASH_MUTANT,
     IMAGE, ["暂停图只比静置多"]),
    ("M1097", "标签的暂停分支关掉了（像素判据）", CONTROLLER, LABEL_NEEDLE, LABEL_MUTANT,
     PIXEL, ["暂停记号太弱或没画"]),
    ("M1098", "标签读错钥匙（源判据）", CONTROLLER, KEY_NEEDLE, KEY_MUTANT,
     SOURCE, ["标签视图读的不是设置页/采集侧那把钥匙"]),
    ("M1099", "12 的 refresh 不读暂停（源判据）", CONTROLLER, REFRESH_NEEDLE, REFRESH_MUTANT,
     SOURCE, ["12 的 refresh 没读暂停状态"]),
    ("M1100", "12 没有挂订阅（源判据）", CONTROLLER, ATTACH_NEEDLE, ATTACH_MUTANT,
     SOURCE, ["install 没有挂订阅"]),
    ("M1101", "订阅的不是 defaults 变化（源判据）", CONTROLLER, NOTIFY_NEEDLE, NOTIFY_MUTANT,
     SOURCE, ["12 的图标没有订阅 defaults 变化"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r418-mut-shots-")
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
                    if "MENUBAR_PAUSE" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(CONTROLLER) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R418_MENUBAR_PAUSE_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
