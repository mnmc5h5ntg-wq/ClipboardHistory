#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R219 的变异表：亮档骨架墨（BACKLOG 242 的修法）三条线各一把刀。

对象是产品与判据本身：

M752 `inkOpacities(dark:)` 忽略参数（两档都回暗档那两个数）⇒
     真值表里「亮档底色墨必须深于暗档」必须红。这一刀就是 242 那个缺陷本身：
     亮档条带对比度退回实测的 1.12（组件帧），也就是"几乎看不见"。
M753 只抬亮档的 base、不抬 highlight（0.26 ⇒ 0.20，抬升掉到 0.06）⇒
     亮档那一格的 lift 下界必须红。这一刀钉的是 242 写下的条件：
     **抬 base 必须同时抬 highlight**，否则扫光退回 R214 注释里那个峰值 0.0000。
M754 视图里把"按档取墨"换回直接吃那两个档盲常量（不再问系统是哪一档）⇒
     接线守卫 `testSkeletonViewReadsItsInkPerAppearance` 必须红。这一刀钉的是 D-055 那一族：
     值全对而没人按档取，等于 0.14 只是台账里的一个数。
     （第一版这刀是把 `@Environment` 换成写死的 `.dark` —— 编译不过 ⇒ NOT_RUN 而不是 CAUGHT，
      已换成能编译的那一种坏法；NOT_RUN 不算拦住，这条记在正文里。）

三把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
SHIMMER = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift'
FILT = 'SkeletonMotionTests'

ARMS = [
    ('M752', u'按档取墨的函数忽略参数（亮档退回暗档那两个数）', SHIMMER,
     '        dark ? (baseOpacity, highlightOpacity)\n'
     '             : (lightBaseOpacity, lightHighlightOpacity)',
     '        dark ? (baseOpacity, highlightOpacity)\n'
     '             : (baseOpacity, highlightOpacity)',
     'testInkOpacitiesArePerAppearanceAndKeepTheLift'),
    ('M753', u'只抬亮档底色、不抬亮带（抬升预算被吃掉）', SHIMMER,
     '    static let lightHighlightOpacity: Double = 0.26',
     '    static let lightHighlightOpacity: Double = 0.20',
     'testInkOpacitiesArePerAppearanceAndKeepTheLift'),
    ('M754', u'按档取墨被换回档盲常量（视图不再问系统是哪一档）', SHIMMER,
     '        SkeletonMotion.inkOpacities(dark: colorScheme == .dark)',
     '        (SkeletonMotion.baseOpacity, SkeletonMotion.highlightOpacity)',
     'testSkeletonViewReadsItsInkPerAppearance'),
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
            print('%s NOT_RUN 那一格根本没跑（Executed 0，多半是没编译过）⇒ 不算 CAUGHT：%s'
                  % (arm_id, why), flush=True)
            continue
        if code != 0 and failed:
            caught += 1
            print('%s CAUGHT  %s.%s ⇒ %s' % (arm_id, FILT, filt, why), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s.%s ⇒ %s' % (arm_id, FILT, filt, why), flush=True)
    print('R219_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
