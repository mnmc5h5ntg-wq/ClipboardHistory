#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两次 CI 跑的**红名单对账**（BACKLOG 166 的仪器；R110 写）。

为什么要有它：R108 那跑 runner 上红的是 `testBandCaptureIsCheaperAndStillSeesTheMotion`，
R109 那跑（产品只差一行声明）红的是 `testFrameIntervalsUnderStateChanges` —— 同一台机器、
同一份尺、相邻两跑，**动效那两朵红互相换班**。以前这件事只能靠我读两份日志然后用嘴说，
而"我读了两份日志"这句话本身就是下一轮的账（D-176 那一族：结论要能被机器复查）。

这把尺只做一件事：把两次跑的红**归约成名字**（用例名 + 断言形状），然后分成三格：
  BOTH_RED   两跑都红 ⇒ 这条红可以当真（可复现）
  ONLY_A / ONLY_B  只在一跑红 ⇒ **换班**，它不能当"这一版有这条问题"的证据
退出码：0 = 没有换班；1 = 有换班；2 = 有一份日志读不到（读不到不等于"没有红"）。

用法：
  python3 scripts/ci_red_stability.py <runA> <runB>
  python3 scripts/ci_red_stability.py --from-file a.log b.log
"""

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ci_read  # noqa: E402  同一套日志解析与"两种红形状"（R105 的 U-320）

TEST_NAME = re.compile(r"\btest[A-Za-z0-9_]+")
MACRO = re.compile(r"XCTAssert[A-Za-z]*")


def fingerprint(body):
    """没有用例名时的**替身身份**：取消息本体（` - ` 之后）前 48 个字符、压掉数字。

    为什么需要：`XCTAssertGreaterThan failed: ("0") is greater than ("0") - 参照臂 cardprobe-…`
    这一族的红，**名字在另一行**（`Test Case '-[…]' failed`），单看这一行抽不出 `testXxx`。
    上一版把它们全塞进 `<无名>` 一个桶 ⇒ 两跑各有两朵不同的无名红也会被报成"两跑都红"，
    换班就被吞掉（U-364：一把只报"数量一致"的尺，看不见身份换了）。
    """
    tail = body.split(" - ", 1)[1] if " - " in body else body
    return "无名:" + re.sub(r"\d+", "#", tail)[:48].strip()


def red_names(rows):
    """返回 {身份: 该身份出现的断言形状集合}。

    身份优先取**用例名**（`-[Suite testFoo] : failed - …` 与
    `FAILED testFoo：XCTAssert… failed: …` 两种形状里都有它），取不到就用消息指纹；
    形状取宏名，裸 `XCTFail` 记成 `bare` ⇒ "同一用例换了红法"也算换班。
    """
    found = {}
    for body in ci_read.assertion_reds(rows):
        name = TEST_NAME.search(body)
        key = name.group(0) if name else fingerprint(body)
        macro = MACRO.search(body)
        found.setdefault(key, set()).add(macro.group(0) if macro else "bare")
    return found


def rows_from_run(run_id):
    text = ci_read.log_text(run_id)
    if text is None:
        return None
    return ci_read.parse_log(text)[0]


def rows_from_file(path):
    if not os.path.exists(path):
        return None
    return ci_read.parse_log(io.open(path, encoding="utf-8", errors="replace").read())[0]


def compare(a_rows, b_rows, label_a, label_b):
    a = red_names(a_rows)
    b = red_names(b_rows)
    both = sorted(set(a) & set(b))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    shape_shift = sorted(k for k in both if a[k] != b[k])
    print("RED_STABILITY A=%s 红=%d B=%s 红=%d" % (label_a, len(a), label_b, len(b)))
    for k in both:
        print("  BOTH_RED   %s 形状=%s%s" % (k, "/".join(sorted(a[k])),
                                             "" if k not in shape_shift else "  ← 但形状换了：/" + "/".join(sorted(b[k]))))
    for k in only_a:
        print("  ONLY_A     %s 形状=%s" % (k, "/".join(sorted(a[k]))))
    for k in only_b:
        print("  ONLY_B     %s 形状=%s" % (k, "/".join(sorted(b[k]))))
    drifting = len(only_a) + len(only_b) + len(shape_shift)
    print("RED_STABILITY 两跑都红=%d 只在一跑=%d 形状换=%d 换班=%d"
          % (len(both), len(only_a) + len(only_b), len(shape_shift), 1 if drifting else 0))
    return 0 if drifting == 0 else 1


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--from-file":
        if len(args) != 3:
            print("用法：--from-file <A.log> <B.log>")
            return 64
        a_rows = rows_from_file(args[1])
        b_rows = rows_from_file(args[2])
        if a_rows is None or b_rows is None:
            print("RED_STABILITY_UNREADABLE=1（有一份日志读不到 ⇒ 这不叫『没有红』）")
            return 2
        return compare(a_rows, b_rows, os.path.basename(args[1]), os.path.basename(args[2]))
    if len(args) != 2:
        print("用法：<runA> <runB>  或  --from-file <A.log> <B.log>")
        return 64
    a_rows = rows_from_run(args[0])
    b_rows = rows_from_run(args[1])
    if a_rows is None or b_rows is None:
        print("RED_STABILITY_UNREADABLE=1（有一份 run 的日志下载不到 ⇒ 这不叫『没有红』）")
        return 2
    return compare(a_rows, b_rows, args[0], args[1])


if __name__ == "__main__":
    sys.exit(main())
