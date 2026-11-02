# -*- coding: utf-8 -*-
"""生成 R557 的三把变异表（M1443/M1444/M1445）。"""
import io

TEMPLATE = u'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R557 变异表 {MID}：{DESC}"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE = "{FILE}"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
TEST = "{TEST}"
OLD = """{OLD}"""
NEW = """{NEW}"""


def verdict(out):
    u"""只抄被计数物自己打的结论行（`Executed N tests, with M failures`）。"""
    pairs = re.findall(r"Executed (\\d+) test[s]?, with (\\d+) failure[s]?", out)
    if not pairs:
        return "DID-NOT-RUN"
    if sum(int(a) for a, _ in pairs) == 0:
        return "NOT_RUN"
    return "CAUGHT" if sum(int(b) for _, b in pairs) > 0 else "PASSED"


def run():
    env = dict(ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r557-knife-shots"
    proc = subprocess.run(["swift", "test", "--filter", TEST], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=3600)
    out = proc.stdout + proc.stderr
    if "Test Case" not in out:
        return "DID-NOT-RUN", out
    return verdict(out), out


def main():
    path = os.path.join(ROOT, FILE)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")
    code, out = run()
    print(u"预检:", code)
    if code != "PASSED":
        print(out[-800:])
        return 2
    if text.count(OLD) != 1:
        print(u"needle 命中", text.count(OLD))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(OLD, NEW, 1))
    try:
        code, out = run()
    finally:
        open(path, "wb").write(orig)
    print("{MID}:", code)
    for line in out.splitlines():
        if "XCTAssert" in line and "failed" in line:
            print(u"  红:", line.split(" : ")[-1][:170])
    for line in out.splitlines():
        if "CAPTURE_" in line or "PROTECTED_READS" in line:
            print(u"  读数:", line.strip()[:170])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

HARNESS = u"Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
DETAIL = u"Sources/ClipboardHistoryApp/Views/DetailView.swift"
CAP_TEST = u"UICaptureTests/testCaptureOpensNoProtectedFiles"
MEMO_TEST = u"ProtectedFileAccessTests/testHeightEstimateReusesOneSampleAcrossWidthChanges"
LEAK_TEST = u"ProtectedFileAccessTests/testHeightEstimateDoesNotLeakTheSampleToAnotherFile"

specs = [
    (u"mutate_r557_fixture_path_real.py", u"M1443",
     u"把一条夹具路径指向真实存在的文件（帧开始依赖磁盘）", HARNESS,
     u'URL(fileURLWithPath: "/nonexistent")',
     u'URL(fileURLWithPath: "/etc/hosts")', CAP_TEST),
    (u"mutate_r557_memo_never_hits.py", u"M1444",
     u"取样缓存永不命中（回到每次宽度变化都重开文件）", DETAIL,
     u'        if let cached, cached.fileDigest == digest {',
     u'        if let cached, cached.fileDigest == digest, cached.sampleBytes < 0 {',
     MEMO_TEST),
    (u"mutate_r557_memo_ignores_digest.py", u"M1445",
     u"缓存不看文件身份（甲行的取样拿去算乙行的高度）", DETAIL,
     u'        if let cached, cached.fileDigest == digest {',
     u'        if let cached {', LEAK_TEST),
]

for fname, mid, desc, f, old, new, test in specs:
    body = (TEMPLATE.replace(u"{MID}", mid).replace(u"{DESC}", desc)
            .replace(u"{FILE}", f).replace(u"{TEST}", test)
            .replace(u"{OLD}", old).replace(u"{NEW}", new))
    io.open(fname, 'w', encoding='utf-8').write(body)
    compile(body, fname, 'exec')
    print('wrote', fname)
