import json, threading, time, http.server, socketserver, concurrent.futures as cf, requests
import schemathesis, schemathesis.openapi
class H(http.server.ThreadingHTTPServer): pass
class R(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_GET(self):
        body=b'{"doc":"x"}'
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
srv=H(("127.0.0.1",0),R); port=srv.server_address[1]; threading.Thread(target=srv.serve_forever,daemon=True).start()
spec={"openapi":"3.0.3","info":{"title":"t","version":"1"},"servers":[{"url":f"http://127.0.0.1:{port}"}],
 "paths":{"/docs/{id}":{"get":{"operationId":"getDoc","parameters":[{"name":"id","in":"path","required":True,"schema":{"type":"integer"}}],"responses":{"200":{"description":"ok"}}}}}}
schema=schemathesis.openapi.from_dict(spec); schema.config.update(base_url=f"http://127.0.0.1:{port}")
op=schema["/docs/{id}"]["GET"]
# thread-safety/perf: N threads each own Session
def work(i):
    s=requests.Session(); out=[]
    for k in range(50):
        c=op.Case(path_parameters={"id":k}); t=time.perf_counter(); r=c.call(session=s,headers={"X-T":str(i)}); out.append(time.perf_counter()-t)
        assert r.status_code==200
    return out
t0=time.perf_counter()
with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(work,range(8)))
dt=time.perf_counter()-t0
print("400 calls over 8 threads: %.2fs => %.0f req/s"%(dt,400/dt))
# Case construction overhead
t=time.perf_counter()
for k in range(5000): op.Case(path_parameters={"id":k})
print("Case() overhead us:", (time.perf_counter()-t)/5000*1e6)
# does call() accept per-call timeout / allow_redirects / verify kwargs (transport kwargs)?
r=op.Case(path_parameters={"id":1}).call(timeout=2, allow_redirects=False, headers={"Authorization":"Bearer x"})
print("kwargs ok", r.status_code, "request headers sent:", dict(r.request.headers).get("Authorization"), dict(r.request.headers).get("X-Schemathesis-TestCaseId"))
srv.shutdown()
