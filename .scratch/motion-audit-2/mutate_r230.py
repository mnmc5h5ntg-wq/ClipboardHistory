#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R230 的变异表：悬停墨的共享换算 + 两处"直接读令牌"的位点（四把刀）。

判据卷 = `UICaptureTests/testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces`
        + `ControlHoverLadderTests` + `FilterPillMotionTests`
（像素那一条自己把夹具渲进临时目录，不需要 `CLIPBOARD_HISTORY_UI_SHOTS`）。

M771 把段按钮的悬停叠层装回来（`hoverLevel: 0` 改回默认 0.06）⇒ "选中那一段不许变"必须红：
     没有指针的那一段被画上了一层 0.085，而这正是 R20/R230 两家都躲过的叠层形状。
M772 去掉 `HoverInk.opacity` 的 `level == 0` 出口 ⇒ 幽灵层回来（0 被抬成 0.025）⇒ 同一格红。
     这一把是本轮真踩过的那格：R229 推上线的 `a7e3154` 就带着它。
M773 让段按钮那一层回到"两档共用一个数"（不抬亮档）⇒ 亮档比值掉到地板下 ⇒ 红，
     同时该名册守卫也会红（这一行不再命中任何一条"已接共享换算"的豁免）。
M774 把玻璃圆那处的档位改成 0（层没了）⇒ 空闲与点亮两帧同一块逐字节相同 ⇒ 红。
     这一把钉的是"接线"那一半：令牌算对了、调用点没接，屏幕上什么都没变（R219 同一族）。

四把刀都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核 RESTORE_CLEAN。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
SIDEBAR = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift'
STYLE = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/PressableStyle.swift'
GLASS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/GlassControls.swift'
FILTER = ('UICaptureTests/testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces'
          '|ControlHoverLadderTests|FilterPillMotionTests')

ARMS = [
    ('M771', u'段按钮把悬停叠层装回来（样式那一层不再让位）', SIDEBAR,
     "        .pressedStyle(in: VisualShape.rounded(VisualRadius.control), hoverLevel: 0)",
     "        .pressedStyle(in: VisualShape.rounded(VisualRadius.control))"),
    ('M772', u'悬停换算少一个 level==0 的出口 ⇒ 0 被抬成 0.025（幽灵层）', STYLE,
     "        guard level > 0 else { return 0 }\n",
     ""),
    ('M773', u'段按钮那一层回到两档共用一个数（亮档不抬）', SIDEBAR,
     # R334 重钉：胶囊那一层从"共用 controlHover + 抬量"改成"暗档走 pillHover、亮档仍走共享换算"，
     # 旧 needle 在盘上命中 0 次（预检当场报 bad=1）。刀的意思没变：让两档回到同一个数。
     ("        return dark ? VisualFill.pillHover\n"
      "                    : HoverInk.opacity(level: VisualFill.controlHover, dark: dark)"),
     "        return VisualFill.controlHover"),
    ('M774', u'玻璃圆的档位改成 0（接错了：令牌对、屏幕上没有这一层）', GLASS,
     "        .pressedStyle(in: Circle(), hoverLevel: VisualFill.controlHover)",
     "        .pressedStyle(in: Circle(), hoverLevel: 0)"),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run():
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', FILTER],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    names = sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", text)))
    ran = ('Executed ' in text) or ('error: ' in text)
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
    print('R230_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
