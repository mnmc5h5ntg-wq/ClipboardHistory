#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R98 变异对照：种子通道那两条守卫有没有牙（六刀，全部期望 CAUGHT）。

R98 修的是"判据量的不是交付的那一页"：`render` 以前不应用 `Fixture.seed`，
于是 `settings-privacy-excluded` 在判据卷里比交付卷少 60pt 的两行（逐字节差 13079 B）。
新立的 `testSeededFixtureRendersTheSeededPage` 用三格判据钉它：
  ① 拍之前故意把那个键种成**别的条数** ⇒ 只有"`render` 用了夹具自己的种子"能给出期望条数；
  ② 整页零墨 ⇒ 这台机器拍不出，记未运行，不许算通过；
  ③ 拍完之后那个键必须还是我种进去的那一条 ⇒ `render` 只借不占。

六刀分别对应：
  M543 `render` 不种（= 把本轮修复整块撤掉）        ⇒ ① 红（读到 1 段，期望 2）
  M544 mergeGap 8pt → 2px（一颗字被降部数成两颗）   ⇒ ① 红（读到 4 段）
  M545 窄带的段永不合并                             ⇒ ① 与真值表 ③ 都红
  M546 先筛高度、后合并                             ⇒ ① 与真值表 ④ 都红（钉的是**顺序**）
  M547 `render` 拍完不还原                          ⇒ ③ 红
  M548 右边缘窄带从 684pt 放宽到 660pt              ⇒ ① 红（正文段落漏进来）
      —— 这一刀证明那条带是**量出来的**（段落最长写到 681.0pt，「移除」的字尾在 685.5pt），
         不是抄来的常数。

模板四件套沿用 R29d 那一支：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、
读失败消息确认**红得对**。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r98_seed.py
退出码：0 = 六刀全 CAUGHT 且还原干净；非 0 = 有刀漏了或没跑。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r98-seed-mut-shots"

BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
BASE_ENV["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS

SEED = ("UICaptureTests/(testSeededFixtureRendersTheSeededPage"
        "|testInkRunCountArithmeticIsATruthTable)")

CALLSITES = "UICaptureTests/testSeedIsAppliedOnlyInsideRender"

# (编号, 标题, 锚点, 变异后, 跑哪支, 期望红在哪句话)
MUTATIONS = [
    ("M543", "render 不应用 fixture.seed（把 R98 的修复整块撤掉）",
     "            UserDefaults.standard.set(seed.value, forKey: seed.key)",
     "            // M543：撤掉这一句 ⇒ 回到『种子只在捕获那一条路里种』",
     SEED, "右边缘那一列读到 1 段墨"),
    ("M544", "mergeGap 从 8pt 收到 2px（一颗按钮的字被自己的降部数成两颗）",
     "                let found = Self.inkRunCount(column: rightEdge, minRunHeight: 4,\n"
     "                                             mergeGap: Int(8 * scale))",
     "                let found = Self.inkRunCount(column: rightEdge, minRunHeight: 4,\n"
     "                                             mergeGap: 2)",
     SEED, "右边缘那一列读到 4 段墨"),
    ("M545", "窄带的段永不合并（`< mergeGap` 改成 `< 0`）",
     "            if let last = merged.last, run.top - last.bottom - 1 < mergeGap {",
     "            if let last = merged.last, run.top - last.bottom - 1 < 0 {",
     SEED, "一颗按钮被自己的降部切开"),
    ("M546", "先筛高度、后合并（钉的是顺序，不是数值）",
     "        return merged.filter { $0.bottom - $0.top + 1 >= minRunHeight }.count",
     "        let pre = runs.filter { $0.bottom - $0.top + 1 >= minRunHeight }\n"
     "        var again: [(top: Int, bottom: Int)] = []\n"
     "        for run in pre {\n"
     "            if let last = again.last, run.top - last.bottom - 1 < mergeGap {\n"
     "                again[again.count - 1] = (last.top, run.bottom)\n"
     "            } else {\n"
     "                again.append(run)\n"
     "            }\n"
     "        }\n"
     "        return again.count",
     SEED, "两段都不够高、但合并后够"),
    ("M547", "render 拍完不还原（只借不占那一格失去证人）",
     "                if let back = seededOriginal {\n"
     "                    UserDefaults.standard.set(back, forKey: key)",
     "                    if let back = seededOriginal {\n"
     "                        _ = back  // M547：不还原",
     SEED, "没有把"),
    ("M548", "右边缘窄带放宽到 660pt（正文段落漏进来）",
     "                let rightEdge = Self.columnInk(bytes: base, bytesPerRow: rep.bytesPerRow,\n"
     "                                               xRange: Int(684 * scale)..<Int(706 * scale),",
     "                let rightEdge = Self.columnInk(bytes: base, bytesPerRow: rep.bytesPerRow,\n"
     "                                               xRange: Int(660 * scale)..<Int(706 * scale),",
     SEED, "右边缘那一列读到"),
    # M549 打的是**调用点守卫**，不是像素判据：把种子的应用复制回捕获那条路，
    # 帧一张都不变（`render` 已经种过了），所以像素判据不会红 —— 只有写法守卫会红。
    # 这一刀存在的理由：R98 的缺陷形状正是"副本先漂开、帧后不同"，
    # 只留像素判据的话，下一次漂开在"帧还没不同"的那一刻是没人看见的。
    ("M549", "在调用方再种一次（种子的应用重新散落 = 本轮病根的形状）",
     "                let metrics = try render(fixture, appearance: appearance, to: file)\n"
     "                if fixture.contentMustFit { mustFitNames.insert(fixture.name) }",
     "                if let seed = fixture.seed {\n"
     "                    UserDefaults.standard.set(seed.value, forKey: seed.key)\n"
     "                }\n"
     "                let metrics = try render(fixture, appearance: appearance, to: file)\n"
     "                if fixture.contentMustFit { mustFitNames.insert(fixture.name) }",
     CALLSITES, "只准在 `render` 里"),
]


def run(test_filter):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=2400)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not concluded:
        return "DID-NOT-RUN", "整条被 skip：" + (lines[-1][:200] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    originals = {path: open(path, encoding="utf-8").read() for path in (HARNESS,)}
    snapshots = {path: open(path, "rb").read() for path in (HARNESS,)}

    print("=== 预检（不注入任何变异，判据必须绿）===", flush=True)
    ok = True
    for test in (SEED, CALLSITES):
        verdict, out = run(test)
        print("  %-70s %s" % (test, verdict), flush=True)
        if verdict != "ESCAPED":
            ok = False
            print("  " + (out.splitlines() or [""])[-1][:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    only = set(sys.argv[1:])
    results = []
    for mid, title, needle, mutant, test, expect_text in MUTATIONS:
        if only and mid not in only:
            continue
        text = originals[HARNESS]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        with open(HARNESS, "w", encoding="utf-8") as handle:
            handle.write(text.replace(needle, mutant))
        try:
            verdict, out = run(test)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(HARNESS, "wb") as handle:
                handle.write(snapshots[HARNESS])
        reason = ""
        if verdict == "CAUGHT":
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            reason = "对  「" + hit[0].strip()[-150:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else out[-150:])
        results.append((mid, verdict, title, reason))
        print("%s: %s %s %s" % (mid, verdict, title, reason), flush=True)

    print("\n=== R98 种子通道变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print("  %-5s %-12s %s%s  %s" % (mid, verdict, mark, line, reason))
    dirty = [p for p, snap in snapshots.items() if open(p, "rb").read() != snap]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), caught,
             sum(1 for _, v, _, r in results if v == "ESCAPED" or r.startswith("!!")),
             sum(1 for _, v, _, _ in results if v == "DID-NOT-RUN")))
    return 0 if not dirty and caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
