# -*- coding: utf-8 -*-
"""R146 / BACKLOG 186 · 文件通道那四条判据的变异对照（一次性仪器，不进登记表）。

为什么单独造一台临时树：`test_ui_probe_report.py` 里有两处**读仓库文件**的接线判据，
它们的 REPO 由 `parents[2]` 推出来 ⇒ 只拷 `scripts/` 会让那两格红在"找不到仓库"上，
而那种红说的是临时树的形状，不是被判的那条判据（R88 记过同一族：变异跑的临时树要与仓库同形）。
⇒ 这里把 `scripts/`、`.github/workflows/ci.yml`、那一个 Swift 测试文件按同形摆好。

四刀都是**往松里改**，所以每一刀都必须被至少一条测试抓住；漏一刀就说明那条判据是装饰。
"""
import shutil
import subprocess
import sys
import os
from pathlib import Path

REPO = Path("/Users/wangziyi/Codex_Project0")
SANDBOX = Path("/tmp/r146_mut")
TARGET = SANDBOX / "scripts" / "ui_probe_report.py"

# (编号, 说明, 原串, 替换串)
ARMS = [
    ("K1 闭合行根本没解析（通道只接了一半）⇒ 文件分支不该跑",
     "    done = _names(DONE, pulse_text)\n",
     "    done = []\n"),
    ("K2 未闭差集不算闭合（回到那条会丢的减数）",
     "    open_heartbeats = [n for n in pulse if n not in done_set]\n",
     "    open_heartbeats = [n for n in pulse]\n"),
    ("K3 两颗未闭也允许点名（把拒绝放宽成只拦三颗）",
     "    if len(open_heartbeats) >= 2:\n",
     "    if len(open_heartbeats) >= 3:\n"),
    ("K4 日志与文件对同一条给相反的话时不再红（挑一条信）",
     "    if unexplained:\n",
     "    if False:\n"),
]


def build_tree():
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    (SANDBOX / "scripts").mkdir(parents=True)
    shutil.copytree(REPO / "scripts" / "tests", SANDBOX / "scripts" / "tests")
    for name in sorted((REPO / "scripts").glob("*.py")):
        shutil.copy(name, SANDBOX / "scripts" / name.name)
    for name in ("probe_coverage_expectations.json", "motion_surface_ledger.json"):
        source = REPO / "scripts" / name
        if source.exists():
            shutil.copy(source, SANDBOX / "scripts" / name)
    if (REPO / "docs").exists():
        shutil.copytree(REPO / "docs", SANDBOX / "docs")
    (SANDBOX / ".github" / "workflows").mkdir(parents=True)
    shutil.copy(REPO / ".github" / "workflows" / "ci.yml", SANDBOX / ".github" / "workflows" / "ci.yml")
    swift_dir = SANDBOX / "ClipboardHistory" / "Tests" / "ClipboardHistoryAppTests"
    swift_dir.mkdir(parents=True)
    shutil.copy(REPO / "ClipboardHistory" / "Tests" / "ClipboardHistoryAppTests" / "UIInteractionProbeTests.swift",
                swift_dir / "UIInteractionProbeTests.swift")
    # 同形不是一个恒真的路径等式，而是"测试文件按 parents[2] 去读的那两处**真的在**"：
    # 缺一个，接线判据就会红在"找不到仓库"上，那种红说的是临时树，不是被判的那条判据。
    for required in (SANDBOX / ".github" / "workflows" / "ci.yml",
                     SANDBOX / "ClipboardHistory" / "Tests" / "ClipboardHistoryAppTests"
                     / "UIInteractionProbeTests.swift"):
        if not required.exists():
            raise SystemExit("TREE_MISSING %s ⇒ 临时树不同形，后面的 CAUGHT 都不作数" % required)


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", "scripts.tests.test_ui_probe_report"],
                          cwd=str(SANDBOX), env=dict(os.environ, PYTHONPATH=str(SANDBOX), PYTHONUTF8="1"),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def main():
    build_tree()
    baseline_rc, baseline_out = run_tests()
    print("BASELINE exit=%d  %s" % (baseline_rc, baseline_out.strip().splitlines()[-1]))
    if baseline_rc != 0:
        print("基线不绿 ⇒ 后面每一刀的 CAUGHT 都不说明是判据抓住了，是树坏了")
        return 1
    source = TARGET.read_text(encoding="utf-8")
    bad = 0
    for label, needle, replacement in ARMS:
        if source.count(needle) != 1:
            print("NOT-RUN %s 锚点命中 %d 次（要恰好 1 次）" % (label, source.count(needle)))
            bad += 1
            continue
        TARGET.write_text(source.replace(needle, replacement), encoding="utf-8")
        rc, out = run_tests()
        verdict = "CAUGHT" if rc != 0 else "ESCAPED"
        if rc == 0:
            bad += 1
        named = [line for line in out.splitlines() if line.startswith("FAIL:")]
        print("%s %s" % (verdict, label))
        for line in named[:4]:
            print("      %s" % line)
        TARGET.write_text(source, encoding="utf-8")
    print("R146_KNIVES arms=%d bad=%d" % (len(ARMS), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
