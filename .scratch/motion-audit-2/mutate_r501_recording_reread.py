#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R501 变异表：录制帧重复渲染确定性（M1345–M1346）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"; FILE="Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="UICaptureTests/testRecordingCardFrameIsDeterministicAcrossRenders"
NEEDLE="            _ = try render(fixture, appearance: appearance, to: second)"
ARMS=[
  ("M1345","第二次渲染换成非录制帧",
   NEEDLE,
   '''            _ = try render(fixtures(appearance: appearance).first(where: { $0.name == "settings-shortcuts" })!,
                           appearance: appearance, to: second)'''),
  ("M1346","第二次渲染换成另一外观",
   NEEDLE,
   '''            _ = try render(fixture, appearance: .darkAqua, to: second)'''),
]
def run():
    p=subprocess.run(["swift","test","--filter",TEST],cwd=ROOT,capture_output=True,text=True,env=ENV,timeout=2400)
    out=p.stdout+p.stderr
    if "Test Case" not in out: return "DID-NOT-RUN",out
    return ("CAUGHT" if " failed" in out else "PASSED"),out
def main():
    path=os.path.join(ROOT,FILE); orig=open(path,encoding="utf-8").read(); code,out=run(); print("预检:",code)
    if code!="PASSED": print(out[-500:]); return 2
    ok=True
    for mid,desc,old,new in ARMS:
        if orig.count(old)!=1: print(mid,"needle",orig.count(old)); ok=False; continue
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=open(path,"rb").read()==orig.encode("utf-8"); print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
