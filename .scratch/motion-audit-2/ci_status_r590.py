# -*- coding: utf-8 -*-
"""R590 的 ⓪：接线的第一证人 —— 三条以上都要**分开**回答"跑没跑到、有没有行"。

R589 把三条形状守卫接进 CI 的打印步骤，但它自己那一跑签不了自己。所以本笔的 ⓪ 不是"看红没红"，
而是回答派单点名的那三种情形，而且**分开记**：
  ①跑到了那一步、且印出了结论行        ⇒ 有读数（这一维从此有外部证人）
  ②跑到了那一步、却没印出结论行        ⇒ `SHAPE_GUARD_READING_MISSING` 那一支**应该**当场拦；
                                        它没拦而整步静过 ⇒ 这就是本轮的真缺陷（接线是假的）
  ③根本没跑到那一步（更早的步骤红了）  ⇒ 具名 `CI_STEP_NOT_RUN`，不许写成"接上了"
取处一律写进步骤名 + 通道前缀（R588 缺第三格、R589 补成第四格，这里沿用四格写法）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, ".scratch", "motion-audit-2"))
TMP = "/tmp/r590"
if not os.path.isdir(TMP):
    os.mkdir(TMP)

from ci_status_r589 import PREDICTIONS_R590      # 标签/判法/取处三格逐字接过来   # noqa: E402

PAIRS = [("42159254212", "5fcac1c", u"R589 主笔：分支穷尽 + 守卫认 if 链 + 副本名册"),
         ("42159607721", "f477d96", u"R589 补记笔：⓪ 成对号 + 落盘后门复算")]

# R591 的 ⓪ 从这里接：**四条都要有判法与取处**，不许只留散文（R588 缺第三格、R589 补成第四格）。
# 第四格 = 这条通道究竟由哪一步、以什么方式印出去；只在测试里被调用的守卫在 runner 上没有读数。
PREDICTIONS_R591 = [
    {u"主张": u"STEP[9] 里 `FAIL:` 四条红名**少掉**本轮修的那三条（`unmatched_corpus` / `working_corpus` / "
              u"`rows_from_another_machine`），`test_skip_roster` 那条借红要么消失要么只剩内层新红 ⇒ "
              u"本轮 ③ 那三条落地的**唯一**外部证人",
     u"取处": u"步骤名 `Release script tests` 的正文行（按 `FAIL:` 前缀数）",
     u"判法": lambda g: sum(1 for l in g if l.startswith(u"FAIL:") and any(
         n in l for n in (u"unmatched_corpus", u"working_corpus_either_judges",
                          u"rows_from_another_machine"))) <= 0},
    {u"主张": u"STEP[9] 里 `SHAPE_GUARD_EXIT … rc=<数字>` 与 `IDENTICAL_WITNESS_EXIT=<数字>` **读得到值** ⇒ "
              u"本轮把值槽与说明分开那一格的外部证人（读不到就是还没修好，或 runner 把新形状也弄坏了）",
     u"取处": u"步骤名 `Release script tests` 里以 SHAPE_GUARD_EXIT / IDENTICAL_WITNESS_EXIT 开头的行",
     u"判法": lambda g: len([l for l in g if re.search(u"rc=\\d", l)]) >= 2
                       and len([l for l in g if l.startswith(u"IDENTICAL_WITNESS_EXIT=")
                                and re.search(u"=\\d", l)]) >= 1},
    {u"主张": u"STEP[9] 里出现 `WITNESS_SCAN_SCOPE … swift文件=` 且那个数 >0 ⇒ 靶 1 那一维第一次在 runner 上有扫描面读数",
     u"取处": u"步骤名 `Release script tests` 里以 WITNESS_SCAN_SCOPE 开头的行",
     u"判法": lambda g: any(int(re.search(u"swift文件=(\\d+)", l).group(1)) > 0
                            for l in g if u"swift文件=" in l)},
    {u"主张": u"STEP[11]（Frame baseline vs working manifest）这次**跑到了**（不是 skipped），并且里面出现 "
              u"`FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` ⇒ R589/R590 两跑都欠着的那第③态今天补齐",
     u"取处": u"步骤名含 `Frame baseline vs working manifest` 的那一步里以 FRAME_BASELINE_SCALE_ 开头的行",
     u"判法": lambda g: any(l.startswith(u"FRAME_BASELINE_SCALE_BASELINE_UNKNOWN=") for l in g)},
]

# 本轮真正要答的那一格：这几条通道在 `Release script tests` 里出现了吗
WIRE_CHANNELS = (u"SHAPE_GUARD_EXIT", u"TIER_SHAPE_RESULT", u"STAGE_GATE_RESULT",
                 u"IDENTICAL_WITNESS_EXIT", u"IDENTICAL_PAIR_RESULT",
                 u"SHAPE_GUARD_READING_MISSING", u"TIER_BRANCH_BLIND",
                 u"IDENTICAL_WITNESS_NOT_RUN", u"IDENTICAL_WITNESS_READING_MISSING")


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def status_line(run):
    rc, out, err = sh([u"gh", u"run", u"view", run, u"--json", u"status,conclusion,headSha",
                       u"--jq", u'[.status,.conclusion,.headSha[0:7]]|join(" ")'])
    return (out or u"").strip() or u"（gh 读不到 ⇒ 这一格记未读到：%s）" % (err or u"")[:80]


def step_conclusions(run):
    rc, out, _e = sh([u"gh", u"run", u"view", run, u"--json", u"jobs",
                      u"--jq", u'.jobs[0].steps | map("\\(.conclusion) \\(.name)") | .[]'])
    if rc != 0:
        return {}
    got = {}
    for line in (out or u"").splitlines():
        parts = line.split(u" ", 1)
        if len(parts) == 2:
            got[parts[1].strip()] = parts[0].strip()
    return got


def fetch_log(run, tmp=None):
    log = os.path.join(tmp or TMP, "log_%s.txt" % run)
    if os.path.exists(log) and os.path.getsize(log) > 0:
        return log
    fetch = subprocess.Popen([u"gh", u"run", u"view", run, u"--log"], cwd=ROOT,
                             stdout=open(log, u"w"), stderr=subprocess.DEVNULL)
    try:
        fetch.communicate(timeout=900)
    except subprocess.TimeoutExpired:
        fetch.kill()
    return log


def lines_in_step(log, step_needle, prefixes):
    """按步骤名取正文，返回 (命中行数, 每个前缀的行数, 取处说明, **正文行本身**)。

    第四个返回值是给预测的判法用的 —— 判法要读**行**（`l.startswith("TIER_SHAPE_RESULT=ok")`），
    不能读前缀名；把前缀名喂给判法就等于把"我筛过"当成"它说了"，那正是 R588 ⑤·(a) 的同一个洞。
    """
    if not os.path.exists(log):
        return 0, {}, u"日志不在盘上 ⇒ 未读到", []
    hits = 0
    per = {}
    lines = []
    degraded = False
    for raw in io.open(log, encoding="utf-8", errors="replace"):
        parts = raw.rstrip(u"\n").split(u"\t")
        if len(parts) < 3:
            continue
        if parts[1] == u"UNKNOWN STEP":
            degraded = True
        body = re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*", u"", parts[2])
        # **先剥 ANSI 再锚定**：runner 的行是 `<时间戳>Z ^[[37;1mFAIL: …`，
        # 带着色码去 `startswith("FAIL:")` 会恒假 ⇒ 空集合让"红名少掉三条"变成**空真**（R591 ⓪ 实测到的一处假中）。
        body = re.sub(u"\x1b\\[[0-9;]*m", u"", body).strip()
        for p in prefixes:
            if body.startswith(p):
                per[p] = per.get(p, 0) + 1
                lines.append(body)
                if step_needle in parts[1]:
                    hits += 1
    how = (u"按步骤名 `%s` 命中 %d 行%s；按前缀筛到的正文行 %d 条" % (
        step_needle, hits,
        u"（步骤名本次退化成 UNKNOWN STEP ⇒ 只能按通道串在全跑里数）" if degraded else u"",
        len(lines)))
    return hits, per, how, lines


def main():
    report = {}
    for run, sha, note in PAIRS:
        rc, steps, err = sh([u"python3", u"scripts/ci_read.py", u"steps", run])
        item = {u"sha": sha, u"备注": note, u"status行": status_line(run),
                u"失败步骤": [l.strip() for l in (steps or u"").splitlines() if u"⇒ failure" in l],
                u"逐步骤结论": step_conclusions(run)}
        item[u"到数"] = u"是" if u"in_progress" not in item[u"status行"] else (
            u"否（status=in_progress ⇒ 这一跑**未读**：作业还没走完，"
            u"部分步骤已有 conclusion 不等于整跑结论，R588 第 1 步那条）")
        if item[u"到数"] != u"是":
            report[run] = item
            continue
        log = fetch_log(run)
        item[u"log_bytes"] = os.path.getsize(log) if os.path.exists(log) else 0
        if item[u"log_bytes"] == 0:
            # 0 字节 = 通道里还没有内容，不等于内容里没有（三种坏法的第一种，R470）。
            item[u"接线三态"] = u"未读到（`CI_LOG_EMPTY=not-finished`）⇒ 三态一条都不判"
            item[u"WIRE_HOW"] = u"日志 0 字节 ⇒ 没有正文可数"
            report[run] = item
            continue
        step_status = item[u"逐步骤结论"].get(u"Release script tests", u"（读不到）")
        hits, per, how, _lines = lines_in_step(log, u"Release script tests", WIRE_CHANNELS)
        if step_status in (u"success", u"failure"):
            item[u"接线三态"] = (u"②跑到了那一步但一条结论行都没印 ⇒ 接线的证人没到手"
                                 if hits == 0 else
                                 u"①跑到了且印出了结论行（见 WIRE_READINGS）")
        else:
            item[u"接线三态"] = u"③根本没跑到那一步（`CI_STEP_NOT_RUN`）⇒ 不许写「接上了」"
        item[u"WIRE_READINGS"] = dict(per)
        item[u"WIRE_HOW"] = how
        preds = []
        for spec in PREDICTIONS_R590:
            claim = spec[u"主张"]
            if claim.startswith(u"STEP[11]"):
                needle, prefixes = u"Frame baseline vs working manifest", (u"FRAME_BASELINE_SCALE",)
            elif u"TIER_SHAPE" in claim:
                # 判法要读两类行（`TIER_SHAPE_RESULT=ok` 与 `TIER_BRANCH_SCAN 分支链=`），
                # 第一版只筛了 `TIER_SHAPE_` ⇒ 把"我的筛面窄"读成"预测不中"（R588 ⑤·(a) 同一族的第三种坏法）。
                needle, prefixes = u"Release script tests", (u"TIER_",)
            elif u"STAGE_GATE" in claim:
                needle, prefixes = u"Release script tests", (u"STAGE_GATE_",)
            elif u"IDENTICAL_PAIR_RESULT" in claim:
                needle, prefixes = u"Release script tests", (u"IDENTICAL_PAIR_",)
            else:
                needle, prefixes = u"Release script tests", (u"SHAPE_GUARD_EXIT",)
            _h, _per, how2, lines = lines_in_step(log, needle, prefixes)
            # 判法给 False 的前提是"那一步真的跑过、正文里确实没有"。步骤本身没跑到（skipped/读不到）
            # 时不许判"不中" —— 那是把缺证据冒充成反证（R557/R588 第 4 步那条）。
            ran = any(needle in k and v in (u"success", u"failure")
                      for k, v in item[u"逐步骤结论"].items())
            if not ran:
                preds.append([claim[:78], u"未读到（`CI_STEP_NOT_RUN` ⇒ 那一步没跑到，不判中/不中）",
                              u"%s ｜ %s" % (needle, how2)])
                continue
            try:
                ok = spec[u"判法"](lines)
            except Exception as e:
                ok = u"判法抛了：%s" % e
            if ok is False and u"rc=0" in claim:
                # False 有两种：真读了个 rc≠0，与**值槽被日志通道打死**（`rc=` 后面不是数字）。
                # 把后者写成"不中"就是拿缺证据冒充反证 ⇒ 这里分开。
                glued = [l for l in lines if u"rc=" in l and not re.search(u"rc=\d", l)]
                if glued:
                    ok = u"读不到值（值槽被日志通道打死：`%s`）⇒ 不判中/不中" % glued[0][:78]
            preds.append([claim[:78], (u"中" if ok is True else (u"不中" if ok is False else ok)),
                          u"%s ｜ %s" % (needle, how2)])
        item[u"预测"] = preds
        report[run] = item

    out = []
    for run, it in report.items():
        out.append(u"RUN=%s ↔ %s 到数=%s status=%s" % (run, it[u"sha"], it[u"到数"], it[u"status行"]))
        out.append(u"  失败步骤=%s" % (u" | ".join(it.get(u"失败步骤", [])) or u"（没有/未读到）"))
        for nm in (u"Release script tests", u"Frame baseline vs working manifest (fixture-set gate)",
                   u"On-screen probe coverage floor", u"Swift tests (executed-count gate)"):
            out.append(u"  逐步骤结论 %-58s ⇒ %s" % (nm, it[u"逐步骤结论"].get(nm, u"（读不到）")))
        if u"接线三态" in it:
            out.append(u"  接线三态：%s" % it[u"接线三态"])
            out.append(u"  结论行计数（按前缀）=%s" % json.dumps(it[u"WIRE_READINGS"], ensure_ascii=False))
            out.append(u"  取处：%s" % it[u"WIRE_HOW"])
        for pv in it.get(u"预测", []):
            out.append(u"  预测=%s ⇒ %s〔%s〕" % (pv[0], pv[1], pv[2]))
    text = u"\n".join(out)
    io.open(os.path.join(TMP, "ci_status.txt"), u"w", encoding=u"utf-8").write(text + u"\n")
    io.open(os.path.join(TMP, "ci_readings.json"), u"w", encoding=u"utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    print(text)
    return 0


if __name__ == u"__main__":
    sys.exit(main())
