#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R56 变异对照：读数的第二条通道（Swift 那一半 + CI 那一半）。

R56 做的事是"让证据不再依赖一条已知会整次消失的通道"。这种"加一条保险"的改动
最容易被做成**装饰**：文件写了但没人读、读了但每次都覆盖、扫描列表空了还自称在扫。
所以九支里五支打在 Swift 侧、四支打在 CI 侧 —— 少任何一侧，另一半就能悄悄失效。

  M277 把一行读数退回 `print`            ⇒ 守卫的源码扫描该红（"有条读数只走 stdout"）。
  M278 `emit` 只 print 不落盘            ⇒ 该红（文件里没有这一遍的 marker）。
       本轮在这格上翻过一次车：第一版判据只比"末尾两格"，于是**上一遍留下的旧文件**
       会让它红在一条写错的理由上（红是对的，理由是假的）。现在先判 marker 在不在。
  M279 每次都整份重写（不追加）          ⇒ 该红（marker 在，但不在末尾两格）。
       这一支是本轮最像"能工作"的坏法：文件在、内容也在，只是**只剩最后一行**。
  M280 读数文件挪到别处（NSTemp）        ⇒ 该红（与胶片不同目录 ⇒ CI 那一步找不到它）。
  M281 扫描列表清空                       ⇒ 该红（正对照那一格）。
       没有正对照，这一支会**绿着通过**：一条"什么都不许出现"的扫描，把判据删掉就是删列表。
  M282 删掉 CI 的并集整段                ⇒ 自检该红。红在"夹具替换没有落地"——
       这是**另一种有效红**（ci.yml 改了写法而自检的锚点还在原地），不是场景红，理由写清楚。
  M283 并集永远不触发（`if false`）      ⇒ 自检该红（两个恢复场景都拿不到结论行）。
       这一支钉的是"第二条通道是摆设"：文件写了，但 CI 从来不用它。
  M284 只 echo 不并回去                   ⇒ 自检该红（同上，红在恢复场景）。
  M285 并集写成"文件覆盖 stdout"          ⇒ 自检该红（半丢那一格的 MOTION_SUMMARY 被扔掉）。
       本轮实现先写成"以文件为准"，加这一支时才发现它会扔掉 stdout 独有的行 ⇒ 改回并集。
       **这一支是本轮最有价值的一支**：它不是测实现，是把一个设计错误在提交前顶了回去。

**知道没被钉住的**：把并集改成"只在缺结论行时才并"。健康路径与整片丢都仍然绿，
只有"半丢且结论行恰好活着"那种形状会退回 REASONLESS 假红 —— 而那种形状今天还没有实测样本。
记在 BACKLOG 79：下一次再看到 `stdout=N 文件=M` 且 N≠M，就该回来补这一格。

用法：`python3 .scratch/motion-audit-2/mutate_r56_readings_channel.py [--measure] [M277 …]`
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
REPO = os.path.join(ROOT, "ClipboardHistory")
TESTS = os.path.join(REPO, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
CAPTURE = os.path.join(REPO, "Tests/ClipboardHistoryAppTests/CaptureReadings.swift")
CI = os.path.join(ROOT, ".github/workflows/ci.yml")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

GUARD = "MotionFilmstripTests.testMotionReadingsUseTheFileChannel"
SELFTEST = ["python3", "-m", "unittest", "scripts.tests.test_ci_report_selftest"]

# CI 里那段并集（锚点按整段取：删掉它 = 通道白建）
CI_BLOCK = (
    "          readings=/tmp/motion-ci/motion-readings.log\n"
    "          if [ -s \"$readings\" ]; then\n"
    "            from_stdout=$(grep -c '^MOTION_' /tmp/motion.log || true)\n"
    "            cat \"$readings\" >> /tmp/motion.log\n"
    "            echo \"MOTION_CHANNEL_UNIONED=1 stdout=$from_stdout "
    "文件=$(wc -l < \"$readings\" | tr -d ' ')\"\n"
    "          else\n"
    "            echo \"MOTION_READINGS_FILE_ABSENT=1 只剩 stdout 这一条通道（文件通道没写出来）\"\n"
    "          fi\n")

NEEDLES_DECL = '        let needles = ["print" + "(\\"MOTION_", "print" + "(String(format: \\"MOTION_"]'

MUTATIONS = [
    ("M277", "把一行读数退回 print", TESTS, "swift",
     '        emit("MOTION_SUMMARY " + rows.map',
     '        print("MOTION_SUMMARY " + rows.map',
     GUARD, ["只走 stdout"]),
    # R374：emit 的实现在 CaptureReadings（本文件那层壳只转发），针跟着搬；两种红都合法（文件在⇒marker 不在；文件不在⇒没写出来）。
    ("M278", "emit 只 print 不落盘", CAPTURE, "swift",
     "    static func emit(_ line: String, to url: URL) {\n        writeStdoutLine(line)\n",
     "    static func emit(_ line: String, to url: URL) {\n        writeStdoutLine(line)\n        return   // MUTANT: 只 stdout，不落盘\n",
     GUARD, ["文件里没有这一遍的 marker", "文件通道没写出来"]),
    # R374 / BACKLOG 367：追加逻辑搬进 `CaptureReadings.appendLocked`（R302/R358），旧针随 `readingsOpened` 一起消失。
    ("M279", "每次都整份重写（不追加）", CAPTURE, "swift",
     "        if !openedURLs.contains(url) {",
     "        if true {   // MUTANT: 每次都整份重写",
     GUARD, ["不在末尾两格"]),
    ("M280", "读数文件挪到别处", TESTS, "swift",
     '        filmsDirectory.appendingPathComponent("motion-readings.log")',
     '        URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)\n'
     '            .appendingPathComponent("motion-readings.log")   // MUTANT',
     GUARD, ["CI 那一步找不到它"]),
    # R374：扫描改成「同一函数喂真源码 + 合成样本」，M281 改成清空那个函数的来源。
    ("M281", "扫描列表清空", TESTS, "swift",
     "            text.components(separatedBy: \"\\n\").filter { line in",
     "            [].filter { line in   // MUTANT: 扫描列表清空",
     GUARD, ["扫描函数在合成样本上抓不到"]),
    ("M282", "删掉 CI 的并集整段", CI, "ci", CI_BLOCK, "", None, ["夹具替换没有落地"]),
    ("M283", "并集永远不触发（文件通道成了摆设）", CI, "ci",
     '          if [ -s "$readings" ]; then',
     "          if false; then   // MUTANT",
     None, ["stdout_lost_but_file_channel_recovers"]),
    ("M284", "只喊用了文件、却不并回去", CI, "ci",
     '            cat "$readings" >> /tmp/motion.log\n',
     '            : "MUTANT 不并回"\n',
     None, ["stdout_lost_but_file_channel_recovers"]),
    ("M285", "并集写成「文件覆盖 stdout」", CI, "ci",
     '            cat "$readings" >> /tmp/motion.log\n',
     "            grep -v '^MOTION_' /tmp/motion.log > /tmp/m.merged.log || true\n"
     '            cat "$readings" >> /tmp/m.merged.log\n'
     "            mv /tmp/m.merged.log /tmp/motion.log\n",
     None, ["partial_stdout_loss_recovers_resolve"]),
]


def run(kind, filter_name):
    if kind == "swift":
        argv, cwd = ["swift", "test", "--filter", filter_name], REPO
    else:
        argv, cwd = SELFTEST, ROOT
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          env=BASE_ENV, timeout=1800)
    out = proc.stdout + proc.stderr
    if kind == "swift":
        verdicts = [l for l in out.splitlines()
                    if "Test Case" in l and ("passed" in l or " failed" in l)]
        if not verdicts:
            return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
        failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
        if "error:" in out and not failed:
            return "BROKEN-MUTATION", out, []
        return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed
    # R374：自检从 1 格长到 5 格之后，写死的 "Ran 1 test" 把整张表卡在 BROKEN-MUTATION（预检就先死）。
    # 判的是「跑起来了没有」，不是「跑了几格」——格数是自检自己的事。
    if not re.search(r"^Ran \d+ tests?", out, re.M):
        return "BROKEN-MUTATION", out, []
    names = [l.split()[0] + "/" + l.split()[1] for l in out.splitlines() if " FAIL" in l]
    return ("ESCAPED" if out.strip().splitlines()[-1].startswith("OK") else "CAUGHT"), out, names


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    for mid, desc, path, kind, old, new, filter_name, needles in MUTATIONS:
        n = open(path, encoding="utf-8").read().count(old)
        if n != 1:
            raise SystemExit("预检中止：%s 的锚点出现 %d 次（要 1 次）\n  %s" % (mid, n, old[:160]))
    for kind, filter_name in (("swift", GUARD), ("ci", None)):
        code, out, _ = run(kind, filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检 %s 失败：%s\n%s" % (kind, code, out[-2500:]))
        print("预检 OK " + (filter_name or "ci_report_selftest"))
    results = []
    for mid, desc, path, kind, old, new, filter_name, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run(kind, filter_name)
        finally:
            ok = restore(path, original)
        hit = [needle for needle in needles if needle in out]
        right = code == "CAUGHT" and len(hit) >= 1
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s 命中=%s 还原干净=%s"
              % (mid, desc, code, right, failed[:3], hit, ok))
        if measure or not right:
            for line in [l for l in out.splitlines() if "error: -[" in l or "FAIL" in l
                         or "AssertionError" in l][:6]:
                print("   MSG| " + line.strip()[:300])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes" or r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对/未抓到=%d  还原不干净=%d" % (len(bad), len(dirty)))
    code, _, _ = run("swift", GUARD)
    print("还原后复跑（Swift 守卫）：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R56_MUTATION_PROBLEM")


main()
