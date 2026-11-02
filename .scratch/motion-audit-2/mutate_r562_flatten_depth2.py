#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R562 变异表 M1460：把夹具里第三级的缩进**两行一起**抹平 ⇒ 三级塌成两级 ⇒ 对象证人必须红。

这一把钉的是「判据有没有对象」：`BULLET_LEVELS` 那格断言帧上数到的正文列数 == 产品解析出的深度
集合大小。第一版只抹平了一行（`第三层第一项`），读数**逐字不变**（列还是 3、步进还是 [32,32]）——
因为另一行还留着 4 个空格 ⇒ depth2 仍在 ⇒ 那是一把空刀，已按 ④ 撤掉重做：现在 needle 是**两行一起**
（needle 命中恰好 1 次，语义是一格：夹具没画出第三级）。
登记前自检（④）：变化量 = 深度集合 {0,1,2}→{0,1}、正文列 3→2 ⇒ 远在容差之外。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
TEST = "UICaptureTests/testNestedBulletLevelsKeepOneUniformTextColumn"
ARM = "M1460"
OLD = (u'        "# 三级列表\\n\\n- 顶层第一项\\n  - 第二层第一项\\n    - 第三层第一项\\n"\n'
       u'        + "- 顶层第二项\\n  - 第二层第二项\\n    - 第三层第二项\\n"')
NEW = (u'        "# 三级列表\\n\\n- 顶层第一项\\n  - 第二层第一项\\n  - 第三层第一项\\n"\n'
       u'        + "- 顶层第二项\\n  - 第二层第二项\\n  - 第三层第二项\\n"')


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
