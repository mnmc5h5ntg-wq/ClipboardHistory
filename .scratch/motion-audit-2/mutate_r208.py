#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R208 的变异表：缺席断言的"在场"判定，三种坏法各一把刀（BACKLOG 226 的收尾）。

被改的对象是**闸门自己**（`scripts/motion_surface_gate.py`），不是产品：
这一族的牙在于"尺子坏了要能红"，所以三把刀打的都是判据的相反方向 ——

M739 把边界匹配退回**忽略大小写子串**（R208 之前的写法）⇒
     `test_a_word_only_embedded_in_a_longer_identifier_is_not_present` 必须红：
     `focusEffectDisabled()` 会把 `缺席:...=disabled` 判成"词在里面"，于是人被迫去换更怪的词，
     缺席断言挑的词与被讨论的东西脱钩（尺子量错对象）。
M740 把边界匹配改成**永远说"不在场"**（把 search 结果丢掉）⇒
     `test_a_standalone_identifier_still_makes_the_claim_false` 必须红：
     这一刀是"修过头"的证人 —— 把误报修掉的正确做法不是让判据闭嘴。
M741 把**调用形词元**的放松改回去（两侧一律要边界）⇒
     `test_a_dotted_or_call_form_token_still_matches` 必须红：
     这一刀钉的是 R208 自己写坏过的第二格 —— 第一版边界规则把 `ForEach(` 判成"不在场"，
     而它在 SettingsView 里出现 4 次。误报逼人在换词，假清白让缺席断言变成免检，后者更坏（见 D-205）。

三把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
GATE = 'scripts/motion_surface_gate.py'
CLS = 'scripts.tests.test_motion_surface_gate.AbsenceTokenBoundaryTests'

BOUNDARY_LINE = '        if absence_pattern(token).search(text):'
SUBSTR_LINE = '        if token.lower() in text.lower():'
TAIL_LINE = '    tail = r"(?![\\w])" if token[-1:].isalnum() or token[-1:] == "_" else ""'

ARMS = [
    ('M739', u'缺席判定退回忽略大小写子串（focusEffectDisabled 会把 disabled 判成在场）', GATE,
     BOUNDARY_LINE, SUBSTR_LINE, CLS + '.test_a_word_only_embedded_in_a_longer_identifier_is_not_present'),
    ('M740', u'缺席判定改成永远"不在场"（修过头：把误报修掉不等于让判据闭嘴）', GATE,
     BOUNDARY_LINE, '        if False:', CLS + '.test_a_standalone_identifier_still_makes_the_claim_false'),
    ('M741', u'调用形词元的放松改回去（两侧一律要边界 ⇒ ForEach( 这类"确实在场"被判成不在场）', GATE,
     TAIL_LINE, '    tail = r"(?![\\w])"', CLS + '.test_a_dotted_or_call_form_token_still_matches'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_id):
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    proc = subprocess.run([sys.executable, '-m', 'unittest', test_id], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = bool(re.search(r'Ran (\d+) tests?', text))
    n = int(re.search(r'Ran (\d+) tests?', text).group(1)) if ran else 0
    return proc.returncode, n, text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        if needle == repl:
            not_run += 1
            print('%s NOT_RUN 变异文与原文逐字相同 ⇒ 这一刀没有对象' % arm_id, flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, _ = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 2
        if n_ran == 0:
            not_run += 1
            print('%s NOT_RUN 那一格根本没跑（Ran 0）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print('%s CAUGHT  %s ⇒ %s' % (arm_id, filt.split('.')[-1], why), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ⇒ %s' % (arm_id, filt.split('.')[-1], why), flush=True)
    print('R208_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
