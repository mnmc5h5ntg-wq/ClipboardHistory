#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 补段 C：把「绝对根打死 runner」与「通道值里的裸空格打死判它的测试」收成**一条**守卫。

为什么是一条：两次事故是同一族 —— 判据的**输出契约**（哪些字符串会被下游按空格/斜杠切）从来没被
任何门判过。R564 的 `ROOT = "/Users/…"` 让 runner 上 `subprocess.run(cwd=…)` 抛异常（STEP[9] 红、
STEP[10]-[14] 整段 skipped）；R565 的 `范围=…（未推的为空 ⇒ 退化）` 让判它的测试在
`dict(kv.split("=", 1) …)` 上崩（`element #1 has length 1`）。两次都是"本机绿、别人只能崩"。

三格各判什么：
  ① 名单不许为空：会进 CI 的脚本名单**从 `.github/workflows/*.yml` 现读**，读不出 ⇒ 红
     （刀 M1471 钉"解析器静默返回空表"这一坏法）。
  ② 绝对根：名单里的脚本（含电池目录里被 CI 跑的 `.py`）不许有**运行时当路径用**的机器绝对路径；
     合成机器路径（`/Users/someone/…`）与 runner 自己的 `/Users/runner/…` 放行 —— 判据的正对照需要坏形状，
     不需要任何人的真家目录。再加一条更宽的 B 格：**真人**家目录（`/Users/<开发者>`）在 CI 跑的脚本里
     一笔都不许出现，注释与文档字符串也算（R565 现读：电池里三个文件拿真路径当正对照样本）。
  ③ 通道值：一行按空格切成「键=值」的读数，值里不许有裸空格；判法是"这个 `%s` 槽位喂的那个名字，
     在本文件里被赋过一个含空格的字符串字面量"。

用法：`python3 scripts/ci_channel_hygiene.py`（退出码 0=绿、1=红、2=读不到工作树）。
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 机器路径的形状：`/Users/<名字>/` 开头。合成形状（someone/else）由下面 is_synthetic_machine_path 放行。
ABS_HOME_RE = re.compile(r'/Users/[^\'"\s]*')
# 显式放行：runner 自己的家目录（账里要引用那一台的现场）与示例名。
SYNTHETIC_USERS = {'runner', 'example', 'demo', 'acme', 'sample'}


def real_local_accounts():
    # 这台机器上**真实存在**的账号目录名（+ 当前用户）。按"存不存在"判而不是按形状判，是因为
    # 这条格要拦的两件事都以"那一个真账号"为对象：①换一台机器就只能报错的运行时根（R262/R273/R564），
    # ②把私人路径写进仓库。而判据的正对照需要"机器绝对路径"这个**形状**（`/Users/ming/…`），
    # 那个形状在这台机器上不存在 ⇒ 不许被咬 —— 与 R555 那条"新界值要能在无害处退化"同一形。
    names = set()
    tail = os.path.expanduser('~').rstrip('/').split('/')
    if len(tail) > 2:
        names.add(tail[-1])
    # ⚠ 不探 '/home'：macOS 上它是一个 autofs 挂载点，`os.listdir('/home')` 会挂住整台机器等它
    #   （R565 实测：守卫自己卡死 5 分钟，被杀）。账号只在这台机器上的 /Users 下面。
    try:
        names.update(os.listdir('/Users'))
    except OSError:
        pass
    return set(n.lower() for n in names if n)
# 运行时真的会被当路径用的调用名（只有喂进这些的绝对根才算缺陷）
PATH_CONSUMERS = {'open', 'join', 'exists', 'isdir', 'isfile', 'listdir', 'walk',
                  'chdir', 'remove', 'makedirs', 'run', 'check_output', 'call',
                  'Popen', 'abspath', 'realpath', 'read_text', 'write_text'}


def ci_script_roster(workflows_dir=None):
    """从 `.github/workflows/*.yml` 现读"会进 CI 的脚本"名单（相对路径，逐字取自 run 行）。"""
    workflows_dir = workflows_dir or os.path.join(ROOT, '.github', 'workflows')
    roster = set()
    for name in sorted(os.listdir(workflows_dir)):
        if not name.endswith(('.yml', '.yaml')):
            continue
        text = io.open(os.path.join(workflows_dir, name), encoding='utf-8').read()
        for match in re.finditer(r'(?:python3?|bash|sh|zsh)?\s*((?:scripts|\.scratch)/[^\s"\'`]+?\.(?:py|sh))',
                                 text):
            roster.add(match.group(1))
    return sorted(roster)


def battery_scripts():
    """电池目录里的 `.py`（CI 的 STEP[9] 跑的就是这一卷）。"""
    tests_dir = os.path.join(ROOT, 'scripts', 'tests')
    return sorted('scripts/tests/' + n for n in os.listdir(tests_dir) if n.endswith('.py'))


def string_constants(tree):
    """全部字符串常量（含文档字符串）；**注释本来就不在 AST 里** ⇒ 注释天然不算。"""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def is_synthetic_machine_path(value, accounts=None):
    match = ABS_HOME_RE.search(value)
    if not match:
        return False
    parts = match.group(0).split('/')
    user = parts[2] if len(parts) > 2 else ''
    accounts = accounts if accounts is not None else real_local_accounts()
    if not user or user.lower() in SYNTHETIC_USERS:
        return True
    return user.lower() not in accounts


def names_used_as_paths(source, accounts=None):
    """被喂进 PATH_CONSUMERS 的变量/字面量里的绝对机器路径 ⇒ 这才是运行时缺陷。

    返回 [(行号, 片段)]：只收"这一行里同时出现消费者与 `/Users/…` 形状"的粗粒度证据，
    再加 AST 兜底（Assign 到名字含 ROOT/REPO 的字面量、以及 Call 的参数常量）。
    """
    hits = []
    accounts = accounts if accounts is not None else real_local_accounts()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [('parse-error', str(exc))]

    consumed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fname = node.func.attr if isinstance(node.func, ast.Attribute) else \
                (node.func.id if isinstance(node.func, ast.Name) else '')
            if fname not in PATH_CONSUMERS:
                continue
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                for const in _const_strings(arg):
                    if ABS_HOME_RE.search(const) and not is_synthetic_machine_path(const, accounts):
                        consumed.add((node.lineno, const))
        # `ROOT = "/Users/…"` 这一族：名字里带 ROOT/REPO 的赋值即使没直接喂进消费者也算缺陷，
        # 因为它就是给别人当根用的（R564 那一次正是赋给 ROOT 再喂 subprocess 的 cwd）。
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and re.search(r'(ROOT|REPO|DIR)$', target.id):
                    for const in _const_strings(node.value):
                        if ABS_HOME_RE.search(const) and not is_synthetic_machine_path(const, accounts):
                            consumed.add((node.lineno, const))
    return sorted(consumed)


def _const_strings(node):
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def spacey_assigned_names(tree):
    """在本文件里被赋成"含 ASCII 空格的字符串字面量"的名字（合成坏形状的候选）。"""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for const in _const_strings(node.value):
                if ' ' in const:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            names.add(target.id)
    return names


def channel_space_risks(source):
    """读数行里「键=值」的值槽喂了一个含空格的字面量 ⇒ 按空格切的下游解析会断。"""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    offenders = spacey_assigned_names(tree)
    if not offenders:
        return []
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) \
                or node.func.id != 'print':
            continue
        for literal, fed in _print_slots(node):
            if '=' not in literal:
                continue
            # 值槽形状：`=` 后面紧跟一个替换位（`%s` 或 `{…}`），且这一位喂进来的名字在嫌疑名单里
            for match in re.finditer(r'=(?:%s|\{([A-Za-z_][A-Za-z0-9_]*)\})', literal):
                if match.group(1):
                    if match.group(1) in offenders:
                        out.append((node.lineno, literal.strip()[:60]))
                    continue
                for name in fed:
                    if name in offenders:
                        out.append((node.lineno, literal.strip()[:60]))
    return sorted(set(out))


def _print_slots(call):
    """把 `print("…%s…" % (a, b))` / `print(f"…{a}…")` 拆成 (字面量, 喂进去的名字列表)。"""
    args = call.args
    if not args:
        return []
    first = args[0]
    names = []
    if isinstance(first, ast.BinOp) and isinstance(first.op, ast.Mod):
        literal = first.left.value if isinstance(first.left, ast.Constant) else ''
        right = first.right
        if isinstance(right, ast.Tuple):
            names = [e.id for e in right.elts if isinstance(e, ast.Name)]
        elif isinstance(right, ast.Name):
            names = [right.id]
        return [(literal, names)]
    if isinstance(first, ast.JoinedStr):
        literal = ''.join(v.value if isinstance(v, ast.Constant) else '{x}' for v in first.values)
        names = [v.value.id for v in first.values
                 if isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name)]
        return [(literal, names)]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return [(first.value, [a.id for a in args[1:] if isinstance(a, ast.Name)])]
    return []


def joined_constant_strings(tree):
    """把 `'a' + 'b' + 'c'` 这类拼接常量合成一个串再看形状。

    存在的理由（R565 现读）：电池里有一支守卫自己就是这么写正对照的
    （`'/' + 'Users' + '/' + 'wangziyi'`）—— 按单条字面量扫会被这种拆法绕过去，
    于是"不许把真人路径写进 CI 跑的脚本"这条格只剩一半。
    """
    out = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            parts = []
            cur = node
            while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Add):
                if isinstance(cur.right, ast.Constant) and isinstance(cur.right.value, str):
                    parts.append(cur.right.value)
                cur = cur.left
            if isinstance(cur, ast.Constant) and isinstance(cur.value, str):
                parts.append(cur.value)
            if len(parts) > 1:
                out.append(''.join(reversed(parts)))
    return out


def real_home_mentions(text, accounts=None):
    """B 格：会进 CI 的脚本里不许出现**真人**的家目录（注释与正对照也算）。

    判的是**这台机器上真存在的那个账号**：`/Users/runner`（作业自己那台）与 `/Users/ming/…`（这台机器
    上没这个人，只是形状）放行，而 `/Users/<开发者的名字>` 一律红 —— 它既是"换一台机器只能报错"的成因
    （R262/R273/R564），也是把私人路径写进仓库的那只手。`accounts` 可注入，是为了让正对照能判形状，
    而不是让控制样本恰好撞上一个真账号。
    """
    out = []
    accounts = accounts if accounts is not None else real_local_accounts()
    for lineno, line in enumerate(text.split('\n'), 1):
        for match in ABS_HOME_RE.finditer(line):
            parts = match.group(0).split('/')
            user = parts[2] if len(parts) > 2 else ''
            if user and user.lower() not in SYNTHETIC_USERS and user.lower() in accounts:
                out.append((lineno, match.group(0)))
    # 第二遍：拼接后的常量（拆成三段写的那一种）
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for value in joined_constant_strings(tree):
        for match in ABS_HOME_RE.finditer(value):
            parts = match.group(0).split('/')
            user = parts[2] if len(parts) > 2 else ''
            if user and user.lower() not in SYNTHETIC_USERS and user.lower() in accounts:
                needle = match.group(0)
                if needle not in ' '.join(line for _, line in out):
                    out.append((0, needle))
    return out


def referenced_by_battery():
    # 电池正文里以 `scripts/<name>.py` 形状引用过的工具。只按 ci.yml 抽名单会漏掉 R564 那支守卫 ——
    # STEP[9] 跑的是 `python3 -m unittest discover -s scripts/tests`，守卫是从测试里被 subprocess 调的；
    # 它两次打死机器（runner 一次、本机电池一次），却不在任何"会进 CI 的脚本"名单上。
    tests_dir = os.path.join(ROOT, 'scripts', 'tests')
    out = set()
    for name in sorted(os.listdir(tests_dir)):
        if not name.endswith('.py'):
            continue
        text = io.open(os.path.join(tests_dir, name), encoding='utf-8').read()
        for match in re.finditer(r'scripts/([A-Za-z0-9_]+\.py)', text):
            rel = 'scripts/' + match.group(1)
            # 只收**真存在**的那一颗：电池正文里的假样本（`('scripts/x.py', …)` 那种合成数据）
            # 不是引用。ci.yml 名单里的缺件仍然算 red，走的是 scan() 的 missing 那一格。
            if os.path.exists(os.path.join(ROOT, rel)):
                out.add(rel)
    return sorted(out)


def scan(paths):
    bad = []
    for rel in paths:
        full = os.path.join(ROOT, rel)
        if not os.path.exists(full):
            bad.append((rel, 'missing', ''))
            continue
        source = io.open(full, encoding='utf-8').read()
        if not source.strip():
            bad.append((rel, 'empty', ''))
            continue
        for lineno, frag in real_home_mentions(source):
            bad.append((rel, 'real-home-in-script', 'L%s %s' % (lineno, frag[:60])))
        if rel.endswith('.py'):
            for lineno, frag in names_used_as_paths(source):
                bad.append((rel, 'abs-root', 'L%s %s' % (lineno, frag[:60])))
            for lineno, frag in channel_space_risks(source):
                bad.append((rel, 'channel-space', 'L%s %s' % (lineno, frag)))
        else:
            for lineno, line in enumerate(source.split('\n'), 1):
                if line.lstrip().startswith('#'):
                    continue
                for match in ABS_HOME_RE.finditer(line):
                    parts = match.group(0).split('/')
                    if len(parts) > 2 and parts[2].lower() not in SYNTHETIC_USERS \
                            and parts[2].lower() in real_local_accounts():
                        bad.append((rel, 'abs-root', 'L%s %s' % (lineno, match.group(0)[:60])))
    return bad


def build_parser():
    ap = argparse.ArgumentParser(prog='ci_channel_hygiene.py',
                                 description='判"会进 CI 的脚本"的两条输出契约：不许写死机器根、通道值里不许裸空格')
    ap.add_argument('--extra', default='', help='额外要扫的相对路径（逗号分隔，电池测试用）')
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        roster = ci_script_roster()
    except OSError as exc:
        print('CI_CHANNEL_HYGIENE_RESULT=unreadable %s' % exc)
        return 2
    battery_refs = referenced_by_battery()
    paths = sorted(set(roster) | set(battery_scripts()) | set(battery_refs)
                   | set(p for p in args.extra.split(',') if p))
    # ①名单不许为空：解析器坏了不能读成"没有脚本要查"
    if not roster:
        print('CI_CHANNEL_HYGIENE ROSTER_EMPTY=workflow-scripts=0 ⇒ 从 ci.yml 抽不出任何脚本 ⇒ 这一格没有对象，不许绿')
        return 1
    bad = scan(paths)
    print('CI_CHANNEL_HYGIENE ci脚本=%d 电池脚本=%d 电池引用=%d 合计=%d 绝对根=%d 真人路径=%d 通道空格=%d'
          % (len(roster), len(battery_scripts()), len(battery_refs), len(paths),
             sum(1 for b in bad if b[1] == 'abs-root'),
             sum(1 for b in bad if b[1] == 'real-home-in-script'),
             sum(1 for b in bad if b[1] == 'channel-space')))
    for rel, kind, frag in bad:
        print('  %s %s %s' % (rel, kind, frag))
    if bad:
        print('CI_CHANNEL_HYGIENE_RESULT=red')
        return 1
    print('CI_CHANNEL_HYGIENE_RESULT=ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
