#!/usr/bin/env python3
"""Serve only this generated guide on localhost. Ctrl+C to stop."""
import argparse,functools,http.server,pathlib,webbrowser

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    root=pathlib.Path(__file__).resolve().parent
    # The renderer copies this launcher to the output root.
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
    with http.server.ThreadingHTTPServer(('127.0.0.1',a.port),handler) as server:
        url='http://127.0.0.1:'+str(server.server_port)+'/index.html'
        print('打开 '+url+'；按 Ctrl+C 停止。',flush=True)
        if not a.no_browser:webbrowser.open(url)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
if __name__=='__main__':main()
