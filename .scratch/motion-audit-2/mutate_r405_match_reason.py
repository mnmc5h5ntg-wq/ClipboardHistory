#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R405 变异对照：QuickPick 的来源命中理由必须进入行文案、也必须在帧上可见。"""
import os, subprocess, sys, time, tempfile, shutil
ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
MODEL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Utilities/QuickPickModel.swift")
CTRL = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/QuickPickController.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
MODEL_NEEDLE = '''        guard let name = entry.sourceAppName, !name.isEmpty,
              name.localizedCaseInsensitiveContains(needle),
              !matchesNonSource(entry, needle: needle) else { return nil }
        return name'''
MODEL_MUTANT = '''        guard let name = entry.sourceAppName, !name.isEmpty,
              name.localizedCaseInsensitiveContains(needle),
              !matchesNonSource(entry, needle: needle) else { return nil }
        // MUTANT: 来源命中不再给理由
        return nil'''
# R430 重钉：时间从标题串里拆走后，旧针依赖的那行注释也改了位置；
# 针改钉「理由 append + 紧接着的 return」这一整段（M1052 的变异是删掉理由）。
CTRL_NEEDLE = '''        if let reason = QuickPickModel.sourceMatchReason(for: entry, query: query) {
            pieces.append("来自 \\(reason)")
        }
        return pieces.joined(separator: "  ·  ")'''
CTRL_MUTANT = '''        return pieces.joined(separator: "  ·  ")'''
MUTATIONS = [
    ("M1051", "来源命中不再给出理由（源/管线判据）", MODEL, MODEL_NEEDLE, MODEL_MUTANT,
     "UICaptureTests/testQuickPickSourceOnlyMatchCarriesItsReason",
     ["来源是唯一命中依据的行没有把理由写出来"]),
    ("M1052", "来源命中理由不进入行文案（像素判据）", CTRL, CTRL_NEEDLE, CTRL_MUTANT,
     "UICaptureTests/testQuickPickSourceMatchReasonExtendsTheTypedRow",
     ["来源理由没有画出来"]),
]
def read(p):
    with open(p, encoding="utf-8") as h: return h.read()
def run(f):
    shots = tempfile.mkdtemp(prefix="r405-mut-shots-"); env=dict(BASE_ENV); env["CLIPBOARD_HISTORY_UI_SHOTS"]=shots
    try:
        p=subprocess.run(["swift","test","--filter",f],cwd=ROOT,capture_output=True,text=True,env=env,timeout=1800)
    finally:
        shutil.rmtree(shots,ignore_errors=True)
    out=p.stdout+p.stderr
    verdicts=[l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts: return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"),out,[]
    if "error:" in out and not any(" failed" in l for l in verdicts): return "BROKEN-MUTATION",out,[]
    failed=[l.split("]")[0].replace("Test Case '-[","") for l in verdicts if " failed" in l]
    return ("CAUGHT" if p.returncode!=0 else "ESCAPED"),out,failed
def main():
    originals={p:read(p) for p in (MODEL,CTRL)}
    for mid,_,path,old,new,_f,_n in MUTATIONS:
        if read(path).count(old)!=1: raise SystemExit("预检中止：%s 针 %d 次"%(mid,read(path).count(old)))
        if old in new: raise SystemExit("预检中止：%s 变异文含原文"%mid)
    filters=[]
    for row in MUTATIONS:
        if row[5] not in filters: filters.append(row[5])
    for f in filters:
        code,out,_=run(f)
        if code!="ESCAPED": raise SystemExit("预检失败 %s %s\n%s"%(f,code,out[-1500:]))
    print("预检 OK "+",".join(filters))
    caught=wrong=0
    for mid,desc,path,old,new,f,needles in MUTATIONS:
        stamp=time.time()+2
        open(path,"w",encoding="utf-8").write(originals[path].replace(old,new,1)); os.utime(path,(stamp,stamp))
        landed=old not in read(path) and new in read(path)
        try: code,out,failed=run(f)
        finally:
            open(path,"w",encoding="utf-8").write(originals[path]); os.utime(path,(stamp+1,stamp+1))
        hit=all(n in out for n in needles); right=code=="CAUGHT" and hit and landed
        caught+=1 if code=="CAUGHT" else 0; wrong+=0 if right else 1
        print("%s %s ⇒ %s 红得对=%s 命中=%s 红在 %s 还原干净=%s"%(mid,desc,code,right,hit,failed,read(path)==originals[path]))
    clean=all(read(p)==originals[p] for p in originals); reruns=[]
    for f in filters:
        c,_,_=run(f); reruns.append("%s=%s"%(f,c))
    print("还原后复跑："+" ".join(reruns))
    print("R405_MATCH_REASON_MUTATE 刀=%d CAUGHT=%d 红得不对=%d RESTORE_CLEAN=%s"%(len(MUTATIONS),caught,wrong,"yes" if clean else "NO"))
    return 0 if (caught==len(MUTATIONS) and wrong==0 and clean and all(s.endswith("=ESCAPED") for s in reruns)) else 1
if __name__=="__main__": sys.exit(main())
