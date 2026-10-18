#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 的变异表：药丸几何这颗纯核 + 那条两态像素判据，各自有没有牙。

为什么不复用 `mutate_r172.py` 那一系的壳：那个壳只有**一个**原文槽（BACKLOG 207 记着），
多靶表会拿后一靶的原文去覆盖前一靶的文件，而结论照打 CAUGHT —— 本轮的表跨三个文件，所以自带一条
"每臂自己读、自己写、自己还原"的循环，任何一步不满足就 exit 1，不出表。

臂的形状按 `mutate_needle_precheck.arm_sites` 认的那一种写：`(编号, 说明, 文件, needle, 变异文, 该跑的卷)` ——
第一版我把文件放在第二位，预检当场报"静态抽不出 needle ⇒ 不在覆盖里"（R189 实测），
也就是说：**表能跑不等于表被查重**。查重管的是"needle 还指得到东西"，跑管的是"它红了谁"。

规矩（都是账里栽过的）：
· needle 必须在目标文件里**恰好命中一次**，否则该臂记 NOT_RUN（不是通过）；
· 还原用**内存快照**，绝不 `git checkout` —— 本轮工作树是脏的（未提交的判据就在里面）；
· 每臂跑完立刻还原并核对字节，最后 RESTORE_CLEAN 必须是 yes；
· 结论行走文件通道（本机 swift test 会丢 stdout 尾巴）。
"""
import io
import os
import subprocess
import sys
import tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
GEO = "Sources/ClipboardHistoryApp/Views/FilterPillGeometry.swift"
VIEW = "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"
TEST = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
PURE = "FilterPillGeometryTests"
PIXEL = "UICaptureTests/testFilterPillBrightBandFollowsTheSelectedSegment"

ARMS = [
    ("M696", "段号反号：选中第 0 段却画到第 1 段", GEO,
     "let clamped = min(max(index, 0), count - 1)",
     "let clamped = min(max(count - 1 - index, 0), count - 1)", PURE),
    ("M697", "药丸钉死在第 0 段（不跟选中走）", GEO,
     "x: track.minX + CGFloat(clamped) * segment + horizontalInset",
     "x: track.minX + horizontalInset", PURE),
    ("M698", "视图绕开纯核的摆放约定（接线断）", VIEW,
     ".position(x: rect.midX, y: rect.midY)",
     ".offset(x: rect.minX, y: rect.minY)", PURE),
    ("M699", "两态塌成一态（对照失去对象）", TEST,
     "favStore.perform(.updateFilter(.favorites))",
     "favStore.perform(.updateFilter(.all))", PIXEL),
    ("M700", "越上界不夹住：索引算错被画成轨道外的药丸", GEO,
     "let clamped = min(max(index, 0), count - 1)",
     "let clamped = max(index, 0)", PURE),
    ("M701", "把「有名字的未判定」变成唯一出口（判据被出口吃掉）", TEST,
     "canJudge = cAll >= 0 && cFav >= 0",
     "canJudge = false", PIXEL),
    ("M702", "退化输入不再给空矩形（除零路径被放行）", GEO,
     "guard count > 0, track.width > 0, track.height > 0 else {",
     "guard count >= 0, track.width > 0, track.height > 0 else {", PURE),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run_test(filter_name, shots_dir):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots_dir
    proc = subprocess.run(["swift", "test", "--filter", filter_name],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode


def main():
    only = sys.argv[1:] or None
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        if only and arm_id not in only:
            continue
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print("%s NOT_RUN needle 命中 %d 次（要 1）on %s" % (arm_id, hits, target), flush=True)
            continue
        shots = tempfile.mkdtemp(prefix="r189-mut-")
        try:
            write(target, original.replace(needle, repl))
            code = run_test(filt, shots)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表（工作树已被改坏）" % arm_id, flush=True)
            return 2
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s" % (arm_id, filt, why), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s 仍绿 ⇒ %s（这一支没有牙）" % (arm_id, filt, why), flush=True)
    total = caught + escaped + not_run
    print("MUTATE_R189 CAUGHT=%d/%d, RESTORE_CLEAN=yes" % (caught, total))
    print("SUMMARY caught=%d escaped=%d not_run=%d" % (caught, escaped, not_run))
    if only:
        return 0
    return 0 if (escaped == 0 and not_run == 0 and total == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
