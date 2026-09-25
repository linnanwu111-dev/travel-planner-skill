#!/usr/bin/env python3
"""Query the hosted travel service. Credentials stay in ~/.travel-planner/service.json."""
import argparse,datetime,getpass,json,math,os,pathlib,subprocess,sys,time,uuid
BASE=os.environ.get('TRAVEL_SERVICE_URL','https://124.221.232.250').rstrip('/')
if BASE not in ('https://124.221.232.250','https://www.xiaotouai.online'):raise ValueError('仅支持已配置的HTTPS旅行服务入口')
CONFIG=pathlib.Path.home()/'.travel-planner/service.json'
ENDPOINTS={'places':'/v1/places/search','routes':'/v1/routes/search','trains':'/v1/trains/search','hotels':'/v1/hotels/search','maps':'/v1/maps/create'}
def connection_error():
    # A public health probe only: never send credentials or itinerary data over HTTP.
    try:
        probe=subprocess.run(['curl','--silent','--show-error','--connect-timeout','3','--max-time','5','--proto','=http','--dump-header','-','--output',os.devnull,BASE.replace('https://','http://',1)+'/health'],text=True,capture_output=True)
        headers=probe.stdout.lower()
        if probe.returncode==0 and 'location: https://dnspod.qcloud.com/static/webblock.html' in headers:
            return '检测到腾讯云域名备案拦截：请服务维护者完成备案/接入并复验；无需重装Skill或更换高德、FlyAI密钥。不重试，不降级为HTTP查询。'
    except (OSError,subprocess.SubprocessError):
        pass
    return '旅行服务连接失败，未确认具体原因；请检查服务状态及网络，不自动反复重试'

def save_config(value):
    CONFIG.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(CONFIG,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f)
    os.chmod(CONFIG,0o600)

def call(path,data,token=''):
    r=subprocess.run(['curl','--silent','--show-error','--connect-timeout','10','--max-time','85','--proto','=https','--header','@-','--header','Content-Type: application/json','--data-binary',json.dumps(data,ensure_ascii=False),BASE+path],input=('Authorization: Bearer '+token) if token else '',text=True,capture_output=True)
    if r.returncode:raise ValueError(connection_error())
    try:result=json.loads(r.stdout)
    except ValueError:raise ValueError('旅行服务未返回JSON') from None
    if 'error' in result:raise ValueError('旅行服务：'+str(result['error']))
    return result

def access_token():
    config=json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    token=config.get('token','')
    if token and config.get('mode')!='trial':return token
    if token and config.get('expires_at',0)>time.time()+300:return token
    installation=config.get('installation_id') or uuid.uuid4().hex
    # Save stable installation identity before enrollment, so retry cannot reset quotas.
    config['installation_id']=installation;save_config(config)
    result=call('/v1/access/trial',{'installation_id':installation})
    if not result.get('token') or not isinstance(result.get('expires_at'),(int,float)):raise ValueError('体验凭证返回无效')
    save_config(dict(result,installation_id=installation))
    return result['token']

def request(kind,data):
    token=access_token()
    if not isinstance(token,str) or not token or '\n' in token or '\r' in token:raise ValueError('服务凭证无效')
    return call(ENDPOINTS[kind],data,token)

# WGS84 conversion ported from bundled Wandergis coordtransform.js (MIT).
# See assets/current/coordtransform-LICENSE for the upstream license.
def gcj_point(c):
    lng,lat=c['lng'],c['lat']
    if c['crs']=='GCJ02':return [lng,lat]
    if c['crs']!='WGS84':raise ValueError('Unknown coordinate system')
    if not (73.66<lng<135.05 and 3.86<lat<53.55):return [lng,lat]
    x,y=lng-105,lat-35;pi=math.pi;sin=math.sin
    common=(20*sin(6*x*pi)+20*sin(2*x*pi))*2/3
    dy=-100+2*x+3*y+.2*y*y+.1*x*y+.2*math.sqrt(abs(x))+common
    dy+=(20*sin(y*pi)+40*sin(y/3*pi))*2/3+(160*sin(y/12*pi)+320*sin(y*pi/30))*2/3
    dx=300+x+2*y+.1*x*x+.1*x*y+.1*math.sqrt(abs(x))+common
    dx+=(20*sin(x*pi)+40*sin(x/3*pi))*2/3+(150*sin(x/12*pi)+300*sin(x/30*pi))*2/3
    rad=lat/180*pi;ee=.00669342162296594323;a=6378245;magic=1-ee*sin(rad)**2
    dy=dy*180/((a*(1-ee))/(magic*math.sqrt(magic))*pi)
    dx=dx*180/(a/math.sqrt(magic)*math.cos(rad)*pi)
    return [lng+dx,lat+dy]

def map_days(plan):
    places={p['id']:p for p in plan['places']};zone=__import__('zoneinfo').ZoneInfo(plan['brief'].get('timezone') or 'Asia/Shanghai')
    def date(value):return datetime.datetime.fromisoformat(value).astimezone(zone).date()
    days=[];start=datetime.date.fromisoformat(plan['brief']['start_date']);end=datetime.date.fromisoformat(plan['brief']['end_date'])
    for offset in range((end-start).days+1):
        d=start+datetime.timedelta(days=offset);rows=sorted([a for a in plan['activities'] if date(a['start'])<=d<=date(a['end'])],key=lambda a:a['start'])
        cities={places[a['place_id']]['city'] for a in rows if a['kind']!='journey' and a.get('place_id') in places} or {plan['brief']['destination']}
        points=[]
        for a in rows:
            ids=[a.get('departure_place_id'),a.get('arrival_place_id')] if a['kind']=='journey' else [a.get('place_id')]
            for pid in ids:
                p=places.get(pid)
                if not p or p['city'] not in cities:continue
                c=p.get('coordinates')
                if not c:raise ValueError('地图地点缺坐标：'+p['name'])
                point=gcj_point(c)
                if not points or point!=points[-1]:points.append(point)
        if points:days.append({'date':d.isoformat(),'points':points})
    if not days:raise ValueError('无地图地点')
    return days

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('configure')
    q=sub.add_parser('query');q.add_argument('kind',choices=ENDPOINTS);q.add_argument('--input',type=pathlib.Path,required=True);q.add_argument('--out',type=pathlib.Path,required=True)
    m=sub.add_parser('prepare-maps');m.add_argument('plan',type=pathlib.Path);m.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    try:
        if a.command=='configure':
            token=getpass.getpass('旅行服务访问凭证（隐藏输入）：').strip()
            if not token:raise ValueError('凭证不能为空')
            CONFIG.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            fd=os.open(CONFIG,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
            with os.fdopen(fd,'w') as f:json.dump({'token':token},f)
            os.chmod(CONFIG,0o600);print('凭证已保存，未输出内容。');return
        if a.out.exists():raise ValueError('输出已存在，请使用新文件以保留当前版本')
        if a.command=='query':result=request(a.kind,json.loads(a.input.read_text()))
        else:
            plan=json.loads(a.plan.read_text());result=plan
            response=request('maps',{'days':map_days(plan),'end_date':plan['brief']['end_date'],'allowed_points':[gcj_point(p['coordinates']) for p in plan['places'] if p.get('coordinates') and 73<=p['coordinates']['lng']<=136 and 3<=p['coordinates']['lat']<=54]})
            plan['maps']=response['result']['maps']
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('已保存：'+str(a.out))
    except (ValueError,OSError,KeyError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
