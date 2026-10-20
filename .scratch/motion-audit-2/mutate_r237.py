import io, os, subprocess, sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILTER = "MenuBarSeamReaderIsolationTests|MenuBarSwiftUIDismissRowInkTests"

# R237（BACKLOG 268 / D-222）：runner 的 STEP[4] 编译 error 本机复现不出来 ⇒ 编译器不替我记账，
# 补了一把与 SDK 无关的静态尺（MenuBarSeamReaderIsolationTests）。这一刀问的是**这把尺有没有牙**：
# 把那一行 `@MainActor` 删掉（删除型：替换串不留原 token）⇒ 尺必须自己在「未标注」那一格红，
# 而不是等下一跑 CI 编译失败才知道。
TESTFILE = "Tests/ClipboardHistoryAppTests/MenuBarSwiftUIDismissRowInkTests.swift"
KNIVES = [
    ("M792", TESTFILE,
     '    @MainActor\n    func testSeamInkClearsTheTextFloorInBothStates() throws {',
     '    func testSeamInkClearsTheTextFloorInBothStates() throws {',
     "删掉读缝那一格的 @MainActor（正是 runner 判 error 的那种写法）⇒ 静态尺必须红在「未标注=1」"),
]


def run_tests():
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    p = subprocess.run(["swift", "test", "--filter", FILTER], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=1800)
    return p.stdout + p.stderr


def red_names(out):
    names = []
    for ln in out.splitlines():
        if "' failed" in ln and "Test Case" in ln:
            frag = ln.split("-[")[-1].split("]'")[0]
            names.append(frag.replace(" ", "."))
    return names


def main():
    if os.environ.get("R237_BASELINE") == "1":
        out = run_tests()
        names = red_names(out)
        tail = [ln for ln in out.splitlines() if "SEAM_READER_ISOLATION" in ln]
        print("R237_BASELINE 红名=%s" % (names or "无"))
        for t in tail:
            print("R237_BASELINE 读数=%s" % t[-200:])
        if names:
            print("R237_BASELINE 基线红 ⇒ 不出表（先修基线）")
            return 1
        print("R237_BASELINE 绿")
        return 0

    summary = {"CAUGHT": 0, "ESCAPED": 0, "NOT_RUN": 0}
    restored = []
    for kid, rel, old, new, why in KNIVES:
        path = os.path.join(ROOT, rel)
        with io.open(path, encoding="utf-8") as f:
            src = f.read()
        n = src.count(old)
        if n != 1:
            print("R237_KNIFE %s NOT_RUN needle 命中=%d（要恰好 1 次）%s" % (kid, n, why))
            summary["NOT_RUN"] += 1
            continue
        try:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(src.replace(old, new, 1))
            out = run_tests()
            names = red_names(out)
            if not names:
                if "error:" in out and "Compiling" in out:
                    print("R237_KNIFE %s NOT_RUN 编译失败（不是判据红）" % kid)
                    summary["NOT_RUN"] += 1
                else:
                    print("R237_KNIFE %s ESCAPED %s" % (kid, why))
                    summary["ESCAPED"] += 1
            else:
                print("R237_KNIFE %s CAUGHT EXTRA=%s" % (kid, "|".join(names[:3])))
                summary["CAUGHT"] += 1
        finally:
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(src)
            check = io.open(path, encoding="utf-8").read() == src
            restored.append(check)
            print("R237_KNIFE %s RESTORE=%s" % (kid, "clean" if check else "DIRTY"))

    ok = all(restored) and summary["NOT_RUN"] == 0
    print("R237_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s" % (
        len(KNIVES), summary["CAUGHT"], summary["ESCAPED"], summary["NOT_RUN"],
        "yes" if ok else "no"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
