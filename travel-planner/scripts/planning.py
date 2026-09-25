#!/usr/bin/env python3
"""Assess intake and validate/export a planning work package; does not render C14 HTML."""
import argparse, copy, datetime as dt, json, math, pathlib, urllib.parse

class Invalid(ValueError): pass

def require(ok, message):
    if not ok: raise Invalid(message)

def assess(brief):
    links=bool(brief.get('links')); existing=bool(brief.get('fixed') or brief.get('draft'))
    primary='existing' if existing else 'links' if links else 'explore'
    missing=[k for k in ['origin','start_date','end_date','travelers'] if not brief.get(k)]
    tasks=[]
    if existing: tasks.append('preserve_fixed_and_audit_conflicts')
    if links: tasks.append('read_supplied_material_before_search')
    if missing: tasks.append('ask_missing_constraints')
    if not brief.get('destination'): tasks.append('compare_destination_directions')
    else: tasks.append('plan_within_destination')
    return {'primary':primary,'has_links':links,'has_existing_plan':existing,'questions':missing[:3],
            'remaining_missing':missing[3:],'next_tasks':tasks,
            'exact_price_ready':all(brief.get(k) for k in ['origin','destination','start_date','end_date','travelers'])}

def finite(v): return type(v) in (int,float) and math.isfinite(v)
def cents(v): return type(v) is int and v>=0

def parse_date(s):
    try: return dt.date.fromisoformat(s)
    except (ValueError,TypeError): raise Invalid('日期需要YYYY-MM-DD') from None

def instant(s):
    try:
        value=dt.datetime.fromisoformat(s)
        require(value.tzinfo is not None,'活动时间必须带时区')
        return value
    except (TypeError,ValueError): raise Invalid('活动时间必须为含时区ISO8601') from None

def public_url(value):
    url=urllib.parse.urlparse(value)
    require(url.scheme=='https' and bool(url.netloc) and not url.username and not url.password,'公开URL必须HTTPS且不含账号凭证')
    require(not any(k.lower() in ('key','token','access_token','xsec_token','cookie','authorization') for k,_ in urllib.parse.parse_qsl(url.query)),'公开URL含凭证/访问参数')

def validate(plan, directory=None):
    require(isinstance(plan,dict) and plan.get('planning_version')==1,'不支持的planning_version')
    require(type(plan.get('demo')) is bool,'demo需明确布尔值')
    require(type(plan.get('revision')) is int and plan['revision']>0,'revision需正整数')
    require(plan.get('status') in ('research','review','confirmed'),'未知工作包状态')
    brief=plan['brief'];start,end=parse_date(brief['start_date']),parse_date(brief['end_date'])
    require(start<=end,'旅行结束早于开始')
    require(type(brief.get('travelers')) is int and brief['travelers']>0,'人数需要正整数')
    require(isinstance(brief.get('currency'),str) and len(brief['currency'])==3,'需要统一币种')
    tables={}
    for field in ['sources','places','activities','transfers','costs','media','decisions','pending','packing']:
        values=plan.get(field);require(isinstance(values,list),field+'需要列表')
        require(all(isinstance(v,dict) and isinstance(v.get('id'),str) and v['id'] for v in values),field+'缺稳定ID')
        tables[field]={v['id']:v for v in values};require(len(tables[field])==len(values),field+'存在重复ID')
    def refs(obj, needed=False):
        ids=obj.get('source_ids',[]);require(isinstance(ids,list),'source_ids需列表')
        require(not needed or bool(ids),'该记录需要来源')
        require(all(i in tables['sources'] for i in ids),'引用不存在的来源')
        if needed: require(any(tables['sources'][i]['status'] in ('read','user_provided','demo') for i in ids),'摘要/无法读取的来源不足以支持已核实数据')
    for s in plan['sources']:
        require(s.get('status') in ('read','snippet','unavailable','user_provided','demo'),'来源读取状态无效')
        require(plan['demo'] or s['status']!='demo','正式工作包不能使用演示证据')
        require(s.get('supports') and (s.get('url') or s.get('material')),'来源需要材料与支持内容')
        if s.get('url'):
            public_url(s['url'])
    for p in plan['places']:
        require(p.get('name') and p.get('city'),'地点缺名称或城市')
        require(p.get('selection') in ('candidate','selected','booked'),'地点选择状态无效');refs(p)
        c=p.get('coordinates')
        if c is not None:
            require(isinstance(c,dict) and c.get('crs') in ('WGS84','GCJ02'),'坐标系必须明确')
            require(finite(c.get('lat')) and finite(c.get('lng')) and abs(c['lat'])<=90 and abs(c['lng'])<=180,'坐标无效');refs(c,True)
    by_day={}
    for a in plan['activities']:
        require(a.get('kind') in ('journey','hotel','meal','place','stay','rest'),'活动类型无效')
        begin,finish=instant(a['start']),instant(a['end']);require(begin<finish,'活动结束必须晚于开始')
        require(start<=begin.date()<=end and start<=finish.date()<=end,'活动超出出行日期')
        require(a.get('place_id') is None or a['place_id'] in tables['places'],'活动引用地点不存在');refs(a)
        require(all(pid in tables['places'] for pid in a.get('candidate_place_ids',[])),'候选引用地点不存在')
        for key in ('departure_place_id','arrival_place_id'):
            if a.get('kind')=='journey': require(a.get(key) in tables['places'],'城际活动缺起终点')
        by_day.setdefault(begin.date(),[]).append((begin,finish,a))
    for activities in by_day.values():
        ordered=sorted(activities,key=lambda x:x[0])
        for previous,current in zip(ordered,ordered[1:]): require(previous[1]<=current[0],'活动时间重叠：'+current[2]['id'])
    # Cross-midnight overlaps must not escape per-day checks.
    ordered=sorted(plan['activities'],key=lambda a:instant(a['start']))
    for a,b in zip(ordered,ordered[1:]): require(instant(a['end'])<=instant(b['start']),'跨日活动时间重叠')
    pairs=set();warnings=[]
    for t in plan['transfers']:
        a=tables['activities'].get(t.get('from_activity_id'));b=tables['activities'].get(t.get('to_activity_id'))
        require(a is not None and b is not None,'转场引用活动不存在')
        require(ordered.index(b)==ordered.index(a)+1,'转场必须连接相邻活动')
        pair=(a['id'],b['id']);require(pair not in pairs,'重复转场');pairs.add(pair)
        expected_from=a.get('arrival_place_id') if a['kind']=='journey' else a.get('place_id')
        expected_to=b.get('departure_place_id') if b['kind']=='journey' else b.get('place_id')
        require(t.get('status') in ('ready','unknown','stale'),'转场状态无效')
        if t['status']=='ready':
            require(t.get('from_place_id')==expected_from and t.get('to_place_id')==expected_to,'旧转场起终点与当前选择不一致')
            for pid in [expected_from,expected_to]: require(pid in tables['places'] and tables['places'][pid].get('coordinates'),'已就绪路线需要准确地点坐标')
            refs(t,True);options=t.get('options',[])
            require(len({o['id'] for o in options})==len(options),'方案ID重复')
            selected=next((o for o in options if o['id']==t.get('recommended')),None);require(selected is not None,'缺少推荐通勤方案')
            for o in options:
                require(o.get('mode') in ('walk','bus','car') and finite(o.get('duration_minutes')) and o['duration_minutes']>=0 and finite(o.get('distance_meters')) and o['distance_meters']>=0,'路线距离/时间/方式无效')
                require(o.get('price_cents') is None or cents(o['price_cents']),'路线金额无效')
            require((instant(b['start'])-instant(a['end'])).total_seconds()/60>=selected['duration_minutes'],'转场时间不足')
        else: warnings.append('通勤未核实：'+t['id'])
    for a,b in zip(ordered,ordered[1:]):
        if instant(a['start']).date()==instant(b['start']).date() and (a['id'],b['id']) not in pairs: warnings.append('缺少相邻转场：'+a['id']+' → '+b['id'])
    low=high=paid=unknown=0
    for c in plan['costs']:
        targets=[('activities',c.get('activity_id')),('transfers',c.get('transfer_id'))];targets=[(k,i) for k,i in targets if i is not None]
        require(len(targets)==1 and targets[0][1] in tables[targets[0][0]],'费用必须只关联一个存在的活动/转场')
        require(c.get('status') in ('quote','reference','estimate','actual','unknown'),'费用状态无效')
        require(type(c.get('quantity')) is int and c['quantity']>0 and c.get('unit'),'费用数量/单位缺失')
        require(cents(c.get('paid_cents')),'已付金额需非负整数分');paid+=c['paid_cents']
        if c['status']=='unknown':
            require(c.get('low_cents') is None and c.get('high_cents') is None,'未知费用不能用0或数字冒充');unknown+=1
        else:
            require(cents(c.get('low_cents')) and cents(c.get('high_cents')) and c['low_cents']<=c['high_cents'],'费用区间无效')
            if c['status']=='actual': require(c['low_cents']==c['high_cents'],'实际金额不应为区间')
            low+=c['low_cents']*c['quantity'];high+=c['high_cents']*c['quantity'];refs(c,c['status'] in ('quote','reference','actual'))
        if targets[0][0]=='transfers' and tables['transfers'][targets[0][1]]['status']!='ready': require(c['status'] in ('unknown','estimate'),'未核实路线不得引用已确认报价')
    covered={c.get('activity_id') for c in plan['costs']}
    for a in plan['activities']:
        if a['kind'] in ('journey','hotel','meal','place') and a['id'] not in covered:
            warnings.append('费用覆盖待确认：'+a['id'])
    if paid>high: warnings.append('已付超过已知预算上限，需核对未知费用或退款')
    for m in plan['media']:
        if m.get('url'): public_url(m['url'])
        require(m.get('use_status') in ('permitted','reference_only','unknown'),'图片使用状态无效');refs(m,True)
        if m.get('place_id'): require(m['place_id'] in tables['places'],'图片地点不存在')
        if m['use_status']=='permitted': require(m.get('credit') and (m.get('path') or m.get('url')),'可用图片缺署名/素材')
        if m.get('path'):
            path=pathlib.Path(m['path']);require(not path.is_absolute() and '..' not in path.parts,'图片路径越界')
            if directory is not None: require((directory/path).resolve().is_relative_to(directory.resolve()) and (directory/path).is_file(),'图片不存在或路径越界')
    for w in plan.get('weather',[]):
        require(start<=parse_date(w['date'])<=end,'天气不属于游玩日期');require(w.get('status') in ('forecast','unknown','historical'),'天气状态无效')
        if w['status']=='forecast':refs(w,True);require(finite(w.get('low')) and finite(w.get('high')) and w['low']<=w['high'],'预报温度不完整')
    for m in plan.get('maps',[]):
        require(m.get('scope')=='all' or start<=parse_date(m.get('scope'))<=end,'地图日期不属于行程')
        public_url(m.get('url',''))
        url=urllib.parse.urlparse(m['url'])
        require(url.netloc in ('www.xiaotouai.online','124.221.232.250') and url.path=='/v1/maps/image','地图必须来自旅行服务')
        require(instant(m.get('expires_at')) is not None,'地图缺少到期时间')
        overlay=m.get('overlay',{})
        require(isinstance(overlay,dict),'地图覆盖层无效')
        for path in overlay.get('paths',[]):
            import re
            require(bool(re.fullmatch(r'#[0-9a-fA-F]{6}',path.get('color',''))),'地图颜色无效')
            require(all(isinstance(pt,list) and len(pt)==2 and all(finite(n) for n in pt) for pt in path.get('points',[])),'地图折线无效')
        for marker in overlay.get('markers',[]):
            require(all(finite(marker.get(k)) for k in ('x','y','lng','lat')) and isinstance(marker.get('label'),str),'地图标记无效')
    if plan['status']=='confirmed':
        require(any(d.get('confirmed') is True and d.get('revision')==plan['revision'] and d.get('scope')=='itinerary' for d in plan['decisions']),'当前版本尚无用户行程确认')
        require(not any(p.get('blocking') for p in plan['pending']),'仍有阻塞性待确认项')
    return {'valid':True,'warnings':warnings,'known_low_cents':low,'known_high_cents':high,'paid_cents':paid,'unknown_cost_items':unknown,'status':plan['status']}

def export(plan,directory=None):
    report=validate(plan,directory)
    # Allowlist: private research and arbitrary extra fields never flow to the page.
    fields={'places':'id name city address selection coordinates source_ids','activities':'id kind start end place_id title fixed departure_place_id arrival_place_id booking_state source_ids vehicle description candidate_place_ids','transfers':'id from_activity_id to_activity_id from_place_id to_place_id status recommended options source_ids checked_at','costs':'id activity_id transfer_id category unit quantity low_cents high_cents status paid_cents source_ids conditions checked_at','media':'id role place_id path url kind use_status credit source_ids','weather':'date city timezone status low high rain_probability checked_at source_ids clothing carry','packing':'id label reason source_ids','sources':'id kind status title url material checked_at supports','pending':'id scope question blocking'}
    packet={'packet_version':1,'revision':plan['revision'],'status':plan['status'],'demo':plan['demo'],'brief':{k:plan['brief'].get(k) for k in ['origin','destination','start_date','end_date','travelers','currency','timezone']},'budget_summary':report}
    packet['maps']=[{k:m[k] for k in ('scope','url','expires_at','overlay') if k in m} for m in plan.get('maps',[])]
    for m in packet['maps']:
        if 'overlay' in m:
            m['overlay']={'paths':[{k:path[k] for k in ('color','points')} for path in m['overlay'].get('paths',[])],'markers':[{k:marker[k] for k in ('x','y','lng','lat','label')} for marker in m['overlay'].get('markers',[])]}
    packet['days']=[{k:copy.deepcopy(d[k]) for k in ('date','title') if k in d} for d in plan.get('days',[])]
    for field,keys in fields.items(): packet[field]=[{k:copy.deepcopy(v[k]) for k in keys.split() if k in v} for v in plan.get(field,[]) if field!='media' or v['use_status']=='permitted']
    for place in packet['places']:
        if place.get('coordinates'):
            place['coordinates']={k:v for k,v in place['coordinates'].items() if k in ('lat','lng','crs','source_ids')}
    for transfer in packet['transfers']:
        transfer['options']=[{k:v for k,v in o.items() if k in ('id','mode','duration_minutes','distance_meters','price_cents','basis','lines','reason')} for o in transfer.get('options',[])]
    return packet

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['assess','validate','export']);p.add_argument('input',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path);args=p.parse_args()
    try:
        data=json.loads(args.input.read_text());result=assess(data) if args.command=='assess' else validate(data,args.input.parent) if args.command=='validate' else export(data,args.input.parent)
        text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.out:
            require(not args.out.exists(),'输出已存在，请使用新路径以保留旧版本');args.out.write_text(text)
        else:print(text,end='')
    except (Invalid,KeyError,TypeError,ValueError,OSError) as error:p.exit(1,'规划工作包检查失败：'+str(error)+'\n')
if __name__=='__main__':main()
