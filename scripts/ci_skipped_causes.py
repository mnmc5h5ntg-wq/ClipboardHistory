#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R591 / 靶 1：把「这一步为什么没出声」做成两种**相反成因**，并各配一把会红的门。

为什么这一支存在（R590 ⑦/③ 那一格的更正，forward 不回头改历史）：
R590 读到 `42159254212` / `42159607721` 里 `STEP[10]–[14]` 全是 `skipped`，把那一格写成
「第③态 = 这一步本就没跑 ⇒ 这一维今天没人判」。监工本轮现读驳回去一半：那五步的 `skipped` 是
**被 STEP[9] 的红连带**（`ci.yml` 里那几步没有 `if: always()`），而"这台机器没对象"是**另一种**成因 ——
两种成因的修法相反（前者改接线顺序/条件，后者改名册/机器维度），并成一条就等于把"尺从没被调用"
读成"尺判了但没东西可判"（正是本仓库那条「读不到要拆成修法相反且有名字的几种出口」的第四次复发）。

两种模式（同一支脚本，读数都自带扫描面）：
  · `static`（默认，接进 CI ⇒ runner 上有读数）：扫 `ci.yml` 的步骤正文，
    **会印通道串的步骤 = 证据型步骤**；证据型步骤既没有 `if: always()`、又不在具名豁免名册里 ⇒ 红
    （`CI_EVIDENCE_STEP_SKIPPABLE`）。这条判的是"它有没有机会出声"，不判它今天响没响。
  · `run`（每轮由读取器拿 `gh run view --json jobs` 的那份步骤结论喂进来）：结论里有 `skipped`
    而**台账最新那一节没给它成因名字** ⇒ 红（`CI_SKIPPED_UNNAMED`）。名字用两个固定 token：
    `第③甲`=被上游红连带（这一步本就没跑），`第③乙`=跑了但这台机器没对象。

退出码：0=判过；1=有红；2=**没有对象**（`ci.yml` 读不到 / 步骤清单为空 / 一个证据型步骤都没认出）
—— 2 那一支单独印 `CI_SKIPPED_NOT_JUDGED=`，因为"扫描器看不见对象"与"没有违规"是两格账（R565/R589 同族）。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CI_YML = os.path.join(ROOT, ".github", "workflows", "ci.yml")
LEDGER = os.path.join(ROOT, "AGENT_STATE.md")

# 通道串的形状：全大写（≥4 字）紧跟 `=`。注释行与 YAML 的 `- name:` 行都靠这条来判"这一步印不印读数"。
CHANNEL_RE = re.compile(r"[A-Z][A-Z0-9_]{3,}=")
ALWAYS_RE = re.compile(r"(?m)^\s{8}if:\s+always\(")
CAUSE_JIA = u"第③甲"      # 被上游红连带 ⇒ 这一步本就没跑
CAUSE_YI = u"第③乙"       # 跑了，但这台机器没有对象

# 允许"没 always() 也不响"的证据型步骤：必须带**理由**，理由为空或步骤名不存在 ⇒ 算红而不是算豁免。
SILENT_ROSTER = os.path.join(ROOT, "docs", "ci_evidence_step_exemptions.json")


def read(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def split_steps(ci_text):
    """把 `jobs.*steps` 那一段切成 [{index, name, body, has_always}]。

    锚点用 `^      - name:`（六空格 + `- name:`），与文件里既有抽取一致；正文取到下一个 `- name:` 或
    `if:` 之外的下一个步骤头为止。**没有正文的步骤（只有一行 name）也算一步**，它印不出东西 ⇒ 非证据型。
    """
    heads = [(m.start(), m.group(1).strip().strip('"'))
             for m in re.finditer(r"(?m)^      - name: (.+)$", ci_text)]
    steps = []
    for i, (pos, name) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(ci_text)
        body = ci_text[pos:end]
        # 只看这一步自己的 `if:`（在它自己的块里，第一行之后、`run:` 之前那段）
        has_always = bool(ALWAYS_RE.search(body))
        steps.append({"index": i + 1, "name": name, "body": body, "always": has_always})
    return steps


def prints_channels(body):
    """正文里**真的**印通道串吗？注释行（`#` 开头）与 YAML 键行不算 —— 注释里提一个名字不等于这一步会印它。"""
    hits = []
    for line in body.split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("- name:"):
            continue
        if s.startswith("run:") or s.startswith("uses:") or s.startswith("timeout-") \
                or s.startswith("continue-on-error:") or s.startswith("if:"):
            continue
        if CHANNEL_RE.search(s):
            hits.append(s[:80])
    return hits


def load_exemptions(path=None):
    p = path or SILENT_ROSTER
    if not os.path.exists(p):
        return []
    try:
        rows = json.loads(read(p)).get("rows", [])
    except (ValueError, OSError):
        return None          # 名册读不出来 ⇒ 不许当成"没有豁免"
    return rows


def judge_static(ci_text, exemptions):
    steps = split_steps(ci_text)
    evidence = [s for s in steps if prints_channels(s["body"])]
    exempt_names = set()
    bad_rows = []
    for r in (exemptions or []):
        reason = (r.get("reason") or "").strip()
        nm = (r.get("name") or "").strip()
        if not reason or not nm:
            bad_rows.append(r)
        else:
            exempt_names.add(nm)
    silent = [s for s in evidence if not s["always"] and s["name"] not in exempt_names]
    # 豁免**必须真会命中**：名字不在现读的证据型步骤里、或那一步其实已经带 always() ⇒ 这条豁免是空的，
    # 空豁免比没豁免更坏（它让下一次"新增一个无声的证据步骤"看起来仍然合规）。R587 那条同形规矩。
    dead = []
    ev_names = set(s["name"] for s in evidence)
    always_names = set(s["name"] for s in evidence if s["always"])
    for nm in sorted(exempt_names):
        if nm not in ev_names:
            dead.append((nm, u"名字不在现读的证据型步骤里"))
        elif nm in always_names:
            dead.append((nm, u"那一步已经带 if: always() ⇒ 豁免是空的"))
    return {"steps": len(steps), "evidence": len(evidence),
            "always": sum(1 for s in evidence if s["always"]),
            "exempted": sum(1 for s in evidence if not s["always"] and s["name"] in exempt_names),
            "bad_rows": bad_rows, "silent": silent, "dead": dead}


def latest_section(ledger_text, round_tag):
    """只在**本轮那一节**里找成因名字 —— 全文找会命中历史节（R569 那一族的第 14 次预防）。"""
    m = re.search(r"(?m)^## %s 状态（" % re.escape(round_tag), ledger_text)
    if not m:
        return None
    nxt = re.search(r"(?m)^## R\d+ (状态|补记)", ledger_text[m.end():])
    return ledger_text[m.start(): m.end() + (nxt.start() if nxt else len(ledger_text) - m.end())]


def parse_steps_dump(text):
    """接受 `9 failure Release script tests` 这种行（`gh run view --json jobs` 的 to_entries 输出）。"""
    rows = []
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s+(\S+)\s+(.+)$", line)
        if m:
            rows.append({"index": int(m.group(1)), "conclusion": m.group(2), "name": m.group(3).strip()})
    return rows


def judge_run(rows, section_text):
    skipped = [r for r in rows if r["conclusion"] == "skipped"]
    unnamed = []
    for r in skipped:
        # 成因名字必须**与这一步在同一行里**（只写"今天有 skipped"不算具名）
        pat = u"%s" % r["index"]
        hit = False
        if section_text:
            for line in section_text.splitlines():
                if (CAUSE_JIA in line or CAUSE_YI in line) and (
                        pat in line or r["name"][:24] in line):
                    hit = True
                    break
        if not hit:
            unnamed.append(r)
    return {"skipped": len(skipped), "unnamed": unnamed,
            "conclusions": len(rows)}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ci_skipped_causes.py", description=__doc__.split("\n")[0])
    ap.add_argument("--mode", default="static", choices=["static", "run"])
    ap.add_argument("--ci", default=CI_YML)
    ap.add_argument("--steps", default="", help="run 模式：步骤结论清单文件（`index conclusion name`）")
    ap.add_argument("--ledger", default=LEDGER)
    ap.add_argument("--round", default="", help="run 模式：在台账哪一节里找成因名字（如 R591）")
    ap.add_argument("--exemptions", default=None)
    args = ap.parse_args(argv)

    if args.mode == "static":
        if not os.path.exists(args.ci):
            print(u"CI_SKIPPED_NOT_JUDGED=ci-missing %s ⇒ 扫描器没有对象，不许读成「所有证据步骤都会出声」"
                  % args.ci)
            return 2
        exemptions = load_exemptions(args.exemptions)
        if exemptions is None:
            print(u"CI_SKIPPED_NOT_JUDGED=exemptions-broken ⇒ 名册读不出来时不许当成「没有豁免」")
            return 1
        v = judge_static(read(args.ci), exemptions)
        print(u"CI_SKIPPED_CAUSES 步骤=%d 证据型=%d 带always=%d 具名豁免=%d 无声=%d 名册坏行=%d 空豁免=%d "
              u"口径=按 ci.yml 里 - name: 的顺序（与 GitHub 日志的 STEP[N] 相差 2）"
              % (v["steps"], v["evidence"], v["always"], v["exempted"], len(v["silent"]),
                 len(v["bad_rows"]), len(v["dead"])))
        for s in v["silent"]:
            print(u"  CI_EVIDENCE_STEP_SKIPPABLE 步=%d 名=%s ⇒ 上游一步红它就一行都不印；"
                  u"要么 `if: always()`，要么进 `docs/ci_evidence_step_exemptions.json` 并写理由"
                  % (s["index"], s["name"][:70]))
        for nm, why in v["dead"]:
            print(u"  CI_EVIDENCE_EXEMPT_DEAD 名=%s 因=%s ⇒ 空豁免比没豁免更坏（它让下一次新增无声步骤看起来仍合规）"
                  % (nm[:60], why))
        for r in v["bad_rows"]:
            print(u"  CI_EVIDENCE_EXEMPT_BADROW %s ⇒ 豁免必须同时有名字与理由，缺一个就当红" % json.dumps(r, ensure_ascii=False)[:120])
        if v["evidence"] == 0:
            print(u"CI_SKIPPED_NOT_JUDGED=no-evidence-step 证据型步骤=0 ⇒ 这把尺今天没看见对象，"
                  u"不许把「无声=0」读成「接线都对」")
            return 2
        if v["silent"] or v["bad_rows"] or v["dead"]:
            print(u"CI_SKIPPED_CAUSES_RESULT=red")
            return 1
        print(u"CI_SKIPPED_CAUSES_RESULT=ok")
        return 0

    # run 模式
    if not args.steps or not os.path.exists(args.steps):
        print(u"CI_SKIPPED_NOT_JUDGED=steps-missing ⇒ 没有步骤结论清单 ⇒ 这一格按未读到处理")
        return 2
    rows = parse_steps_dump(read(args.steps))
    if not rows:
        print(u"CI_SKIPPED_NOT_JUDGED=steps-empty 清单里一行都没解析出来 ⇒ 不许读成「没有 skipped」")
        return 2
    tag = args.round
    if not tag and os.path.exists(args.ledger):
        m = re.search(r"(?m)^## (R\d+) 状态（", read(args.ledger))
        tag = m.group(1) if m else u""
    if not tag:
        print(u"CI_SKIPPED_NOT_JUDGED=round-tag-missing ⇒ 不知道要在哪一节找成因名字，就不许判")
        return 2
    section = latest_section(read(args.ledger), tag) if os.path.exists(args.ledger) else None
    if section is None:
        print(u"CI_SKIPPED_NOT_JUDGED=ledger-section-missing 节=%s ⇒ 找不到本轮那一节就不许判" % tag)
        return 2
    v = judge_run(rows, section)
    print(u"CI_SKIPPED_CENSUS 节=%s 步骤结论=%d skipped=%d 未具名=%d"
          % (tag, v["conclusions"], v["skipped"], len(v["unnamed"])))
    for r in v["unnamed"]:
        print(u"  CI_SKIPPED_UNNAMED 步=%d 名=%s ⇒ skipped 而没有成因名字（%s=被上游红连带 / %s=跑了但本机没对象）"
              % (r["index"], r["name"][:70], CAUSE_JIA, CAUSE_YI))
    if v["unnamed"]:
        print(u"CI_SKIPPED_CAUSES_RESULT=red")
        return 1
    print(u"CI_SKIPPED_CAUSES_RESULT=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
