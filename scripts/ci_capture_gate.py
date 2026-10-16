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

用法：`python3 scripts/ci_capture_gate.py <swift-test 日志文件> [--readings capture-readings.log] [--min-passed N]`

R64 / BACKLOG 96 起多了一条通道：`--readings` 指向捕获卷自己写的第二份读数
（`CaptureReadings.emit` 落盘的那一份）。加了它，闸门判的是**两条通道的并集** ——
理由不是"多一份保险"，是本轮量到的事实：`swift test` 的 stdout 会**成块**丢，
丢掉的里面就有**判据自己写的结论**（本机两遍：488 行读数里 stdout 少了 324 行与 238 行，
少的都是**连续大块**、切点落在行中间；五条 marker 两遍全丢，而用例的 `passed` 结论行一条没少）。
只读 stdout 时，"今天判了什么"可以整块消失而作业仍然是绿的。

退出码：
  0  跑到了用例，一条红都没有（`*_NOT_RUN` 不算红，但会原样打出来），且判出绿的用例数 >= `--min-passed`
  1  有红 / 根本没跑到任何用例 / 绿的数量低于门 / 日志读不到 /（给了 `--readings` 而）第二条通道缺文件或空
     —— **"没跑"、"全是 skip"、"只剩一条通道"都不是通过**
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


def read_log(path):
    """读一份日志，返回 (文本, 错误)。错误为 None 表示读到了。

    单独抽出来是因为**两条通道的读法必须一模一样**：读数文件如果走另一条更"宽容"的路
    （比如读不到就当空串继续判绿），那条通道坏了的时候报表上看不出任何区别。
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read(), None
    except OSError as error:
        return "", str(error)


def union_lines(stdout_text, readings_text):
    """把第二条通道里**stdout 没有的**那些行挑出来（按整行精确比对，且文件内部也去重）。

    为什么整行精确比对而不是"按 marker 名去重"：一条读数的**读数部分**才是要看的，
    同一句里数字变了就是另一条结论（本机实测：stdout 丢了 `QUICKPICK_FIXTURE_ROWS` 那一行，
    文件里留着 `all=5 typed(访达)=2 empty(zzz 不存在)=0`；拿 marker 名去重的话，
    只要 stdout 里出现过**任何**同名行就会把它当成"已经有了"，那条读数就又没了）。
    """
    seen = set(stdout_text.splitlines())
    recovered = []
    for line in readings_text.splitlines():
        if not line.strip() or line in seen:
            continue
        seen.add(line)
        recovered.append(line)
    return recovered


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ci_capture_gate.py",
        description="判一份 swift-test 日志里有没有**未登记**的红色：红=1，全绿或只有 *_NOT_RUN=0，"
                    "一条用例都没跑到=1（没跑不算通过）。",
    )
    parser.add_argument("log", help="swift test 的日志文件（`tee` 出来的那一份）")
    parser.add_argument("--readings", metavar="PATH",
                        help="捕获卷的第二条读数通道（`capture-readings.log`）。给了这个参数就等于宣布"
                             "**这次必须有第二条通道**：文件读不到或一行读数都没有 ⇒ 红（R64 / BACKLOG 96）。"
                             "理由：stdout 会**成块**丢（本机两遍各丢 324/488 与 238/488 行读数），"
                             "只读它的闸门等于把结论交给一次骰子。")
    parser.add_argument("--min-passed", type=int, default=0, metavar="N",
                        help="至少要有 N 个用例**判出绿**，否则红。挡住的是另一种"
                             "'红了没人看'：全部改成 skip，步骤一样是 0 条红")
    parser.add_argument("--quiet", action="store_true",
                        help="只打结论行，不逐条列 NOT_RUN 与红的原文")
    args = parser.parse_args(argv)

    text, error = read_log(args.log)
    if error:
        print(f"CAPTURE_GATE_RESULT=fail 日志读不到：{error}", flush=True)
        return 1
    log_lines = len(text.splitlines())
    log_bytes = len(text.encode("utf-8"))

    # 第二条读数通道（R64 / BACKLOG 96）：**并集**，不是替换。
    # 只读 stdout 的闸门会把"今天判了什么"交给一次骰子 —— R63 本机十遍里同一个类的三条读数
    # 各自到没到的计数是 `1/0/1`、`0/0/0`、`2/1/1`，runner 上也丢了 `CAPTURE_PROBE quickpick`
    # 与 `QUICKPICK_FIXTURE_ROWS` 两条，而那两条都是判据自己写的结论。
    # 只并"stdout 没有的行"，是为了让这份日志**同时**是"当时打出来的"和"当时想说的"。
    readings_lines = []
    readings_error = None
    readings_count = 0
    readings_text = ""
    if args.readings:
        readings_text, readings_error = read_log(args.readings)
        if readings_error is None:
            readings_count = sum(1 for line in readings_text.splitlines() if line.strip())
            readings_lines = union_lines(text, readings_text)
    if readings_lines:
        text = text + "\n" + "\n".join(readings_lines)

    result = analyse(text)
    # 结论行必须打在**任何能力闸门之前**（R53 的 BACKLOG 75 就是这一格）：
    # 通道坏了也要先让人看见"这次判了多少"，不能一红就把读数一起吞掉。
    if args.readings:
        state = "缺文件" if readings_error else ("空" if readings_count == 0 else f"{readings_count} 行")
        print(f"CAPTURE_GATE_CHANNELS stdout=1 readings={state} "
              f"补回={len(readings_lines)} 行（stdout 没有的读数）", flush=True)
        # R92：把**这一格读到了多大的东西**印出来。理由不是美观：这两次 run 里
        # 那句"这一步没跑到用例"是假的，而要看穿它只能去翻作业日志里另一步的 `Executed 47` ——
        # 一个闸门说得出"我读到的日志只有 27 字节"，它的红就自己带上了一半诊断。
        print(f"CAPTURE_GATE_INPUT 日志通道={log_lines} 行/{log_bytes} 字节 @ {args.log}"
              f"（读数通道另计 {len(readings_lines)} 行）", flush=True)
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
        #
        # R92 / BACKLOG 128：**但"没结论行"有三种完全不同的成因，以前这里只说其中一种**，
        # 而那一种在这两次 run 里都是错的。现场（run 38838819089 / 38846896495）：
        # 这句话打印的同时，同一次 run 的捕获那一步自己打的是
        # `Executed 47 tests, with 9 tests skipped and 0 failures`、`captured frames: 124` ——
        # 真的跑完了。成因是 `scripts/tests/test_ci_report_selftest.py` 的夹具把
        # `cp FAKE_LOG /tmp/frames.log` 写进了作业共享的 /tmp，把这里要读的日志覆盖了
        # （`started=probeA` 那个"用例名"就是夹具里的名字）。三种成因的处置不一样，
        # 所以说"没跑到用例"之前必须先看看第二条通道怎么讲：
        #   ① 读数通道里有**这一份文件自己的**同源证人（`CAPTURE_READINGS_SELFTEST … @ <同一路径>`）
        #      ⇒ 这一步确实跑到过用例，是日志通道整块丢/被覆盖 —— 处置是查通道，不是查产品；
        #   ② 读数通道有行，但没有同源证人 ⇒ 那份读数可能来自别的步骤/别的一次运行，
        #      不能拿它证明"跑到过"，也不能拿它证明"没跑到" —— 只能说不分可信；
        #   ③ 读数通道也空/缺文件 ⇒ 才是原来那句"这一步没跑到用例"。
        # 三支**全都保持红**：这一格的规矩是"读不到结论就不许当通过"，本轮动的只是**成因**，
        # 不是标准（软化警报是另一类错，见 U-101 那一族）。
        same_source = args.readings and any(
            line.startswith("CAPTURE_READINGS_SELFTEST") and args.readings in line
            for line in readings_text.splitlines())
        if same_source:
            print(f"CAPTURE_GATE_RESULT=fail CAPTURE_LOG_CHANNEL_LOST_CONCLUSIONS=1 "
                  f"日志通道里没有任何 `Test Case ... passed|failed|skipped` 行，"
                  f"而读数通道有 {readings_count} 行、且里面有指认这份文件自己的同源证人"
                  f"（`CAPTURE_READINGS_SELFTEST … @ {args.readings}`）"
                  f" ⇒ 这一步**跑到过**用例：坏的是日志通道（整块丢或被别的步骤覆盖），"
                  f"不是产品。**仍然红**：结论读不到就不算通过。"
                  f"先查有没有第二个写 `/tmp/frames.log` 的人，再查 `swift test` 的缓冲", flush=True)
        elif readings_count > 0:
            print(f"CAPTURE_GATE_RESULT=fail CAPTURE_READINGS_FOREIGN_SOURCE=1 "
                  f"日志通道没有结论行，读数通道有 {readings_count} 行却**没有**指向 "
                  f"`{args.readings}` 的同源证人 ⇒ 那 {readings_count} 行可能是别的步骤/别一次运行留下的，"
                  f"既不能证明这一步跑到过，也不能证明它没跑到。**没读到结论就不算通过**", flush=True)
        else:
            print("CAPTURE_GATE_RESULT=fail 日志里没有任何 `Test Case ... passed|failed|skipped` 行"
                  "，读数通道也是空的 ⇒ 这一步没跑到用例（挂死、崩溃、或 filter 打错）。**没跑不算通过**",
                  flush=True)
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
        if args.readings and readings_lines:
            only_file = [line for line in result["reds"] if line in {l.strip() for l in readings_lines}]
            if only_file:
                print(f"  其中 {len(only_file)} 条断言行**只在文件通道里** —— stdout 把它们丢了。"
                      f"没有并集这一步，这次的红会伪装成绿（BACKLOG 96 要挡的就是这一种）", flush=True)
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
    # 第二条通道单独算一条红，而且要放在**所有别的判据之后**：
    # 通道坏了时，前面那些结论仍然是这次真判出来的，先报最有处置价值的那一条。
    # 这一格挡的是"并集这一步自己坏了"：`--readings` 给了路径而文件不存在/为空，
    # 说明 `emit` 一行都没落盘 ⇒ 这次**只剩 stdout**，BACKLOG 96 等于没修。
    if args.readings and (readings_error or readings_count == 0):
        reason = f"读不到：{readings_error}" if readings_error else "存在但一行读数都没有"
        print(f"CAPTURE_GATE_RESULT=fail 第二条读数通道 {args.readings} {reason} "
              f"⇒ 这次只剩 stdout 一条通道，而它**会成块丢**（本机两遍：488 行读数里 stdout 少了 324 行 / 238 行，"
              f"少的都是连续大块、切点落在行中间）。"
              f"上面那些结论可能已经少了若干条，只是看不出来", flush=True)
        return 1
    print("CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
