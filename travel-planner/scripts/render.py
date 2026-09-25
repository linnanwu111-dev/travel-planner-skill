#!/usr/bin/env python3
"""Build the current C page from a validated planning work package."""
import argparse,hashlib,json,pathlib,shutil,tempfile,html
import planning,delivery_check

def build(input_path,out):
    input_path=pathlib.Path(input_path);out=pathlib.Path(out)
    if out.exists():raise ValueError('输出目录已存在；请生成新目录，保留用户已有修改')
    plan=json.loads(input_path.read_text());packet=planning.export(plan,input_path.parent)
    audit=delivery_check.check(plan,input_path.parent) if not plan.get('demo') else {'ready':True,'issues':[],'scope':'合成演示，不代表真实调研'}
    if plan.get('status')=='confirmed' and not audit['ready']:raise ValueError('正式交付缺少研究证据：'+'；'.join(audit['issues']))
    if not packet['activities']:raise ValueError('至少需要一个活动才能生成页面')
    packet['trip_id']=plan.get('trip_id') or hashlib.sha256(json.dumps({k:packet['brief'][k] for k in ['origin','destination','start_date','end_date']},sort_keys=True).encode()).hexdigest()[:20]
    assets=pathlib.Path(__file__).resolve().parents[1]/'assets/current'
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as temp:
        stage=pathlib.Path(temp)/'page';stage.mkdir();shutil.copytree(assets,stage/'assets',ignore=shutil.ignore_patterns('template.html','serve.py'))
        shutil.copy2(assets/'serve.py',stage/'serve.py')
        (stage/'delivery-check.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
        for m in packet['media']:
            if m.get('path'):
                source=input_path.parent/m['path'];rel=pathlib.Path('media')/(hashlib.sha256(source.read_bytes()).hexdigest()[:16]+source.suffix.lower())
                if source.suffix.lower() not in ('.jpg','.jpeg','.png','.webp','.gif'):raise ValueError('图片仅支持jpg/png/webp/gif')
                (stage/rel).parent.mkdir(exist_ok=True);shutil.copy2(source,stage/rel);m['path']=rel.as_posix()
        payload=json.dumps(packet,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
        page=(assets/'template.html').read_text().replace('__PAGE_PACKET__',payload)
        credits='<h1>图片署名</h1>'+''.join('<p>'+html.escape(m.get('credit',''))+'</p>' for m in packet['media'] if m.get('credit'))
        (stage/'image-credits.html').write_text('<!doctype html><meta charset="utf-8"><title>图片署名</title>'+credits)
        page=page.replace('</main>','<footer><a href="image-credits.html">图片署名</a></footer></main>')
        (stage/'index.html').write_text(page)
        (stage/'page-packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
        (stage/'README.md').write_text('在本目录运行 python3 serve.py，通过 http://127.0.0.1:8766/index.html 打开攻略（端口占用可加 --port 8767）。按 Ctrl+C 停止服务。直接双击 index.html 仅离线阅读正文与地点连线，不请求地理底图。地图底图、远程图片与外部导航需要网络；HTTP 打开不保证第三方服务可用。\n页面调整保存在本浏览器，可导出trip-changes.json交回Agent；新版本不会自动覆盖旧版本调整。\n工作包需私有保留，不要直接公开原始研究材料。\n')
        # Retain only public, human-readable evidence, not the private planning brief.
        (stage/'sources.json').write_text(json.dumps(packet['sources'],ensure_ascii=False,indent=2)+'\n')
        stage.rename(out)
    return {'output':str(out.resolve()),'revision':packet['revision'],'days':(planning.parse_date(packet['brief']['end_date'])-planning.parse_date(packet['brief']['start_date'])).days+1,'warnings':packet['budget_summary']['warnings']+audit['issues']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);a=p.parse_args()
    try:print(json.dumps(build(a.input,a.out),ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as e:p.exit(1,'生成失败：'+str(e)+'\n')
if __name__=='__main__':main()
