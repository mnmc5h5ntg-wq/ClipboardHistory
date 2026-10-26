#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R403 变异对照：空带必须靠同帧证人区分能力出口与尺坏。"""
import os, subprocess, sys, time
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TARGET = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
NEEDLE = "        return witnessInk > 0 ? .rulerBroken : .capabilityAbsent(witnessInk: witnessInk)"
MUTANT = "        return .capabilityAbsent(witnessInk: witnessInk)"
FILTER = "UICaptureTests/testLongTextBandEmptyNeedsANonEmptyWitness"
def read(p):
    with open(p, encoding="utf-8") as h: return h.read()
def run():
    p = subprocess.run(["swift","test","--filter",FILTER], cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=1800)
    out = p.stdout + p.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts: return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    if "error:" in out and not any(" failed" in l for l in verdicts): return "BROKEN-MUTATION", out, []
    failed = [l.split("]")[0].replace("Test Case '-[","") for l in verdicts if " failed" in l]
    return ("CAUGHT" if p.returncode != 0 else "ESCAPED"), out, failed
def main():
    original = read(TARGET)
    if original.count(NEEDLE) != 1: raise SystemExit("针出现 %d 次" % original.count(NEEDLE))
    code,out,_=run()
    if code != "ESCAPED": raise SystemExit("预检失败 %s\n%s" % (code,out[-1500:]))
    print("预检 OK " + FILTER)
    stamp=time.time()+2
    open(TARGET,"w",encoding="utf-8").write(original.replace(NEEDLE,MUTANT,1))
    os.utime(TARGET,(stamp,stamp))
    try: code,out,failed=run()
    finally:
        open(TARGET,"w",encoding="utf-8").write(original)
        os.utime(TARGET,(stamp+1,stamp+1))
    hit = "证人非空但目标带空" in out
    right = code=="CAUGHT" and hit
    print("M1046 空带忽略证人 ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s" % (code,right,hit,failed,read(TARGET)==original))
    code2,out2,_=run()
    print("还原后复跑：" + code2)
    print("R403_MUTATE 刀=1 CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s" % (1 if code=="CAUGHT" else 0,0 if right else 1,"yes" if read(TARGET)==original else "NO"))
    return 0 if (code=="CAUGHT" and right and read(TARGET)==original and code2=="ESCAPED") else 1
if __name__=="__main__": sys.exit(main())
