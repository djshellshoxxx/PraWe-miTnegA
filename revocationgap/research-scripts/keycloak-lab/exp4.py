from kclab import *
import urllib.parse, os
exec(open("exp1.py").read().split('print("== E0')[0])
import os
cid=[c for c in kc.a("GET",f"/{REALM}/clients?clientId=tester").json()][0]["id"]
c=kc.a("GET",f"/{REALM}/clients/{cid}").json()
c["attributes"]["backchannel.logout.url"]="http://127.0.0.1:9998/bcl"
c["attributes"]["backchannel.logout.session.required"]="true"
c["attributes"]["backchannel.logout.revoke.offline.tokens"]="false"
print("set bcl url",kc.a("PUT",f"/{REALM}/clients/{cid}",json=c).status_code)
def lastlog(n0):
    L=open("bcl.log").read().splitlines() if os.path.exists("bcl.log") else []
    return L[n0:]
def nlog(): return len(open("bcl.log").read().splitlines()) if os.path.exists("bcl.log") else 0
for label,act in [("POST users/{id}/logout",lambda sid:kc.a("POST",f"/{REALM}/users/{uid}/logout")),
                  ("DELETE sessions/{sid}",lambda sid:kc.a("DELETE",f"/{REALM}/sessions/{sid}")),
                  ("PUT enabled=false",lambda sid:kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=False))),
                  ("PUT role-removal",lambda sid:kc.a("DELETE",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]])),
                  ("PUT reset-password",lambda sid:kc.a("PUT",f"/{REALM}/users/{uid}/reset-password",json=dict(type="password",value="Passw0rd!",temporary=False))),
                  ("POST logout-all",lambda sid:kc.a("POST",f"/{REALM}/logout-all")),
                  ("DELETE user bob-like (skip)",lambda sid:None)]:
    reset(); j=tok().json(); at=j["access_token"]; sid=jwt_payload(at)["sid"]; n0=nlog(); t0=time.time()
    r=act(sid); time.sleep(0.5)
    L=lastlog(n0)
    print(label,"->",getattr(r,'status_code',None),"bcl hits:",len(L))
    for l in L:
        d=json.loads(l); lt=urllib.parse.parse_qs(d["body"]).get("logout_token",[""])[0]
        if lt: print("   latency s",round(d["t"]-t0,3),"logout_token claims:",{k:v for k,v in jwt_payload(lt).items()})
# end-session via RP-initiated logout with id_token_hint
reset(); j=tok().json(); n0=nlog()
r=requests.get(f"{BASE}/realms/{REALM}/protocol/openid-connect/logout",params=dict(id_token_hint=j["id_token"],client_id="tester"),allow_redirects=False)
print("GET logout (id_token_hint)",r.status_code,r.headers.get("location"),"bcl hits",len(lastlog(n0)))
print("   after: introspect",short(introspect(j["access_token"]))[1].get("active"),"refresh",refresh(j["refresh_token"]).status_code)
# legacy direct POST logout with refresh token
reset(); j=tok().json()
r=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/logout",data=dict(client_id="tester",client_secret="tester-secret",refresh_token=j["refresh_token"]))
print("POST logout refresh_token",r.status_code,"introspect",short(introspect(j["access_token"]))[1].get("active"))
c["attributes"]["backchannel.logout.url"]=""; kc.a("PUT",f"/{REALM}/clients/{cid}",json=c)
