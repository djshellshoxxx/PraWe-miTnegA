from kclab import *
import base64
exec(open("exp1.py").read().split('print("== E0')[0])
realm=kc.a("GET",f"/{REALM}").json()
realm["eventsListeners"]=["jboss-logging","ssf-events"]
realm["attributes"]["ssf.transmitterEnabled"]="true"
print("listeners",kc.a("PUT",f"/{REALM}",json=realm).status_code)
r=kc.a("POST",f"/{REALM}/clients",json=dict(clientId="ssf-rx",secret="ssf-secret",serviceAccountsEnabled=True,directAccessGrantsEnabled=False,standardFlowEnabled=False,publicClient=False,attributes={"ssf.enabled":"true","ssf.defaultSubjects":"ALL","ssf.validPushUrls":"http://127.0.0.1:8500/*"}))
print("create rx",r.status_code,r.text[:200]); rid=r.headers["Location"].rsplit("/",1)[1]
for sc in ["ssf.read","ssf.manage"]:
    sid=[s["id"] for s in kc.a("GET",f"/{REALM}/client-scopes").json() if s["name"]==sc][0]
    print("assign scope",sc,kc.a("PUT",f"/{REALM}/clients/{rid}/optional-client-scopes/{sid}").status_code)
tk=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token",data=dict(grant_type="client_credentials",client_id="ssf-rx",client_secret="ssf-secret",scope="ssf.read ssf.manage")).json()
rtok=tk["access_token"]; H={"Authorization":"Bearer "+rtok}
ev=["https://schemas.openid.net/secevent/caep/event-type/session-revoked","https://schemas.openid.net/secevent/caep/event-type/credential-change","https://schemas.openid.net/secevent/risc/event-type/account-disabled","https://schemas.openid.net/secevent/risc/event-type/account-enabled","https://schemas.openid.net/secevent/risc/event-type/account-purged"]
r=requests.post(f"{BASE}/realms/{REALM}/ssf/transmitter/streams",headers=H,json=dict(delivery=dict(method="urn:ietf:rfc:8936"),events_requested=ev,description="lab"))
print("create stream",r.status_code,json.dumps(r.json())[:600]); st=r.json()
poll=st["delivery"]["endpoint_url"]
def pollit(ack=None):
    r=requests.post(poll,headers=H,json=dict(maxEvents=50,returnImmediately=True,ack=ack or []))
    return r.json()
def show(label,t0):
    time.sleep(1.5); j=pollit(); sets=j.get("sets",{})
    print(f"--- {label}: {len(sets)} SETs")
    for jti,s in sets.items():
        p=jwt_payload(s); print("   ",{"iat_rel_ms":int(p["iat"]*1000-t0),"events":list(p["events"].keys()),"sub_id":p.get("sub_id"),"payload":{k:v for e in p["events"].values() for k,v in e.items()}})
    pollit(list(sets.keys()))
pollit(pollit().get("sets",{}).keys() and list(pollit().get("sets",{}).keys()))
import time as _t
# subscribe alice explicitly (default ALL anyway)
for label,act in [("DELETE sessions/{sid}",lambda sid:kc.a("DELETE",f"/{REALM}/sessions/{sid}")),
                  ("POST users/{id}/logout",lambda sid:kc.a("POST",f"/{REALM}/users/{uid}/logout")),
                  ("PUT enabled=false",lambda sid:kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=False))),
                  ("PUT reset-password",lambda sid:kc.a("PUT",f"/{REALM}/users/{uid}/reset-password",json=dict(type="password",value="Passw0rd!",temporary=False))),
                  ("DELETE role mapping",lambda sid:kc.a("DELETE",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]])),
                  ("DELETE group membership",lambda sid:kc.a("DELETE",f"/{REALM}/users/{uid}/groups/{gid}")),
                  ("RP logout GET end_session",None)]:
    reset(); pollit(list(pollit().get("sets",{}).keys())); j=tok().json(); sid=jwt_payload(j["access_token"])["sid"]; t0=_t.time()*1000
    if act: r=act(sid)
    else: requests.get(f"{BASE}/realms/{REALM}/protocol/openid-connect/logout",params=dict(id_token_hint=j["id_token"],client_id="tester"),allow_redirects=False)
    show(label,t0)
print("--- user delete")
r=kc.a("POST",f"/{REALM}/users",json=dict(username="carol",enabled=True,email="c@e.test",firstName="c",lastName="c",emailVerified=True,credentials=[dict(type="password",value="Passw0rd!",temporary=False)])); cid_=r.headers["Location"].rsplit("/",1)[1]
pollit(list(pollit().get("sets",{}).keys())); t0=_t.time()*1000; kc.a("DELETE",f"/{REALM}/users/{cid_}"); show("DELETE user",t0)
