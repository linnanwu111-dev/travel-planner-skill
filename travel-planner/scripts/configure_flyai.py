#!/usr/bin/env python3
"""Run manually in a local terminal. Never paste the API key into chat."""
import getpass,json,os,tempfile
from pathlib import Path

def main():
    key=getpass.getpass('FlyAI API Key（输入不回显）：').strip()
    if not key:raise SystemExit('未输入，未修改配置。')
    directory=Path.home()/'.flyai';directory.mkdir(mode=0o700,exist_ok=True)
    path=directory/'config.json'
    data=json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(data,dict):raise SystemExit('现有配置格式异常，未覆盖。')
    data['FLYAI_API_KEY']=key
    fd,temp=tempfile.mkstemp(dir=directory,prefix='.config-')
    try:
        with os.fdopen(fd,'w') as stream:json.dump(data,stream);stream.write('\n')
        os.chmod(temp,0o600);os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    print('已保存到本机 FlyAI 配置；未显示密钥。请重新查询验证权限和价格。')
if __name__=='__main__':main()
