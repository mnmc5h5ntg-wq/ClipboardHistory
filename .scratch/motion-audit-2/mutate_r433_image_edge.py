#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R433 变异对照：详情大图的可见边与「只缩不放」（ImagePreviewView.swift 一张表三把刀）。"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/ImagePreviewView.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "ImagePreviewLayoutTests|UICaptureTests/testDetailImagePreviewHasAVisibleEdge"

EDGE_NEEDLE = """                    .frame(width: fitted.width, height: fitted.height)
                    .padding(1)
                    .background(Color.primary.opacity(VisualTint.chipStroke))
                    .padding(20)
"""
MUTATIONS = [
    ("M1189", "图片的 1pt 中性边撤掉（白底图又看不见边界）", FILE,
     EDGE_NEEDLE,
     """                    .frame(width: fitted.width, height: fitted.height)
                    .padding(20)
""",
     ["图没有可见的边"]),
    ("M1190", "边画成透明", FILE,
     EDGE_NEEDLE,
     """                    .frame(width: fitted.width, height: fitted.height)
                    .padding(1)
                    .background(Color.primary.opacity(0))
                    .padding(20)
""",
     ["图没有可见的边"]),
    ("M1191", "贴合尺寸又开始放大（240×140 被拉到 680）", FILE,
     "        let scale = min(1, min(available.width / image.width, available.height / image.height))\n",
     "        let scale = min(available.width / image.width, available.height / image.height)\n",
     ["小图被放大了"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r433-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
        out = proc.stdout + proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout or b""
        out = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else (raw or "")
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
        hit = all(any(needle in line for line in failed) or needle in out for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))
    clean = read(FILE) == original
    code, _, _ = run(FILTER)
    print("还原后复跑：%s=%s" % (FILTER, code))
    print("R433_IMAGE_EDGE_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
