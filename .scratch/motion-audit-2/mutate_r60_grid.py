#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R60 变异对照：网格的行序、合成夹具、以及"框退化成整幅"。

R59 之后剩下的两个已知洞（BACKLOG 84 行序没判据、以及"新判据到底有没有牙"）。
这一支电池全部打在**尺子**上，产品零改动。

  M308 网格行序翻回去（第 0 行 = 画面底部）  ⇒ 该红在 `testChangeGridPrintsRowZeroAtTheTop`。
       这就是 R58 之前那个坏形状；它当时能活半年，正因为网格只输出字符串、不参与断言。
  M309 合成夹具的 `inRows && inCols` 改成 `||` ⇒ 该红：两条方向测试都得发现自己那份夹具坏了。
       这一支钉的是"夹具自己不对称就红"那一格 —— 夹具坏了还绿，比没判据更糟。
  M310 网格里把 band 传成 nil（每格读整幅）   ⇒ 该红：每行都会一样亮，行序就无从谈起。
       这一支是"格子退化"的坏法：读数仍然在变、字符串仍然好看，但它已经不是位置了。

用法：`python3 .scratch/motion-audit-2/mutate_r60_grid.py [--measure] [M308 …]`
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
REPO = os.path.join(ROOT, "ClipboardHistory")
TESTS = os.path.join(REPO, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
BASE_ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
BASE_ENV["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r60-mut"

GRID = "MotionFilmstripTests.testChangeGridPrintsRowZeroAtTheTop"
DIRECTION = "MotionFilmstripTests.testBandRectMapsToTheEndItClaims"

MUTATIONS = [
    ("M308", "网格行序翻回去（第 0 行 = 画面底部）", TESTS,
     """                let band = CGRect(x: CGFloat(col) / CGFloat(cols), y: CGFloat(row) / CGFloat(rows),
                                  width: 1 / CGFloat(cols), height: 1 / CGFloat(rows))""",
     """                let band = CGRect(x: CGFloat(col) / CGFloat(cols),
                                  y: CGFloat(rows - 1 - row) / CGFloat(rows),   // MUTANT
                                  width: 1 / CGFloat(cols), height: 1 / CGFloat(rows))""",
     GRID, ["第 0 行必须整行亮", "最后一行才该亮"]),
    ("M309", "合成夹具的与改成或（夹具自己不再不对称）", TESTS,
     "            return inRows && inCols ? ink : nil",
     "            return inRows || inCols ? ink : nil   // MUTANT",
     "%s|%s" % (DIRECTION, GRID), ["夹具", "不该亮"]),
    ("M310", "网格里每格都读整幅（band 退化成 nil）", TESTS,
     "                let v = changedFraction(bitmaps[index], bitmaps[index + 1], band: band)",
     "                _ = band\n                let v = changedFraction(bitmaps[index], bitmaps[index + 1], band: nil)   // MUTANT",
     GRID, ["不该亮"]),
]


def run(filter_name):
    proc = subprocess.run(["swift", "test", "--filter", filter_name], cwd=REPO,
                          capture_output=True, text=True, env=BASE_ENV, timeout=1800)
    out = proc.stdout + proc.stderr
    verdicts = [l for l in out.splitlines()
                if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    open(path, "w", encoding="utf-8").write(text.replace(old, new))
    return text


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    for mid, _d, path, old, _n, _f, _needles in MUTATIONS:
        n = open(path, encoding="utf-8").read().count(old)
        if n != 1:
            raise SystemExit("预检中止：%s 的锚点出现 %d 次（要 1 次）\n  %s" % (mid, n, old[:160]))
    # 预检：还原态必须**不红**，否则"红了"不能算变异的功劳。
    for f in (GRID, DIRECTION):
        code, out, _ = run(f)
        if code != "ESCAPED":
            raise SystemExit("预检失败（%s）：%s\n%s" % (f, code, out[-1500:]))
        print("预检 OK " + f)
    results = []
    for mid, desc, path, old, new, filt, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run(filt)
        finally:
            ok = (restore(path, original) == original)
        hit = [x for x in needles if x in out]
        right = code == "CAUGHT" and len(hit) >= 1
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s 命中=%s 还原干净=%s" % (mid, desc, code, right, failed[:3], hit, ok))
        if measure or not right:
            for line in [l for l in out.splitlines() if "error: -[" in l][:4]:
                print("   MSG| " + line.strip()[:260])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes" or r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对/未抓到=%d  还原不干净=%d" % (len(bad), len(dirty)))
    code, _, _ = run(GRID)
    print("还原后复跑（网格行序判据）：" + code)
    if bad or dirty or code != "ESCAPED":
        raise SystemExit("R60_MUTATION_PROBLEM")


def restore(path, text):
    open(path, "w", encoding="utf-8").write(text)
    return open(path, encoding="utf-8").read()


main()
