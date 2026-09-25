#!/usr/bin/env python3
"""Read-only POI/route lookup. Key stays in AMAP_KEY or ~/.amap/config.json."""
import argparse, json, os, pathlib, urllib.parse, urllib.request
from datetime import datetime, timezone

def request(path, params):
    key = os.environ.get('AMAP_KEY') or os.environ.get('AMAP_API_KEY')
    config = pathlib.Path.home()/'.amap/config.json'
    if not key and config.exists():
        key = json.loads(config.read_text()).get('key')
    if not key:
        raise ValueError('尚未配置高德 Web 服务 Key')
    url = 'https://restapi.amap.com'+path+'?'+urllib.parse.urlencode({**params, 'key': key, 'output': 'JSON'})
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.load(response)
    except Exception:
        raise ValueError('地图服务连接失败，请检查网络') from None
    if data.get('status') != '1':
        raise ValueError('地图服务返回错误：'+str(data.get('infocode', 'unknown')))
    return data

def search(name, city):
    if not name or not city or len(name)>160 or len(city)>60:
        raise ValueError('需要有效的地点名称和城市')
    data=request('/v3/place/text', {'keywords':name,'city':city,'citylimit':'true','offset':5,'page':1,'extensions':'base'})
    places=[]
    for p in data.get('pois',[]):
        if not p.get('location'): continue
        lng,lat=map(float,p['location'].split(','))
        places.append({'id':p['id'],'name':p['name'],'city':p.get('cityname') or city,'address':str(p.get('adname') or '')+str(p.get('address') or ''),'lng':lng,'lat':lat,'crs':'GCJ-02'})
    return {'places':places,'checked_at':datetime.now(timezone.utc).isoformat(),'source':'amap'}

def routes(origin, destination, city):
    for point in [origin,destination]:
        lng,lat=map(float,point.split(','))
        if not -180<=lng<=180 or not -90<=lat<=90: raise ValueError('坐标无效')
    base={'origin':origin,'destination':destination}
    result={}
    for mode,path,extra in [('walk','walking',{}),('car','driving',{'extensions':'all'}),('transit','transit/integrated',{'city':city,'cityd':city,'strategy':0,'extensions':'all'})]:
        result[mode]=request('/v3/direction/'+path,{**base,**extra})
    return {'origin_gcj02':origin,'destination_gcj02':destination,'city':city,'checked_at':datetime.now(timezone.utc).isoformat(),'source':'amap','results':result}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('search');s.add_argument('--name',required=True);s.add_argument('--city',required=True)
    r=sub.add_parser('routes');r.add_argument('--origin',required=True);r.add_argument('--destination',required=True);r.add_argument('--city',required=True)
    args=p.parse_args()
    try: result=search(args.name,args.city) if args.command=='search' else routes(args.origin,args.destination,args.city)
    except ValueError as e: p.exit(1,str(e)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
