import json, threading, http.server, socketserver
import schemathesis, schemathesis.graphql, requests
seen=[]
class R(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); b=self.rfile.read(n)
        seen.append((self.path, dict(self.headers), b))
        body=json.dumps({"data":{"me":{"id":"1"}}}).encode()
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.send_header("Set-Cookie","sid=abc; Path=/"); self.end_headers(); self.wfile.write(body)
    do_GET=do_POST
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),R); port=srv.server_address[1]; threading.Thread(target=srv.serve_forever,daemon=True).start()
sdl="type Query { me: User } type User { id: ID! }"
schema=schemathesis.graphql.from_file(sdl); schema.config.update(base_url=f"http://127.0.0.1:{port}/graphql")
ops=[r.ok() for r in schema.get_all_operations()]
print("graphql ops",[o.label for o in ops])
op=ops[0]
print([m for m in dir(op) if not m.startswith('_')][:40])
case=op.Case(body=schemathesis.graphql.nodes.Object([]) if False else None) if False else None
# generate one case via strategy to see what body looks like
from hypothesis import given, settings
@settings(max_examples=1, database=None)
@given(op.as_strategy())
def t(c):
    r=c.call(headers={"Authorization":"Bearer t"}); print("gql call", r.status_code, seen[-1][2][:80], seen[-1][1].get("User-Agent"))
t()
# cookies & session
spec={"openapi":"3.0.3","info":{"title":"t","version":"1"},"paths":{"/x":{"post":{"responses":{"200":{"description":"ok"}}}}}}
s2=schemathesis.openapi.from_dict(spec); s2.config.update(base_url=f"http://127.0.0.1:{port}")
o2=s2["/x"]["POST"]
sess=requests.Session()
o2.Case().call(session=sess); o2.Case().call(session=sess)
print("cookie sent on 2nd call via shared session:", "sid=abc" in seen[-1][1].get("Cookie",""))
o2.Case().call(); print("no session -> cookie:", seen[-1][1].get("Cookie"))
print("Connection hdr:", seen[-1][1].get("Connection"), "UA:", seen[-1][1].get("User-Agent"))
srv.shutdown()
