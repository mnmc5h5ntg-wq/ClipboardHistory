#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R496 变异表：浮层候选行命中高亮（M1339–M1340）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"; FILE="Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}; TEST="UICaptureTests/testQuickPickTypedRowsHighlightTheMatchedReason"
ARMS=[
  ("M1339","命中高亮永不画",
   '''    var titleHighlightEnabled = true''',
   '''    var titleHighlightEnabled = false'''),
  ("M1340","整行标题都高亮（不按命中段）",
   '''        for span in spans {
            result.addAttribute(.backgroundColor, value: DetailTypography.highlightColor,
                                range: NSRange(location: span.location, length: span.length))
        }''',
   '''        result.addAttribute(.backgroundColor, value: DetailTypography.highlightColor,
                            range: NSRange(location: 0, length: (title as NSString).length))'''),
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
