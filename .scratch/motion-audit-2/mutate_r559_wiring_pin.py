#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R559 变异表 M1452：摘掉产品的 `.id(title)` ⇒ 635 那根 grep 钉子必须红。

这一把是 635 的**证人**：R558 的四臂探针已实测胶片对这三行接线是盲的
（单摘/全摘，`MOTION_MARKDOWN_MODE_FADE` 读数逐字相同），所以"接线还在"这句话
今天只有 grep 钉子在说。如果摘掉一行它不红，那 635 的降级就没有任何东西兜底 ——
这条钉子会变成第二张"写在注释里的契约"（本仓库的老形状）。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Sources/ClipboardHistoryApp/Views/DetailView.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MotionFilmstripTests/testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt"
ARM = "M1452"
OLD = """                    .id(title)
                    .transition(.opacity)"""
NEW = """                    .transition(.opacity)"""


def verdict(out):
    pairs = re.findall(r"Executed (\d+) test[s]?, with (\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=ENV, timeout=3600)
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
        if "MOTION_WIRING_UNJUDGED" in line:
            print(u"  读数:", line.strip()[:220])
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:200])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
