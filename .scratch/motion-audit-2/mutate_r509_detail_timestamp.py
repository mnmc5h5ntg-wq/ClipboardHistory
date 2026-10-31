#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R509 变异表：详情时间戳与列表同一套日期语言（M1364–M1365）。"""
import os, subprocess, sys
ROOT="/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILE="Sources/ClipboardHistoryApp/Utilities/ClipboardDateFormatters.swift"
ENV={k:v for k,v in os.environ.items() if k!="SDKROOT"}
TEST="TimestampYearPolicyTests/testDetailTimestampUsesTheSameDateLanguageAsTheList"
ARMS=[
  ("M1364","详情时间戳回到 ISO 短横线",
   '''        formatter.dateFormat = "yyyy年M月d日 HH:mm:ss"''',
   '''        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"'''),
  ("M1365","列表时间戳也改成 ISO 短横线（两处一起漂）",
   '''    static let sidebarTimeWithYear: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy年M月d日 HH:mm"
        return formatter
    }()''',
   '''    static let sidebarTimeWithYear: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy-MM-dd HH:mm"
        return formatter
    }()'''),
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
