# -*- coding: utf-8 -*-
"""档位词表的**唯一一份真值**（R587 / 靶 B）。

为什么要有这个文件（派单原话：同一件"档位"事实现在有两份写法，而其中一份坏了不会红）：
R586 把两态差尺的地板选择从子串换成按段解析，但**词表本身**在 python 仪器里当时有五份拷贝：
  · `hover_two_state_diff.py` 的 `TIERS = ('light','dark')`（判定用）
  · `hover_two_state_diff.py` 的 `PRESS_LADDER_PROOF (light|dark)` 正则（读 Swift 打印用）
  · `hover_two_state_diff.py` 的 `for tag in ('light','dark')`（报表分组）
  · `frame_baseline.py` 的 `-(?:light|dark)\\.png$`（倍率解析）
  · `frame_recording_proof.py` 的 `for shade in ("light","dark")`
加一档或改名时，`frame_baseline.py` 那一份会**静默**退化成"帧名里推不出倍率"（走的是不红的
`SCALE_NOT_RUN` 出口），而两态差尺照判 ⇒ 上一轮刚修好的按段解析在另一侧不再生效，且没有一格会红。

这里只放**词表 + 按段解析**这一件事。Swift 侧（`UICaptureHarness.swift` 里 `for tag in ["light","dark"]`
若干处）本轮不碰（派单红线：不许碰捕获侧 Swift），只在台账里把数量与位置记成读数，
由 `test_tier_vocabulary.py` 的扫描守卫盯着 python 侧不再出现第二份声明。
"""

TIERS = ("light", "dark")

# 旧写法（子串法）保留在这里只服务一件事：报"哪些帧名会被它读错"。任何判定路径都不许调它，
# 这一条由 `test_no_judgment_path_uses_substring_tier` 会红地签，不靠注释。
SUBSTRING_TIER_FORBIDDEN_IN_JUDGMENT = True


def tier_from_name(name: str) -> str:
    """按**段**解析档位：从右往左找第一个独立等于词表里某档的段；认不出返回空串（= 不知道）。"""
    stem = name[:-4] if name.endswith(".png") else name
    for seg in reversed(stem.split("-")):
        if seg in TIERS:
            return seg
    return ""


def tier_alternation() -> str:
    """给正则用的 `light|dark`（从词表现推，不另抄一份）。"""
    return "|".join(TIERS)


def tier_suffix_pattern() -> str:
    """帧名尾巴 `-<尺寸>-<档>.png` 里档位那一段的正则片段（不含捕获组）。"""
    return "(?:%s)" % tier_alternation()
