#!/usr/bin/env python3
"""在屏探针的覆盖闸门：**「CI 跑不了这条判据」必须是一条有名有姓的登记，不能是一句「没跑完」**（R62 / BACKLOG 92）。

来历（这一步原来的形状）：`.github/workflows/ci.yml` 的 `On-screen interaction probes`
在 runner 上被步骤自带的 240s 看门狗收掉，读数是
`ui suite exit: 137  executed: 0  已下结论的用例: 0`，脚本于是打一句
「在屏探针在无头 runner 上不可用，记成 R3-D9 的已知边界」然后 `exit 0`。
那句话本身是真的 —— 但它是一张**免检牌**：R61 给侧栏「跟随选中揭示」写的三条行为判据
（臂 1 近处不许跳 / 臂 2 视口外要滚过去 / 臂 5 行号漂了不许动）全部住在这卷里，
所以 **BACKLOG 61 的回归在 CI 上一条判据都没跑**，而 CI 是绿的、那句解释也仍然成立。
「这条判据从此没人跑」与「这条判据今天没跑成」必须分开 —— 后者是事实，前者是盲区。

判什么（每一条都会红，且各自红在不同形状上）：
  BAD_RUNNER_FIELD 清单里 runner 字段不是 can / cannot ⇒ 红（拼错的登记等于没登记）。
  UNLISTED        源码里有一个 `func test…` 而清单里没有 ⇒ 红。
                  新加一条在屏判据必须同时回答「runner 跑得了吗？跑不了的话为什么？」，
                  否则它会静默地变成「只在作者机器上有效」的产品判据。
  STALE           清单里有、源码里已经没有这条用例 ⇒ 红（删掉这行，别留免检牌）。
  REASONLESS      登记为 cannot 却没写 reason ⇒ 红。
                  「跑不了」可以接受，「跑不了且说不清为什么」不行（同 motion 闸门那条）。
  NOT_RUN         登记为 can 而这次日志里没有它的结论行 ⇒ 红（今天本该跑到却没跑到）。
  NOW_RUNS        登记为 cannot 而这次它下结论了 ⇒ 红。
                  这是好消息，但清单必须跟着改，否则它会慢慢攒成一堆免检牌。
  FAILED          日志里有 `error: -[…testXxx] : XCTAssert…` ⇒ 红，并把用例名与断言名打出来
                  （R59 的教训：红必须能被读；`exit 137` 不算汇报）。

**明确不判的**：单条用例的耗时，以及「整卷有没有跑完」——后者由 CI 那一步自己汇报。
本闸门只判**形状**：谁在、谁不在、不在的理由是什么、理由过期了没有。
（同一族的老账：R36 把捕获那一步从 report-only 改成有闸，R46 给动效覆盖率做地板，
这一条是把同一个规矩搬到在屏探针上。）

**只报不判的两行**（R94 / BACKLOG 134 加的，因为登记里那句「排在 X 之后」必须是读数而不是我的推断）：
  PROBE_ORDER   露面了几条、其中几条开了口没闭口、结论是不是执行序的连续前缀。
                「前缀=无从判定」= 一条都没露面，此时这个问题没有对象（不许写成 1 蒙过去）。
  PROBE_QUEUED  一次都没轮到的那些**名字** ⇒ 今天没有资格评价它们，登记只能写「排在空洞之后」。
  这两行**故意不判红**：它们说的是「为什么没结论」，把诊断做成门禁就会在另一种执行序下假红。
  判据不因此变松 —— `NOT_RUN` 仍然按 `runner=can` 逐条红。
  与 `ui_probe_report.py` 的分工（R86 定下、`NonRedundancyTests` 钉住）：
  **名字只在那一支出** —— 它拿 stdout 与探针心跳两条通道互相签字（`UI_PROBE_CHANNELS_AGREE`），
  这一支只有一份日志，抢那个名字就会造出第二颗尺子（R87：两把尺问同一件事时定罪权要按样本数分）。
  所以这里只有计数 `未闭口=1`，没有 `UI_PROBE_HUNG=<谁>`。

用法：
    python3 scripts/probe_coverage_gate.py <ui.log> \\
        --expectations scripts/probe_coverage_expectations.json \\
        --source ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift

退出码：0 一切都在登记之内 / 1 上面任何一条红 / 2 清单、源码或日志读不到（读不到 ≠ 通过）。
"""
import argparse
import os
# R148 / BACKLOG 187 · 心跳与闭合这两行的**正则不在这里复制**：`main()` 里 import `ui_probe_report`，
# 同一条规则两份实现会互相掩盖（R130 记过），改一处忘另一处的后果是两支闸门各说一套。
import json
import re
import sys

CASE_FUNC = re.compile(r"^\s*func (test[A-Za-z0-9_]+)\s*\(\s*\)", re.MULTILINE)
# XCTest 的结论行：`Test Case '-[Mod.Class testSomething]' passed (1.234 seconds).`
# skipped 也算「下过结论」：skip 不是通过，但它证明这条被执行到了（区别于整卷没跑到）。
CONCLUDED = re.compile(r"Test Case '-\[[^\]]*?\b(test[A-Za-z0-9_]+)[^\]]*\]' (passed|failed|skipped)")
# 同一条用例的"露面"行：started 与三种结论都算。R94（BACKLOG 134）加它的理由写在
# `execution_order()` 的文档串里 —— 一句话版本：名册里"排在某条之后"这种话以前只能推断，
# 有了执行序它才变成读数。
ANY_CASE_LINE = re.compile(r"Test Case '-\[[^\]]*?\b(test[A-Za-z0-9_]+)[^\]]*\]' (started\.|passed|failed|skipped)")
ASSERTION_RED = re.compile(r"error: -\[[^\]]*?\b(test[A-Za-z0-9_]+)[^\]]*\] : (XCTAssert\w+)([^\n]*)")
# R143 的洞（独立审查抓出来的，见账）：只认 `XCTAssert` 的话，**崩溃 / 超时 / `XCTFail` 那一类只有结论行、没有断言行**的红会整个看不见 —— 而 `CONCLUDED` 又把 `failed` 算成"下过结论"，# 隔壁 `ci_capture_gate.py` 早就把这两个来源并起来了（它的文档串就写着这句话），这一支漏了。
CASE_FAILED = re.compile(r"Test Case '-\[[^\]]*?\b(test[A-Za-z0-9_]+)[^\]]*\]' failed")


def source_cases(text):
    """只认真正的定义行（行首缩进 + `func test…()`）。

    守卫不许命中自己，也不许命中注释里提到的用例名 —— 同 R53 那条
    「region() 会先命中守卫自己写的名字」。
    """
    return [m.group(1) for m in CASE_FUNC.finditer(text)]


def concluded_cases(log_text):
    out = {}
    for name, verdict in CONCLUDED.findall(log_text):
        out[name] = verdict
    return out


def execution_order(log_text):
    """返回 (第一次露面的顺序, {名字: 是否下过结论}, [结论之后又出现 started 的名字])。

    为什么需要顺序（R94 / BACKLOG 134）：缺席有**两种完全不同的成因**——
      ① 跑到它了，但它被看门狗收掉 / 永不返回 ⇒ 那是产品或探针的毛病；
      ② 一次都没轮到它 ⇒ 那只是整卷被截断，本条今天没有资格被评价。
    只报"缺席了哪几条"（`PROBE_NOT_RUN` 老写法）会把两种混成一句，于是"排在挂住那条之后"
    这种话只能是**我的推断**（XCTest 在同一卷里按字母序执行，我是在同一次 run 的**另一步**
    里数了一遍那 10 条的顺序才敢这么说）。按步骤名过滤才不被另一条步骤的全 skip 顶掉 ——
    那一整卷在同一次 run 里有 20 行结论，全是 skip，属于 `Swift tests` 步骤而不是探针步骤。
    有了这里的第一次露面顺序，①②各自有自己的名字，推断就不必再写进登记。
    """
    order = []
    concluded = {}
    interleaved = []
    for name, kind in ANY_CASE_LINE.findall(log_text):
        if name not in concluded:
            order.append(name)
            concluded[name] = False
        if kind != "started.":
            concluded[name] = True
        elif concluded[name]:
            # 结论之后又见到一次 `started.` ⇒ 这份日志**不止一个写入者**（或同一例被跑了第二遍）。
            # 第一版让这条把状态改回"未结论"，于是 `未闭口` 凭空 +1 —— 而那正是登记的依据
            # （M521 那一刀当时是**故意留着绿**的，因为它没有判据覆盖 ⇒ BACKLOG 135）。
            # 现在两件事分开：结论是**粘的**（下过就算下过），交错本身打成一条有名字的读数。
            interleaved.append(name)
    return order, concluded, sorted(set(interleaved))


def analyse(source_names, expectations, log_text, closed=None, pulsed=None):
    """返回 (读数, 红清单)。纯函数：所有 IO 都在 main() 里，这样它自己可测。

    R148 / BACKLOG 187 · `closed` / `pulsed`：闭合通道（`PROBE_DONE` / `PROBE_PULSE`）给的两份名单，
    `None` = 这一格今天没接线 ⇒ **完全维持旧行为**（只看日志）。接上之后"这条在 runner 上到底跑没跑过"
    由 `日志的结论行 ∪ 闭合行` 判，而不是只由那条会被 SIGKILL 整块带走的 stdout 判（R146 的 U-494）。
    """
    reds = []
    for name, entry in sorted(expectations.items()):
        runner = entry.get("runner")
        if runner not in ("can", "cannot"):
            reds.append(f"BAD_RUNNER_FIELD {name} runner={runner!r}（只许 can / cannot）")
        elif runner == "cannot" and not str(entry.get("reason", "")).strip():
            reds.append(f"REASONLESS {name} 登记为 cannot 但没有 reason")

    concluded = concluded_cases(log_text)
    # 闭合通道接没接，决定"跑过"这句话有多少依据。**不**把它写成默认空集：
    # 空集与"没接线"在旧行为上长得一样，但读数上不一样（`闭合通道=未接` 要说出口）。
    file_channel = closed is not None
    ran = set(concluded) | set(closed or ())
    log_lost = sorted(set(closed or ()) - set(concluded))
    contradicted = sorted(name for name in (expectations or {})
                          if expectations[name].get("runner") == "cannot"
                          and name in ran and name not in concluded)
    pulse_only = sorted(set(pulsed or ()) - set(closed or ()))
    close_without_pulse = sorted(set(closed or ()) - set(pulsed or ())) if pulsed is not None else []
    for name in source_names:
        if name not in expectations:
            reds.append(f"UNLISTED {name}：源码里有这条在屏判据，清单里没有 ⇒ "
                        "它要么在 runner 上跑得了（登记 can），要么跑不了（写清为什么）")
    for name in sorted(expectations):
        if name not in source_names:
            reds.append(f"STALE {name}：清单里有、源码里已经没有这条用例 ⇒ 删掉这行登记")
        runner = expectations[name].get("runner")
        if runner == "can" and name not in ran:
            basis = "日志没有它的结论行，闭合通道也没有它的闭合行" if file_channel else "这次日志里没有它的结论行"
            reds.append(f"NOT_RUN {name}：登记为 runner=can，而{basis}")
        if runner == "cannot" and name in concluded:
            reds.append(f"NOW_RUNS {name}：登记说 runner 跑不了，而这次它下结论了"
                        f"（{concluded[name]}）⇒ 把登记改成 can")
    # 闭合通道自己讲不通 ⇒ 红：有闭合行却没有心跳行，说明这份文件被写坏了或者路径对错了，
    # 那时上面那句"跑过"就没有依据，不许拿它给任何一条登记签字。
    for name in close_without_pulse:
        reds.append(f"PROBE_CLOSE_WITHOUT_PULSE {name}：文件里有它的闭合行却没有心跳行 ⇒ 闭合通道不可信，"
                    "这一格的『跑过』不能由它支撑")

    for name, kind, message in ASSERTION_RED.findall(log_text)[:8]:
        # R99 / BACKLOG 145：**名字不够，还要那一句为什么**（同一行里就有，是这颗正则丢掉的）。
        # run 38898253512（R98 的 CI）这一步打的是
        #   FAILED testFrameIntervalsUnderStateChanges：XCTAssertLessThanOrEqual 在这份日志里打红了
        # 而"哪个数、超过哪条线、判据自己写的那句理由"就在**同一行**里 ——
        # `error: -[... testX] : XCTAssertLessThanOrEqual failed: ("6.0") is greater than ("4.5") - …`。
        # 于是"runner 上到底为什么红"只能靠猜，而这一族里靠猜出来的修法已经错过一次（R51）。
        # 同一个教训 R59 在 motion 那一步记过一次（`红的理由（XCTAssert 原文…）`），这一支漏了。
        detail = message.strip()[:300]
        reds.append("FAILED %s：%s %s" % (name, kind,
                                          detail if detail else "在这份日志里打红了"))

    # 第二个红的来源：**只有结论行**的失败（崩溃 / 超时 / XCTFail）。不并进来的话，
    # 一份"全部红"的日志会被读成"全部下过结论"⇒ 地板绿。
    already = {name for name, _k, _m in ASSERTION_RED.findall(log_text)}
    for name in CASE_FAILED.findall(log_text):
        if name in already:
            continue
        reds.append("FAILED %s：结论行是 failed，而这份日志里没有它的 XCTAssert 行"
                    "（崩溃 / 超时 / XCTFail 那一类）⇒ 它**下过结论**不等于**通过**" % name)
        already.add(name)

    can = sum(1 for e in expectations.values() if e.get("runner") == "can")
    order, appeared, interleaved = execution_order(log_text)
    # 缺席分两种，但**这一支只点"一次都没轮到"的名字**：
    # 「跑到它了却没闭口」那条的名字归 `ui_probe_report.py`（它有 stdout + 心跳两条通道可以互相签字，
    # `UI_PROBE_CHANNELS_AGREE`），这一支只有一条日志，抢那个名字就会造出第二颗尺子
    # —— 同 R86 写在 `NonRedundancyTests` 里那条分工，R94 是照它办的，不是绕它走的。
    open_not_closed = sum(1 for n in order if not appeared[n])
    queued = [n for n in source_names if n not in appeared]
    # 执行序前缀：结论必须是"从头连续的一段"。断了后面还有结论 ⇒ 要么执行序不是我想的那样，
    # 要么看门狗之后还有孤儿在跑（读那一步的 UI_PROBE_ORPHAN_XCTEST）。
    first_hole = next((i for i, n in enumerate(order) if not appeared[n]), None)
    # 一条都没露面 ⇒ 「前缀」这个问题本身没有对象。写成 1 就是一句**空洞的真话**
    # （R85 那一族：初值恰好等于期望值）；那种时候要说的是"无从判定"。
    prefix = None if not order else (first_hole is None or all(not appeared[n] for n in order[first_hole:]))
    reading = {
        "source_cases": len(source_names),
        "listed": len(expectations),
        "can": can,
        "cannot": len(expectations) - can,
        "concluded": len(concluded),
        "absent": [n for n in source_names if n not in ran],
        "file_channel": file_channel,
        "ran": len([n for n in source_names if n in ran]),
        "log_lost": log_lost,
        "contradicted": contradicted,
        "pulse_only": pulse_only,
        "appeared": len(order),
        "open_not_closed": open_not_closed,
        "interleaved": interleaved,
        "queued": queued,
        "prefix": prefix,
    }
    return reading, reds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log")
    parser.add_argument("--expectations", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--pulse", default=None,
                        help="心跳/闭合那份文件（`probe-pulse.log`）。不传 ⇒ 只看日志（旧行为）")
    args = parser.parse_args(argv)

    try:
        with open(args.expectations, encoding="utf-8") as handle:
            expectations = json.load(handle).get("cases", {})
        with open(args.source, encoding="utf-8") as handle:
            source_names = source_cases(handle.read())
        # 日志读不到 ≠ 通过：这一步存在的理由就是「缺席必须被看见」。
        with open(args.log, encoding="utf-8", errors="replace") as handle:
            log_text = handle.read()
    except (OSError, ValueError) as error:
        print(f"PROBE_GATE_ERROR 输入读不到：{error}")
        return 2

    closed = pulsed = None
    if args.pulse:
        # 复用同一颗解析器（见模块头那句）：把脚本自己那一层放进 sys.path 再 import。
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from ui_probe_report import DONE, PULSE
        try:
            with open(args.pulse, encoding="utf-8", errors="replace") as handle:
                pulse_text = handle.read()
        except OSError as error:
            print(f"PROBE_PULSE_UNREADABLE={args.pulse}（{error}）⇒ 闭合通道**未接**，"
                  "下面那句『跑过』退回只看日志的旧口径")
        else:
            closed = [m.group(1) for m in DONE.finditer(pulse_text)]
            pulsed = [m.group(1) for m in PULSE.finditer(pulse_text)]

    reading, reds = analyse(source_names, expectations, log_text, closed=closed, pulsed=pulsed)
    print(f"PROBE_COVERAGE_SUMMARY 源码用例={reading['source_cases']} 登记={reading['listed']} "
          f"runner可跑={reading['can']} runner不可跑={reading['cannot']} "
          f"本次下结论={reading['concluded']} "
          f"闭合通道={'接' if reading['file_channel'] else '未接'} "
          f"本次跑过={reading['ran']} 红={len(reds)}")
    for red in reds:
        print("  " + red)
    # 缺席本身要打得**具体**：只说「没跑完」会让人以为所有判据都只是延迟。
    if reading["absent"]:
        absent = reading["absent"]
        print(f"  PROBE_NOT_RUN {len(absent)}/{reading['source_cases']} 条在屏判据这次没下结论："
              + " ".join(absent[:12]) + (" …" if len(absent) > 12 else ""))
    # R94（BACKLOG 134）：把上面那句的"缺席"拆成两种**各有出处**的缺席。
    # 这不为好看 —— 名册里"本条排在 X 之后"以前只能由我从另一步的字母序**推断**，
    # 现在它是一条读数；推断与读数的区别就是：读数的下一轮能证伪它。
    # 名字归它自己的那支：`未闭口` 只报数，`UI_PROBE_HUNG=<名字>` 由 ui_probe_report 出。
    print(f"  PROBE_ORDER 露面={reading['appeared']}/{reading['source_cases']} "
          f"未闭口={reading['open_not_closed']} "
          f"前缀={'无从判定' if reading['prefix'] is None else (1 if reading['prefix'] else 0)}")
    if reading["interleaved"]:
        print("  PROBE_ORDER_INTERLEAVED %d 条在**下过结论之后**又出现 started：%s"
              % (len(reading["interleaved"]), " ".join(reading["interleaved"]))
              + " ⇒ 这份日志不止一个写入者（或同一例被跑了两遍）。结论按粘的处理（下过就算下过），"
                "但 `未闭口` 这一格今天不可信 —— 132 的分诊要先解决写入者是谁")
    # 三条闭合通道带来的读数，全部**只报不判**（除了上面那条通道自相矛盾的）：
    # 「挂在哪一条」的名字归 `ui_probe_report.py`（它现在有两条文件内的通道可以对账），这里抢名字就是第二颗尺子。
    if reading["log_lost"]:
        print(f"  PROBE_LOG_LOSE_CONCLUSION {len(reading['log_lost'])} 条有闭合行却没有日志结论行："
              + " ".join(reading["log_lost"][:12])
              + " ⇒ 丢的是那一行 stdout，不是这条用例；这一格不许被读成『它没跑』")
    if reading["pulse_only"]:
        print(f"  PROBE_PULSE_OPEN {len(reading['pulse_only'])} 条有心跳没闭合："
              + " ".join(reading["pulse_only"][:12])
              + " ⇒ 正跑着被收掉的那一条**由 ui_probe_report 点名**（UI_PROBE_HUNG_CHANNEL=file），这里只报数")
    if reading["contradicted"]:
        print(f"  PROBE_REGISTRATION_CONTRADICTED {len(reading['contradicted'])} 条登记为 cannot，而闭合行说它跑完了："
              + " ".join(reading["contradicted"][:12])
              + " ⇒ 登记该翻面；**这一格今天只报不判**（升红的判据与目标名写在 BACKLOG 187）")
    if reading["queued"]:
        print(f"  PROBE_QUEUED {len(reading['queued'])}/{reading['source_cases']} 条一次都没轮到："
              + " ".join(reading["queued"][:12]) + (" …" if len(reading["queued"]) > 12 else ""))
    if reading["prefix"] is False:
        print("  PROBE_ORDER_WARNING 前缀断了 ⇒ 「排在空洞之后」这句登记不成立，"
              "要么执行序不是字母序，要么看门狗收掉之后还有孤儿在往下跑"
              "（读同一步骤里那一支报的孤儿数与『挂住的是谁』）"
              " —— 这一格**不判红**：它说的是成因，不是产品有没有过；红会把一条诊断变成门禁。")
    return 1 if reds else 0


if __name__ == "__main__":
    sys.exit(main())
