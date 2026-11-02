#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R559 变异表 M1453：把胶片那一格里的「接线不判」具名读数删掉 ⇒ 钉子的交叉核对必须红。

635 有两条腿：一条**会红的钉子**（M1452 签它）和一句**具名的不判**（这一把签它）。
少了后一条，胶片的绿就会被下游读成"接线验过了" —— 而 R558 的探针说它验不到。
这句话光写在注释里等于没写（本仓库的旧形状：分类法住在注释里 ⇒ 没人执行），
所以钉子必须能在"有人把 emit 行删掉"时红。

注意搜索范围：判据只看 `testMarkdownModeLabelChangeIsAVisibleProcess` 自己的函数体，
所以这一把删掉 emit 之后，钉子不会在"它自己那行字面量"里读到它（R53/R55 那一族自满足）。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "MotionFilmstripTests/testMarkdownModeLabelWiringIsPinnedBecauseTheFilmCannotSeeIt"
ARM = "M1453"
OLD = """        emit("MOTION_NOT_RUN=markdown-wiring-unjudged markdown-mode-label：本格只判标签有没有中间态；"
             + "那三行接线像素通道判不到（四臂探针逐字相同，BACKLOG 635）⇒ 由 grep 钉子 + M1452 签")
"""
NEW = ""


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
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
