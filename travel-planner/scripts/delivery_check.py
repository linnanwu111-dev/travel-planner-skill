#!/usr/bin/env python3
"""Check durable evidence coverage, not the truth of source claims."""
import argparse,json,pathlib
from planning import media_permission_issue

def check(plan,root):
    root=pathlib.Path(root).resolve();issues=[]
    def artifact(value):
        if not isinstance(value,str) or not value:return False
        p=(root/value).resolve()
        return p.is_relative_to(root) and p.is_file() and p.stat().st_size>0
    for s in plan.get('sources',[]):
        if s.get('status')=='read' and not artifact(s.get('evidence_path')):
            issues.append('来源 '+s['id']+' 标记已读，但缺少私有 evidence_path 原始摘录/返回文件')
    media=[m for m in plan.get('media',[]) if m.get('use_status')=='permitted']
    if not plan.get('demo'):
        for m in media:
            issue=media_permission_issue(m,root)
            if issue: issues.append('图片 '+str(m.get('id','?'))+'：'+issue)
    missing=[]
    if not any(m.get('role')=='cover' for m in media):missing.append('cover')
    for pid in sorted({a.get('place_id') for a in plan.get('activities',[]) if a.get('kind') in ('place','hotel','stay','meal')}-{None}):
        if not any(m.get('role')=='place' and m.get('place_id')==pid for m in media):missing.append(pid)
    logpath=root/'research-log.json'
    try:log=json.loads(logpath.read_text())
    except (OSError,ValueError):log={}
    if log.get('revision')!=plan.get('revision'):issues.append('research-log.json 缺失或不对应当前 revision')
    channels=log.get('channels',{})
    for name in ['web_images','xiaohongshu','dianping','flyai','amap']:
        c=channels.get(name,{})
        if c.get('status')=='read':
            if not artifact(c.get('evidence_path')):issues.append(name+' 查询缺少留存证据')
        elif c.get('status')=='not_needed':
            if not c.get('reason'):issues.append(name+' 未说明无需调用的原因')
        elif c.get('status')=='alternative':
            if not c.get('reason') or not artifact(c.get('evidence_path')):issues.append(name+' 替代查询缺少原因或证据')
        else:issues.append(name+' 尚未完成查询或说明处理结果')
    exceptions=log.get('image_exceptions',{})
    for target in missing:
        ex=exceptions.get(target,{})
        if not ex.get('reason') or not artifact(ex.get('evidence_path')):issues.append('缺少配图或已告知用户的查找失败记录：'+target)
    return {'ready':not issues,'issues':issues,'scope':'仅检查证据文件与覆盖情况；不证明内容真实，也不替代浏览器验收'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=pathlib.Path);a=p.parse_args()
    result=check(json.loads(a.input.read_text()),a.input.parent);print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['ready'] else 1)
if __name__=='__main__':main()
