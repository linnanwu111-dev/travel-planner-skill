#!/usr/bin/env python3
"""Persistent serial research pacing. No credentials or page content are stored."""
import argparse, datetime, fcntl, json, random, time
from pathlib import Path

STOPS={'login_required','verification_required','risk_blocked','rate_limited','access_denied','technical_error','empty_result'}

def transition(state, action, outcome=None, now=None, rng=None):
    now=time.time() if now is None else now
    rng=rng or random.SystemRandom()
    state=dict(state)
    if action=='login-completed':
        if state.get('status')!='login_required':
            return state, {'allowed':False,'reason':'Only a pending ordinary login can resume this way.'}
        state['status']='ready'
        return state, {'allowed':True,'reason':'User reports login completed; check visible page before searching.'}
    if action=='report':
        if not state.get('in_flight'):
            return state, {'allowed':False,'reason':'No reserved operation.'}
        state['in_flight']=False
        state['status']=outcome if outcome in STOPS else 'ready'
        state['next_at']=now+rng.uniform(15,30)
        return state, {'allowed':outcome=='success','status':state['status']}
    if state.get('status') in STOPS:
        return state, {'allowed':False,'reason':state['status'],'next_step':'Pause; ordinary login may resume after user confirmation. Risk/verification stops require manual review, not automatic retries.'}
    if state.get('in_flight'):
        return state, {'allowed':False,'reason':'An operation is already reserved; report its result before another.'}
    today=datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d')
    if state.get('day')!=today: state.update(day=today,search=0,detail=0)
    wait=state.get('next_at',0)-now
    if wait>0:return state, {'allowed':False,'reason':'pacing','wait_seconds':round(wait,1)}
    cap={'search':2,'detail':3}[action]
    if state.get(action,0)>=cap:return state, {'allowed':False,'reason':'daily_sample_cap'}
    state[action]=state.get(action,0)+1
    state.update(in_flight=True,status='running',last_action=action,last_at=now)
    return state, {'allowed':True,'action':action,'limit':3 if action=='search' else 1}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir',type=Path,required=True)
    p.add_argument('--platform',choices=['xiaohongshu','dianping'],required=True)
    p.add_argument('action',choices=['search','detail','report','login-completed'])
    p.add_argument('--outcome',choices=['success',*sorted(STOPS)])
    a=p.parse_args()
    if a.action=='report' and not a.outcome:p.error('report requires --outcome')
    a.state_dir.mkdir(parents=True,exist_ok=True)
    dest=a.state_dir/(a.platform+'.json')
    with (a.state_dir/(a.platform+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads(dest.read_text()) if dest.exists() else {}
        state,result=transition(state,a.action,a.outcome)
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['allowed'] else 2

if __name__=='__main__':raise SystemExit(main())
