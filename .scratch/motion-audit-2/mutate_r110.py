#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R110 的变异表：BACKLOG 164「两棵表面同一颗图标」那条判据要能被打红（M598–M601）。

本轮做的事：macOS 12 的状态项图标从手写 `NSBezierPath` 换成系统符号，并且把符号名
收成**一个常量**（`MenuBarController.statusSymbolName`），13+ 的 `MenuBarExtra` 也引用它。
判据两格：运行时逐像素（产品那张 == 我自己按同一个 symbolName 画的参考）+ 源码（字面量只许 1 次）。

四刀的期望都从当轮实测来，不是推的：
  M598 把符号那一支变成永不到达（`if false, let symbol = …`）⇒ 期望 CAUGHT ——
       产品交出手画兜底，与参考符号逐像素不同。这一格钉的是"换素材这件事真的发生了"，
       没有它，"我把 12 那颗换掉了"就只是注释里的一句话。
  M599 删掉 `symbol.size = 18×18` ⇒ 期望 CAUGHT —— 红在几何那一格（占位那一格不能跟着素材一起漂）。
  M600 `isTemplate = true` 换成 `false` ⇒ 期望 CAUGHT —— 暗色菜单栏里会是一块黑。
  M601 App.swift 的调用点退回字面量 `"clipboard"` ⇒ 期望 CAUGHT ——
       红在源码那一格（contains 失败 + 字面量计数 2）。这一格钉的是结构：
       名字一旦又能各写各的，两棵表面下一次就会分叉。

**没被这四刀覆盖的一格要说清楚**：把常量本身改成另一个 symbolName（两棵表面一起换）
在本表里**不会红** —— 因为两条臂都用同一个新名字，逐像素仍相等，字面量仍是 1 次。
那一格的牙在**帧**里（`statusitem-glyph-*` 进基线，换名字 ⇒ CHANGED）。登记为"按实由帧拦"。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r110.py [M598 ...]
退出码：0 = 每一臂都拿到自己那条期望，且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
MENU = "Sources/ClipboardHistoryApp/Managers/MenuBarController.swift"
APP = "Sources/ClipboardHistoryApp/App.swift"
RUNTIME_JUDGE = "MenuBarPopulationTests/testStatusBarGlyphIsTheSystemSymbolNotTheDrawnFallback"
SOURCE_JUDGE = "MenuBarPopulationTests/testBothSurfacesReferenceTheOneSymbolName"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M598", "符号那一支永不到达 ⇒ 产品交出手画兜底，与参考符号必须逐像素不同", MENU,
     "        if let symbol = NSImage(systemSymbolName: Self.statusSymbolName,",
     "        if false, let symbol = NSImage(systemSymbolName: Self.statusSymbolName,",
     RUNTIME_JUDGE, "CAUGHT"),
    ("M599", "删掉 18×18 那一行 ⇒ 几何那一格必须红（素材换了不许顺手挪占位）", MENU,
     "            symbol.size = NSSize(width: 18, height: 18)",
     "            // M599：故意不设占位尺寸",
     RUNTIME_JUDGE, "CAUGHT"),
    ("M600", "模板位丢掉 ⇒ 暗色档里它不再随系统染色", MENU,
     "            symbol.isTemplate = true",
     "            symbol.isTemplate = false",
     RUNTIME_JUDGE, "CAUGHT"),
    ("M601", "调用点退回字面量 ⇒ 源码那一格必须红（两棵表面又能各写各的名字）", APP,
     'MenuBarExtra("时间剪史", systemImage: MenuBarController.statusSymbolName) {',
     'MenuBarExtra("时间剪史", systemImage: "clipboard") {',
     SOURCE_JUDGE, "CAUGHT"),
]

FILES = {}


def path_of(key):
    return os.path.join(ROOT, key)


def read(key):
    return open(path_of(key), encoding="utf-8").read()


def write(key, text):
    open(path_of(key), "w", encoding="utf-8").write(text)


def run(judge):
    env = dict(BASE_ENV)
    r = subprocess.run(["swift", "test", "--filter", judge], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    if "Executed 0 tests" in out:
        return "DID-NOT-RUN", out
    if "' failed" in out:
        return "CAUGHT", out
    if "with 0 failures" in out:
        if "skipped" in out and "Executed 1 test, with 1 test skipped" in out:
            return "SKIPPED", out
        return "PASSED", out
    return "DID-NOT-RUN", out


def main():
    originals = {}
    for key in set([a[2] for a in ARMS]):
        originals[key] = read(key)
    # 预检：不注入时两格判据都必须是 PASSED（否则变异表无从判起，见 D-175）
    print("=== 预检（不注入：两格判据都必须 PASSED）===")
    for judge in (RUNTIME_JUDGE, SOURCE_JUDGE):
        verdict, _ = run(judge)
        print("  %s %s" % (judge, verdict))
        if verdict != "PASSED":
            print("PREFLIGHT_FAILED：干净树上不是绿的 ⇒ 先修判据/产品，再谈牙")
            return 1
    wanted = sys.argv[1:]
    tally = {}
    mismatch = 0
    not_run = 0
    results = []
    for name, note, fkey, needle, replacement, target, expect in ARMS:
        if wanted and name not in wanted:
            continue
        text = originals[fkey]
        hits = text.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]（期望 1）" % (name, hits))
            tally["DID-NOT-RUN"] = tally.get("DID-NOT-RUN", 0) + 1
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, "needle 命中 %d ⇒ 不注入" % hits))
            continue
        write(fkey, text.replace(needle, replacement, 1))
        verdict, out = run(target)
        write(fkey, originals[fkey])
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = (verdict == expect)
        if not ok:
            mismatch += 1
        if verdict == "DID-NOT-RUN":
            not_run += 1
        snippet = ""
        for line in out.splitlines():
            if "error:" in line and ("XCTAssert" in line or "failed" in line):
                snippet = line.strip()[:170]
                break
        results.append((name, expect, verdict, note,
                        ("对  期望 %s｜%s" % (expect, snippet)) if ok
                        else ("**不符** 期望 %s 实得 %s｜%s" % (expect, verdict, snippet))))
        print("%s: %s %s" % (name, verdict, note))
    dirty = [k for k in originals if read(k) != originals[k]]
    for k in dirty:
        write(k, originals[k])
    restored = "yes" if not dirty else "二次还原仍不干净：" + ",".join(dirty)
    print("\n=== R110 汇总（每臂按自己的期望判定）===")
    for name, expect, verdict, note, detail in results:
        mark = "OK" if expect == verdict else "!!"
        print("  %s  exp=%-8s got=%-12s %s %s  %s" % (name, expect, verdict, mark, note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and len(results) > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
