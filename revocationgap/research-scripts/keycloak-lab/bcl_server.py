import http.server, json, time, sys, urllib.parse
LOG="/workspace/rg-scratch/providers-a/lab/bcl.log"
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(s):
        n=int(s.headers.get('content-length',0)); b=s.rfile.read(n).decode()
        open(LOG,"a").write(json.dumps(dict(t=time.time(),path=s.path,body=b,ct=s.headers.get('content-type')))+"\n")
        s.send_response(200); s.end_headers()
    def log_message(*a): pass
http.server.HTTPServer(("127.0.0.1",9998),H).serve_forever()
