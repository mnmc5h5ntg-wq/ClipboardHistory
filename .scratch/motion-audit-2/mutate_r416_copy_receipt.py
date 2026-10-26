#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R416 变异对照：复制回执文字必须从两态算出来、画在药丸上方、带过渡与不折行。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
CONTROLS = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/GlassControls.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
PIXEL = "UICaptureTests/testCopyReceiptToastAppearsForSuccessAndFailure"
PURE = "CopyReceiptTests/testCopyReceiptTruthTable"
SOURCE = "CopyReceiptTests/testCopyReceiptIsWiredIntoThePill"

OVERLAY_NEEDLE = "                CopyReceiptView(receipt: receipt)\n"
OVERLAY_MUTANT = "                EmptyView()\n"
TRUTH_NEEDLE = """        if copyFailed { return Receipt(text: "复制失败", tone: .failure) }
        if copyConfirmed { return Receipt(text: "已复制", tone: .success) }
"""
TRUTH_MUTANT = """        if copyConfirmed { return Receipt(text: "已复制", tone: .success) }
        if copyFailed { return Receipt(text: "复制失败", tone: .failure) }
"""
TRANSITION_NEEDLE = "                    .transition(.opacity.combined(with: .move(edge: .bottom)))\n"
TRANSITION_MUTANT = ""
FIXEDSIZE_NEEDLE = """                .fixedSize(horizontal: true, vertical: false)
        }
        // 药丸本体只有约 64pt 宽；回执不能跟着它折行（R416 首拍「已复制」被拆成竖排）。
        .fixedSize(horizontal: true, vertical: false)
"""
FIXEDSIZE_MUTANT = """        }
        // 药丸本体只有约 64pt 宽；回执不能跟着它折行（R416 首拍「已复制」被拆成竖排）。
"""

MUTATIONS = [
    ("M1084", "回执视图不挂到药丸上（像素判据）", CONTROLS, OVERLAY_NEEDLE, OVERLAY_MUTANT,
     PIXEL, ["成功回执带只有", "失败回执带只有"]),
    ("M1085", "两态同真时把失败说成已复制（纯判据）", CONTROLS, TRUTH_NEEDLE, TRUTH_MUTANT,
     PURE, ["失败优先"]),
    ("M1086", "回执没有出现/消失过渡（源判据）", CONTROLS, TRANSITION_NEEDLE, TRANSITION_MUTANT,
     SOURCE, ["没有出现/消失过渡"]),
    ("M1087", "回执允许被药丸窄宽折行（源判据）", CONTROLS, FIXEDSIZE_NEEDLE, FIXEDSIZE_MUTANT,
     SOURCE, ["又允许被药丸的窄宽折行"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r416-mut-shots-")
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
    original = read(CONTROLS)
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
                    if "COPY_RECEIPT_TOAST" in line][-1:] or "无"
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红色读数=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, readings, failed, read(path) == original))

    clean = read(CONTROLS) == original
    reruns = []
    for filter_name in filters:
        code, _, _ = run(filter_name)
        reruns.append("%s=%s" % (filter_name, code))
    print("还原后复跑：" + " ".join(reruns))
    print("R416_COPY_RECEIPT_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean
                 and all(text.endswith("=ESCAPED") for text in reruns)) else 1


if __name__ == "__main__":
    sys.exit(main())
