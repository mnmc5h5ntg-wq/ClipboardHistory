# -*- coding: utf-8 -*-
"""R585 的 ⓪：读上一轮那两跑，并把 R584 补记里那条**可证伪预测**逐条对拍。

预测（R584 补记原文）：含本笔的那一跑应读到
  ⑴ `FRAME_BASELINE_AGAINST=working`、`FRAME_BASELINE_MACHINE=github-runner`、`FRAME_BASELINE_OWNER=local:MacBook-Air.local` 三行都在；
  出口·乙 `FRAME_BASELINE_DRIFT … 判=不判 … 变帧=356 … 本机行=0 他机行=8 … 未登记（不判）=356`；
  （NOT_JUDGED 那一格是出口·乙的读数，不是新出口）`FRAME_BASELINE_DRIFT_NOT_JUDGED=baseline-owned-by:local_MacBook_Air_local`；
  出口·甲的判据 `FRAME_BASELINE_RESULT=ok 拦路=0（缺席0 未登记不判 …）` ⇒ **STEP[11] 不许红**。

**编号口径**（监工 2026-11-06 指出：两套编号不同义，必须拆开）：
本脚本报的是**出口·甲/乙/丙/丁** —— 甲=判=判（且 STEP[11] 红 ⇒ 未登记真漂移）、
乙=判=不判（基线不是这台机器的产物 ⇒ 那一维今天没人判）、丙=那一行命中 0 次（通道没跑）、
丁=`FRAME_BASELINE_SKIPPED`（帧集太小 ⇒ 今天没判，绝不等于"第二台绿了"）。
而 **658 的三条出路**用的是另一套编号 ⑴CI 打印逐机器清单 ⑵那一台自己 update 并提交 ⑶永久只归主人判 ——
**两条轴**：出口·乙 说的是"今天有没有人判"，出路 ⑵ 说的是"将来怎么办"；
读到 出口·乙 **不等于** 出路 ⑵ 成立，更不等于"那朵红消失了"。

三条老规矩照用：自己 `gh run view --log` 落盘再切（`readings` 每通道只采样）、
按**步骤**归属（自测那一步印的是合成树）、按**行首**匹配（CI 会 echo 自己的脚本行）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = "/tmp/r585"
PAIRS = [("42093340563", "3e13d47", u"R584 主笔：机器维度第一次上 runner"),
         ("42094125984", "aa8ef88", u"R584 补记笔：只带台账，不替主笔签")]
GATE_STEP_IN = "Frame baseline vs working manifest"
ESC = re.compile(r"\x1b\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*")

PREDICTIONS = [
    (u"AGAINST=working", lambda g: any(l.startswith("FRAME_BASELINE_AGAINST=working") for l in g)),
    (u"MACHINE=github-runner", lambda g: any(l == "FRAME_BASELINE_MACHINE=github-runner" for l in g)),
    (u"OWNER=local:MacBook-Air.local", lambda g: any(l == "FRAME_BASELINE_OWNER=local:MacBook-Air.local" for l in g)),
    (u"判=不判 且 变帧=356 且 他机行=8", lambda g: any(
        l.startswith("FRAME_BASELINE_DRIFT ") and u"判=不判" in l and u"变帧=356" in l
        and u"他机行=8" in l for l in g)),
    (u"未登记（不判）=356", lambda g: any(u"未登记（不判）=356" in l for l in g)),
    (u"NOT_JUDGED=baseline-owned-by:local_MacBook_Air_local",
     lambda g: any(l.startswith("FRAME_BASELINE_DRIFT_NOT_JUDGED=baseline-owned-by:local_MacBook_Air_local")
                   for l in g)),
    (u"RESULT=ok 且 未登记不判", lambda g: any(
        l.startswith("FRAME_BASELINE_RESULT=ok") and u"未登记不判" in l for l in g)),
    (u"STEP[11] 不红", None),      # 由步骤级结论判，见 classify
]


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def parse_log(path):
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


def classify(steps_out, rows):
    lines = [l.strip() for l in (steps_out or "").splitlines()]
    concluded = [l for l in lines if re.search(r"⇒\s*(failure|success|skipped)\s*$", l)]
    if not concluded:
        return (u"未问", u"一个非空结论都没有（作业还在跑）⇒ 四种出口一条都不许选，整格 NOT-RUN；"
                        u"「STEP[11] 在列表里」不算到数（R557 那一课）", [])
    failed = [l for l in concluded if u"⇒ failure" in l]
    step11_red = any("STEP[11]" in l for l in failed)
    gate = [b for s, b in rows if GATE_STEP_IN in s]
    skipped = [b for b in gate if b.startswith("FRAME_BASELINE_SKIPPED=")]
    drift = [b for b in gate if re.match(r"FRAME_BASELINE_DRIFT (本机=|变帧=)", b)]
    unjudged = [b for b in gate if b.startswith("FRAME_BASELINE_DRIFT_NOT_JUDGED=")]
    result = [b for b in gate if b.startswith("FRAME_BASELINE_RESULT=")]
    evidence = drift + result + unjudged
    if skipped:
        return (u"出口·丁", u"帧集太小 ⇒ 那一格今天**根本没跑**；只能读成「这台机器今天没判」，"
                      u"绝不能读成「第二台绿了」。逐字：%s" % u" || ".join(skipped), evidence)
    if not drift:
        return (u"出口·丙", u"通道没跑：STEP[11] 有结论而门那一行取不到 ⇒ 先读 executed= 与全部失败步骤。逐字步骤：%s"
                 % u" / ".join(failed), evidence)
    if unjudged:
        hit = []
        for label, test in PREDICTIONS:
            if test is None:
                continue
            hit.append(u"%s=%s" % (label, u"中" if test(gate) else u"不中"))
        verdict = u"出口·乙" if not step11_red else u"出口·乙+红"
        return (verdict, u"判=不判 ⇒ 那条预测逐条对拍：%s；STEP[11]=%s ⇒ %s"
                 % (u"、".join(hit), u"红" if step11_red else u"没红",
                    u"预测成立" if not step11_red else u"预测不成立（不判却拦了门）"),
                 evidence)
    if step11_red:
        return (u"出口·甲", u"判=判 而 STEP[11] 红 ⇒ 那一台真有未登记漂移 ⇒ 为那一台补登记（走 register-drift）。逐字：%s"
                 % u" || ".join(evidence), evidence)
    return (u"出口·甲绿", u"判=判 且 STEP[11] 没红 ⇒ 那一维在那台机器上闭合了。逐字：%s" % u" || ".join(evidence), evidence)


def main():
    if not os.path.isdir(TMP):
        os.mkdir(TMP)
    report = {}
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
        hit, disp, evidence = classify(steps, rows)
        report[run] = {"sha": sha, "note": note, "steps_rc": rc,
                       "steps": (steps or err).strip()[:1200], "log_rc": log_rc,
                       u"出口": hit, u"处置": disp, u"门那一步的逐字读数": evidence[:6],
                       u"红名单": sorted({m.group(1) for s, b in rows
                                        for m in [re.match(
                                            r"Test Case '-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\]' failed", b)] if m}),
                       u"D12登记": [b for s, b in rows if b.startswith("D12_SHAPE_SCAN_REGISTRY ")][:1],
                       u"探针": [b for s, b in rows if b.startswith("PROBE_COVERAGE_SUMMARY")][:1]}
    with io.open(os.path.join(TMP, "ci_readings.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    for run, sha, _note in PAIRS:
        item = report[run]
        print(u"RUN=%s ↔ %s 出口=%s 日志=%d 字节(rc=%d)" % (run, item["sha"], item[u"出口"],
              os.path.getsize(os.path.join(TMP, "log_%s.txt" % run)) if os.path.exists(
                  os.path.join(TMP, "log_%s.txt" % run)) else 0, item["log_rc"]))
        print(u"  处置=%s" % item[u"处置"][:520])
        for line in item[u"门那一步的逐字读数"]:
            print(u"  逐字=%s" % line[:240])
        print(u"  红名=%s" % u" ".join(item[u"红名单"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
