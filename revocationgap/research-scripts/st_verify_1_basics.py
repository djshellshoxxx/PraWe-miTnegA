"""Verification of Schemathesis 4.30.1 extension points relied on by RevocationGap (research script, not product code)."""
import json, threading, time, http.server, socketserver
import schemathesis, schemathesis.openapi
from schemathesis import hooks

print("schemathesis", schemathesis.__version__)

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        ok = self.headers.get("Authorization")=="Bearer good"
        body=json.dumps({"doc":"secret-42"} if ok else {"error":"denied"}).encode()
        self.send_response(200 if ok else 401); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
srv=socketserver.TCPServer(("127.0.0.1",0),H); port=srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()

spec={"openapi":"3.0.3","info":{"title":"t","version":"1"},"servers":[{"url":f"http://127.0.0.1:{port}"}],
 "components":{"securitySchemes":{"b":{"type":"http","scheme":"bearer"}}},"security":[{"b":[]}],
 "paths":{"/docs/{id}":{"get":{"operationId":"getDoc","parameters":[{"name":"id","in":"path","required":True,"schema":{"type":"integer"}}],
   "responses":{"200":{"description":"ok","content":{"application/json":{"schema":{"type":"object"}}}},"401":{"description":"no"}}}}}}
schema=schemathesis.openapi.from_dict(spec)
schema.config.update(base_url=f"http://127.0.0.1:{port}")
BASE=f"http://127.0.0.1:{port}"

# 1. operation enumeration (public API)
ops=[r.ok() for r in schema.get_all_operations()]
print("ops:",[ (o.method,o.path,o.label) for o in ops])
op=schema["/docs/{id}"]["GET"]

# 2. deterministic Case construction with explicit values (no hypothesis)
case=op.Case(path_parameters={"id":7})
print("curl:",case.as_curl_command(headers={"Authorization":"Bearer good"}))

# 3. timestamping via hooks: before_call/after_call (global) - capture wall + monotonic
stamps=[]
@schemathesis.hook
def before_call(ctx, case, kwargs):
    stamps.append(("before",time.time(),time.monotonic()))
@schemathesis.hook
def after_call(ctx, case, response):
    stamps.append(("after",time.time(),time.monotonic()))

# 4. Case.call with explicit headers; no reauth, no validation
r=case.call(headers={"Authorization":"Bearer good"})
print("status",r.status_code,"elapsed",r.elapsed,"hdr keys",sorted(r.headers)[:6],"json",r.json() if hasattr(r,'json') else None)
r2=case.call(headers={"Authorization":"Bearer revoked"})
print("status",r2.status_code)
print("stamps",len(stamps), [s[0] for s in stamps])
print("response has timestamp attrs?",[a for a in r.__slots__ if 'time' in a or 'date' in a])

# 5. validate_response with custom check - assert body content not just status
@schemathesis.check
def doc_is_returned(ctx,response,case):
    if response.status_code==200 and response.json().get("doc")!="secret-42":
        raise AssertionError("marker missing")
case.validate_response(r, checks=[doc_is_returned])
print("custom check ok")

# 6. Auth provider path: does call() apply schema-level auth? (registered provider)
class P:
    def get(self,case,ctx): return "good"
    def set(self,case,data,ctx): case.headers["Authorization"]=f"Bearer {data}"
schemathesis.auth()(P)
r3=op.Case(path_parameters={"id":1}).call()
print("registered-auth call() status (does call() apply auth providers?):",r3.status_code)
srv.shutdown()
