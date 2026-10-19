#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 的变异表：热图梯子的**色觉模拟那根轴**有没有牙。

四把刀，catcher 各不相同，而且第 3 把是本轮真正的收获：

M732 把 g 行换成恒等（`0.700 g + 0.300 r` → `lin.g`）⇒ 红绿不再混合 ⇒
     由**合成纯色那条真值表**红（`rgAfter < byAfter` 给 255 < 255）。
     注意它**不会**弄红产品那 16 条读数（恒等变换让模拟后恰好等于模拟前，全都远在地板之上）——
     那正是本轮要钉的形状：只压地板的判据分不开"梯子挺住了"与"我压根没模拟"。
M733 把 b 行退回 R198 第一版那个量纲 bug（丢掉 `encodeSRGB`，蓝留线性）⇒
     同样**只有真值表红**（中性灰不再是不动点，漂移从 0.00 变成 73）。
     这把刀是"尺子坏了而产品测试全绿"的实物证人，也是那条正对照存在的全部理由。
M734 把模拟的两格换成同一格（`renders[i]` → `renders[i - 1]`）⇒ **产品判据的地板**必须红 ⇒
     这是给那根地板配的正对照：两档真并成一档时，18/255 那条线会响。
M735 让相邻对少跑一对（`1..<` → `2..<`）⇒ **16 条读数的计数闸门**必须红。
     这把刀需要三行整的 needle：`for i in 1..<Self.levels.count {` 那两行在姊妹判据里逐字相同，
     单行会命中 2 次 ⇒ 按规矩把下一行（`let normal = …Simulated 之上那一行`）带上凑成唯一。
"""
import io, os, re, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TEST = "Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift"
CVD = "HeatmapHoverEvidenceTests/testAdjacentHeatLevelsStaySeparableUnderDeuteranopia"
MATRIX = "HeatmapHoverEvidenceTests/testDeuteranopiaSimulationMatrixIsWired"

PAIR_LOOP = (
    "                for i in 1..<Self.levels.count {\n"
    "                    let a = Self.levels[i - 1], b = Self.levels[i]\n"
    "                    let normal = Self.meanMaxChannelDelta(renders[i - 1], renders[i], over: band, size: size)\n"
)

ARMS = [
    ("M732", "deuteranopia 的 g 行退回恒等（红绿不再混 ⇒ 整根轴没接电）", TEST,
     "encodeSRGB(0.700 * lin.g + 0.300 * lin.r)", "lin.g", MATRIX),
    ("M733", "b 行丢掉重新编码（R198 第一版的量纲 bug 原样复现 ⇒ 灰不再是不动点）", TEST,
     "encodeSRGB(0.960 * lin.b + 0.040 * lin.g)", "lin.b", MATRIX),
    ("M734", "模拟拿同一格和自己比（两档真的并成一档 ⇒ 地板必须响）", TEST,
     "Self.meanMaxChannelDeltaSimulated(renders[i - 1], renders[i], over: band, size: size)",
     "Self.meanMaxChannelDeltaSimulated(renders[i - 1], renders[i - 1], over: band, size: size)", CVD),
    ("M735", "相邻对少跑一对（4 对变 3 对 ⇒ 16 条读数的计数闸门必须红）", TEST,
     PAIR_LOOP,
     PAIR_LOOP.replace("for i in 1..<Self.levels.count {", "for i in 2..<Self.levels.count {"), CVD),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), "w", encoding="utf-8") as h:
        h.write(t)


def run(filter_name):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(["swift", "test", "--filter", filter_name], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    executed = failures = skipped = None
    for line in text.splitlines():
        if line.strip().startswith("Executed "):
            m = re.search(r"Executed (\d+) tests?, with (\d+) failures?", line)
            if m:
                executed, failures = int(m.group(1)), int(m.group(2))
            s = re.search(r"(\d+) tests? skipped", line)
            if s:
                skipped = int(s.group(1))
    return proc.returncode, executed, failures, skipped


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print("%s NOT_RUN needle 命中 %d 次（要 1）" % (arm_id, hits), flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl))
            code, executed, failures, skipped = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print("%s RESTORE_FAILED ⇒ 立刻停表" % arm_id, flush=True)
            return 2
        if not executed or skipped:
            not_run += 1
            print("%s NOT_RUN 跑到=%s skip=%s ⇒ 不算 CAUGHT：%s" % (arm_id, executed, skipped, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print("%s CAUGHT  %s ⇒ %s（失败 %d，跑到 %d）" % (arm_id, filt, why, failures, executed), flush=True)
        else:
            escaped += 1
            print("%s ESCAPED %s ⇒ %s" % (arm_id, filt, why), flush=True)
    print("R198_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes"
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == "__main__":
    sys.exit(main())
