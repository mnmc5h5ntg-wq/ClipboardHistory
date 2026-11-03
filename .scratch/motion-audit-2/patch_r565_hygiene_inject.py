#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# R565 补段 C：把"这台机器上有哪些真账号"做成可注入的参数 —— 正对照要判的是形状被抓，
# 而不是"控制样本恰好长得像某个真账号"。默认值仍是现读的那一台。
import io

P = 'scripts/ci_channel_hygiene.py'
t = io.open(P, encoding='utf-8').read()
pairs = [
    ("""def names_used_as_paths(source):""",
     """def names_used_as_paths(source, accounts=None):"""),
    ("""    hits = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [('parse-error', str(exc))]""",
     """    hits = []
    accounts = accounts if accounts is not None else real_local_accounts()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [('parse-error', str(exc))]"""),
    ("""                    if ABS_HOME_RE.search(const) and not is_synthetic_machine_path(const):
                        consumed.add((node.lineno, const))
        # `ROOT = "/Users/…"` 这一族""",
     """                    if ABS_HOME_RE.search(const) and not is_synthetic_machine_path(const, accounts):
                        consumed.add((node.lineno, const))
        # `ROOT = "/Users/…"` 这一族"""),
    ("""                        if ABS_HOME_RE.search(const) and not is_synthetic_machine_path(const):
                        consumed.add((node.lineno, const))
    return sorted(consumed)""",
     """                        if ABS_HOME_RE.search(const) and not is_synthetic_machine_path(const, accounts):
                        consumed.add((node.lineno, const))
    return sorted(consumed)"""),
    ("""def real_home_mentions(text):""",
     """def real_home_mentions(text, accounts=None):"""),
    ("""    out = []
    accounts = real_local_accounts()
    for lineno, line in enumerate(text.split('\\n'), 1):""",
     """    out = []
    accounts = accounts if accounts is not None else real_local_accounts()
    for lineno, line in enumerate(text.split('\\n'), 1):"""),
]
for old, new in pairs:
    if t.count(old) != 1:
        raise SystemExit('ANCHOR_BAD %r count=%d' % (old[:46], t.count(old)))
    t = t.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(t)
print('INJECTION_ADDED')

P2 = 'scripts/tests/test_ci_channel_hygiene.py'
t2 = io.open(P2, encoding='utf-8').read()
pairs2 = [
    ("""        self.assertIn('scripts/commit_round_identity.py', roster,
                      'R564 那支守卫不在 CI 名单里 ⇒ 名单解析漏了它（它红过一整批 STEP[9]）')""",
     """        # R564 那支守卫**不在** ci.yml 的名单上（STEP[9] 跑的是 `unittest discover`，它是被电池调的）
        # ⇒ 只按 ci.yml 抽名单会漏掉那个两次打死机器的文件。这一格钉的就是"闭包要覆盖到它"。
        self.assertNotIn('scripts/commit_round_identity.py', roster,
                         '它若进了 ci.yml 名单，下面那一格就该改成断言名单里有它')
        self.assertIn('scripts/commit_round_identity.py', chi.referenced_by_battery(),
                      '电池引用闭包没抽到 R564 那支守卫 ⇒ 扫描范围漏了红过两次的对象')"""),
    ("""        self.assertTrue(chi.real_home_mentions(source),
                        '拆段拼接的真人路径没被抓到 ⇒ B 格只剩一半')""",
     """        self.assertTrue(chi.real_home_mentions(source, accounts={'ming'}),
                        '拆段拼接的真人路径没被抓到 ⇒ B 格只剩一半（注入"这台机器上有 ming 这个账号"）')
        # 同一颗源在默认（这台机器的真账号）下不该被咬 —— 否则 B 格会把自己的正对照判成缺陷。
        self.assertEqual([], chi.real_home_mentions(source))"""),
    ("""        self.assertTrue(chi.real_home_mentions(source))
        self.assertTrue(chi.names_used_as_paths(source), 'ROOT 赋值那一行必须被当运行时缺陷')""",
     """        self.assertTrue(chi.real_home_mentions(source, accounts={'ming'}))
        self.assertTrue(chi.names_used_as_paths(source, accounts={'ming'}),
                        'ROOT 赋值那一行必须被当运行时缺陷')"""),
]
for old, new in pairs2:
    if t2.count(old) != 1:
        raise SystemExit('ANCHOR2_BAD %r count=%d' % (old[:46], t2.count(old)))
    t2 = t2.replace(old, new, 1)
io.open(P2, 'w', encoding='utf-8').write(t2)
print('TESTS_INJECTED')
