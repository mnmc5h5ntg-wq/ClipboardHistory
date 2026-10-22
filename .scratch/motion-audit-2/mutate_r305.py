#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R305 的变异表（第 304 轮 / Round 302）：动效那两朵红的登记**按机器切**这件事要有牙。

本轮把 `scripts/motion_floor_gate.py` 的 `suite_reds` 从"一张全局名单"改成"按机器切片的名单"
（BACKLOG 354 的②：那两朵红只在 runner 上出现过，出现率 1/17 与 1/7；登记成有名字的未覆盖
比每轮重读一次单跑诚实，前提是它**不许跨机顶检**、**能退场**）。
判的对象是一支 python 闸门，所以「跑起来了没」按 `Ran N tests` 那条结论行认，
编译错 / 收集不到用例都不算 CAUGHT（D-243 在 python 侧同样成立）。

· M880 **把机器切片退回全局** —— 每条登记都算在"这台机器"名下。
  `testRegistrationForAnotherMachineDoesNotExcuseThisOne` 必须红：
  这是整件事的要点，runner 上的登记一旦能顶掉本机的红，这张表就变回免检牌堆。
· M881 **让退场提示不分机器** —— stale 那一站扫全部机器而不是本机那一份。
  `testStaleNoticeOnlyCountsThisMachinesEntries` 必须红：
  本机替 runner 喊"删掉这条登记"比不退场更坏（那条在 runner 上还会红）。

字节码缓存：`-B` + `PYTHONDONTWRITEBYTECODE=1` 一起上。R223 一批记过 macOS 那个坑
（仓库外的字节码让"同长度变异 + 同一秒还原"之后仍然执行旧代码），这里不冒这个险。
根由 `__file__` 推（D-260/D-262）；needle 恰好命中一次；还原逐字节一致（RESTORE_CLEAN）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = 'scripts/motion_floor_gate.py'
MODULE = 'scripts.tests.test_motion_floor_gate'

SLICE_NEEDLE = u'        registry.setdefault(entry["machine"], {})[name] = entry'
SLICE_GLOBAL = u'        registry.setdefault(machine, {})[name] = entry'
STALE_NEEDLE = u'    stale = [name for name in sorted(mine) if name not in named]'
STALE_GLOBAL = (u'    stale = [name for name in sorted(n for table in registry.values() for n in table)\n'
                u'               if name not in named]')

ARMS = [
    ('M880', u'登记不分机器 = runner 的免检顶掉本机的红', GATE, SLICE_NEEDLE, SLICE_GLOBAL,
     'testRegistrationForAnotherMachineDoesNotExcuseThisOne'),
    ('M881', u'退场提示不分机器 = 本机替 runner 删登记', GATE, STALE_NEEDLE, STALE_GLOBAL,
     'testStaleNoticeOnlyCountsThisMachinesEntries'),
]

RAN = re.compile(r'^Ran (\d+) tests', re.M)
FAILED_BLOCK = re.compile(r'^FAIL: (\w+) ', re.M)


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def run_module():
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    proc = subprocess.run([sys.executable, '-B', '-W', 'ignore', '-m', 'unittest', '-v', MODULE],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = int(RAN.findall(text)[-1]) if RAN.findall(text) else 0
    return proc.returncode, ran, sorted(set(FAILED_BLOCK.findall(text))), text


def baseline():
    code, ran, fails, text = run_module()
    if not ran:
        print('R305_BASELINE NOT_RUN 没有结论行（Ran N tests）⇒ 收集失败不是通过', flush=True)
        print(text.strip()[-400:], flush=True)
        return None
    if fails or code != 0:
        print('R305_BASELINE RED 未变异就已经红：%s ⇒ 先修基线再谈刀' % fails, flush=True)
        return None
    print('R305_BASELINE OK Ran %d' % ran, flush=True)
    return ran


def run_arm(arm_id, why, target, needle, repl, want_fail):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        code, ran, fails, text = run_module()
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not ran:
        print('%s NOT_RUN 没有结论行（跑崩了不等于刀有牙）：%s'
              % (arm_id, text.strip().splitlines()[-1] if text.strip() else ''), flush=True)
        return 'NOT_RUN'
    if want_fail in fails:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 红=%d exit=%d）'
              % (arm_id, why, ', '.join(fails), ran, len(fails), code), flush=True)
        return 'CAUGHT'
    print('%s %s ｜ 跑=%d 红=%s ⇒ 期望 %s 红而它没红'
          % (arm_id, 'ESCAPED' if not fails else 'WRONG_CELL', ran, fails, want_fail), flush=True)
    return 'ESCAPED' if not fails else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    if baseline() is None:
        print('R305_MUTATE NOT_RUN 基线不绿（拒绝出表）', flush=True)
        return 1
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R305_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'no' if 'RESTORE_FAILED' in kinds else 'yes'
    print('R305_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
