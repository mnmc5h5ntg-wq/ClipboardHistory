#!/usr/bin/env python3
"""CI 帧捕获步骤的闸门：**红必须有名字**（R36 / BACKLOG 49 / U-59）。

来历：`.github/workflows/ci.yml` 里 "Offscreen frame capture" 那一步是 report-only
（`continue-on-error: true` + 命令尾巴 `|| true`），理由是"无头 runner 上在屏/离屏窗口的稳定性
未证明，拿它当硬门只会让人学会无视红色"。这个理由成立，但代价是：**runner 上现在正好有 4 条红
被吞着**（一条正对照帧读 0% 墨、两条"捕获失效"、一条"材质黑带消失了"，逐字见
`scripts/tests/test_ci_capture_gate.py` 的 `RUNNER_LOG`），而"红了没人看"与"没有红"在报表里长得一模一样。

所以这一步改成两件事分开：
1. 测试自己把"这台机器判不了的那一条"登记成 `*_NOT_RUN`（带读数、带原因），不再红；
2. 这一步只问一句：**还有没有没被登记的红色？** 有就红。

"红"在这里有两个来源，两个都要认，因为它们的形状不同：
- `error: -[套件.类 方法] :` —— 断言失败会打这一行，里面自带用例名（这就是"有名字"）；
- `Test Case '-[套件.类 方法]' failed` —— 崩溃 / 超时那类**没有**断言行，只有结论行。
  只盯前一种的话，"用例整个没跑完"会伪装成"一条红都没有"。

用法：`python3 scripts/ci_capture_gate.py <swift-test 日志文件>`

退出码：
  0  跑到了用例，一条红都没有（`*_NOT_RUN` 不算红，但会原样打出来），且判出绿的用例数 >= `--min-passed`
  1  有红 / 根本没跑到任何用例 / 绿的数量低于门 / 日志读不到 —— **"没跑"与"全是 skip"都不是通过**
"""
import argparse
import re
import sys

# 真实行（runner 上带 `2026-10-13T21:58:18.9379670Z ` 时间戳前缀，本机没有，所以不锚行首）：
#   .../UICaptureHarness.swift:321: error: -[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews] : XCTAssertGreaterThan failed: ...
# 名字一律限定成 ASCII 标识符，有两层原因：
# ① 类名里有点、类与方法之间有空格，用 `\w+` 单段会把"类 方法"整段漏掉
#    —— 本脚本的第一版就栽在这两个正则上（4 条真红解析成 0 条，正对照直接通过，见它的单测）；
# ② Python 的 `\w` 默认含中文，于是**本文件顶部注释里那句"`error: -[类 方法]`"自己就会被匹配成红** ——
#    夹具与注释都会污染它。被测的日志里只有 Swift 标识符，所以按 ASCII 收紧才是对的尺。
RED = re.compile(r"error: -\[([A-Za-z0-9_.]+) ([A-Za-z0-9_]+)\]")
#   Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews]' failed (22.256 seconds).
CASE_VERDICT = re.compile(r"Test Case '-\[([A-Za-z0-9_. ]+)\]' (passed|failed|skipped)")
# 已登记的"这台机器判不了"：`XCTAssert* NOT_RUN` 那种标记一律由测试自己打，名字必须全大写。
NOT_RUN = re.compile(r"\b([A-Z][A-Z0-9_]*_NOT_RUN)\b(.*)")


def analyse(text: str) -> dict:
    """把一份 swift-test 日志分成三堆：红（两个来源）、已登记的 NOT-RUN、结论统计。"""
    lines = text.splitlines()
    red_lines = [line.strip() for line in lines if RED.search(line)]
    verdicts = CASE_VERDICT.findall(text)
    not_run = [line.strip() for line in lines if NOT_RUN.search(line)]

    named = {match.group(1) + " " + match.group(2) for match in RED.finditer(text)}
    failed_cases = sorted({name.strip() for name, verdict in verdicts if verdict == "failed"})
    # 两个来源并起来才是"有名字的红"：只有结论行而没有断言行（崩溃）也必须进来。
    red_cases = sorted(named | set(failed_cases))

    return {
        "reds": red_lines,
        "red_cases": red_cases,
        "failed_cases": failed_cases,
        "ran_cases": len(verdicts) > 0,
        "not_run": not_run,
        "not_run_markers": sorted({match.group(1) for match in NOT_RUN.finditer(text)}),
        "passed": sum(1 for _, v in verdicts if v == "passed"),
        "skipped": sum(1 for _, v in verdicts if v == "skipped"),
        "skipped_names": sorted({name.strip() for name, v in verdicts if v == "skipped"}),
        # 红了但**连一条断言行都没有** ⇒ 崩溃/超时那一类，日志里只有结论行。
        # 单列出来是因为它的处置完全不同：不是判据被判红，是用例根本没跑到结论。
        "crashed": sorted(set(failed_cases) - named),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ci_capture_gate.py",
        description="判一份 swift-test 日志里有没有**未登记**的红色：红=1，全绿或只有 *_NOT_RUN=0，"
                    "一条用例都没跑到=1（没跑不算通过）。",
    )
    parser.add_argument("log", help="swift test 的日志文件（`tee` 出来的那一份）")
    parser.add_argument("--min-passed", type=int, default=0, metavar="N",
                        help="至少要有 N 个用例**判出绿**，否则红。挡住的是另一种"
                             "'红了没人看'：全部改成 skip，步骤一样是 0 条红")
    parser.add_argument("--quiet", action="store_true",
                        help="只打结论行，不逐条列 NOT_RUN 与红的原文")
    args = parser.parse_args(argv)

    try:
        with open(args.log, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError as error:
        print(f"CAPTURE_GATE_RESULT=fail 日志读不到：{error}", flush=True)
        return 1

    result = analyse(text)
    print(f"CAPTURE_GATE_CASES passed={result['passed']} skipped={result['skipped']} "
          f"failed={len(result['failed_cases'])} 有名字的红={len(result['red_cases'])} "
          f"NOT_RUN={len(result['not_run'])}", flush=True)
    if result["skipped_names"]:
        print("  被 skip 的用例（skip 不是通过，它只是**不红**）：" + " ".join(
            name.split(" ")[-1] for name in result["skipped_names"]), flush=True)
    if not args.quiet and result["not_run_markers"]:
        print("  已登记的标记：" + " ".join(result["not_run_markers"]), flush=True)
        for line in result["not_run"]:
            print("    " + line[:200], flush=True)

    if not result["ran_cases"]:
        # 这一步"跑了但一个用例都没下结论"是最坏的一种：报表上它是绿的。
        print("CAPTURE_GATE_RESULT=fail 日志里没有任何 `Test Case ... passed|failed|skipped` 行"
              " ⇒ 这一步没跑到用例（挂死、崩溃、或 filter 打错）。**没跑不算通过**", flush=True)
        return 1
    if result["red_cases"]:
        print(f"CAPTURE_GATE_RESULT=fail 有 {len(result['red_cases'])} 个用例红了（红有名字，这正是这一步存在的理由）：",
              flush=True)
        for name in result["red_cases"]:
            print("  " + name, flush=True)
        if result["crashed"]:
            print("  其中只有结论行、没有断言行（崩溃/超时那一类，处置是查为什么没跑完，不是查判据）："
                  + " ".join(result["crashed"]), flush=True)
        if not args.quiet:
            for line in result["reds"]:
                print("    " + line[:260], flush=True)
        print("处置只有两种：①它确实是产品/判据的缺陷 ⇒ 修；"
              "②它是这台机器判不了的那一条 ⇒ 让测试把它登记成 *_NOT_RUN（带读数与原因），"
              "不要把它留成一条被吞掉的红。", flush=True)
        return 1
    # skip 的口径和"红"不一样，但一样能骗人：把 8 条像素判据全改成 `throw XCTSkip` 之后，
    # 这一步**一条红都没有**，报表和"全都验过了"长得一模一样 —— 这正是 U-59 抱怨的那个形状，
    # 只不过换了个方向。所以除了"红=0"，还要求"判出绿的用例数"不低于门。
    if result["passed"] < args.min_passed:
        print(f"CAPTURE_GATE_RESULT=fail 判出绿的用例只有 {result['passed']} 个，低于这道步的门 "
              f"{args.min_passed} ⇒ 有一批像素判据退回成了 skip（skip 不是通过，它只是不红）。"
              f"被 skip 的：{(' '.join(result['skipped_names']) or '无')}", flush=True)
        return 1
    print("CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
