#!/usr/bin/env python3
"""R81 的变异对照：那条并发锤击判据**有没有牙**。

背景（读 R79 的 CI 读出来的，记在 BACKLOG 112）：`CaptureReadings.emit` 的两条腿都不是原子的
—— `print(line)` 把内容与换行分两次 write，文件通道 `seekToEndOfFile()` + `write()` 也不是一个
原子动作，而 `opened` 那个 `nonisolated(unsafe) static var` 本身就是竞争点。
后果是有实锤的：R79 那一遍里决定 BACKLOG 109 的那条读数被缝进了另一条判据的行。

三刀（每刀跑 3 遍，因为并发缺陷不是每次都复现 —— 复现率本身就是这一格的"分辨率"）：
  M434 `appendForced` 拿掉锁                ⇒ 锤击判据该红（至少一遍）
  M435 只拿掉锁、保留 openedURLs 的原子性   ⇒ 与 M434 同一形状，作为复现率的第二次测量
  M436 把"整份重写"的判断挪到锁外           ⇒ 拦的是"两个线程都以为自己是第一行"
若三遍都不红，就照实记"这条修没有红钉着"，不许写成钉住了（账本里"监视器自己没验过"那一族）。

用法：`python3 .scratch/motion-audit-2/mutate_r81_channel_lock.py`
"""
import io
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
CR = "ClipboardHistory/Tests/ClipboardHistoryAppTests/CaptureReadings.swift"
CASE = "testConcurrentReadingsNeitherSpliceNorDropALine"
ATTEMPTS = 3

MUTATIONS = [
    ("M434", "把 `appendForced` 的锁拿掉（回到 R79 之前那个形状）",
     """    static func appendForced(_ line: String, to url: URL) {
        lock.lock()
        defer { lock.unlock() }
        do {""",
     """    static func appendForced(_ line: String, to url: URL) {
        // R81 变异：锁拿掉
        do {"""),
    ("M435", "同一刀再跑一遍（并发缺陷的复现率本身要被量出来）",
     """    static func appendForced(_ line: String, to url: URL) {
        lock.lock()
        defer { lock.unlock() }
        do {""",
     """    static func appendForced(_ line: String, to url: URL) {
        // R81 变异：锁拿掉（第二次）
        do {"""),
    # 原来这一刀想做的是"把第一次写的判断挪到锁外"，但那样写编译不过（`payload` 还没算出来），
    # 而"编译不过"不是判据的失败、是**刀的失败** —— 换成同一条承重关系的另一刀：
    # "整份重写"这条分支如果每次都走，追加就不存在了 ⇒ 行数那一条必须红。
    # 这一刀钉的是"这一卷是**累积**起来的"这件事有人看着（M341 那一族：文件通道的历史本身）。
    ("M436", "『第一次写要整份重写』这条分支每次都走 ⇒ 每一行都把整卷抹掉（追加逻辑作废）",
     """        if !openedURLs.contains(url) {""",
     """        if true {  // R81 变异：整份重写不再只走第一次"""),
]


def read(path):
    return io.open(os.path.join(REPO, path), encoding="utf-8").read()


def write(path, text):
    io.open(os.path.join(REPO, path), "w", encoding="utf-8").write(text)


def run_once():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r81_mutation_shots"
    proc = subprocess.run(["swift", "test", "--filter", "UICaptureTests/" + CASE],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=1200)
    text = proc.stdout + proc.stderr
    red = bool(re.search(r"%s[^\n]*' failed" % re.escape(CASE), text))
    # **分类器本身要认得崩溃**（R81 的第一版不认，把三刀全报成"编译没过"）：
    # swift-testing 的崩溃行是 `error: Exited with unexpected signal code 11` ——
    # 它带 "error: " 却没有 `error: -[类 方法]` 那个形状，于是被旧分类器归进"没跑成"。
    # 而崩溃在这里恰恰是**最硬的证据**：没有锁，两个线程同时改同一个 Set / 同一个 FileHandle，
    # 进程直接段错误 —— 那不是"这一刀没落地"，是"这一刀比预想的更狠"。
    crashed = bool(re.search(r"Exited with unexpected signal|signal code \d+", text))
    compile_error = (not red) and (not crashed) and "error: " in text
    msgs = [l[:220] for l in text.splitlines()
            if "error: -[" in l or "signal" in l.lower()][:3]
    return red, (compile_error, crashed), msgs


def main():
    original = read(CR)
    print("=== 基线（带锁）：3 遍都必须绿 ===")
    base = [run_once() for _ in range(ATTEMPTS)]
    print("   基线红=%d/%d 崩溃=%d/%d"
          % (sum(1 for r, _, _ in base if r), ATTEMPTS,
             sum(1 for _, (_, c), _ in base if c), ATTEMPTS))
    if any(r or c for r, (_, c), _ in base):
        print("DRIFT-BASELINE 带锁还会红 ⇒ 这一格测的不是锁，整批作废")
        for _, _, msgs in base:
            for m in msgs:
                print("     " + m)
        return 1
    summary = []
    for tag, note, needle, replacement in MUTATIONS:
        print("\n%s %s" % (tag, note))
        text = read(CR)
        if needle not in text:
            print("   NOT-APPLIED 锚点没找到")
            summary.append((tag, "NOT-APPLIED"))
            continue
        if needle in replacement:
            print("   NOT-APPLIED 变异文包含原文")
            summary.append((tag, "NOT-APPLIED"))
            continue
        write(CR, text.replace(needle, replacement, 1))
        after = read(CR)
        if needle in after or replacement not in after:
            print("   NOT-APPLIED 回读证明这一刀没落地")
            write(CR, original)
            summary.append((tag, "NOT-APPLIED"))
            continue
        try:
            results = [run_once() for _ in range(ATTEMPTS)]
        finally:
            write(CR, original)
            print("   已还原（逐字节相同：%s）" % (read(CR) == original))
        reds = sum(1 for r, _, _ in results if r)
        crashes = sum(1 for _, (_, c), _ in results if c)
        broken = sum(1 for _, (ce, c), _ in results if ce)
        for _, _, msgs in results:
            for m in msgs:
                print("     " + m)
        if broken:
            print("   NOT-RUN 有 %d 遍编译没过" % broken)
            summary.append((tag, "NOT-RUN"))
        elif reds or crashes:
            print("   CAUGHT 红 %d/%d 遍、崩溃 %d/%d 遍（崩溃=没有锁时两个线程同时改同一个"
                  " Set / FileHandle，进程直接段错误 —— 这一刀比预想的更狠，但**必须由判据自己说出口**）"
                  % (reds, ATTEMPTS, crashes, ATTEMPTS))
            summary.append((tag, "CAUGHT"))
        elif False:
            print("   CAUGHT %d/%d 遍红（复现率 %d%%）" % (reds, ATTEMPTS, reds * 100 // ATTEMPTS))
            summary.append((tag, "CAUGHT"))
        else:
            print("   NO-TEETH %d 遍全绿 ⇒ 这一格钉不住这一刀，只能照实记" % ATTEMPTS)
            summary.append((tag, "NO-TEETH"))
    print("\n=== 汇总 ===")
    for tag, mark in summary:
        print("   %-6s %s" % (tag, mark))
    return 0


if __name__ == "__main__":
    sys.exit(main())
