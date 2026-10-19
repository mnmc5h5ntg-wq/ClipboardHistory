#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R214 的变异表：`freezeLoadingForCapture` 的两格证人各一把刀（BACKLOG 236 结案）。

对象是产品与判据本身，不是台账：

M748 把 `DetailFileView` 的**唯一一处**默认值（init 参数）从 `false` 翻成 `true` ⇒
     `testDefaultsStartTheLoad` 必须红 —— 这一格就是 R211 注释里那句"有测试钉住"当时**没有**的东西。
     默认值被翻动的后果不是红，是产品里每一条记录的详情预览永远停在骨架。
M749 把纯函数 `MediaLoadingPlan.startsLoad` 的取反去掉（`!freeze` ⇒ `freeze`）⇒
     `testStartsLoadTruthTable` 必须红：真值表两格同时翻面。

**故意没配的第三把**（记成 BACKLOG 240，不假装跑过）：把 `.task` 里的
`guard MediaLoadingPlan.startsLoad(freezeLoadingForCapture: freezeLoadingForCapture)` 写成恒加载
（传死值 false）—— 今天**没有任何一格会红**：默认值守卫读的是字段，调用点守卫读的是源码，
而"冻结真的让界面停在骨架"这个行为只在帧基线里被看见（它会报"像素变了"，说不出原因）。
补那把刀之前要先补行为证人（同一视图两臂的像素判据：冻结臂有骨架、默认臂没有）。

R214 的读数：第一版这里其实有**两处**默认（属性初始化 + init 参数），刀打在死的那一处 ⇒ ESCAPED。
已合并成一处（属性不再自带默认值，只由 init 赋），这一刀才咬得到。

两把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
VIEW = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift'
PLAN = 'ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/MediaLoadingPlan.swift'
FILT = 'MediaLoadingPlanTests'

ARMS = [
    ('M748', u'把注入点默认值翻成 true（产品里每条详情都会永远停在骨架）', VIEW,
     '         freezeLoadingForCapture: Bool = false) {',
     '         freezeLoadingForCapture: Bool = true) {',
     'testDefaultsStartTheLoad'),
    ('M749', u'去掉纯函数的取反（冻结与加载的关系翻面）', PLAN,
     '        !freezeLoadingForCapture',
     '        freezeLoadingForCapture',
     'testStartsLoadTruthTable'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_name):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run(['env', '-u', 'SDKROOT', 'swift', 'test', '--filter',
                           '%s/%s' % (FILT, test_name)],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    m = re.search(r'Executed (\d+) tests?', text)
    # 摘要行只有一条用例时印的是「with 1 failure」（单数）—— 只认复数会把真红读成 ESCAPED。
    fm = re.search(r'with (\d+) failure', text)
    failed = bool(fm) and int(fm.group(1)) > 0
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
            print('%s NOT_RUN 那一格根本没跑（Executed 0）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        if code != 0 and failed:
            caught += 1
            print('%s CAUGHT  %s.%s ⇒ %s' % (arm_id, FILT, filt, why), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s.%s ⇒ %s' % (arm_id, FILT, filt, why), flush=True)
    print('R214_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
