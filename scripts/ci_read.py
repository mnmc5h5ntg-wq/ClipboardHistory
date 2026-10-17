#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读 CI 的固定动作（R102 立，替代每一轮临时 `gh run view | grep`）。

为什么要有它：这一族已经烧掉过好几轮 ——
  · U-178：状态行会在全量卷与动效卷**各打一次且取值不同**，跨步骤 grep 会造出
    「同一族既 ok 又 skipped」的假矛盾，我差点据此去修一个不存在的排序 bug；
  · U-179：「没有 Test Case 行」有两种成因（进程真没开始 vs 我拿错了文件），
    后者会被写成一句关于产品的假话；
  · U-145/146：那一步只报「哪条红了」不报「红在哪一句」。
所以这一支把三件事写进结构里：**按步骤名分组**、**通道没有行就说「没有行」而不是「没有」**、
**红必须连原文一起给**。

它只读不写（`gh run list` / `gh run view` / `gh api …/logs`），不改任何东西。

用法：
  python3 scripts/ci_read.py latest [--workflow UI]
  python3 scripts/ci_read.py steps   <run-id>
  python3 scripts/ci_read.py readings <run-id> [通道前缀 …]
退出码：0=拿到并打印了；1=要求的 run/日志取不到；2=用法错。
"""
import json
import re
import subprocess
import sys

DEFAULT_CHANNELS = ("CARD_PROBE_ARM", "CARD_STATS_", "CARD_INSET_", "CARD_ABOVE_",
                    "CARD_BELOW_", "CARD_BAND", "CARD_FILL_CANDIDATES")


def gh(*args):
    proc = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write("gh %s 失败（exit=%d）：%s\n"
                         % (" ".join(args), proc.returncode, proc.stderr.strip()[:300]))
        return None
    return proc.stdout


def latest(workflow=None):
    cmd = ["run", "list", "--limit", "8", "--json",
           "databaseId,headSha,conclusion,status,displayTitle,workflowName"]
    out = gh(*cmd)
    if out is None:
        return None
    runs = json.loads(out)
    if workflow:
        runs = [r for r in runs if workflow.lower() in (r.get("workflowName") or "").lower()]
    if not runs:
        sys.stderr.write("没有匹配的 run（workflow=%s）\n" % workflow)
        return None
    return runs[0]


def steps(run_id):
    out = gh("run", "view", str(run_id), "--json", "conclusion,jobs")
    if out is None:
        return None
    data = json.loads(out)
    print("RUN=%s conclusion=%s" % (run_id, data.get("conclusion")))
    for job in data.get("jobs", []):
        print("  JOB %s ⇒ %s" % (job.get("name"), job.get("conclusion")))
        for st in job.get("steps", []):
            if st.get("conclusion") not in ("success", None):
                print("    STEP[%s] %s ⇒ %s" % (st.get("number"), st.get("name"),
                                                st.get("conclusion")))
    return data


def log_text(run_id):
    """整份 run 的日志（zip 由 gh 处理；这里拿的是合并后的纯文本）。"""
    out = gh("run", "view", str(run_id), "--log")
    return out


TS_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*")


def parse_log(text):
    """`gh run view --log` 每行是 `<job>\t<step>\t<时间戳 正文>`（实测 4766/4868 行是这个形状）。

    第一版这里写成「要求 ≥4 个字段、把 parts[2] 当步骤」⇒ **三字段行整批被丢掉**，
    于是它在 R101 那份真日志上把 `CARD_FILL_CANDIDATES` 报成「没有一行」，而实际有 **104 行**
    （R102 / U-302：一支专门用来防「读错 run / 跨步骤 grep」的工具，自己坏在字段数上，
    而且坏的方向正好是「把有读数说成没读数」—— 那是最坏的一侧，因为它会让下一轮把已跑过的判据记成未跑）。
    """
    rows, unparsed = [], 0
    for line in text.splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            unparsed += 1
            continue
        job, step, rest = parts[0].strip(), parts[1].strip(), parts[2]
        rows.append((job, step, TS_PREFIX.sub("", rest).strip()))
    return rows, unparsed


def assertion_reds(rows):
    """从 (job, step, body) 里挑出**断言红**的行。

    两种形状都必须数（R105 / run 38975204376 实证）：
      ① `XCTAssertLessThanOrEqual failed: ("32.19") is greater than …` —— 带宏名的；
      ② `error: -[Suite test] : failed - light：搜索那一行…` —— **裸 `XCTFail` 的**，
         它没有 `XCTAssert` 这个词。上一版只数①，于是那一跑明明有六行红，
         这一格报的是 4 行 / 去重 2 条 —— 我新写的那条判据在 runner 上整个不见了都没报出来。
    """
    out = []
    for _, _, body in rows:
        if "XCTAssert" in body and "failed" in body:
            out.append(body)
        elif "error:" in body and " : failed - " in body:
            out.append(body)
    return out


def readings(run_id, prefixes, text=None):
    if text is None:
        text = log_text(run_id)
    if text is None:
        return 1
    rows, unparsed = parse_log(text)
    print("READINGS run=%s 解析出 %d 行（丢掉 %d 行）通道=%s"
          % (run_id, len(rows), unparsed, ", ".join(prefixes)))
    if unparsed:
        print("  !! 有 %d 行连三个字段都凑不齐 ⇒ 日志格式可能变了，先怀疑这把尺" % unparsed)
    seen = set()
    for p in prefixes:
        hits = [(j, s, b) for (j, s, b) in rows if p in b]
        if not hits:
            # 关键一格：**「一行都没有」有三种成因，都不许记成通过，也不许记成「这件事没发生」**
            print("  !! 通道 %s 没有一行 ⇒ 先判：该步骤没跑 / 判据没走到 / 打印机被改名 / 这把尺读错字段（U-179、U-302）" % p)
            continue
        steps = sorted({"%s / %s" % (j, s) for j, s, _ in hits})
        print("  %s ⇒ %d 行，来自步骤：%s" % (p, len(hits), " | ".join(steps)))
        for j, s, b in hits[:6]:
            print("      [%s] %s" % (s, b[:190]))
        if len(hits) > 6:
            print("      …另有 %d 行" % (len(hits) - 6))
        seen |= {b for _, _, b in hits}
    reds = assertion_reds(rows)
    distinct = sorted(set(re.sub(r"^\s*", "", r) for r in reds))
    print("ASSERTION_RED 行=%d 去重后=%d" % (len(reds), len(distinct)))
    for r in distinct[:10]:
        print("   ", r[-200:])
    return 0


def main():
    args = sys.argv[1:]
    # `--help` 必须退 0：`scripts/tests/test_script_help_runs.py` 会对 `scripts/` 下每一支脚本
    # 跑一次 `--help` 并要求 exit 0（R102 / U-303：这一支第一版把"未知参数"与 `--help` 都返回 2，
    # 于是新工具一进 `scripts/` 就被自家守卫拦下 —— 那是**守卫在起作用**，不是守卫坏了）。
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if len(args) < 1 or args[0] not in ("latest", "steps", "readings"):
        print(__doc__)
        return 2
    if args[0] == "latest":
        wf = args[args.index("--workflow") + 1] if "--workflow" in args else None
        r = latest(wf)
        if not r:
            return 1
        print("RUN=%s sha=%s status=%s conclusion=%s title=%s workflow=%s"
              % (r["databaseId"], (r.get("headSha") or "")[:7], r.get("status"),
                 r.get("conclusion"), (r.get("displayTitle") or "")[:60], r.get("workflowName")))
        return 0
    if args[0] == "steps":
        return 0 if steps(args[1]) else 1
    return readings(args[1], args[2:] or list(DEFAULT_CHANNELS))


if __name__ == "__main__":
    sys.exit(main())
