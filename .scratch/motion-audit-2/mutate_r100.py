#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R100 的变异对照：卡片**水平**内缩这把新尺，今天三刀（M556/M557/M559），全部期望 CAUGHT；
M558 已于 R102 退役，理由与接班者见下面"四刀各钉一角"那一节。

本轮做的事（结论是"138 不是缺陷"，所以这一轮的产物是**判据**而不是产品改动）：
  ① 修 R100 自己写的第一版横向尺 —— 它把"材质"和"墨"两条问句压在**同一条
     26pt 带子**上（卡片顶往下 26pt）。那一格有两个错：
       · 材质被**圆角**骗：探针那张卡片只有 26pt 高，带子里外都是角，
         左沿读晚 7.5pt，正好落在字上 ⇒ 报出"内缩 0.0pt"（一个没有的产品数值）；
       · 墨被**带子**骗：`settings-general` 报 26.0pt，因为带子只盖住第一行，
         而那一行的墨是复选框**后面**的标签；其余四屏第一行是小标题 ⇒ 5.5pt。
         同一扇窗口里"卡片内缩"被量成两个差 20 倍的数，而产品一行都没错。
     现在：材质问卡片**纵向中点**那一行（直边），墨问**整张卡片内沿**。
  ② 门限扫过 12..64（`r100_gate.py`）⇒ 读数对门限不敏感，六屏 × 两档全是 5.0/5.5。
  ③ 判据钉成"与系统 `GroupBox` 同档（±1pt）"，不是"≥16pt"：量出来的系统自己那一档
     就是 5.5pt，"macOS 通常 16–20pt"没有出处。

四刀各钉一角：
  M556 产品：共享的 `.settingsCardInset()` 加 12pt 横向留白 ⇒ 二十格全红
              —— 这一刀钉的是"判据拦得住真正会发生的那件事"（以后有人给卡片配横向内边距）
  M557 尺子：墨的 y 带还原成本轮那个"卡片顶往下 26pt" ⇒ `settings-general` 26pt 红
              （= 本轮修掉的那个 bug 本身，这一刀证明修它是必要的、且判据能看见它）
  M558 【已退役 · R102】尺子：把系统参照从名单里摘掉 ⇒ "参照缺席"必须红（对照不是装饰）。
       退役理由：它钉的那一行 `let isProbe = fixture.name == "cardprobe-groupbox-default"`
       被 **R101 的角色分账**重写成了 `hasPrefix("cardprobe-")`（参照从一臂变成一梯子），
       而那一轮**已经把同一个靶搬进 `mutate_r101.py` 的 M565**（M565 的说明里就写着
       "M558 的靶在新结构下仍有牙"）—— 只是当时没有把 M558 摘下来，于是它的 needle 命中 0 次，
       在 R102 的电池里以 `not_run=1 / MUT_EXIT=1` 响出来（R102 / U-301）。
       处置与 R101 对 M560 的做法一致：**写明接班者并从 ARMS 里移除**，不删记录、不放宽期望。
  M559 尺子：墨门限从 60 降到 4 ⇒ 读到边框/抗锯齿 ⇒ 内缩塌到 ~0.5pt 红
              （这一刀反过来钉住②：12..64 是**平台**，不是碰巧读数一致）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r100.py [M556 ...]
退出码：0 = 全部 CAUGHT 且还原干净。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
SETTINGS = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"

BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

INSET = "UICaptureTests/testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox"
TRUTH = "UICaptureTests/testHorizontalEdgeRulerIsATruthTable"

# (编号, 标题, 文件, needle, mutant, 期望红在哪句话)
ARMS = [
    ("M556", "产品：共享的 settingsCardInset 加 12pt 横向留白", SETTINGS,
     "padding(.vertical, SettingsViewLayout.cardEdgeInset)",
     "padding(.horizontal, 12).padding(.vertical, SettingsViewLayout.cardEdgeInset)",
     "差超过 1pt"),
    ("M557", "尺子：墨的 y 带还原成「卡片顶往下 26pt」（本轮修掉的那个 bug）", HARNESS,
     "inkYRange: (cardTopPx + 3)..<(cardBottomPx - 3),",
     "inkYRange: cardTopPx..<(cardTopPx + Int(26 * scale)),",
     "差超过 1pt"),
    # M558 已退役（R102 / U-301）：needle 那一行被 R101 的角色分账重写掉了，
    # 同一个靶由 `mutate_r101.py` 的 **M565** 接手（那里注释写着"M558 的靶在新结构下仍有牙"，
    # 但当时漏了把这一刀摘下来 ⇒ 它空转了一轮）。理由全文在文档串里。
    # 这一刀是 M559 第一版（把墨门限 60→4）**逃掉之后**换出来的：
    # 门限那一刀让参照与被告**同偏** ⇒ 等式判据看不见（相对判据对"整把尺一起偏"免疫，
    # 这是本轮最值钱的一条工具结论）。换成圆角那一刀 —— 它同样让两边同偏，
    # 但本轮补上的**绝对锚点**（参照左沿必须落在夹具声明的 .padding(24) 上）咬得住它。
    ("M559", "尺子：材质带压回卡片顶（= 圆角那一族错法，等式免疫、锚点不免疫）", HARNESS,
     "materialYRange: (mid - 1)..<(mid + 2),",
     "materialYRange: cardTopPx..<(cardTopPx + 3),",
     "尺却把卡片左沿读在"),
]


def run(test_filter, timeout=2400):
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True,
                          env=BASE_ENV, timeout=timeout)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        # 编译器崩了（M556 第一版就是这样：两语句塞进 `-> some View` 的单表达式体，
        # 前端直接 fatalError）时**最后几行**只有 "error: fatalError"，看不出为什么。
        # 所以把带 `error:` 的行都捞出来，DID-NOT-RUN 必须说得出原因。
        errs = [l.strip()[:160] for l in lines if "error:" in l][:4]
        return "DID-NOT-RUN", out, " || ".join(errs) or "\n".join(lines[-3:])
    concluded = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not concluded:
        return "DID-NOT-RUN", out, "整条被 skip：" + (lines[-1][:200] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, ""


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    only = set(sys.argv[1:])
    results = []
    paths = sorted({HARNESS, SETTINGS})
    originals = {p: read(p) for p in paths}
    snapshots = {p: open(os.path.join(ROOT, p), "rb").read() for p in paths}

    print("=== 预检（不注入任何变异，两支判据都必须绿）===", flush=True)
    ok = True
    for test in (INSET, TRUTH):
        verdict, out, note = run(test)
        print("  %-70s %s" % (test, verdict), flush=True)
        if verdict != "ESCAPED":
            ok = False
            print("  " + note[:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    for mid, title, path, needle, mutant, expect in ARMS:
        if only and mid not in only:
            continue
        text = originals[path]
        got = text.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, "needle 命中 %d 次，期望 1 ⇒ 不注入" % got))
            print("%s: DID-NOT-RUN needle 命中 %d 次" % (mid, got), flush=True)
            continue
        write(path, text.replace(needle, mutant))
        try:
            verdict, out, note = run(INSET)
            if verdict == "CAUGHT":
                hit = [l for l in out.splitlines() if expect in l]
                if not hit:
                    verdict = "MISMATCH"
                    note = "!! 红得不对（找不到期望文本「%s」）" % expect
                else:
                    note = "对  " + hit[0].strip()[-150:]
                    # M558 那一刀只允许"参照缺席"这一条红；其余三刀要看到红格数 >0。
                    bad = [l for l in out.splitlines() if "XCTAssert" in l and "failed" in l]
                    note += " | 红行数=%d" % len(bad)
            else:
                note = note or "整条判据没红"
        except subprocess.TimeoutExpired:
            verdict, note = "DID-NOT-RUN", "timeout"
        finally:
            write(path, originals[path])
        results.append((mid, verdict, title, note))
        print("%s: %s %s %s" % (mid, verdict, title, note), flush=True)

    print("\n=== R100 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print("  %-5s %-12s %s%s  %s" % (mid, verdict, mark, line, reason))
    dirty = [p for p in paths
             if open(os.path.join(ROOT, p), "rb").read() != snapshots[p]]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    caught = sum(1 for _, v, _, _ in results if v == "CAUGHT")
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), caught,
             sum(1 for _, v, _, r in results if v in ("ESCAPED", "MISMATCH")
                 or r.startswith("!!")),
             sum(1 for _, v, _, _ in results if v == "DID-NOT-RUN")))
    want = len(ARMS) if not only else len(only)
    return 0 if not dirty and caught == want else 1


if __name__ == "__main__":
    sys.exit(main())

