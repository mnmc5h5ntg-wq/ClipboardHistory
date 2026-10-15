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

用法：
    python3 scripts/probe_coverage_gate.py <ui.log> \\
        --expectations scripts/probe_coverage_expectations.json \\
        --source ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift

退出码：0 一切都在登记之内 / 1 上面任何一条红 / 2 清单、源码或日志读不到（读不到 ≠ 通过）。
"""
import argparse
import json
import re
import sys

CASE_FUNC = re.compile(r"^\s*func (test[A-Za-z0-9_]+)\s*\(\s*\)", re.MULTILINE)
# XCTest 的结论行：`Test Case '-[Mod.Class testSomething]' passed (1.234 seconds).`
# skipped 也算「下过结论」：skip 不是通过，但它证明这条被执行到了（区别于整卷没跑到）。
CONCLUDED = re.compile(r"Test Case '-\[[^\]]*?\b(test[A-Za-z0-9_]+)[^\]]*\]' (passed|failed|skipped)")
ASSERTION_RED = re.compile(r"error: -\[[^\]]*?\b(test[A-Za-z0-9_]+)[^\]]*\] : (XCTAssert\w+)")


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


def analyse(source_names, expectations, log_text):
    """返回 (读数, 红清单)。纯函数：所有 IO 都在 main() 里，这样它自己可测。"""
    reds = []
    for name, entry in sorted(expectations.items()):
        runner = entry.get("runner")
        if runner not in ("can", "cannot"):
            reds.append(f"BAD_RUNNER_FIELD {name} runner={runner!r}（只许 can / cannot）")
        elif runner == "cannot" and not str(entry.get("reason", "")).strip():
            reds.append(f"REASONLESS {name} 登记为 cannot 但没有 reason")

    concluded = concluded_cases(log_text)
    for name in source_names:
        if name not in expectations:
            reds.append(f"UNLISTED {name}：源码里有这条在屏判据，清单里没有 ⇒ "
                        "它要么在 runner 上跑得了（登记 can），要么跑不了（写清为什么）")
    for name in sorted(expectations):
        if name not in source_names:
            reds.append(f"STALE {name}：清单里有、源码里已经没有这条用例 ⇒ 删掉这行登记")
        runner = expectations[name].get("runner")
        if runner == "can" and name not in concluded:
            reds.append(f"NOT_RUN {name}：登记为 runner=can，而这次日志里没有它的结论行")
        if runner == "cannot" and name in concluded:
            reds.append(f"NOW_RUNS {name}：登记说 runner 跑不了，而这次它下结论了"
                        f"（{concluded[name]}）⇒ 把登记改成 can")

    for name, kind in ASSERTION_RED.findall(log_text)[:8]:
        reds.append(f"FAILED {name}：{kind} 在这份日志里打红了 ⇒ 红要能被读，也要有人负责")

    can = sum(1 for e in expectations.values() if e.get("runner") == "can")
    reading = {
        "source_cases": len(source_names),
        "listed": len(expectations),
        "can": can,
        "cannot": len(expectations) - can,
        "concluded": len(concluded),
        "absent": [n for n in source_names if n not in concluded],
    }
    return reading, reds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log")
    parser.add_argument("--expectations", required=True)
    parser.add_argument("--source", required=True)
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

    reading, reds = analyse(source_names, expectations, log_text)
    print(f"PROBE_COVERAGE_SUMMARY 源码用例={reading['source_cases']} 登记={reading['listed']} "
          f"runner可跑={reading['can']} runner不可跑={reading['cannot']} "
          f"本次下结论={reading['concluded']} 红={len(reds)}")
    for red in reds:
        print("  " + red)
    # 缺席本身要打得**具体**：只说「没跑完」会让人以为所有判据都只是延迟。
    if reading["absent"]:
        absent = reading["absent"]
        print(f"  PROBE_NOT_RUN {len(absent)}/{reading['source_cases']} 条在屏判据这次没下结论："
              + " ".join(absent[:12]) + (" …" if len(absent) > 12 else ""))
    return 1 if reds else 0


if __name__ == "__main__":
    sys.exit(main())
