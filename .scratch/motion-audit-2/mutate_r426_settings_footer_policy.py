#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R426 变异对照：设置侧栏版本行的纯策略（回退、裁空白、采集覆盖、应用名）。"""
import os, subprocess, sys, time, shutil, tempfile

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
POLICY = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/SettingsSidebarFooterPolicy.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
FILTER = "SettingsSidebarFooterTests"

NAME_NEEDLE = "    static let appName = \"时间剪史\"\n"
NAME_MUTANT = "    static let appName = \"时间简史\"\n"
FALLBACK_NEEDLE = "        guard let version = normalized(shortVersion) else { return appName }\n"
FALLBACK_MUTANT = "        guard let version = normalized(shortVersion) else { return \"\" }\n"
TRIM_NEEDLE = "        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)\n"
TRIM_MUTANT = "        let trimmed = text\n"
OVERRIDE_NEEDLE = "        if let override = normalized(override) {\n"
OVERRIDE_MUTANT = "        if false, let override = normalized(override) {\n"

MUTATIONS = [
    ("M1144", "读不到版本时不回退到应用名", POLICY, FALLBACK_NEEDLE, FALLBACK_MUTANT,
     FILTER, ["testVersionTextFallsBackToTheAppNameOnly"]),
    ("M1145", "版本/名字不裁两端空白", POLICY, TRIM_NEEDLE, TRIM_MUTANT,
     FILTER, ["testVersionTextFallsBackToTheAppNameOnly"]),
    ("M1146", "采集覆盖值被忽略", POLICY, OVERRIDE_NEEDLE, OVERRIDE_MUTANT,
     FILTER, ["testResolvedTextPrefersTheCaptureOverride"]),
    ("M1147", "应用名写错字", POLICY, NAME_NEEDLE, NAME_MUTANT,
     FILTER, ["testVersionTextCarriesANonBlankShortVersion"]),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def run(filter_name):
    shots = tempfile.mkdtemp(prefix="r426-mut-shots-")
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
    print("R426_SETTINGS_FOOTER_POLICY_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"
          % (len(MUTATIONS), caught, wrong, "yes" if clean else "NO"))
    return 0 if (caught == len(MUTATIONS) and wrong == 0 and clean and code == "ESCAPED") else 1


if __name__ == "__main__":
    sys.exit(main())
