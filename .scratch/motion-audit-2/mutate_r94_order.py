#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R94 变异对照：新加的执行序那把尺，每改坏一种坏法都必须有测试红。

为什么在**临时树**里跑而不是改仓库文件（R92 那支是原地改再恢复）：
这一轮的判据全部住在 `scripts/tests/`，而它们用 `Path(__file__).resolve().parents[2]`
去找 Swift 源码与 `probe_coverage_expectations.json` —— 只要把 `scripts/`、那份 json、
那一个 swift 文件（软链）摆成同样的相对形状，变异就发生在一个副本上，
仓库里那颗尺子从头到尾没被写过（R88 的教训：跑着的脚本不许边跑边改）。
也刻意**不**补 `__init__.py`：仓库里没有它（靠命名空间包导入），补了就是在一份
与仓库形状不同的树上验判据，那种「绿」不说明任何事。

七刀（M516..M522，编号先在台账查重：已用到 M515）：
  M516 前缀判断恒真（「断了」这一格被抹掉）
  M517 把露面顺序改成排序后的顺序（尺悄悄按它想证明的东西排 ⇒ 永远证明那个东西）
  M518 打印里的「未闭口」写死成 0（读数与它宣称的那个字段脱钩）
  M519 把 queued 退回「所有没结论的」（两种缺席又被缝成一种）
  M520 去掉「一条都没露面 ⇒ 无从判定」那一格（空洞的真话冒充结论）
  M521 **预期 ESCAPED**：结论行之后又出现 started 时把状态改回「未结论」——
      现有任何夹具都不产生这种交错 ⇒ 这一刀会绿。它对应真实缺口：一份日志里若混进
      第二个写入者（R80b 那一族），「未闭口」就会说谎 ⇒ BACKLOG 135。
  M522 让这一支自己打印 PROBE_HUNG（把因果级的名字复制成第二颗尺子）
      ⇒ 必须被 NonRedundancyTests 抓住，证明 R94 改写过的那条守卫仍然有牙。
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = '/Users/wangziyi/Codex_Project0'
GATE_REL = 'scripts/probe_coverage_gate.py'
SWIFT_REL = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift'
MODULES = ['scripts.tests.test_probe_coverage_gate', 'scripts.tests.test_ui_probe_report']

# 锚点全部用「运行期才出现的形状」，不拿注释当锚：那样一改文档串就会 NOT-RUN。
# R383 重钉：旧写法是两块字面量用 `+` 拼的，`ast.literal_eval` 解不出来 ⇒ hidden_arms 把 M518
# 报成 rot（盘上其实命中 1 次）。改成单个字面量，值一字不变。
PRINT_OPEN = '''f"未闭口={reading['open_not_closed']} '''
QUEUED_FIELD = '        "queued": queued,'
DICT_ANCHOR = '    reading = {\n'
TALLY = ('        if kind != "started.":\n            concluded[name] = True\n'
         '        elif concluded[name]:')
QUEUE_IF = '    if reading["queued"]:'
PREFIX_FULL = ('prefix = None if not order else '
               '(first_hole is None or all(not appeared[n] for n in order[first_hole:]))')
PREFIX_HEAD = 'prefix = None if not order else'


def sub_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit('%s 的锚点命中 %d 次（只许 1 次）⇒ 拒绝造变异' % (tag, n))
    return text.replace(old, new)


def build_tree():
    root = tempfile.mkdtemp(prefix='r94_mutate-')
    shutil.copytree(os.path.join(REPO, 'scripts'), os.path.join(root, 'scripts'))
    os.makedirs(os.path.join(root, 'ClipboardHistory/Tests/ClipboardHistoryAppTests'))
    os.symlink(os.path.join(REPO, SWIFT_REL), os.path.join(root, SWIFT_REL))
    # `test_ui_probe_report` 里有一格直接读 `.github/workflows/ci.yml`（接线判据）。
    # 第一次跑时临时树缺它 ⇒ 基线 RED，而脚本按自己写死的规矩**拒绝出表** ——
    # 这正是"基线绿"必须先覆盖全部被跑模块的那条账（R88）在这里替我把关了一次。
    os.makedirs(os.path.join(root, '.github'), exist_ok=True)
    os.symlink(os.path.join(REPO, '.github/workflows'), os.path.join(root, '.github/workflows'))
    return root


def gate_path(root):
    return os.path.join(root, GATE_REL)


def reset(root):
    shutil.copy(os.path.join(REPO, GATE_REL), gate_path(root))


def run_tests(root):
    env = dict(os.environ, PYTHONUTF8='1')
    proc = subprocess.run([sys.executable, '-m', 'unittest'] + MODULES,
                          cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode('utf-8', 'replace')
    if proc.returncode == 0:
        return 'GREEN', out
    if 'FAILED (' in out:
        return 'RED', out
    if 'Traceback' in out:
        return 'ERROR', out
    return 'UNKNOWN', out


MUTATIONS = [
    ("M516", "前缀恒真", lambda t: sub_once(t, PREFIX_FULL,
                                           'prefix = None if not order else True', "M516"), 'RED'),
    ("M517", "露面顺序被排序", lambda t: sub_once(t, "    return order, concluded",
                                                 "    return sorted(order), concluded", "M517"), 'RED'),
    # R383：针的值不带源码的收尾引号（源码是 `f"...} "`），所以变异文也不能带 ——
    # 旧写法替换出 `f"未闭口=0""`（多一个引号）⇒ 语法错、被读成 ERROR。去掉收尾引号后
    # 源码行才是 `f"未闭口=0"`，与「读数与字段脱钩」的坏法一字不差。
    ("M518", "打印里的未闭口写死成 0", lambda t: sub_once(t, PRINT_OPEN, 'f"未闭口=0', "M518"), 'RED'),
    ("M519", "两种缺席又被缝成一种", lambda t: sub_once(t, QUEUED_FIELD,
                                                     '        "queued": absent_hack,', "M519"), 'RED'),
    ("M520", "空洞的真话冒充结论", lambda t: sub_once(t, PREFIX_HEAD,
                                                    'prefix = True if not order else', "M520"), 'RED'),
    # M521 在 R94 是**故意留着绿**的那一刀（没有判据覆盖 ⇒ 开成 BACKLOG 135）。
    # R95 补了 `InterleavedLogTests` 之后，同一个坏法必须变 RED：这一行的期望从 GREEN 改成 RED，
    # 就是 135 结案的证据。锚点也跟着代码形状改了（现在那里是 if/elif 两段）。
    ("M521", "结论之后再见到 started 就把状态改回未结论（交错日志会说谎）",
     lambda t: sub_once(t, TALLY,
                        '        concluded[name] = (kind != "started.")\n        if False:',
                        "M521"), 'RED'),
    ("M522", "这一支自己打印 PROBE_HUNG（复制因果级的名字）",
     lambda t: sub_once(t, QUEUE_IF, '    print("  PROBE_HUNG=none")\n' + QUEUE_IF, "M522"), 'RED'),
]


def apply(root, tag, fn):
    with open(gate_path(root), encoding='utf-8') as handle:
        text = handle.read()
    if tag == "M519":
        text = sub_once(text, DICT_ANCHOR,
                        '    absent_hack = [n for n in source_names if n not in concluded]\n'
                        + DICT_ANCHOR, 'M519-prelude')
    with open(gate_path(root), 'w', encoding='utf-8') as handle:
        handle.write(fn(text))


def main():
    root = build_tree()
    reset(root)
    baseline, out = run_tests(root)
    print('基线（临时树里的真判据，两个模块一起跑）：%s' % baseline)
    if baseline != 'GREEN':
        print(out[-2000:])
        raise SystemExit('临时树本身跑不绿 ⇒ 形状没搭对，这一轮的变异表不作数')
    rows = []
    for tag, desc, fn, want in MUTATIONS:
        reset(root)
        apply(root, tag, fn)
        got, out = run_tests(root)
        rows.append((tag, desc, got, want))
        print('%s %-54s %s（期望 %s）' % (tag, desc, got, want))
        if got == 'RED':
            names = [l for l in out.splitlines() if l.startswith('FAIL:')]
            print('    红在：%s' % '; '.join(n[6:].split(' (')[0] for n in names[:4]))
    reset(root)
    after, out = run_tests(root)
    print('恢复后基线复跑：%s' % after)
    wrong = [r for r in rows if r[2] != r[3]]
    print('MUTATE_TABLE n=%d caught=%d intended_escaped=%d mismatch=%d not_run=%d' % (
        len(rows), sum(1 for r in rows if r[2] == 'RED'),
        sum(1 for r in rows if r[2] == 'GREEN'), len(wrong),
        sum(1 for r in rows if r[2] in ('ERROR', 'UNKNOWN'))))
    for tag, desc, got, want in wrong:
        print('  MISMATCH %s %s got=%s want=%s' % (tag, desc, got, want))
    shutil.rmtree(root, ignore_errors=True)
    return 1 if (wrong or after != 'GREEN') else 0


if __name__ == '__main__':
    sys.exit(main())
