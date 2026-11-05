# -*- coding: utf-8 -*-
"""R586 的 ⓪：读上一轮那两跑，并登记本轮留给下一跑的那几条**可证伪预测**。

三条老规矩照用：自己 `gh run view --log` 落盘再切（`readings` 每通道只采样）、
按**步骤**归属（自测那一步印的是合成树）、按**行首**匹配（CI 会 echo 自己的脚本行）。

两套编号仍然分开（R585 / 监工点出来的那条）：
· 本报的**出口·甲/乙/丙/丁**说的是「今天这一维有没有人判」；
· **658/659/660 的出路**说的是「将来怎么办」；读到某个出口 ≠ 某条出路成立。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = "/tmp/r586"
PAIRS = [("42107518932", "955aa69", u"R585 主笔：写路径 + 出处 + 证伪"),
         ("42108062173", "ba093be", u"R585 补记笔：只带台账")]
GATE_STEP_IN = "Frame baseline vs working manifest"
HOVER_STEP_IN = "Surface left-axis ruler"     # 现读 ci.yml 里 hover 那一步的名字（下面按子串匹配，过期就报没命中）
ESC = re.compile(r"\x1b\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*")

# 本轮留给下一跑的预测（**由脚本判，不由我念**）：每条都是"那一跑应该/不应该印出这一串"。
# 这些预测**只对含 R586 那一笔的跑**有意义：上一轮的跑里那些字符串还不存在，
# 报"不中"就是把「还没落到那棵树」读成「那条判定是假的」（R555/R565 那一族的另一种形态）。
# 所以每条都带 `since`，不匹配的跑一律打印成 `不适用`。
def _my_shas():
    """本轮那一笔（或那几笔）的 sha 从文件里读：把 sha 抄进代码就等于抄一份会腐烂的常量。"""
    path = os.path.join(TMP, "my_shas.txt")
    if not os.path.exists(path):
        return set()
    return {l.strip()[:7] for l in io.open(path, encoding="utf-8") if l.strip() and not l.startswith(u"#")}


R586_SHAS = _my_shas()
PREDICTIONS = [
    (u"BAKE 出处=无（工作基线仍是 R586 之前烤的旧文档，本轮没跑 update）", u"R586",
     lambda g: any(l.startswith(u"FRAME_BASELINE_BAKE 出处=无") for l in g)),
    (u"BAKE_PROVENANCE=absent 具名", u"R586",
     lambda g: any(l.startswith(u"FRAME_BASELINE_BAKE_PROVENANCE=absent") for l in g)),
    (u"同批0（缺出处不许被默认成此刻这一笔 —— 这正是 M1543 钉的那条）", u"R586",
     lambda g: any(l.startswith(u"FRAME_BASELINE_RESULT=") and u"同批0" in l for l in g)),
    (u"不许出现 SAME_BAKE（runner 上这一趟判的是旧文档，没有出处可言）", u"R586",
     lambda g: not any(l.startswith(u"FRAME_BASELINE_SAME_BAKE=") for l in g)),
    (u"STEP[11] 仍读 判=不判（署名仍是本机，runner 那份 by_machine 不存在 ⇒ 658 出路⑵ 仍没发生）", u"R586",
     lambda g: any(l.startswith(u"FRAME_BASELINE_DRIFT ") and u"判=不判" in l for l in g)),
    (u"HOVER_TIER 认不出档=0（1x 那批帧名里每对都带档位段）", u"R586",
     lambda g: True),   # 由 hover 那一步自己判，见下面 hover_checks
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


def classify(steps_out, rows, applies):
    lines = [l.strip() for l in (steps_out or "").splitlines()]
    concluded = [l for l in lines if re.search(r"⇒\s*(failure|success|skipped)\s*$", l)]
    if not concluded:
        return (u"未问", u"一个非空结论都没有（作业还在跑）⇒ 四种出口一条都不许选，整格 NOT-RUN；"
                        u"「STEP[11] 在列表里」不算到数（R557 那一课）", [], [])
    failed = [l for l in concluded if u"⇒ failure" in l]
    step11_red = any("STEP[11]" in l for l in failed)
    gate = [b for s, b in rows if GATE_STEP_IN in s]
    hover = [b for s, b in rows if s and (HOVER_STEP_IN in s or "ruler" in s.lower())]
    drift = [b for b in gate if re.match(r"FRAME_BASELINE_DRIFT (本机=|变帧=)", b)]
    bake = [b for b in gate if b.startswith("FRAME_BASELINE_BAKE")]
    result = [b for b in gate if b.startswith("FRAME_BASELINE_RESULT=")]
    same = [b for b in gate if b.startswith("FRAME_BASELINE_SAME_BAKE=")]
    evidence = drift + bake + result + same
    hit = []
    for label, since, test in PREDICTIONS:
        if not applies:
            hit.append(u"%s=不适用（那些格子住在本轮那一笔的树上）" % label)
        else:
            hit.append(u"%s=%s" % (label, u"中" if test(gate) else u"不中"))
    hover_rows = [b for b in hover if b.startswith(u"HOVER_TIER ")]
    hover_checks = u"HOVER_TIER 逐字=%s" % (u" ｜ ".join(hover_rows)[:200] or u"（那一步没印出这一行）")
    if not gate:
        return (u"出口·丙", u"通道没跑：STEP[11] 有结论而门那一行取不到 ⇒ 先读 executed= 与全部失败步骤。"
                      u"逐字步骤：%s" % u" / ".join(failed), evidence, hover_checks)
    if same:
        return (u"同批", u"那一跑读到了 SAME_BAKE ⇒ 有人在这棵树上烤过基线并拿同一批帧来判（660 那一支）；"
                    u"预测逐条对拍：%s" % u"、".join(hit), evidence, hover_checks)
    verdict = (u"出口·乙" if any(u"判=不判" in l for l in drift) else u"出口·甲")
    return (verdict, u"%s ⇒ 预测逐条对拍：%s；STEP[11]=%s"
            % (u" ｜ ".join(sorted({l.split()[1] + u"…" for l in drift})) or u"（没有 DRIFT 行）", u"、".join(hit),
               u"红" if step11_red else u"没红"), evidence, hover_checks)


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
            try:
                _out, err2 = proc.communicate(timeout=900)
                log_rc = proc.returncode
            except subprocess.TimeoutExpired:
                log_rc = -1
        else:
            log_rc, err2 = 0, u""
        size = os.path.getsize(log) if os.path.exists(log) else 0
        rows = parse_log(log)
        applies = (sha in R586_SHAS)
        hit, disp, evidence, hover_checks = classify(steps, rows, applies)
        report[run] = {"sha": sha, "note": note, "steps_rc": rc,
                       "steps": (steps or err).strip()[:1400], "log_rc": log_rc, "log_bytes": size,
                       u"出口": hit, u"处置": disp, u"门那一步的逐字读数": evidence[:8],
                       u"hover": hover_checks,
                       u"红名单": sorted({m.group(1) for s, b in rows
                                        for m in [re.match(
                                            r"Test Case '-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\]' failed", b)] if m}),
                       u"D12登记": [b for s, b in rows if b.startswith("D12_SHAPE_SCAN_REGISTRY ")][:1],
                       u"探针": [b for s, b in rows if b.startswith("PROBE_COVERAGE_SUMMARY")][:1]}
    with io.open(os.path.join(TMP, "ci_readings.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    for run, sha, _note in PAIRS:
        item = report[run]
        print(u"RUN=%s ↔ %s 出口=%s 日志=%d 字节(rc=%s)" % (run, item["sha"], item[u"出口"],
              item["log_bytes"], item["log_rc"]))
        print(u"  处置=%s" % item[u"处置"][:520])
        print(u"  步骤=%s" % u" / ".join(l.strip() for l in item["steps"].splitlines() if u"⇒" in l)[:300])
        for line in item[u"门那一步的逐字读数"]:
            print(u"  逐字=%s" % line[:240])
        print(u"  hover=%s" % item[u"hover"][:240])
        print(u"  红名=%s" % u" ".join(item[u"红名单"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
