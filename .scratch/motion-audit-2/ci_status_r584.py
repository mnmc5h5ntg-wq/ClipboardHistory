# -*- coding: utf-8 -*-
"""R584 的 ⓪：成对拿 run↔sha、列**全部**失败步骤、按四种出口处置基线门那一格。

为什么自己下日志而不是用 `ci_read.py readings`：那一把尺**每个通道只采样几行**，
本轮要的正是被采样丢掉的那一行（STEP[11] 的 `FRAME_BASELINE_DRIFT`），
于是要不它在（读到的是自测那一步的 1/1/2），要不它"不在"（报成 ⑶b 通道没跑）—— 两种都是假读数。
按 `read-own-ci-run` 的规矩：**先落盘再切**，同一份文件给后面每一步复用。

三种坏法都在这份脚本里踩过并修掉（每条都留了字在注释里，供下一轮对账）：
· 按 substring 筛 ⇒ 把 CI 自己 echo 的脚本行读成 `FRAME_BASELINE_SKIPPED`（⑷ 假命中）；
· 不归属步骤 ⇒ 把 `Release script tests` 的合成读数（变帧=1）当成那一跑的数（共现当合取，R575 那一族）；
· 按"字段非空"问存在性 ⇒ 把占位文本读成读数（R583 ⑨·1 那一族）。

四种出口（修法各不相同，不许并成一句）：
  ⑵ 判=判 而 STEP[11] 红   ⇒ 那一台真有未登记漂移 ⇒ 为那一台补登记（不许改期望/调宽阈值/改 skip）
  ⑶ 判=不判 + NOT_JUDGED   ⇒ 基线不是这台机器的产物 ⇒ 只能读成「这一维在那儿今天没人判」，出路=658
  ⑶b DRIFT 命中 0 次        ⇒ 通道没跑 ⇒ 先读 executed= 与全部失败步骤，不许读成「与登记相符」
  ⑷ FRAME_BASELINE_SKIPPED  ⇒ 帧集太小，那一格根本没跑 ⇒ 绝不等于「第二台绿了」
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = "/tmp/r584"
PAIRS = [("42077586416", "bce08b4", u"R583 主笔：漂移登记门第一次上 runner"),
         ("42077903445", "d808030", u"R583 补记笔：只带台账，不替主笔签")]
GATE_STEP_IN = "Frame baseline vs working manifest"
TOKENS = ("FRAME_BASELINE_AGAINST", "FRAME_BASELINE_MACHINE", "FRAME_BASELINE_OWNER",
          "FRAME_BASELINE_COMPARED", "FRAME_BASELINE_CHANGED", "FRAME_BASELINE_MISSING",
          "FRAME_BASELINE_ADDED", "FRAME_BASELINE_DRIFT_REGISTRY", "FRAME_BASELINE_DRIFT",
          "FRAME_BASELINE_DRIFT_NOT_JUDGED", "FRAME_BASELINE_RESULT", "FRAME_BASELINE_SKIPPED",
          "D12_SHAPE_SCAN_REGISTRY", "PROBE_COVERAGE_SUMMARY", "MOTION_GATE_RESULT",
          "CAPTURE_GATE_RESULT")
ESC = re.compile(r"\x1b\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*")


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def verify_field_order():
    """解包之前先拿一个**已知**对象验字段顺序（R567/R581 那一族的规矩）。"""
    rc, out, err = sh(["python3", "scripts/ci_read.py", "latest", "--workflow", "CI"])
    if rc != 0:
        return u"latest 取不到（rc=%d）%s" % (rc, err.strip()[:120])
    m = re.search(r"RUN=(\d+) sha=(\w{7,40}) status=(\S+) conclusion=(\S*)", out)
    if not m:
        return u"形状不认识：%s" % out.strip()[:120]
    rc2, out2, _ = sh(["gh", "run", "view", m.group(1), "--json", "headSha,status,conclusion",
                       "-q", r'"\(.headSha) \(.status) \(.conclusion)"'])
    if rc2 != 0:
        return u"gh 复核失败 rc=%d" % rc2
    real = (out2.strip() + "  ").split()
    ok = real[0].startswith(m.group(2)[:7]) and real[1] == m.group(3) and (real[2] or "") == m.group(4)
    return (u"FIELDS_ORDER run=%s 通道=%s/%s gh=%s/%s ⇒ %s"
            % (m.group(1), m.group(3), m.group(4) or u"空", real[1], real[2] or u"空",
               u"对" if ok else u"错（停，别用这份解包）"))


def parse_log(path):
    """日志行 = `作业\\t步骤\\t时间戳 正文` ⇒ 逐行还原成 (步骤, 正文)；剥 ANSI、剥时间戳。"""
    rows = []
    if not os.path.exists(path):
        return rows
    for raw in io.open(path, encoding="utf-8", errors="replace"):
        parts = raw.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        body = TS.sub("", ESC.sub("", "\t".join(parts[2:]))).strip()
        rows.append((parts[1], body))
    return rows


def gate_lines(rows):
    """只取**门自己那一步**的行 —— 同名 token 在自测那一步印的是合成树（共现≠合取）。"""
    return [b for s, b in rows if GATE_STEP_IN in s]


def classify(steps_out, rows):
    lines = [l.strip() for l in (steps_out or "").splitlines()]
    concluded = [l for l in lines if re.search(r"⇒\s*(failure|success|skipped)\s*$", l)]
    if not concluded:
        return (u"未问", u"一个非空结论都没有（作业还在跑）⇒ 四种出口一条都不许选，整格 NOT-RUN；"
                        u"「STEP[11] 在列表里」不算到数（R557 那一课）", [])
    failed = [l for l in concluded if u"⇒ failure" in l]
    step11_red = any("STEP[11]" in l for l in failed)
    gate = gate_lines(rows)
    drift = [b for b in gate if re.match(r"FRAME_BASELINE_DRIFT (本机=|变帧=)", b)]
    skipped = [b for b in gate if b.startswith("FRAME_BASELINE_SKIPPED=")]
    unjudged = [b for b in gate if b.startswith("FRAME_BASELINE_DRIFT_NOT_JUDGED=")]
    result = [b for b in gate if b.startswith("FRAME_BASELINE_RESULT=")]
    evidence = drift + result + unjudged + skipped
    if skipped:
        return (u"⑷", u"帧集太小 ⇒ 那一格今天**根本没跑**。这一行只能读成「这台机器今天没判」，"
                      u"绝不能读成「第二台绿了」；要查的是那一天的捕获。逐字：%s" % u" || ".join(skipped), evidence)
    if not drift:
        return (u"⑶b", u"通道没跑：STEP[11] 有结论而门那一行取不到 ⇒ 先读 executed= 与全部失败步骤再下结论，"
                        u"**不许**把「没有这一行」读成「与登记相符」。步骤级读数：%s"
                 % u" / ".join(failed), evidence)
    if unjudged:
        return (u"⑶", u"判=不判 ⇒ 那份基线不是这台机器的产物 ⇒ 这一维在那台机器上今天没人判。"
                      u"合法处置只有一条：为那台冻结它自己的基线（658）；不许改期望、不许当成绿。逐字：%s"
                 % u" || ".join(unjudged + drift), evidence)
    if step11_red:
        return (u"⑵", u"判=判 而 STEP[11] 红 ⇒ 那一台真有未登记漂移 ⇒ 唯一合法处置是**为那一台补登记**"
                      u"（帧名+理由+单号）；不许把门改回只判 missing、不许调宽阈值/容差、不许改成具名 skip。逐字：%s"
                 % u" || ".join(drift + result), evidence)
    return (u"⑴", u"判=判 且 STEP[11] 没红 ⇒ 那一维在那台机器上闭合了（前提：它已有自己的基线）。逐字：%s"
             % u" || ".join(drift + result), evidence)


def red_names(rows):
    """STEP[15] 那一跑的红名（去重、排序）—— 归因对照要的是**集合**，不是数量。"""
    names = set()
    for step, body in rows:
        m = re.match(r"Test Case '-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\]' failed", body)
        if m:
            names.add(m.group(1))
    return sorted(names)


def main():
    if not os.path.isdir(TMP):
        os.mkdir(TMP)
    report = {"FIELDS_ORDER_CHECK": verify_field_order()}
    for run, sha, note in PAIRS:
        rc, steps, err = sh(["python3", "scripts/ci_read.py", "steps", run])
        log = os.path.join(TMP, "log_%s.txt" % run)
        if not os.path.exists(log) or os.path.getsize(log) == 0:
            proc = subprocess.Popen(["gh", "run", "view", run, "--log"], cwd=ROOT,
                                    stdout=open(log, "w"), stderr=subprocess.PIPE,
                                    universal_newlines=True)
            _, err2 = proc.communicate(timeout=900)
            log_rc = proc.returncode
        else:
            log_rc, err2 = 0, u""
        rows = parse_log(log)
        hit, disposition, evidence = classify(steps, rows)
        report[run] = {"sha": sha, "note": note, "steps": (steps or err).strip()[:1200],
                       "log_rc": log_rc, "log_err": (err2 or "").strip()[:200],
                       "log_bytes": os.path.getsize(log) if os.path.exists(log) else 0,
                       u"出口": hit, u"处置": disposition,
                       u"门那一步的逐字读数": evidence[:6],
                       u"红名单": red_names(rows),
                       u"探针那一卷": [b for s, b in rows if b.startswith("PROBE_COVERAGE_SUMMARY")][:2],
                       u"动效门": [b for s, b in rows if b.startswith("MOTION_GATE_RESULT")][:2]}
    with io.open(os.path.join(TMP, "ci_readings.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(u"CI_STATUS_R584=%s" % report["FIELDS_ORDER_CHECK"])
    for run, _sha, _note in PAIRS:
        item = report[run]
        print(u"RUN=%s ↔ %s 出口=%s 日志=%d 字节(rc=%d) 红名=%d 个"
              % (run, item["sha"], item[u"出口"], item["log_bytes"], item["log_rc"],
                 len(item[u"红名单"])))
        print(u"  处置=%s" % item[u"处置"][:400])
        for line in item[u"门那一步的逐字读数"]:
            print(u"  逐字=%s" % line[:240])
        print(u"  红名=%s" % u" ".join(item[u"红名单"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
