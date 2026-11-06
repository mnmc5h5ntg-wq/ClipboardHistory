# -*- coding: utf-8 -*-
"""R589 的 ⓪：现读两对 + 把 R588 交下来的三条预测**由脚本判**，每条都带「正文从哪一步取」那一格。

R588 ⑤·(a) 那条自伤的规矩在这一跑落地成形状：一条预测要带**三格** ——
①主张（内容）②判法（布尔）③**正文从哪一步/哪条通道取，取不到时报「未读到」**。
上一轮我只写了前两格，于是 `SCALE_NOT_RUN` 那条被我在**门那一步**里找，而它 24 次全在电池那一步，
判出来一个"不中" —— 那是尺错，不是东西错，但它长得一模一样。所以这里的 `取处` 是必填参数，
`判法` 拿到的行集合就是 `取处` 筛出来的，不再是"整个跑拼一起"。

另两格照带：`ci_read.py latest` 只打最新一笔 ⇒ 逐跑 `gh run view --json`；
"不在失败步骤列表里" ≠ "跑过且绿" ⇒ 逐步骤结论另取一趟（R557）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, ".scratch", "motion-audit-2"))
TMP = "/tmp/r589"
if not os.path.isdir(TMP):
    os.mkdir(TMP)

from ci_status_r588 import PREDICTIONS_R589          # 标签逐字接过来，不重写合同   # noqa: E402

PAIRS = [("42139904001", "b8939ce", u"R588 主笔：第③段断言守卫 + 档位逐档点名 + 名册看整帧"),
         ("42142286963", "805e447", u"R588 补记笔：⓪ 到数三判 + 五刀末态")]

# 三条预测各自的「正文来源」—— 第三步是我上一轮漏的那一格
SCOPES = [
    {u"主张": PREDICTIONS_R589[0], u"取处": u"STEP[9] Release script tests 里以 TIER_SHAPE_ 开头的行",
     u"判法": lambda g: (any(l.startswith(u"TIER_SHAPE_SCAN") and
                             u"带return=0" in l and u"无可数格=0" in l for l in g)
                         and any(l.startswith(u"TIER_SHAPE_RESULT=ok") for l in g))},
    {u"主张": PREDICTIONS_R589[1], u"取处": u"STEP[9] Release script tests 里以 STAGE_GATE_ 开头的行",
     u"判法": lambda g: any(l.startswith(u"STAGE_GATE_RESULT=ok") for l in g)},
    {u"主张": PREDICTIONS_R589[2], u"取处": u"**整跑**里以 FRAME_STATE_STOPS / RUNG_STEP_TIER_COVERAGE 开头的行"
                            u"（这两条通道只在少档时才印 ⇒ 「一条都没有」才是绿，所以取处必须是全跑，不能只盯 STEP[9]）",
     u"判法": lambda g: not any(l.startswith((u"FRAME_STATE_STOPS", u"RUNG_STEP_TIER_COVERAGE")) for l in g)},
]


# 交给 R590 的四条预测：每条三格齐（主张 / 判法 / 正文从哪一步取）。R588 那一轮缺的就是第三格。
PREDICTIONS_R590 = [
    {u"主张": u"STEP[11]（Frame baseline vs working manifest）里**第一次**出现 "
              u"`FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` ⇒ 上一轮那条静默格从此在 runner 上有人出声",
     u"取处": u"步骤名含 `Frame baseline vs working manifest` 的那一步里以 FRAME_BASELINE_SCALE_ 开头的行",
     u"判法": lambda g: any(l.startswith(u"FRAME_BASELINE_SCALE_BASELINE_UNKNOWN=") for l in g)},
    {u"主张": u"STEP[9] 里 `TIER_SHAPE_RESULT=ok` 且 `TIER_BRANCH_SCAN 分支链=` 的数字 ≥2 ⇒ "
              u"新加的 R3 那一维第一次在 runner 上有读数行（从前它的 print 全被测试吞在 StringIO 里）",
     u"取处": u"步骤名 `Release script tests` 里以 TIER_ 开头的行",
     u"判法": lambda g: (any(l.startswith(u"TIER_SHAPE_RESULT=ok") for l in g)
                         and any(l.startswith(u"TIER_BRANCH_SCAN") and int(re.search(u"分支链=(\\d+)", l).group(1)) >= 2
                                 for l in g if l.startswith(u"TIER_BRANCH_SCAN") and u"分支链=" in l))},
    {u"主张": u"STEP[9] 里出现 `IDENTICAL_PAIR_RESULT=`（ok 或 not-run 都算出声）⇒ 638② 那条新守卫在 runner 上"
              u"第一次有自己的行；**没有这一行就是接线没跑起来**，不许读成「这台机器没有副本」",
     u"取处": u"步骤名 `Release script tests` 里以 IDENTICAL_ 开头的行",
     u"判法": lambda g: any(l.startswith(u"IDENTICAL_PAIR_RESULT=") for l in g)},
    {u"主张": u"STEP[9] 里 `SHAPE_GUARD_EXIT guard=… rc=0` 恰好两行 ⇒ 接线本身（而不是判据内容）的证人",
     u"取处": u"步骤名 `Release script tests` 里以 SHAPE_GUARD_EXIT 开头的行",
     u"判法": lambda g: sum(1 for l in g if l.startswith(u"SHAPE_GUARD_EXIT") and u" rc=0" in l) == 2},
]


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def status_line(run):
    rc, out, err = sh(["gh", "run", "view", run, "--json", "status,conclusion,headSha",
                       "--jq", '[.status,.conclusion,.headSha[0:7]]|join(" ")'])
    return (out or u"").strip() or u"（gh 读不到 ⇒ 这一格记未读到：%s）" % (err or u"")[:80]


def step_conclusions(run):
    """逐步骤结论（`steps` 视图只给失败的那些 ⇒ 判「跑没跑」必须看 jobs[].steps，R557）。"""
    rc, out, _e = sh(["gh", "run", "view", run, "--json", "jobs",
                      "--jq", '.jobs[0].steps | map("\\(.conclusion) \\(.name)") | .[]'])
    if rc != 0:
        return {}
    got = {}
    for line in (out or u"").splitlines():
        parts = line.split(u" ", 1)
        if len(parts) == 2:
            got[parts[1].strip()] = parts[0].strip()
    return got


def lines_of(log_path, step_needle, channel_prefixes):
    """按**步骤名**取正文；步骤名退化成 `UNKNOWN STEP` 时改按通道串在全跑里找，并把这件事说出来。"""
    if not os.path.exists(log_path):
        return [], u"日志不在盘上 ⇒ 未读到"
    degraded = False
    hits, all_lines = [], []
    for raw in io.open(log_path, encoding="utf-8", errors="replace"):
        parts = raw.rstrip(u"\n").split(u"\t")
        if len(parts) < 3:
            continue
        if parts[1] == u"UNKNOWN STEP":
            degraded = True
        body = re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*", u"", parts[2]).strip()
        body = re.sub(u"\x1b\\[[0-9;]*m", u"", body)
        all_lines.append(body)
        if not degraded and step_needle in parts[1]:
            if any(body.startswith(p) for p in channel_prefixes):
                hits.append(body)
    if hits:
        return hits, (u"按步骤名 `%s` 取到 %d 行" % (step_needle, len(hits)))
    # 步骤名不可用（或那一步正文里就是没有）⇒ 退到全跑按通道串筛，并**说出来**：这是一条更弱的取处
    loose = [l for l in all_lines if any(l.startswith(p) for p in channel_prefixes)]
    return loose, (u"按步骤名没取到 ⇒ 退化：全跑按通道串取到 %d 行（步骤名%s）"
                   % (len(loose), u"本次退化成 UNKNOWN STEP" if degraded else u"可用但正文里没有"))


def main():
    report = {}
    for run, sha, note in PAIRS:
        rc, steps, err = sh(["python3", "scripts/ci_read.py", "steps", run])
        status = status_line(run)
        concluded = [l for l in (steps or u"").splitlines()
                     if re.search(r"⇒\s*(failure|success|skipped)\s*$", l)]
        red_steps = [l.strip() for l in concluded if u"⇒ failure" in l]
        item = {u"sha": sha, u"备注": note, u"status行": status,
                u"结论行数": len(concluded), u"失败步骤": red_steps,
                u"逐步骤结论": step_conclusions(run)}
        if not concluded:
            item[u"到数"] = u"否（未到数 ⇒ 三条预测一条不判，R557）"
            report[run] = item
            continue
        item[u"到数"] = u"是"
        log = os.path.join(TMP, "log_%s.txt" % run)
        if not os.path.exists(log) or os.path.getsize(log) == 0:
            fetch = subprocess.Popen(["gh", "run", "view", run, u"--log"], cwd=ROOT,
                                     stdout=open(log, "w"), stderr=subprocess.DEVNULL)
            try:
                fetch.communicate(timeout=900)
            except subprocess.TimeoutExpired:
                fetch.kill()
        item[u"log_bytes"] = os.path.getsize(log) if os.path.exists(log) else 0
        verdicts = []
        for spec, prefixes in zip(SCOPES, ((u"TIER_SHAPE_",), (u"STAGE_GATE_",),
                                           (u"FRAME_STATE_STOPS", u"RUNG_STEP_TIER_COVERAGE"))):
            got, how = lines_of(log, u"Release script tests" if prefixes[0] != u"FRAME_STATE_STOPS" else u"",
                                prefixes)
            if not got and prefixes[0] != u"FRAME_STATE_STOPS":
                verdicts.append([spec[u"主张"], u"未读到（那条通道今天没有行）", how])
                continue
            ok = spec[u"判法"](got)
            verdicts.append([spec[u"主张"], (u"中" if ok else u"不中"), how])
            if prefixes[0] == u"FRAME_STATE_STOPS":
                verdicts[-1][1] = u"中" if ok else u"不中（那一档的帧没到，不是判据变了）"
        item[u"预测"] = verdicts
        report[run] = item

    out = []
    for run, item in report.items():
        out.append(u"RUN=%s ↔ %s 到数=%s status=%s" % (run, item[u"sha"], item[u"到数"], item[u"status行"]))
        out.append(u"  失败步骤=%s" % (u" | ".join(item[u"失败步骤"]) or u"（没有失败步骤）"))
        for name in (u"Release script tests", u"Frame baseline vs working manifest (fixture-set gate)",
                     u"On-screen probe coverage floor"):
            out.append(u"  逐步骤结论 %-56s ⇒ %s" % (name, item[u"逐步骤结论"].get(name, u"（读不到）")))
        for v in item.get(u"预测", []):
            out.append(u"  预测=%s ⇒ %s〔取处：%s〕" % (v[0][:52], v[1], v[2]))
    text = u"\n".join(out)
    io.open(os.path.join(TMP, "ci_status.txt"), "w", encoding="utf-8").write(text + u"\n")
    print(text)
    io.open(os.path.join(TMP, "ci_readings.json"), "w", encoding="utf-8").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == u"__main__":
    sys.exit(main())
