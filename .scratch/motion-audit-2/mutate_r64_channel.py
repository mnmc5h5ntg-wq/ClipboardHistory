#!/usr/bin/env python3
"""R64 的变异对照：捕获卷的第二条读数通道（BACKLOG 96）到底有没有牙。

被判的对象是 `UICaptureTests.testCaptureReadingsUseTheFileChannel` 这一条用例里的四格：
① 扫描 `UICaptureHarness.swift` 里游离的 stdout 调用（真产品级规则：这个文件 `print` 出现次数 = 0）；
② 正对照三种写法必须被抓到，且 `emit` 不许被抓（这一格验的是**尺子本身**）；
③ 注释剥离器 `codeOnly` 必须真的在剥（否则 ① 会把守卫自己的注释判成违规，
   而下一个人为了变绿会去删注释 —— R55 的 M276 就是这个形状）；
④ uuid marker 必须落进文件、第二条必须在第一条之后、行数 >= 2（这一格验的是通道）。

每一刀只动一个地方，动完必须**红在指定的那一格**；红了别处或没红，都记下来。

两个"电池自己骗人"的坑是本轮量出来的，脚本里专门做了处理：
- **必须先删掉上一遍的读数文件**。`/tmp/capture-readings/capture-readings.log` 会跨进程留着，
  于是"落盘逻辑坏了"那一刀可以靠**读到昨天那一行**伪装成绿（M340 第一版就这么逃过）。
  marker 本身带 uuid，所以坏的时候读旧文件救不了它 —— 但 M340 坏的是"第一次整份重写"，
  旧文件在 ⇒ `FileHandle(forWritingTo:)` 照样成功、marker 照样落进去，那一刀就真的抓不到了。
- **`/proc` 在 mac 上不存在**，上一版的残留锁判定 `os.path.isdir("/tmp/…")` 永远为假，
  锁一旦留下就再也进不去。改成按 pid 探活。

用法：`python3 .scratch/motion-audit-2/mutate_r64_channel.py`
"""
import os
import re
import subprocess
import sys
import time

REPO = "/Users/wangziyi/Codex_Project0"
HARNESS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
READINGS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/CaptureReadings.swift"
CASE = "testCaptureReadingsUseTheFileChannel"
LOCK = "/tmp/r64_mutate.lock"
# 通道坏的两处判据，红在这一格才算抓到
READINGS_FILE = "/tmp/capture-readings/capture-readings.log"

# (编号, 说明, 文件, 原文, 变异后)
MUTATIONS = [
    ("M337", "把一处读数从 emit 改回游离的 stdout 调用 ⇒ ① 必须扫到它",
     HARNESS,
     'emit("CAPTURE_CAPABILITY settings族整体空白=',
     'print("CAPTURE_CAPABILITY settings族整体空白='),

    ("M338", "把扫描用的串改坏（多一个空格）⇒ 必须由**正对照那一格**判红，"
             "而不是安静地『零条游离』。这一刀验的是 ② 不再拿 needle 拼对照",
     HARNESS,
     'let printCall = "pr" + "int("',
     'let printCall = "pr" + "int ("'),

    ("M339", "把 codeOnly 的行注释剥离改坏 ⇒ ① 会读到守卫自己注释里的那串字符 ⇒ 必须红。"
             "这一刀证明『剥注释』是**载荷**，不是装饰",
     HARNESS,
     '            if let range = trimmed.range(of: "//") {',
     '            if let range = trimmed.range(of: "//NOT-A-COMMENT-MARKER-R64") {'),

    ("M340", "通道只 print、不落盘 ⇒ ④ marker 那一格必须红（这就是 BACKLOG 96 没修的状态）",
     READINGS,
     "        print(line)\n        let payload",
     "        print(line)\n        return\n        let payload"),

    ("M341", "去掉『第一次整份重写』⇒ 第一次写变成对**已存在**的文件 append。"
             "读数文件已先删掉，所以这一刀必须红在 ④（旧版本里它逃过，因为旧文件还在）",
     READINGS,
     "            if !opened {\n                opened = true\n                try payload.write(to: url)\n                return\n            }",
     "            if !opened {\n                opened = true\n            }"),

    ("M342", "把 readingsURL 换成一个必然写不进去的目录 ⇒ 通道坏时判据必须**红**而不是崩，"
             "也不许悄悄变成绿（这一格测 do/catch 的处置）",
     READINGS,
     "        let url = URL(fileURLWithPath: base, isDirectory: true)",
     '        let url = URL(fileURLWithPath: "/r64-nope-root/cannot-create-here", isDirectory: true)'),
]


def acquire_lock():
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        holder = ""
        try:
            holder = open(LOCK).read().strip()
        except OSError:
            pass
        alive = False
        if holder.isdigit():
            try:
                os.kill(int(holder), 0)
                alive = True
            except ProcessLookupError:
                alive = False
            except OSError:
                alive = True
        if alive:
            print(f"DRIFT-LOCK {LOCK} 正被 pid {holder} 占用 ⇒ 退出，不共享读数")
            sys.exit(2)
        # 残留锁：上一次自己被 Ctrl-C 打断留下的。清掉，但要说出来。
        print(f"   （清掉一个残留锁：里面写的 pid {holder or '?'} 已经不在了）")
        try:
            os.unlink(LOCK)
        except OSError:
            pass
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def clear_channel():
    """每一遍都从『文件不存在』开始，否则上一遍的读数会冒充这一遍。"""
    removed = []
    for path in (READINGS_FILE,
                  os.environ.get("CLIPBOARD_HISTORY_UI_SHOTS", "") + "/capture-readings.log"):
        if path and os.path.exists(path):
            os.unlink(path)
            removed.append(path)
    return removed


def run_case():
    """返回 ('green'|'red'|'absent', 全文)。absent = 这一条根本没跑（编译失败/崩了/filter 打错）。"""
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(
        ["swift", "test", "--filter", f"UICaptureTests/{CASE}"],
        cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
        capture_output=True, text=True, timeout=2400,
    )
    text = proc.stdout + proc.stderr
    failed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(CASE), text)
    passed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(CASE), text)
    verdict = "red" if failed else ("green" if passed else "absent")
    if verdict != "red":
        # `swift test` 的 stdout 会按条丢（这正是本轮修的东西），
        # 所以"没看到结论行"不能直接当成"没跑"—— 用退出码兜一层。
        if proc.returncode != 0 and not passed:
            verdict = "red" if "error:" not in text else "absent"
    return verdict, text


def failing_cells(text):
    """把断言行原文捞出来，好知道这一刀红在**哪一格**。"""
    cells = []
    for line in text.splitlines():
        if "error: -[" in line and CASE in line:
            cells.append(line.split(" : ", 1)[-1][:120])
    return cells


def main():
    acquire_lock()
    results = []
    try:
        originals = {p: read(p) for p in {HARNESS, READINGS}}
        print("=== 基线（未变异）必须先绿 ===")
        print("   清掉的旧读数文件：" + " ".join(clear_channel()))
        verdict, text = run_case()
        print(f"   baseline = {verdict}")
        if verdict != "green":
            for c in failing_cells(text):
                print("     " + c)
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不能算抓到的证据，整批作废")
            return 1
        for tag, note, path, needle, replacement in MUTATIONS:
            print(f"\n{tag} {note}")
            source = read(path)
            if needle not in source:
                print(f"   DRIFT-NOT-APPLIED 变异原文在 {os.path.basename(path)} 里找不到 ⇒ 这条没跑")
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            # 自证落地：**原文不在了**且**变异文在场**才算落地。
            # 上一版这里写反了，于是每一刀都打一条看着像警告、其实是成功确认的行。
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地 ⇒ 结论作废")
                results.append((tag, "NOT-APPLIED"))
                write(path, originals[path])
                continue
            print(f"   落地确认（{os.path.basename(path)}）")
            print("   清掉的旧读数文件：" + " ".join(clear_channel()))
            try:
                verdict, text = run_case()
                cells = failing_cells(text)
                mark = "CAUGHT" if verdict == "red" else ("ESCAPED" if verdict == "green" else "NOT-RUN")
                print(f"   {mark} verdict={verdict} 红在这一格：{cells[0] if cells else '（没有断言行：崩了？）'}")
                for extra in cells[1:]:
                    print("     还有：" + extra)
                results.append((tag, mark))
            finally:
                write(path, originals[path])
                restored = read(path) == originals[path]
                print("   还原" + ("成功（按内容比对）" if restored else "失败！立刻手工恢复测试文件"))
                if not restored:
                    return 3
            time.sleep(0.2)
        print("\n=== 电池汇总 ===")
        for tag, mark in results:
            print(f"  {tag}: {mark!r}")
        # 汇总自己也要能被证伪：上一版这里比的是 `m != "CAUGHT"`，而 mark 带着一个尾随空格
        # （"CAUGHT "），于是**六刀全抓到、汇总却写『非抓到=6』** —— 报表和逐行结论互相矛盾。
        # 结论行必须由同一份数据算出来，并且把比对的字符串原样打出来（!r），不然这类错看不出来。
        escaped = [t for t, m in results if m.strip() != "CAUGHT"]
        print(f"  CAUGHT={len(results) - len(escaped)} 非抓到={len(escaped)}"
              + (f"（{escaped}）" if escaped else " ⇒ 每一条都红在所指的格上"))
        print("电池结束。")
        return 0
    finally:
        try:
            os.unlink(LOCK)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
