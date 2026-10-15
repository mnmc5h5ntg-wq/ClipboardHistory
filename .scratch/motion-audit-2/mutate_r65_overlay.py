#!/usr/bin/env python3
"""R65 的变异对照：浮层行首那一列（BACKLOG 94）与那条共享左轴（BACKLOG 97）到底有没有牙。

被判的五条判据：
  `EntryPresentationTests.testProductWrittenPreviewsCarryNoEmojiGlyphs`   文案里没有 emoji
  `EntryPresentationTests.testTheEmojiRulerActuallyCatchesAPageGlyph`      那把尺的正对照
  `EntryPresentationTests.testQuickPickRowSymbolsAreDistinctAndActuallyDraw` 四个名字、每个画得出
  `EntryPresentationTests.testOverlaySymbolsAreTheSameNamesTheSidebarUses`  两边同一套名字
  `UICaptureTests.testQuickPickRowsShareOneIconColumnAndOneLabelAxis`      每行有图 + 一条左轴

每一刀只动一个地方，动完必须**红在指定的那一格**。三件"电池自己骗人"的规矩沿用 R64：
① 基线必须先全绿（`--filter` 打错会让整批"红"其实是 NOT-RUN）；
② 每一刀之前删掉上一遍的读数文件（跨进程留着的那份会让"落盘坏了"这一类逃掉）；
③ 落地自证要**同时**要求"原文不在了"和"变异文在场"，汇总比对用 `.strip()`。

用法：`python3 .scratch/motion-audit-2/mutate_r65_overlay.py`
"""
import os
import re
import subprocess
import sys
import time

REPO = "/Users/wangziyi/Codex_Project0"
PRES = "ClipboardHistory/Sources/ClipboardHistoryApp/Models/EntryPresentation.swift"
PICK = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
SIDE = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift"
TESTS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/EntryPresentationTests.swift"
HARNESS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"

E_NO_EMOJI = "testProductWrittenPreviewsCarryNoEmojiGlyphs"
E_RULER = "testTheEmojiRulerActuallyCatchesAPageGlyph"
E_SYMBOLS = "testQuickPickRowSymbolsAreDistinctAndActuallyDraw"
E_SIDEBAR = "testOverlaySymbolsAreTheSameNamesTheSidebarUses"
C_AXIS = "testQuickPickRowsShareOneIconColumnAndOneLabelAxis"

# (编号, 说明, 文件, 过滤用的类/用例, 原文, 变异后)
MUTATIONS = [
    ("M343", "把 📄 塞回文件那一句预览 ⇒ 必须红在『文案里没有 emoji』那一格（这就是改之前的产品）",
     PRES, E_NO_EMOJI,
     '            return url.lastPathComponent\n        case .files(let urls):',
     '            return "\\u{1F4C4} " + url.lastPathComponent\n        case .files(let urls):'),

    ("M344", "把 emoji 那把尺改坏（永远返回 false）⇒ 必须由**正对照那一格**判红，"
             "而不是安静地『四句都干净』",
     TESTS, E_RULER,
     "        text.unicodeScalars.contains { $0.properties.isEmojiPresentation }",
     "        _ = text\n        return false"),

    ("M345", "把一个符号名改错一个字母 ⇒ 必须红在『每个名字都画得出东西』那一格"
             "（NSImage 对不存在的名字返回 nil，而 NSImageView 静默）",
     PICK, E_SYMBOLS,
     '        case .file: return "doc"',
     '        case .file: return "doc.textt"'),

    ("M346", "让文本行与文件行共用同一个符号名 ⇒ 必须红在『四个名字互不相同』那一格"
             "（那一列不携带信息，画了等于没画）",
     PICK, E_SYMBOLS,
     '        case .text: return "doc.text"',
     '        case .text: return "doc"'),

    ("M347", "不再给行设置图 ⇒ 必须红在浮层那一格的『每行都有图』上（列在，但空的）",
     PICK, C_AXIS,
     "        cell.imageView?.image = Self.rowSymbol(for: entry.content)",
     "        _ = entry\n        // cell.imageView?.image = Self.rowSymbol(for: entry.content)"),

    ("M348", "把标签的左锚点从『图标右边』改回『cell 左边』⇒ 必须红在『标签排在图标右边』那一格"
             "（这就是 emoji 时代的布局：文字从列首起，图标压住文字）",
     PICK, C_AXIS,
     "                text.leadingAnchor.constraint(equalTo: symbol.trailingAnchor, constant: 6),",
     "                text.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 6),"),

    ("M349", "改侧栏的符号名而不动浮层 ⇒ 必须红在『两边同一套名字』那一格（跨文件一致性守卫）",
     SIDE, E_SIDEBAR,
     'ThumbnailSymbol(systemName: "doc.on.doc")',
     'ThumbnailSymbol(systemName: "plus.square.on.square")'),
]


def acquire_lock():
    path = "/tmp/r65_mutate.lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        holder = ""
        try:
            holder = open(path).read().strip()
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
            print(f"DRIFT-LOCK {path} 正被 pid {holder} 占用 ⇒ 退出，不共享读数")
            sys.exit(2)
        print(f"   （清掉一个残留锁：里面写的 pid {holder or '?'} 已经不在了）")
        try:
            os.unlink(path)
        except OSError:
            pass
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return path


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def clear_channel():
    removed = []
    for path in ("/tmp/capture-readings/capture-readings.log",):
        if os.path.exists(path):
            os.unlink(path)
            removed.append(path)
    return removed


def run_case(case):
    """跑一条用例，返回 ('green'|'red'|'absent', 全文)。"""
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    cls = "EntryPresentationTests" if case.startswith("testProduct") or case.startswith("testThe") \
        or case.startswith("testQuickPickRowSymbols") or case.startswith("testOverlaySymbols") \
        else "UICaptureTests"
    proc = subprocess.run(
        ["swift", "test", "--filter", f"{cls}/{case}"],
        cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
        capture_output=True, text=True, timeout=2400,
    )
    text = proc.stdout + proc.stderr
    failed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(case), text)
    passed = re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(case), text)
    verdict = "red" if failed else ("green" if passed else "absent")
    if verdict == "absent" and proc.returncode != 0 and "error:" not in text:
        verdict = "red"
    return verdict, text


def failing_cells(text, case):
    return [line.split(" : ", 1)[-1][:130] for line in text.splitlines()
            if "error: -[" in line and case in line]


def main():
    lock = acquire_lock()
    results = []
    try:
        touched = sorted({path for _, _, path, _, _, _ in MUTATIONS})
        originals = {path: read(path) for path in touched}
        print("=== 基线（未变异）：五条判据必须先全绿 ===")
        clear_channel()
        baseline_ok = True
        for case in (E_NO_EMOJI, E_RULER, E_SYMBOLS, E_SIDEBAR, C_AXIS):
            verdict, text = run_case(case)
            print(f"   {case[:46]:46s} = {verdict}")
            if verdict != "green":
                baseline_ok = False
                for cell in failing_cells(text, case):
                    print("     " + cell)
        if not baseline_ok:
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不能算抓到的证据，整批作废")
            return 1
        for tag, note, path, case, needle, replacement in MUTATIONS:
            print(f"\n{tag} {note}")
            source = read(path)
            if needle not in source:
                print(f"   DRIFT-NOT-APPLIED 变异原文在 {os.path.basename(path)} 里找不到 ⇒ 这条没跑")
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地 ⇒ 结论作废")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            print(f"   落地确认（{os.path.basename(path)}）")
            print("   清掉的旧读数文件：" + (" ".join(clear_channel()) or "（本来就没有）"))
            try:
                verdict, text = run_case(case)
                cells = failing_cells(text, case)
                mark = "CAUGHT" if verdict == "red" else ("ESCAPED" if verdict == "green" else "NOT-RUN")
                print(f"   {mark} verdict={verdict} 期望红在={case[:40]}")
                print("     红在这一格：" + (cells[0] if cells else "（没有断言行：崩了或没跑到）"))
                for extra in cells[1:]:
                    print("     还有：" + extra)
                results.append((tag, mark))
            finally:
                write(path, originals[path])
                restored = read(path) == originals[path]
                print("   还原" + ("成功（按内容比对）" if restored else "失败！立刻手工恢复"))
                if not restored:
                    return 3
            time.sleep(0.2)
        print("\n=== 电池汇总 ===")
        for tag, mark in results:
            print(f"  {tag}: {mark!r}")
        escaped = [t for t, m in results if m.strip() != "CAUGHT"]
        print(f"  CAUGHT={len(results) - len(escaped)} 非抓到={len(escaped)}"
              + (f"（{escaped}）" if escaped else " ⇒ 每一条都红在所指的格上"))
        return 0
    finally:
        try:
            os.unlink(lock)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
