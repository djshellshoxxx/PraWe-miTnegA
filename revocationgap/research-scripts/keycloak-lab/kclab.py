import requests, time, json, base64, sys
BASE="http://localhost:8080"
def jwt_payload(t):
    p=t.split('.')[1]; p+='='*(-len(p)%4)
    return json.loads(base64.urlsafe_b64decode(p))
class KC:
    def __init__(s): s.admin_tok=None
    def admin_login(s):
        r=requests.post(f"{BASE}/realms/master/protocol/openid-connect/token",data=dict(grant_type="password",client_id="admin-cli",username="admin",password="admin"))
        r.raise_for_status(); s.admin_tok=r.json()["access_token"]
    def a(s,method,path,**kw):
        s.admin_login() # fresh each call (master default lifespan is short)
        h={"Authorization":"Bearer "+s.admin_tok}
        if "json" in kw: h["Content-Type"]="application/json"
        return requests.request(method,f"{BASE}/admin/realms{path}",headers=h,**kw)
kc=KC()
REALM="lab"
def tok(client="tester",secret="tester-secret",user="alice",pw="Passw0rd!",scope="openid",extra=None):
    d=dict(grant_type="password",client_id=client,client_secret=secret,username=user,password=pw,scope=scope)
    if extra: d.update(extra)
    r=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token",data=d)
    return r
def refresh(rt,client="tester",secret="tester-secret"):
    return requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token",data=dict(grant_type="refresh_token",client_id=client,client_secret=secret,refresh_token=rt))
def introspect(token,client="rs",secret="rs-secret"):
    r=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token/introspect",data=dict(token=token,client_id=client,client_secret=secret))
    return r.status_code,r.json()
def userinfo(at):
    r=requests.get(f"{BASE}/realms/{REALM}/protocol/openid-connect/userinfo",headers={"Authorization":"Bearer "+at})
    return r.status_code,(r.json() if r.headers.get('content-type','').startswith('application/json') else r.text[:100])
def revoke(token,hint=None,client="tester",secret="tester-secret"):
    d=dict(token=token,client_id=client,client_secret=secret)
    if hint: d["token_type_hint"]=hint
    r=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/revoke",data=d)
    return r.status_code,r.text[:200]
def short(x):
    if isinstance(x,tuple): return (x[0], {k:v for k,v in x[1].items() if k in("active","error","error_description","sub","preferred_username","realm_access","exp")} if isinstance(x[1],dict) else x[1])
    return x
