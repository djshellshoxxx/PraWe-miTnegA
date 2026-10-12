import requests, time, json, base64
B="http://localhost:8080"; R="rgap"
def p(t):
    s=t.split('.')[1]; s+='='*(-len(s)%4); return json.loads(base64.urlsafe_b64decode(s))
def admin():
    t=requests.post(f"{B}/realms/{R}/protocol/openid-connect/token",data=dict(grant_type="client_credentials",client_id="rg-admin",client_secret="rg-admin-secret")).json()["access_token"]
    return {"Authorization":"Bearer "+t,"Content-Type":"application/json"}
def A(m,path,**kw): return requests.request(m,f"{B}/admin/realms/{R}{path}",headers=admin(),**kw)
def login(scope="openid"): return requests.post(f"{B}/realms/{R}/protocol/openid-connect/token",data=dict(grant_type="password",client_id="rg-tester",client_secret="rg-tester-secret",username="rg-alice",password="Passw0rd!",scope=scope)).json()
def intro(t): return requests.post(f"{B}/realms/{R}/protocol/openid-connect/token/introspect",data=dict(token=t,client_id="rg-rs",client_secret="rg-rs-secret")).json().get("active")
def ui(t): return requests.get(f"{B}/realms/{R}/protocol/openid-connect/userinfo",headers={"Authorization":"Bearer "+t}).status_code
def rf(rt): 
    r=requests.post(f"{B}/realms/{R}/protocol/openid-connect/token",data=dict(grant_type="refresh_token",client_id="rg-tester",client_secret="rg-tester-secret",refresh_token=rt)); return r.status_code,r.json().get("error_description"),r.json()
uid=A("GET","/users?username=rg-alice").json()[0]["id"]
print("== OFFLINE + POST users/{id}/logout (user notBefore), login->logout gap 0s vs 1.2s")
for gap in (0,1.2):
    j=login("openid offline_access"); at,rt=j["access_token"],j["refresh_token"]; time.sleep(gap)
    A("POST",f"/users/{uid}/logout")
    s,e,_=rf(rt); print(f" gap={gap}s iat={p(rt)['iat']} userNB={A('GET',f'/users/{uid}').json().get('notBefore')} offline refresh -> {s} {e}; introspect AT={intro(at)} userinfo={ui(at)}")
print("== ONLINE realm notBefore boundary: token issued in same second as NB vs 1s before")
j1=login(); time.sleep(1.2); nb=int(time.time()); j2=login()
A("PUT","",json=dict(notBefore=nb))
print(f" NB={nb} tokenA.iat={p(j1['access_token'])['iat']} active={intro(j1['access_token'])}; tokenB.iat={p(j2['access_token'])['iat']} active={intro(j2['access_token'])}")
A("PUT","",json=dict(notBefore=0))
print("== OFFLINE token + disable/enable; + realm role removal of offline_access")
j=login("openid offline_access"); at,rt=j["access_token"],j["refresh_token"]
roles={r["name"]:r for r in A("GET","/roles").json()}
print(" session ids: access sid",p(at)["sid"])
print("== client credentials token: realm notBefore & POST users/{sa}/logout")
cc=requests.post(f"{B}/realms/{R}/protocol/openid-connect/token",data=dict(grant_type="client_credentials",client_id="rg-tester",client_secret="rg-tester-secret"))
print(" cc on tester (confidential client w/o service account):",cc.status_code,cc.json().get("error_description"))
