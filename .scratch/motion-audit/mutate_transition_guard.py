#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变异对照：R5 那条"全 Views 不许留不会执行的过渡声明"到底抓不抓得住。

为什么这一轮要重跑：上一版扫描器的排除项写成 `!line.contains("content")`，
于是角色名 `.contentFade` 把它最该抓的那类声明整行豁免了 —— 变异 M6 报 ESCAPED，
而守卫自己一路绿灯。修好之后必须用**同一支变异**证明它现在会红，
并且补一支"裸写法"变异（`.transition(.opacity)`），因为检测面原来只数目录的工厂名。

规矩（都是以前栽过跟头之后写下来的）：
- 注入前先跑一遍基线，基线不绿就不许注入（否则"红"可能是别的用例坏了）；
- 红必须是**这条断言**的红，且必须是编译成功的红 —— 编译报错当成抓到，是自欺；
- 每个变异用 `cp` 逐文件还原，不用 `git checkout -- .`（那会扫掉未提交的工作）；
- 子进程要摘掉 SDKROOT：python3 会把它注入成 CLT 的 SDK，和 Xcode 编译器不配对，
  表现为"0 个用例有效"，看起来像变异没被抓到。
"""
import os
import shutil
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
TARGET = os.path.join(REPO, "ClipboardHistory/Sources/ClipboardHistoryApp/Views/MenuBarRecommendationsView.swift")
TEST = "MotionFilmstripTests/testNoUnexecutedTransitionClaimsAcrossViews"
NEEDLE = "处 .transition 声明"

ANCHOR = 'message: historyStore.isRefreshingPredictions ? "正在整理推荐…" : "暂无推荐")\n'

MUTANTS = [
    ("M6-role-name", ANCHOR + "                    .transition(MotionCatalog.transition(for: .contentFade))\n"),
    ("M6-bare", ANCHOR + "                    .transition(.opacity)\n"),
]


def run(cmd):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(cmd, cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out, _ = proc.communicate()
    return proc.returncode, out


def run_test():
    return run(["swift", "test", "--filter", TEST])


def classify(code, out):
    if "Build complete" not in out and "error:" in out:
        return "DID-NOT-RUN=build-failed", out
    if "Test Case '-[" not in out:
        return "DID-NOT-RUN=no-test-executed", out
    if "Executed 0 tests" in out:
        return "DID-NOT-RUN=zero-tests", out
    if "failed (" in out and NEEDLE in out:
        return "CAUGHT", out
    if "passed (" in out and "0 failures" in out:
        return "ESCAPED", out
    return "AMBIGUOUS", out


def main():
    backup = "/tmp/menubar_reco_before_mutation.swift"
    shutil.copy2(TARGET, backup)
    original = open(backup, encoding="utf-8").read()
    results = []
    try:
        # ① 基线自测：不绿就不许往下注入。
        code, out = run_test()
        # 基线那一遍的"绿"不能借用变异那套词（ESCAPED/CAUGHT）：同一个词在两个判据里
        # 含义不同，读日志的人会把"基线绿"看成"变异没抓到"。
        print("BASELINE=%s" % ("green" if "0 failures" in out else "NOT-GREEN"))
        if verdict != "CAUGHT" and "passed" not in out:
            print("基线无法判定，停止注入（不把别处的红当成本轮的结论）")
            print(out[-1500:])
            return 2
        if "0 failures" not in out:
            print("基线不绿，停止注入")
            return 2

        # ② 逐个注入。
        for name, injected in MUTANTS:
            if injected.strip() in original:
                print("%s: DID-NOT-RUN=already-present" % name)
                results.append((name, "DID-NOT-RUN=already-present"))
                continue
            with open(TARGET, "w", encoding="utf-8") as fh:
                fh.write(original.replace(ANCHOR, injected, 1))
            code, out = run_test()
            verdict, _ = classify(code, out)
            results.append((name, verdict))
            print("%s: %s" % (name, verdict))
            if verdict.startswith("DID-NOT") or verdict == "AMBIGUOUS":
                print(out[-1200:])
            shutil.copy2(backup, TARGET)
            if open(TARGET, encoding="utf-8").read() != original:
                print("还原失败：文件与注入前不一致，停止")
                return 3
    finally:
        shutil.copy2(backup, TARGET)

    bad = [n for n, v in results if v != "CAUGHT"]
    print("MUTATION_SUMMARY caught=%d/%d %s" % (len(results) - len(bad), len(results),
                                                ("残留: " + ", ".join(bad)) if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
