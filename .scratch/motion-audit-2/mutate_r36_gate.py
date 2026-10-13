#!/usr/bin/env python3
"""R36 变异对照：CI 帧捕获那道**闸门**本身，与它读的三条**机器能力前提**。

闸门这一族的老毛病是"绿着通过"：脚本自己解析不出真实日志（正则打错）、
"一个用例都没跑到"被当成通过、"整批退回 skip"没人管 —— 这三支都要能被打红。
三条能力前提（`CaptureCapability`）都要能在**两台机器的真实读数**上被打红，
否则"0.85 / 0.5"这两个数就是拍脑袋写的。

  M157 `RED` 退回第一版那个漏掉方法名的正则        ⇒ 夹具里 4 条真红解析成 0 条 ⇒ 必须红
  M158 `RED` 放宽到 `[^\]]+`（能吃中文）           ⇒ 夹具的说明文字自己变成假红 ⇒ 必须红
  M159 有红时 `return 1` 改成 `return 0`           ⇒ 闸门变成装饰 ⇒ 必须红
  M160 `ran_cases` 恒真                            ⇒ "没跑"被当成通过 ⇒ 必须红
  M161 摘掉 `--min-passed` 那条门                  ⇒ "整批退回 skip"没人管 ⇒ 必须红
  M162 `captureFamilyBlankFraction` 0.85 → 0.15    ⇒ 本机那一簇被判"整族画不出来" ⇒ 必须红
  M163 同上 → 0.99                                 ⇒ runner 那一簇不再算空白 ⇒ 必须红
  M164 `settings.count >= 2` → `>= 1`              ⇒ 一张帧就能宣告整族空白 ⇒ 必须红（反例臂③）
  M165 `allSatisfy` → `contains(where:)`            ⇒ 兄弟帧画得出来时也放行 ⇒ 必须红（反例臂①）
  M166 `bottomEdgeInkAliveFraction` 0.5 → -1       ⇒ 尺瞎了也算"活着" ⇒ 必须红（反例臂②）
  M167 `bandsSeenHere` 恒真（`!readings.isEmpty`）  ⇒ runner 上"黑带消失了"又要恒红 ⇒ 必须红
  M168 消费者那一侧：`if bandsSeenHere {` → `if true {`
        ⇒ **本机量不出来**（本机确实见过黑带，两条臂在这一台等价）。
           这一支唯一诚实的记法就是"本地不判，由 runner 判"：
           下一次 CI 的日志里 `MATERIAL_BLIND_NOT_RUN` 那行必须还在，
           由 `scripts/ci_capture_gate.py` 把"这一行没出现 + 有用例红"读成红。

模板四件套：剔 SDKROOT、预检不许把 skip 读成绿、还原比自抓的字节、读失败消息确认红得对。
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
ROOT = os.path.join(REPO, "ClipboardHistory")
GATE = os.path.join(REPO, "scripts", "ci_capture_gate.py")
HARNESS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
SHOTS = "/tmp/r36-mut-shots"
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TRUTH_TABLE = "UICaptureTests/testCaptureCapabilityPremisesAreMachineVisible"

# —— Python 那半边：闸门脚本本身 ——
RED_VERSION1 = r'RED = re.compile(r"error: -\[([A-Za-z0-9_.]+) ([A-Za-z0-9_]+)\]")'
RED_LOOSE = r'RED = re.compile(r"error: -\[([^\] ]+) ([^\] ]+)\]")'
RED_NOMETHOD = r'RED = re.compile(r"error: -\[([A-Za-z0-9_.]+)\]")'
RETURN_OK = '''              "不要把它留成一条被吞掉的红。", flush=True)
        return 1'''
RETURN_MUT = '''              "不要把它留成一条被吞掉的红。", flush=True)
        return 0  # MUTANT'''
RAN_CASES = '        "ran_cases": len(verdicts) > 0,'
MIN_PASSED = '    if result["passed"] < args.min_passed:'

# —— Swift 那半边：三条能力前提 ——
FLOOR_BLANK = "        static let captureFamilyBlankFraction: Double = 0.85"
FLOOR_ALIVE = "        static let bottomEdgeInkAliveFraction: Double = 0.5"
COUNT_GUARD = """                settingsFamilyIsBlank: settings.count >= 2
                    && settings.allSatisfy { $0.transparent > InkFloor.captureFamilyBlankFraction },"""
# Swift 没有 `anySatisfy`（第一版把 M165 写成它，结果是一支**编译不过**的假变异，
# 报出来的 DID-NOT-RUN 不是"没被抓到"而是"根本没跑"）⇒ 换成 `contains(where:)`，
# 语义正是"族里有一张空白就算整族空白"，而它是合法 Swift。
BLANK_ONE = """                settingsFamilyIsBlank: settings.count >= 2
                    && settings.contains(where: { $0.transparent > InkFloor.captureFamilyBlankFraction }),"""
BANDS = "                bandsSeenHere: readings.contains { $0.blackBandPt > 0 },"
# 同理：`True` 与 `# MUTANT` 都不是 Swift（`#` 在 Swift 里是宏调用）⇒ 用 `true` 和 `//`。
BANDS_ALWAYS = "                bandsSeenHere: !readings.isEmpty,  // MUTANT"
CONSUMER = "        if bandsSeenHere {"

PY_MUTATIONS = [
    ("M157", "RED 退回第一版（漏方法名）⇒ 4 条真红读成 0 条",
     RED_VERSION1, RED_NOMETHOD),
    ("M158", "RED 放宽到能吃中文 ⇒ 夹具自己的说明文字变成假红",
     RED_VERSION1, RED_LOOSE),
    ("M159", "有红也返回 0（闸门变成装饰）",
     RETURN_OK, RETURN_MUT),
    ("M160", "ran_cases 恒真（没跑也算通过）",
     RAN_CASES, '        "ran_cases": True,  # MUTANT'),
    ("M161", "摘掉 --min-passed 那条门",
     MIN_PASSED, '    if False:  # MUTANT'),
]

SWIFT_MUTATIONS = [
    ("M162", "空白线抬到 0.15：本机那一簇也算「整族画不出来」", FLOOR_BLANK,
     FLOOR_BLANK.replace("0.85", "0.15"), TRUTH_TABLE, "本机 settings 族最低那张只未绘制 20.8%"),
    ("M163", "空白线抬到 0.99：runner 那一簇不再算空白", FLOOR_BLANK,
     FLOOR_BLANK.replace("0.85", "0.99"), TRUTH_TABLE, "runner 上 settings 族 18 张"),
    ("M164", "一张帧就够宣告整族空白", COUNT_GUARD,
     COUNT_GUARD.replace("settings.count >= 2", "settings.count >= 1"),
     TRUTH_TABLE, "只有一张帧时不许宣告整族空白"),
    ("M165", "allSatisfy 换成 contains：兄弟帧画得出来时也放行", COUNT_GUARD,
     BLANK_ONE, TRUTH_TABLE, "族里有画得出来的兄弟帧时"),
    ("M166", "底行墨的活尺线改成 -1：尺瞎了也算活着", FLOOR_ALIVE,
     FLOOR_ALIVE.replace("= 0.5", "= -1"), TRUTH_TABLE, "全帧底行墨 0 ⇒ 尺不活"),
    ("M167", "bandsSeenHere 恒真：拿到没见过黑带的机器上也判「事实变了」", BANDS,
     BANDS_ALWAYS, TRUTH_TABLE, "runner 上 102 帧一处黑带都没有"),
]


def needle_count(text, needle):
    return text.count(needle)


def run_python_suite():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover",
                           "-s", "scripts/tests", "-p", "test_ci_capture_gate.py"],
                          cwd=REPO, capture_output=True, text=True, env=BASE_ENV, timeout=600)
    out = proc.stdout + proc.stderr
    ran = re.search(r"Ran (\d+) tests", out)
    # `Ran 0 tests ... OK` 是最坏的一种绿：它和"全绿"在退出码上一模一样。
    if not ran or int(ran.group(1)) < 11:
        return "DID-NOT-RUN", out, []
    names = re.findall(r"FAIL: (\S+)", out)
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, names


def run_swift(test_filter, expect_needle):
    env = dict(BASE_ENV)
    env["CLIPBOARD_HISTORY_UI_SHOTS"] = SHOTS
    proc = subprocess.run(["swift", "test", "--filter", test_filter],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    lines = out.splitlines()
    if "Test Case" not in out:
        return "DID-NOT-RUN", out, []
    verdicts = [l for l in lines if "Test Case" in l and ("passed" in l or " failed" in l or "skipped" in l)]
    if not [l for l in verdicts if "passed" in l or " failed" in l]:
        return "DID-NOT-RUN", "整条被 skip：" + " | ".join(v[:120] for v in verdicts), []
    failed = [l for l in lines if "Test Case" in l and " failed" in l]
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


def check(expect_needle, out):
    """红要红在对的地方：失败消息里必须出现预期的那句话，否则是"加载报错"那种假红。"""
    return expect_needle in out


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = needle_count(text, old)
    if n != 1:
        raise SystemExit(f"注入中止：{os.path.basename(path)} 里那段话出现 {n} 次，不是 1 次 —— "
                         f"needle 已经和代码脱节，先修电池再谈变异\n  {old[:120]}")
    original = text
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return original


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    now = open(path, encoding="utf-8").read()
    return now == original


def main():
    wanted = set(sys.argv[1:])
    print(f"python={sys.executable}")
    results = []

    # —— 预检：两半都是绿的才能谈变异 ——
    code, out, _ = run_python_suite()
    print("预检 scripts：", code, "（红/绿都必须是真跑出来的）")
    if code != "ESCAPED":
        raise SystemExit("预检失败：闸门脚本的自测在本机不是绿的，先修它\n" + out[-800:])
    code, out, _ = run_swift(TRUTH_TABLE, "")
    print("预检 Swift：", code)
    if code != "ESCAPED":
        raise SystemExit("预检失败：能力前提的真值表在本机不是绿的\n" + out[-800:])

    for mid, desc, old, new in PY_MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(GATE, old, new)
        code, out, names = run_python_suite()
        ok = restore(GATE, original)
        results.append((mid, desc, code, "n/a", "yes" if ok else "NO",
                        ",".join(names[:3]) if names else ""))
        print(f"{mid} {desc} ⇒ {code} 红在 {names[:3]}")
        if code != "CAUGHT":
            print("  这一支没被抓到，看下面的输出")
            print(out[-900:])

    for mid, desc, old, new, filt, needle in SWIFT_MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(HARNESS, old, new)
        code, out, failed = run_swift(filt, needle)
        if code == "DID-NOT-RUN" and "error:" in out:
            # 编译不过的变异**不是逃逸**：它连跑都没跑，报成 ESCAPED/CAUGHT 都是假账。
            code = "BROKEN-MUTATION"
        red_in_right_place = check(needle, out)
        ok = restore(HARNESS, original)
        results.append((mid, desc, code, "yes" if red_in_right_place else "NO",
                        "yes" if ok else "NO", " | ".join(f[:1] for f in failed)))
        print(f"{mid} {desc} ⇒ {code} 红得对={red_in_right_place}")
        if code != "CAUGHT" or not red_in_right_place:
            print(out[-900:])

    # —— 本地判不了的那一支：它必须**绿着通过**，而这是记录，不是成功 ——
    if not wanted or "M168" in wanted:
        original = apply(HARNESS, CONSUMER, "        if true {  // MUTANT M168")
        code, out, failed = run_swift("UICaptureTests/testCaptureKeyViews", "")
        ok = restore(HARNESS, original)
        print(f"M168 消费者侧「黑带见过吗」写死成见过 ⇒ {code}"
              f"（本机确实见过黑带 ⇒ 两条臂在这一台等价，**本地没有判别力**）")
        if code != "ESCAPED":
            print(out[-900:])
        results.append(("M168", "消费者侧 bandsSeenHere 写死", code, "not-judgeable-locally",
                        "yes" if ok else "NO", "runner 判：下一次 CI 的日志里必须有 MATERIAL_BLIND_NOT_RUN"))

    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "CAUGHT"
           and not (r[0] == "M168" and r[2] == "ESCAPED")]
    dirty = [r for r in results if r[4] != "yes"]
    print(f"未被抓到的支数={len(bad)}  还原不干净的支数={len(dirty)}")
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no ⇒ 有支没还原，工作区现在是脏的")
    if bad:
        raise SystemExit(f"MUTATION_UNCAUGHT={len(bad)}")


if __name__ == "__main__":
    main()
