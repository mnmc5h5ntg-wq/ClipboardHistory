#!/usr/bin/env python3
"""R29d 变异对照：把"暗档侧栏文字不可见"这件事从散文变成一条会红的账。

三支：
  M132 从盲区名单里摘掉一条            ⇒ 必须红在"第一次出现反侧墨"（extra 那一半）
  M133 把量尺的框缩到压不住任何字      ⇒ 必须红在"一条都没判"，不许安静地全走 NOT-RUN
  M134 对调 `inkSideCounts` 的两侧计数 ⇒ 必须红在"这些帧现在落在期望侧了"（gone 那一半）

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r29d-mut-shots"

GUARD = "UICaptureTests/testDarkSettingsSidebarTextIsACountedBlindSpot"
TRUTH = "UICaptureTests/testInkDirectionTruthTable"

# R382 重钉：名单已长到 13 张并夹了注释，旧的全表字面量不再命中。
# 同一行在视图树探针那张表里也出现（10492 行），所以针带上 `static let` 那一行做上下文。
# R426 重钉（第二次）：两档负臂现在同一行（`settings-general-no-footer`, `settings-min-no-footer`），
# 下一行才是 settings-general。针以这两行为上下文，避免命中视图树探针里的同名行。
LIST_NEEDLE = """        "settings-general-no-footer", "settings-min-no-footer",
        "settings-general", "settings-general-legacy-helper-font", "settings-shortcuts", "settings-privacy","""
LIST_MUTANT = """        "settings-general-no-footer", "settings-min-no-footer",
        "settings-general-legacy-helper-font", "settings-shortcuts", "settings-privacy","""

BOX_NEEDLE = "static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 102, height: 224)"
BOX_MUTANT = "static let settingsSidebarTextColumn = CGRect(x: 40, y: 60, width: 400, height: 224)"

# R382 重钉：名单尾部两行现在是 tall 那一对；往后面塞一张非 vibrant 的帧。
LIST2_NEEDLE = '        "settings-privacy-tall", "settings-recommendations-tall",'
LIST2_MUTANT = '        "settings-privacy-tall", "settings-recommendations-tall",\n        "content-empty",'

VIB_NEEDLE = """            let name = view.effectiveAppearance.name.rawValue
            if name.contains("Vibrant"), view.convert(view.bounds, to: nil).intersects(column) {"""
VIB_MUTANT = """            let name = ""
            if name.contains("Vibrant"), view.convert(view.bounds, to: nil).intersects(column) {"""

SWAP_NEEDLE = "if signed > gate { brighter += 1 } else if signed < -gate { darker += 1 }"
SWAP_MUTANT = "if signed > gate { darker += 1 } else if signed < -gate { brighter += 1 }"

MUTATIONS = [
    ("M132", "盲区名单里摘掉 settings-general", LIST_NEEDLE, LIST_MUTANT, GUARD,
     "两者必须一致"),
    # R495：M133（缩框）退役 —— 现行守卫在框压不住字时走具名 NOT_RUN（不是静默绿），
    # 缩框/扩框都改不动 roster 判定（框被侧栏视图裁剪）⇒ 这一臂已无法咬，按"空刀不凑数"退役。
    # 它原本要守的"尺没有对象不许绿"由同表的 TEXT_SIDE_CAPABILITY 与 NOT_RUN 出口接管。

    ("M134", "对调 inkSideCounts 的两侧计数", SWAP_NEEDLE, SWAP_MUTANT, GUARD,
     "落在错误一侧"),
    # R30：名单改成由"侧栏子树是不是 vibrant"这条**前提**决定，于是动前提也要能红。
    ("M135", "往名单里塞一条非 vibrant 的帧", LIST2_NEEDLE, LIST2_MUTANT, GUARD,
     "两者必须一致"),
    ("M136", "让 vibrant 探针永远读不到外观", VIB_NEEDLE, VIB_MUTANT, GUARD,
     "两者必须一致"),
]

BASE_ENV = {key: value for key, value in os.environ.items() if key != "SDKROOT"}


def run(test_filter):
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    lines = out.splitlines()
    passed = [line for line in lines if "Test Case" in line and "passed" in line]
    failed = [line for line in lines if "Test Case" in line and " failed" in line]
    if not passed and not failed:
        return "DID-NOT-RUN", "整条被 skip：" + (lines[-1][:160] if lines else "")
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out


def main():
    with open(HARNESS, encoding="utf-8") as handle:
        original = handle.read()
    snapshot = open(HARNESS, "rb").read()

    print("=== 预检（不注入任何变异，两条判据都必须绿）===", flush=True)
    ok = True
    for test in (GUARD, TRUTH):
        verdict, out = run(test)
        print(f"  {test:62s} {verdict}", flush=True)
        if verdict != "ESCAPED":
            ok = False
            print((out.splitlines() or [""])[-1][:220], flush=True)
    if not ok:
        print("PREFLIGHT_FAILED ⇒ 一支都不注入（DID-NOT-RUN 不是结果）", flush=True)
        return 2

    results = []
    for mid, title, needle, mutant, test, expect_text in MUTATIONS:
        got = original.count(needle)
        if got != 1:
            results.append((mid, "DID-NOT-RUN", title, f"needle 命中 {got} 次，期望 1 ⇒ 不注入"))
            print(f"{mid}: DID-NOT-RUN needle 命中 {got} 次", flush=True)
            continue
        with open(HARNESS, "w", encoding="utf-8") as handle:
            handle.write(original.replace(needle, mutant))
        try:
            verdict, out = run(test)
        except subprocess.TimeoutExpired:
            verdict, out = "DID-NOT-RUN", "timeout"
        finally:
            with open(HARNESS, "wb") as handle:
                handle.write(snapshot)
        reason = ""
        if verdict == "CAUGHT" and expect_text:
            hit = [line for line in out.splitlines() if expect_text in line][:1]
            reason = "对  「" + hit[0].strip()[-150:] + "」" if hit else "!! 红得不对（找不到期望文本）"
        if verdict == "DID-NOT-RUN":
            first = [line for line in out.splitlines() if "error:" in line][:1]
            reason = "  " + (first[0][:150] if first else "")
        results.append((mid, verdict, title, reason))
        print(f"{mid}: {verdict} {title} {reason}", flush=True)

    print("\n=== R29d 变异对照汇总 ===")
    for mid, verdict, line, reason in results:
        mark = "OK " if verdict == "CAUGHT" and not reason.startswith("!!") else "!! "
        print(f"  {mid:5s} {verdict:12s} {mark}{line}  {reason}")
    dirty = [] if open(HARNESS, "rb").read() == snapshot else [HARNESS]
    print("RESTORE_CLEAN=" + ("yes" if not dirty else "NO " + ", ".join(dirty)))
    print(f"CAUGHT={sum(1 for _, v, _, _ in results if v == 'CAUGHT')}/{len(results)}")
    return 0 if not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
