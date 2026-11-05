# -*- coding: utf-8 -*-
"""R587 的 ⓪：读三跑，并把 R586 交给本轮的六条预测**由脚本判**（不许目测对拍）。

三条老规矩照用：自己 `gh run view --log` 落盘再切（`readings` 每通道只采样）、
按**步骤**归属（自测那一步印的是合成树）、按**行首**匹配（CI 会 echo 自己的脚本行）。

本轮补两条（都是被自己的读数逼出来的，见台账 ⑨）：
· 步骤名退化成 `UNKNOWN STEP` 时，**机器键不足以**分开真门与电池合成树 —— 电池的模拟行故意用
  `本机=基线署名=github-runner`。能分开的是「基线署名 == 那一笔提交里 `docs/frame_baseline.json`
  自己署的那台机器」，这条判别比按步骤切**更弱**，所以逐字说出来，不悄悄当等价。
· 预测**不许有恒真的**：`HOVER_TIER` 那一条第一版写成 `lambda g: True`（因为那条通道不在 gate 集合里），
  那是把「我没接上」写成「它中了」⇒ 现在把通道交给预测本身，取不到行就报「未读到」而不是「中」。

两套编号仍然分开：
· **出口·甲/乙/丙/丁** = 今天这一维有没有人判；
· **658/659/660 各自的三条出路** = 将来怎么办。读到某个出口 ≠ 某条出路成立。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = "/tmp/r587"
PAIRS = [("42118421683", "0b39576", u"R586 主笔：基线出处 + 同批判定"),
         ("42119000322", "7837e00", u"R586 补记笔：只带台账"),
         ("42108062173", "ba093be", u"R585 补记笔：R586 记的是未到数，本轮现读")]
# R586 那六条预测只对**含 R586 那一笔的树**有意义
R586_SHAS = {u"0b39576", u"7837e00"}
GATE_STEP_IN = "Frame baseline vs working manifest"
ESC = re.compile(r"\x1b\[[0-9;]*m")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*")

PREDICTIONS = [
    (u"BAKE 出处=无（工作基线仍是旧文档，R586/R587 都没跑 update 到它）",
     lambda g, t: any(l.startswith(u"FRAME_BASELINE_BAKE 出处=无") for l in g)),
    (u"BAKE_PROVENANCE=absent 具名",
     lambda g, t: any(l.startswith(u"FRAME_BASELINE_BAKE_PROVENANCE=absent") for l in g)),
    (u"结论行末格 同批0",
     lambda g, t: any(l.startswith(u"FRAME_BASELINE_RESULT=") and u"同批0" in l for l in g)),
    (u"不许出现 SAME_BAKE",
     lambda g, t: not any(l.startswith(u"FRAME_BASELINE_SAME_BAKE=") for l in g)),
    (u"仍读 判=不判（runner 那份 by_machine 不存在 ⇒ 658 出路⑵ 没发生）",
     lambda g, t: any(l.startswith(u"FRAME_BASELINE_DRIFT ") and u"判=不判" in l for l in g)),
    # ⚠ 这一条第一版写的是 `lambda g: True` —— 那是一把**永远中**的尺（R565 那一族：恒真门）。
    # 它之所以被写成 True，是因为 HOVER_TIER 那行不在 `gate` 集合里；正确做法是把通道交给它，不是放行。
    (u"HOVER_TIER 认不出档=0",
     lambda g, t: (any(u"认不出档=0" in l for l in t) if t else None)),
]

# R587 交给 R588 的三条预测（**下一轮由脚本判**，不许目测对拍；今天这一跑还没有它们，因为代码还没推）。
# 形状与 PREDICTIONS 一致：`test(gate, tier)` ⇒ True=中 / False=不中 / None=未读到。
PREDICTIONS_R588 = [
    (u"SCALE_NOT_RUN 是这一支唯一出口（不许出现第二条「不判」通道名）",
     lambda g, t: (not any(l.startswith(u"FRAME_BASELINE_SCALE_AMBIGUOUS") or
                           l.startswith(u"FRAME_BASELINE_SCALE_TIE_NOT_JUDGED") for l in g))
                  and any(l.startswith(u"FRAME_BASELINE_SCALE_NOT_RUN=") for l in g)),
    (u"BAKE 那一行必须带四个新格子（倍率分布=/不一致帧数=/无尺寸段=/原因=）",
     lambda g, t: any(l.startswith(u"FRAME_BASELINE_BAKE ") and
                      all(k in l for k in (u"倍率分布=", u"不一致帧数=", u"无尺寸段=", u"原因=")) for l in g)),
    (u"既有字段含义一字未改：非并列批次的 capture_scale 仍等于该批众数（分布形如 <倍率>:N 且 原因=ok）",
     lambda g, t: any(l.startswith(u"FRAME_BASELINE_BAKE ") and
                      (u"原因=ok" in l or u"原因=（无）" in l) for l in g)),
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


DEGRADED_NOTE = [u""]


def step_attr_degraded(rows):
    """步骤名这一格退化没有？GitHub 的日志在某些 run 里把**每一行**都标成 `UNKNOWN STEP`
    （技能文档里那条：同一台机器同一个仓库不同 run 实测到两种形态）。
    那时 `按步骤名过滤` 恒 0 行，而通道其实跑了 36 行 —— 把 0 行读成"没跑"就是第三种坏法。
    """
    names = {s for s, _b in rows}
    if names and names == {u"UNKNOWN STEP"}:
        return True
    return any(s == u"UNKNOWN STEP" for s, _b in rows) and not any(
        GATE_STEP_IN in s for s in names)


def baseline_signature_at(sha):
    """那一笔提交里 `docs/frame_baseline.json` 自己署的那台机器（真门与电池合成树的判别锚）。"""
    proc = subprocess.Popen(["git", "show", "%s:docs/frame_baseline.json" % sha], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
    out = proc.communicate()[0]
    try:
        return json.loads(out).get("machine") or u""
    except ValueError:
        return u""


def classify(steps_out, rows, applies, sha=u""):
    lines = [l.strip() for l in (steps_out or "").splitlines()]
    concluded = [l for l in lines if re.search(r"⇒\s*(failure|success|skipped)\s*$", l)]
    if not concluded:
        return (u"未问", u"一个非空结论都没有（作业还在跑）⇒ 四种出口一条都不许选，整格 NOT-RUN；"
                        u"「STEP[11] 在不在列表里」不算到数（R557 那一课）", [], u"")
    failed = [l for l in concluded if u"⇒ failure" in l]
    step11_red = any("STEP[11]" in l for l in failed)
    degraded = step_attr_degraded(rows)
    gate = [b for s, b in rows if GATE_STEP_IN in s]
    if not gate and degraded:
        # 退化那一支：改按**判据自己印的通道串**取正文（技能文档第 3 步的出路），并把这个降级说出来，
        # 否则"我按步骤名没找到"会被下一轮读成"那一步没跑"。
        all_lines = [b for _s, b in rows
                     if b.startswith(("FRAME_BASELINE_DRIFT ", "FRAME_BASELINE_RESULT=",
                                      "FRAME_BASELINE_BAKE", "FRAME_BASELINE_SAME_BAKE=",
                                      "FRAME_BASELINE_SCALE", "FRAME_BASELINE_AGAINST=",
                                      "FRAME_BASELINE_CHANGED=", "FRAME_BASELINE_MISSING=",
                                      "FRAME_BASELINE_ADDED=", "FRAME_BASELINE_COMPARED=",
                                      "FRAME_BASELINE_OWNER=", "FRAME_BASELINE_MACHINE=",
                                      "FRAME_BASELINE_REGISTRY_DIGEST=",
                                      "FRAME_BASELINE_DRIFT_REGISTRY="))]
        # ⚠ 第二层陷阱（本轮现读到的，比上一版写的更强）：电池那一步**也会**印 `本机=github-runner`
        # —— `test_frame_baseline.py` 的「手抄一行 machine=github-runner」那一支故意用这台机器的键做模拟，
        # 所以"机器键含 github-runner"根本分不开真门与合成树，上一版据此报出的四行 DRIFT 全是电池行。
        # 能分开的是**基线署名**：真门读的是那一笔提交里 `docs/frame_baseline.json` 自己署的那台机器，
        # 合成树把 `本机` 与 `基线署名` 都填成 github-runner。这是一条比按步骤切**更弱**的判别，所以要说出来。
        sig = baseline_signature_at(sha)
        drift_all = [b for b in all_lines if b.startswith(u"FRAME_BASELINE_DRIFT ")]
        gate = [b for b in all_lines
                if (not b.startswith(u"FRAME_BASELINE_DRIFT "))
                or (sig and (u"基线署名=%s " % sig) in b)]
        DEGRADED_NOTE[0] = (u"按「基线署名=%s」筛 DRIFT 行：电池/真门分开（合成树 %d 行被排除，DRIFT 共 %d 行）；"
                            u"其余通道串（BAKE/RESULT/…）在退化日志里**仍然分不开**，那几条预测只能算「在合并集合上判」"
                            % (sig or u"（读不到）",
                               sum(1 for b in drift_all if sig and (u"基线署名=%s " % sig) not in b),
                               len(drift_all)))
    drift = [b for b in gate if re.match(r"FRAME_BASELINE_DRIFT (本机=|变帧=)", b)]
    bake = [b for b in gate if b.startswith("FRAME_BASELINE_BAKE")]
    result = [b for b in gate if b.startswith("FRAME_BASELINE_RESULT=")]
    same = [b for b in gate if b.startswith("FRAME_BASELINE_SAME_BAKE=")]
    scale = [b for b in gate if b.startswith("FRAME_BASELINE_SCALE")]
    evidence = drift + bake + scale + result + same
    hit = []
    tier = [b for s, b in rows if b.startswith(u"HOVER_TIER ")]
    for label, test in PREDICTIONS:
        if not applies:
            hit.append(u"%s=不适用（那些格子住在 R586 那一笔的树上）" % label)
        else:
            state = test(gate, tier)
            hit.append(u"%s=%s" % (label, u"中" if state is True else
                                   (u"不中" if state is False else u"未读到（那条通道今天没有行）")))
    if not gate:
        return (u"出口·丙", u"通道没跑：STEP[11] 有结论而门那一行取不到（步骤名退化=%s）⇒ 先读 executed= 与全部失败步骤。"
                u"逐字步骤：%s" % (u"是" if degraded else u"否", u" / ".join(failed)),
                evidence, u" ｜ ".join(tier)[:200])
    if degraded:
        return (u"出口·乙（步骤名退化）" if any(u"判=不判" in l for l in drift) else u"出口·甲（步骤名退化）",
                u"⚠ 这一跑的日志里步骤名恒为 `UNKNOWN STEP` ⇒ 正文是按**通道串 + 机器键**取的"
                u"（%s；技能文档第 3 步那条出路的加强版，判别比按步骤切**更弱**，所以单独说一句），" % DEGRADED_NOTE[0] +
                u"不是按步骤名；把「按步骤过滤 0 行」读成「那一步没跑」是第三种坏法。"
                u"STEP[11]=%s ⇒ 预测逐条对拍：%s"
                % (u"红" if step11_red else u"没红", u"、".join(hit)),
                evidence, u" ｜ ".join(tier)[:200] or u"（退化那一支里 HOVER_TIER 也按通道串取）")
    verdict = (u"出口·乙" if any(u"判=不判" in l for l in drift) else u"出口·甲")
    if same:
        verdict = u"同批（660 出路 ⑴/⑵ 被走了）"
    return (verdict, u"STEP[11]=%s ⇒ 预测逐条对拍：%s" % (u"红" if step11_red else u"没红", u"、".join(hit)),
            evidence, u" ｜ ".join(tier)[:200] or u"（那一步没印 HOVER_TIER）")


def main():
    if not os.path.isdir(TMP):
        os.mkdir(TMP)
    report = {}
    for run, sha, note in PAIRS:
        rc, steps, err = sh(["python3", "scripts/ci_read.py", "steps", run])
        rc2, latest, _e = sh(["python3", "scripts/ci_read.py", "latest", "--workflow", "CI"])
        status_line = u""
        for l in (steps or u"").splitlines():
            if l.startswith("RUN="):
                status_line = l.strip()
        log = os.path.join(TMP, "log_%s.txt" % run)
        log_rc = 0
        if not os.path.exists(log) or os.path.getsize(log) == 0:
            proc = subprocess.Popen(["gh", "run", "view", run, "--log"], cwd=ROOT,
                                    stdout=open(log, "w"), stderr=subprocess.PIPE,
                                    universal_newlines=True)
            try:
                _o, _e2 = proc.communicate(timeout=900)
                log_rc = proc.returncode
            except subprocess.TimeoutExpired:
                log_rc = -1
        size = os.path.getsize(log) if os.path.exists(log) else 0
        rows = parse_log(log)
        hit, disp, evidence, tier = classify(steps, rows, sha in R586_SHAS, sha)
        report[run] = {"sha": sha, "note": note, "steps_head": status_line,
                       "steps": (steps or err).strip()[:1400], "log_rc": log_rc, "log_bytes": size,
                       u"出口": hit, u"处置": disp, u"门那一步的逐字读数": evidence[:8],
                       u"hover": tier,
                       u"红名单": sorted({m.group(1) for s, b in rows
                                        for m in [re.match(
                                            r"Test Case '-\[[A-Za-z0-9_.]+ ([A-Za-z0-9_]+)\]' failed", b)] if m}),
                       u"D12登记": [b for s, b in rows if b.startswith("D12_SHAPE_SCAN_REGISTRY ")][:1],
                       u"探针": [b for s, b in rows if b.startswith("PROBE_COVERAGE_SUMMARY")][:1]}
    report[u"PREDICTIONS_R588"] = [label for label, _t in PREDICTIONS_R588]
    with io.open(os.path.join(TMP, "ci_readings.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    for run, sha, note in PAIRS:
        item = report[run]
        print(u"RUN=%s ↔ %s 出口=%s 日志=%d 字节(rc=%s) 头行=%s"
              % (run, item["sha"], item[u"出口"], item["log_bytes"], item["log_rc"], item["steps_head"]))
        print(u"  处置=%s" % item[u"处置"][:600])
        print(u"  步骤=%s" % u" / ".join(l.strip() for l in item["steps"].splitlines() if u"⇒ failure" in l)[:300])
        for line in item[u"门那一步的逐字读数"][:4]:
            print(u"  逐字=%s" % line[:240])
        print(u"  hover=%s" % item[u"hover"][:200])
        print(u"  红名=%s" % u" ".join(item[u"红名单"]))
    print(u"\n交给 R588 的三条预测（写在 PREDICTIONS_R588，下一轮由脚本判；今天这一跑还没有它们 ⇒ 不判、不填数）：")
    for label, _test in PREDICTIONS_R588:
        print(u"  PRED_R588 %s" % label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
