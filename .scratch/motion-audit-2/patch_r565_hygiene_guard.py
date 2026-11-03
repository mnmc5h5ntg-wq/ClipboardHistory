#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R565 补段 C 的守卫补丁：把"真人路径"从按形状判改成按**这台机器上真实存在的账号**判，
# 并把"电池正文里引用过的 scripts/*.py"也纳入扫描范围（R564 那支守卫正是这么被跑起来的）。
# 注意：注入的代码里不许用三引号文档串（这个补丁文件自己就是三引号包着的），一律用 # 注释。
import io

P = 'scripts/ci_channel_hygiene.py'
t = io.open(P, encoding='utf-8').read()

OLD_USERS = """# 合成/示例/runner 用户名：正对照需要「机器绝对路径」这个**形状**，不需要任何人的真家目录。
SYNTHETIC_USERS = {'someone', 'else', 'runner', 'nobody', 'anyone', 'x', 'y', 'tmp',
                   'example', 'demo', 'acme', 'sample', 'someoneelse'}"""
NEW_USERS = """# 显式放行：runner 自己的家目录（账里要引用那一台的现场）与示例名。
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
    for base in ('/Users', '/home'):
        try:
            names.update(os.listdir(base))
        except OSError:
            pass
    return set(n.lower() for n in names if n)"""

OLD_SYN = """def is_synthetic_machine_path(value):
    match = ABS_HOME_RE.search(value)
    if not match:
        return False
    user = match.group(0).split('/')[2] if len(match.group(0).split('/')) > 2 else ''
    return user.lower() in SYNTHETIC_USERS"""
NEW_SYN = """def is_synthetic_machine_path(value, accounts=None):
    match = ABS_HOME_RE.search(value)
    if not match:
        return False
    parts = match.group(0).split('/')
    user = parts[2] if len(parts) > 2 else ''
    accounts = accounts if accounts is not None else real_local_accounts()
    if not user or user.lower() in SYNTHETIC_USERS:
        return True
    return user.lower() not in accounts"""

OLD_LINE_RULE = """    out = []
    for lineno, line in enumerate(text.split('\\n'), 1):
        for match in ABS_HOME_RE.finditer(line):
            parts = match.group(0).split('/')
            user = parts[2] if len(parts) > 2 else ''
            if user and user.lower() not in SYNTHETIC_USERS:
                out.append((lineno, match.group(0)))"""
NEW_LINE_RULE = """    out = []
    accounts = real_local_accounts()
    for lineno, line in enumerate(text.split('\\n'), 1):
        for match in ABS_HOME_RE.finditer(line):
            parts = match.group(0).split('/')
            user = parts[2] if len(parts) > 2 else ''
            if user and user.lower() not in SYNTHETIC_USERS and user.lower() in accounts:
                out.append((lineno, match.group(0)))"""

OLD_JOINED = """    for value in joined_constant_strings(tree):
        for match in ABS_HOME_RE.finditer(value):
            parts = match.group(0).split('/')
            user = parts[2] if len(parts) > 2 else ''
            if user and user.lower() not in SYNTHETIC_USERS:"""
NEW_JOINED = """    for value in joined_constant_strings(tree):
        for match in ABS_HOME_RE.finditer(value):
            parts = match.group(0).split('/')
            user = parts[2] if len(parts) > 2 else ''
            if user and user.lower() not in SYNTHETIC_USERS and user.lower() in accounts:"""

OLD_SH = """                for match in ABS_HOME_RE.finditer(line):
                    parts = match.group(0).split('/')
                    if len(parts) > 2 and parts[2].lower() not in SYNTHETIC_USERS:"""
NEW_SH = """                for match in ABS_HOME_RE.finditer(line):
                    parts = match.group(0).split('/')
                    if len(parts) > 2 and parts[2].lower() not in SYNTHETIC_USERS \\
                            and parts[2].lower() in real_local_accounts():"""

OLD_SCAN = """def scan(paths):"""
NEW_SCAN = """def referenced_by_battery():
    # 电池正文里以 `scripts/<name>.py` 形状引用过的工具。只按 ci.yml 抽名单会漏掉 R564 那支守卫 ——
    # STEP[9] 跑的是 `python3 -m unittest discover -s scripts/tests`，守卫是从测试里被 subprocess 调的；
    # 它两次打死机器（runner 一次、本机电池一次），却不在任何"会进 CI 的脚本"名单上。
    tests_dir = os.path.join(ROOT, 'scripts', 'tests')
    out = set()
    for name in sorted(os.listdir(tests_dir)):
        if not name.endswith('.py'):
            continue
        text = io.open(os.path.join(tests_dir, name), encoding='utf-8').read()
        for match in re.finditer(r'scripts/([A-Za-z0-9_]+\\.py)', text):
            out.add('scripts/' + match.group(1))
    return sorted(out)


def scan(paths):"""

OLD_PATHS = """    paths = sorted(set(roster) | set(battery_scripts())
                   | set(p for p in args.extra.split(',') if p))"""
NEW_PATHS = """    battery_refs = referenced_by_battery()
    paths = sorted(set(roster) | set(battery_scripts()) | set(battery_refs)
                   | set(p for p in args.extra.split(',') if p))"""

OLD_PRINT = """    print('CI_CHANNEL_HYGIENE ci脚本=%d 电池脚本=%d 合计=%d 绝对根=%d 真人路径=%d 通道空格=%d'
          % (len(roster), len(battery_scripts()), len(paths),"""
NEW_PRINT = """    print('CI_CHANNEL_HYGIENE ci脚本=%d 电池脚本=%d 电池引用=%d 合计=%d 绝对根=%d 真人路径=%d 通道空格=%d'
          % (len(roster), len(battery_scripts()), len(battery_refs), len(paths),"""

for old, new in [(OLD_USERS, NEW_USERS), (OLD_SYN, NEW_SYN), (OLD_LINE_RULE, NEW_LINE_RULE),
                 (OLD_JOINED, NEW_JOINED), (OLD_SH, NEW_SH), (OLD_SCAN, NEW_SCAN),
                 (OLD_PATHS, NEW_PATHS), (OLD_PRINT, NEW_PRINT)]:
    if t.count(old) != 1:
        raise SystemExit('ANCHOR_BAD %r count=%d' % (old[:48], t.count(old)))
    t = t.replace(old, new, 1)

io.open(P, 'w', encoding='utf-8').write(t)
print('HYGIENE_GUARD_PATCHED')
