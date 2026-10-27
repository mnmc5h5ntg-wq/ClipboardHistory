#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R425 变异对照：来源 App 图标的纯策略（可见性、bundle 归一、退回符号）。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
POLICY = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/SourceAppBadgePolicy.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "SourceAppBadgeTests|testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed"

VISIBLE_NEEDLE = "        normalized(sourceAppName) != nil\n"
ALWAYS_TRUE = "        true\n"
ALWAYS_FALSE = "        false\n"
BUNDLE_NEEDLE = "        guard let id = normalized(bundleID) else { return nil }\n"
BUNDLE_MUTANT = "        let id = bundleID ?? \"\"\n"
TRIM_NEEDLE = "        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)\n"
TRIM_MUTANT = "        let trimmed = text\n"
FALLBACK_NEEDLE = "    static let fallbackSymbolName = \"app\"\n"
FALLBACK_MUTANT = "    static let fallbackSymbolName = \"questionmark\"\n"
WIDTH_NEEDLE = "    static let minimumDetailWidthForIcon: CGFloat = 400\n"
WIDTH_MUTANT = "    static let minimumDetailWidthForIcon: CGFloat = 0\n"
COMPARE_NEEDLE = "        isVisible(sourceAppName: sourceAppName) && detailWidth >= minimumDetailWidthForIcon\n"
COMPARE_MUTANT = "        isVisible(sourceAppName: sourceAppName) && detailWidth <= minimumDetailWidthForIcon\n"

MUTATIONS = [
    ("M1133", "没有来源名也占一格（可见性恒真）", POLICY, VISIBLE_NEEDLE, ALWAYS_TRUE,
     FILTER, ["testBadgeIsVisibleOnlyForANonBlankSourceName"]),
    ("M1134", "有来源名也不画（可见性恒假）", POLICY, VISIBLE_NEEDLE, ALWAYS_FALSE,
     FILTER, ["testBadgeIsVisibleOnlyForANonBlankSourceName"]),
    ("M1135", "空 bundle ID 也去查（不归一）", POLICY, BUNDLE_NEEDLE, BUNDLE_MUTANT,
     FILTER, ["testResolvedIconTrimsTheBundleIDAndSkipsBlankOnes"]),
    ("M1136", "bundle ID 不裁两端空白", POLICY, TRIM_NEEDLE, TRIM_MUTANT,
     FILTER, ["testResolvedIconTrimsTheBundleIDAndSkipsBlankOnes"]),
    ("M1137", "解析不到时退回问号而不是 app 符号", POLICY, FALLBACK_NEEDLE, FALLBACK_MUTANT,
     FILTER, ["testFallbackSymbolIsAnAppGlyph"]),
    ("M1141", "窄宽阈值归零（12 上窄窗也画图标）", POLICY, WIDTH_NEEDLE, WIDTH_MUTANT,
     FILTER, ["testNarrowDetailWidthHidesTheIconBeforeItStealsMetaText"]),
    ("M1142", "窄宽判反（宽窗不画、窄窗画）", POLICY, COMPARE_NEEDLE, COMPARE_MUTANT,
     FILTER, ["testNarrowDetailWidthHidesTheIconBeforeItStealsMetaText"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r425-mut-shots-")
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = shots
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    finally:
        shutil.rmtree(shots, ignore_errors=True)
    out = proc.stdout + proc.stderr
    verdicts = [line for line in out.splitlines()
                if "Test Case" in line and ("passed" in line or " failed" in line)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in line for line in verdicts):
        return "BROKEN-MUTATION", out, []
    failed = [line.split("]")[0].replace("Test Case '-[", "")
              for line in verdicts if " failed" in line]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def main():
    original = read(POLICY)
    for mid, _desc, path, old, _new, _filter, _needles in MUTATIONS:
        count = read(path).count(old)
        if count != 1:
            raise SystemExit("预检中止：%s 的针在 %s 命中 %d 次" % (mid, path, count))
    code, out, _ = run(FILTER)
    if code != "ESCAPED":
        raise SystemExit("预检失败 %s %s\n%s" % (FILTER, code, out[-2000:]))
    print("预检 OK " + FILTER)

    caught = wrong = 0
    for mid, desc, path, old, new, filter_name, needles in MUTATIONS:
        stamp = time.time() + 2
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original.replace(old, new, 1))
        os.utime(path, (stamp, stamp))
        landed = old not in read(path) and (new in read(path) or new == "")
        try:
            code, out, failed = run(filter_name)
        finally:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(original)
            os.utime(path, (stamp + 1, stamp + 1))
        hit = all(needle in out for needle in needles)
        right = code == "CAUGHT" and hit and landed
        caught += 1 if code == "CAUGHT" else 0
        wrong += 0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"
              % (mid, desc, code, right, hit, failed, read(path) == original))

    clean = read(POLICY) == original
    code, _, _ = run(FILTER)
    print("还原后复跑：%s=%s" % (FILTER, code))
    print("R425_SOURCE_APP_BADGE_POLICY_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
