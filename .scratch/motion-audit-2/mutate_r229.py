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
    # R262 重钉：这一抬在 R229 之后又被搬进 `HoverInk.opacity`（D-215 的规矩 ——
    # 改源码那一轮就把打它的表改到还能跑，旧锚点命中 0 ⇒ NOT_RUN 是假账）。
    # 替换只留 `return level`：两档重新共用一个数，`guard level > 0` 仍在 ⇒ 能编译。
    ('M768', u'去掉亮档 hover 那一抬（两档又共用一个数）', STYLE,
     "        return dark ? level : level + VisualFillLift.hover",
     "        return level"),
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
    # 「跑起来了」由结论行的**形状**判定，不写死数字（R262：这一卷从 4 条长到 6 条，
    # 上一版那句 `'Executed 4 tests' in text` 会把"真红了"读成"根本没跑"）。
    # 取**最后**一条 —— swift 先打单类小结再打总计，取首命中会把内层的数当总数（R147 同一族）。
    executed = re.findall(r'Executed (\d+) tests?, with (\d+) failures?', text)
    n_ran = int(executed[-1][0]) if executed else 0
    # 编译红不许记成 CAUGHT（D-243）：编译失败是把每条断言的机会整个拿走，
    # 那行 `error:` 不是判据在判，所以没有结论行时一律 NOT_RUN。
    return proc.returncode, n_ran, bool(names), text, names


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
            print('%s NOT_RUN 那一卷根本没跑起来（无结论行；编译红不算 CAUGHT = D-243）⇒ 不算 CAUGHT：%s'
                  % (arm_id, why), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s（跑=%d exit=%d）'
                  % (arm_id, why, ', '.join(names) or '仅 exit 非 0', n_ran, code), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s' % (arm_id, why), flush=True)
    print('R229_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
