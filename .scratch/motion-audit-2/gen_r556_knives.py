# -*- coding: utf-8 -*-
"""生成 R556 的三把变异表（M1440/M1441/M1442）。"""
import io

TEMPLATE = u'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R556 变异表 {MID}：{DESC}"""
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
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = "/tmp/r556-knife-shots"
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
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-800:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

T = u"FileThumbnailTests/testAddDoesNotReadTheFileWhileRowDisplayRequestsIt"
STORE = u"Sources/ClipboardHistoryApp/Managers/HistoryStore.swift"
POLICY = u"Sources/ClipboardHistoryApp/Utilities/FileThumbnailPolicy.swift"

specs = [
    (u"mutate_r556_intake_attaches.py", u"M1440",
     u"采集那一步又去补行内缩略图（632 的原形回到 add）", STORE,
     u'        // 现在由行真正显示时按需请求（见 `HistorySidebarView.historyRow` 的 `.task`）。',
     u'        // 现在由行真正显示时按需请求（见 `HistorySidebarView.historyRow` 的 `.task`）。\n'
     u'        requestThumbnail(for: entry.id)'),
    (u"mutate_r556_row_demand_never_reads.py", u"M1441",
     u"按需请求那一格变成永不开文件（正对照：需求路径是空的）", STORE,
     u'        guard FileThumbnailPolicy.shouldAttachThumbnail(for: entry) else { return }',
     u'        guard !FileThumbnailPolicy.shouldAttachThumbnail(for: entry) else { return }'),
    (u"mutate_r556_thumbnail_site_uncounted.py", u"M1442",
     u"缩略图那一格从计数器上摘掉（尺瞎了 ⇒ 零次会变成假绿）", POLICY,
     u'        ProtectedFileAccessLedger.note(.thumbnailSourceOpen, for: url)',
     u'        // 计数器被摘掉：还是开了文件，但没人数得到'),
]

for fname, mid, desc, f, old, new in specs:
    body = (TEMPLATE.replace(u"{MID}", mid).replace(u"{DESC}", desc)
            .replace(u"{FILE}", f).replace(u"{TEST}", T)
            .replace(u"{OLD}", old).replace(u"{NEW}", new))
    io.open(fname, 'w', encoding='utf-8').write(body)
    compile(body, fname, 'exec')
    print('wrote', fname)
