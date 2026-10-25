#!/usr/bin/env python3
# R375 追记：把 2ffc6d0 的 run id 与 84e4381 记进 STATE 的 ⓪ 那一行。
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def rd(name):
    return (ROOT / name).read_text(encoding="utf-8")


def wr(name, text):
    (ROOT / name).write_text(text, encoding="utf-8")


def once(text, anchor, replacement):
    assert text.count(anchor) == 1, (anchor, text.count(anchor))
    return text.replace(anchor, replacement)


state = rd("AGENT_STATE.md")
state = once(
    state,
    "① ⓪ CI：`357a763`（R374）已 success；`a17bc6a`（R373 追记）success；只登记不轮询。\n",
    "① ⓪ CI：`357a763`（R374）已 success；`a17bc6a`（R373 追记）success；"
    "本轮 `2ffc6d0 ↔ 40210881173`（queued、同 workflow 前面=2）与 `84e4381`（R374 追记）仍在队里；"
    "只登记不轮询。\n",
)
wr("AGENT_STATE.md", state)
print("ADDENDUM_R375_OK")
