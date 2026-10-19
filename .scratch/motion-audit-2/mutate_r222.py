#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R222 的变异表：新加的"报告标题格对活账"守卫两把刀（两条 staleness 比较各一条）。

对象是 `scripts/tests/test_final_report_headline.py` 自己 —— 报告里的数对不对，
只有"把比较改成恒不红就会红"这一种证法。

M759 把标题那一格的不等比较改成恒假（`elif int(m.group(1)) != live['last_round']:` ⇒ `elif False:`）⇒
     `test_a_stale_headline_is_named` 必须红：伪造一个旧标题它也不点名。
M760 把 U 上界那一格的不等比较改成恒假 ⇒ 同一格里 U 那半边必须红。
     两把刀分打两条比较，是因为**一条比较坏了另一条还灵**（R74/R75 那一族：
     两条判据对同一台机器给相反处置时，缺的是接线而不是阈值；这里缺的是各自的证人）。

两把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
GUARD = 'scripts/tests/test_final_report_headline.py'

ARMS = [
    ('M759', u'标题格那有界落后的比较恒假（伪造旧标题它也不响）', GUARD,
     "        elif live['last_round'] - claimed > LAG_ROUNDS:",
     "        elif False:",
     'test_a_stale_headline_is_named'),
    ('M760', u'U 上界格那有界落后的比较恒假（伪造 U-675 它也不响）', GUARD,
     "        elif live['u_max'] - claimed_u > LAG_U:",
     "        elif False:",
     'test_a_stale_headline_is_named'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_name):
    """跑整支守卫文件（`-k` 在 discover 下不可靠：这台机器的 python3.9 会把它当成参数报错），
    再从 -v 的输出里点名**那一格**是不是 FAIL —— 只认退出码会把别的格的绿/红混成本刀的结论。"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    proc = subprocess.run(
        [sys.executable, '-m', 'unittest', '-v',
         'scripts.tests.test_final_report_headline'],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    m = re.search(r'Ran (\d+) tests', text)
    # 这台机器的 python3.9 在 `-v` 下把失败印成两段：先 `test_x (Class) ... ` 再单独一行
    # `FAIL: test_x (Class)`。只认行内 `... FAIL` 会把真红读成 ESCAPED（R222 第一版就是这么错的）。
    named = (re.search(r'^FAIL: %s ' % re.escape(test_name), text, re.M)
             or re.search(r'^%s .* \.\.\. FAIL' % re.escape(test_name), text, re.M))
    failed = bool(named)
    return proc.returncode, (int(m.group(1)) if m else 0), failed, text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, failed, text = run(filt)
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
        note = (re.search(r'(FAIL|OK)[^\n]*', text.splitlines()[-2] if len(text.splitlines()) > 1 else '')
                or [None])
        line = [l for l in text.splitlines() if 'FINAL_REPORT' in l or 'Ran ' in l]
        detail = line[-1][:90] if line else u'没有读数行'
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ %s ｜ %s' % (arm_id, filt, why, detail), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ｜ %s ｜ %s' % (arm_id, filt, why, detail), flush=True)
    print('R222_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
