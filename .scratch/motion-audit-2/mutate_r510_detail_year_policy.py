#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R510 变异表：详情时间戳沿用列表年份策略（M1366–M1367）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Utilities/ClipboardDateFormatters.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="TimestampYearPolicyTests/testDetailTimestampUsesTheYearPolicyLikeTheList"
ARMS=[
  ("M1366","详情不再按年份策略省年（永远带年）",
   '''        TimestampYearPolicy.showsYear(for: date, relativeTo: reference)
            ? detailTimestamp.string(from: date)
            : detailTimestampCompact.string(from: date)''',
   '''        detailTimestamp.string(from: date)'''),
  ("M1367","紧凑详情格式回到短横线",
   '''        formatter.dateFormat = "M月d日 HH:mm:ss"''',
   '''        formatter.dateFormat = "M-d HH:mm:ss"'''),
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
        n=orig.count(old)
        if n!=1: print(mid,"needle",n); ok=False; continue
        open(path,"w",encoding="utf-8").write(orig.replace(old,new))
        try: code,out=run()
        finally: open(path,"w",encoding="utf-8").write(orig)
        print("%s: %s"%(mid,code)); ok=ok and code=="CAUGHT"
    clean=open(path,"rb").read()==orig.encode("utf-8"); print("RESTORE_CLEAN="+("yes" if clean else "NO"))
    return 0 if ok and clean else 1
if __name__=="__main__": sys.exit(main())
