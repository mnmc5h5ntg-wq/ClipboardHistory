#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R229 的变异表：亮档反馈梯（hover +0.025 / pressed +0.015）三把刀。

对象是产品源码，判据是新增的 `ControlHoverLadderTests`（跑 `swift test --filter`，按 `FAIL:` 行认红）。

M768 去掉亮档 hover 那一抬（两档又共用一个数）⇒ "亮档药丸对底 ≥1.20" 必须红。
M769 去掉亮档 pressed 那一抬 ⇒ `hover→pressed` 台阶掉到 4/255 之下 ——
     这一刀钉的正是 R14 当年拦下 0.10 的那条理由：只抬一档会把两档压平。
M770 画法不传色档（`dark: colorScheme == .dark` 摘掉）⇒ 数值仍然对，但产品不再读它
     （R219/R225 同一族：令牌写对了、调用点没接 = 屏幕上什么都没变）⇒ 源码守卫必须红。

三把刀都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
TOKENS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift'
STYLE = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/PressableStyle.swift'
FILTER = 'ControlHoverLadderTests'

ARMS = [
    # 锚点跟着 R229 的**结构改动**重钉：抬量从 `VisualFill` 里的两个助手函数
    # 搬进了 `PressableAppearance.fillOpacity`（两条既有守卫要求的形状），
    # 旧锚点会命中 0 ⇒ NOT_RUN。规矩见 D-215：改源码那一轮就把打它的表改到还能跑。
    ('M768', u'去掉亮档 hover 那一抬（两档又共用一个数）', STYLE,
     "        return isHovered ? hoverLevel + (dark ? 0 : VisualFillLift.hover) : 0",
     "        return isHovered ? hoverLevel : 0"),
    ('M769', u'去掉亮档 pressed 那一抬（把 hover→pressed 压平 = R14 拦下的那个形状）', STYLE,
     "            return dark ? VisualFill.pressed : VisualFill.pressed + VisualFillLift.pressed",
     "            return VisualFill.pressed"),
    # 第三刀必须是**能编译**的坏法：第一版把 `dark:` 参数整个摘掉留下悬空括号 ⇒
    # 编译失败被记成 ESCAPED（不是 CAUGHT 也不是 NOT_RUN），那是假账。
    # 现在改成把色档写死成 dark —— 编译通过、屏幕上亮档回到旧样子、源码守卫红。
    ('M770', u'画法把色档写死成 dark（数值对、产品不再问屏幕）', STYLE,
     "                                                   dark: colorScheme == .dark)))",
     "                                                   dark: true)))"),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run():
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', FILTER], cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    names = sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", text)))
    ran = ('Executed 4 tests' in text) or ('error: ' in text)
    return proc.returncode, (1 if ran else 0), (bool(names) or proc.returncode != 0), text, names


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, failed, text, names = run()
        finally:
            write(target, original)
            if read(target) != original:
                print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
                return 2
        if not n_ran:
            not_run += 1
            print('%s NOT_RUN 那一卷根本没跑起来（编译失败？）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s' % (arm_id, why, ', '.join(names) or 'exit=%d' % code), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s' % (arm_id, why), flush=True)
    print('R229_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
