#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R562 变异表 M1461：把 `ListHangingIndent.minimumAdvance` 从 16 降到 12 ⇒ 第三级正文列被推歪 ⇒ 步进等距必须红。

这一把是这条判据的**真牙**：`▪`(U+25AA) 由冬青黑体回退画出、advance 12.00pt（`⦁` 8.11、`◦` 6.06），
正文列取 `max(minimumAdvance, markerWidth + markerGap)`。钳位还在时三级步进都是 16pt；把钳位降到 12
之后第三级变成 32+max(12,14)=46pt，步进从 [16,16] 翻成 [16,18] ⇒ 差 2pt=4px > 容差 2px ⇒ 必须红。
登记前自检（④）：变化量 = 步进多 2pt（4px），容差 2px ⇒ 出容差 2px，不是空刀；余量写进账。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Utilities/ListHangingIndent.swift"
TEST = "UICaptureTests/testNestedBulletLevelsKeepOneUniformTextColumn"
ARM = "M1461"
OLD = "    static let minimumAdvance: CGFloat = 16"
NEW = "    static let minimumAdvance: CGFloat = 12"


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r562-knife-shots"
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return verdict(out), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print(u"预检:", code)
    if code != "PASSED":
        print(out[-800:])
        return 2
    if text.count(OLD) != 1:
        print(u"needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print(ARM + ":", code)
    for line in out.splitlines():
        if ("XCTAssert" in line and "failed" in line) or line.startswith("BULLET_LEVELS"):
            print(u"  ", line.strip()[:240])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
