#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R381 变异对照：设置侧栏图标的「颜色必须随外观翻转」这条判据的牙。

R381 的缺陷是看帧量出来的：整页 `NavigationSplitView` 里未选中行的图标被侧栏材质解析成
255 白、压在 251 的底上（对比 4/255）；同一份 `.primary` 在单行组件帧里是黑的。
修法是**动态系统色** `Color(nsColor: .labelColor)`（亮 76 / 暗 232），不是固定色。
修后亮档 84 行全部有墨、无墨 0（修前 65/78 无墨）。

两把刀（都期望 CAUGHT）：
  M1011 把图标改回 `.primary` ⇒ 亮档重新变白、BLANK 那格必须红。
        这一刀证明新加的 `SIDEBAR_ICON_BLANK` 不是装饰。
  M1012 把动态色换成写死 `Color.black` ⇒ 亮档能看、暗档看不见（反侧/无墨），
        这一刀钉的是"修法不许用固定色讨好亮档"。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
VIEW = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Views/SettingsView.swift")
FILTER = "testSettingsSidebarIconsAreMeasuredRowByRow"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

# R443：文字也用了同一个动态色，而且**外层文字的 foregroundStyle 会给内层图标的
# `.primary` 提供环境** —— 只退图标（内层）不再坏（M1011 第一版就这样逃脱）。针改成
# 图标 + 文字两段 foregroundStyle 的整块，M1011 一起退回 `.primary`（R381/R443 之前的形状）。
NEEDLE = "\n".join([
    '                    .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)',
    '                                                : AnyShapeStyle(Color(nsColor: .labelColor)))',
    '            }',
    '            .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)',
    '                                        : AnyShapeStyle(Color(nsColor: .labelColor)))',
])

MUTATIONS = [
    ("M1011", "图标与文字一起退回 .primary（R381/R443 之前的形状：亮档图标变白）", VIEW,
     NEEDLE, "\n".join([
         '                    .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)',
         '                                                : AnyShapeStyle(.primary))',
         '            }',
         '            .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)',
         '                                        : AnyShapeStyle(.primary))',
     ]),
     ["SIDEBAR_ICON_BLANK", "一个墨都没读到"]),
    ("M1012", "图标动态色换成写死黑（亮档讨好、暗档看不见；文字保持动态色）", VIEW,
     NEEDLE, "\n".join([
         '                    .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)',
         '                                                : AnyShapeStyle(Color.black))',
         '            }',
         '            .foregroundStyle(isSelected ? AnyShapeStyle(Color.accentColor)',
         '                                        : AnyShapeStyle(Color(nsColor: .labelColor)))',
     ]),
     ["SIDEBAR_ICON_INVERTED", "SIDEBAR_ICON_BLANK", "落在**背景那一边**"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER], cwd=ROOT,
                          capture_output=True, text=True, env=BASE_ENV, timeout=600)
    out = proc.stdout + proc.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in l for l in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def main():
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    original = read(VIEW)
    if original.count(NEEDLE) != 1:
        raise SystemExit("预检中止：针出现 %d 次（要 1 次）" % original.count(NEEDLE))
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：%s\n%s" % (code, out[-2500:]))
    print("预检 OK " + FILTER)

    results = []
    stamp = time.time()
    try:
        for mid, desc, path, old, new, needles in MUTATIONS:
            if wanted and mid not in wanted:
                continue
            if read(path).count(old) != 1:
                print("%s: NOT_RUN 锚点命中 %d" % (mid, read(path).count(old)))
                results.append((mid, "NOT_RUN", "NO", "yes"))
                continue
            stamp += 2
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original.replace(old, new, 1))
            os.utime(path, (stamp, stamp))
            text = read(path)
            landed = new in text and old not in text
            try:
                code, out, failed = run()
            finally:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(original)
                os.utime(path, (stamp + 1, stamp + 1))
            hit = [n for n in needles if n in out]
            right = code == "CAUGHT" and bool(hit) and landed
            results.append((mid, code, "yes" if right else "NO", "yes"))
            print("\n%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s" % (mid, desc, code, right, hit, failed))
            if not right:
                for line in [l for l in out.splitlines() if "XCTAssert" in l or l.startswith("FAIL:")][:6]:
                    print("   MSG| " + line.strip()[:300])
    finally:
        with open(VIEW, "w", encoding="utf-8") as handle:
            handle.write(original)
    clean = read(VIEW) == original
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes"]
    print("R381_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(results), sum(1 for r in results if r[1] == "CAUGHT"), len(bad),
             "yes" if clean else "NO"))
    code, out, _ = run()
    print("还原后复跑：" + code)
    return 0 if (results and not bad and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
