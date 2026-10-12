from kclab import *
ids=json.load(open("ids.json")); uid=ids["uid"]; gid=ids["gid"]; roles=ids["roles"]
kc.a("PUT",f"/{REALM}",json=dict(accessTokenLifespan=3600,ssoSessionIdleTimeout=1800,notBefore=0))
def mkadmin(name,rolenames):
    r=kc.a("POST",f"/{REALM}/clients",json=dict(clientId=name,secret=name+"-s",serviceAccountsEnabled=True,standardFlowEnabled=False,directAccessGrantsEnabled=False,publicClient=False))
    cid=r.headers["Location"].rsplit("/",1)[1]
    su=kc.a("GET",f"/{REALM}/clients/{cid}/service-account-user").json()["id"]
    rm=[c for c in kc.a("GET",f"/{REALM}/clients?clientId=realm-management").json()][0]["id"]
    avail={x["name"]:x for x in kc.a("GET",f"/{REALM}/clients/{rm}/roles").json()}
    kc.a("POST",f"/{REALM}/users/{su}/role-mappings/clients/{rm}",json=[avail[n] for n in rolenames])
    t=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token",data=dict(grant_type="client_credentials",client_id=name,client_secret=name+"-s")).json()["access_token"]
    return {"Authorization":"Bearer "+t,"Content-Type":"application/json"}
def call(H,method,path,**kw):
    r=requests.request(method,f"{BASE}/admin/realms{path}",headers=H,**kw); return r.status_code
for name,rn in [("adm-mu",["manage-users"]),("adm-vu",["view-users"]),("adm-mr",["manage-realm"]),("adm-ev",["view-events"]),("adm-mu-qu",["manage-users","query-users"])]:
    try: H=mkadmin(name,rn)
    except Exception as e: print(name,"setup err",e); continue
    # fresh state
    tok_=tok().json(); sid=jwt_payload(tok_["access_token"])["sid"]
    res={}
    res["GET users?username"]=call(H,"GET",f"/{REALM}/users?username=alice")
    res["POST users (create)"]=call(H,"POST",f"/{REALM}/users",json=dict(username="tmp-"+name,enabled=True))
    res["GET users/{id}/sessions"]=call(H,"GET",f"/{REALM}/users/{uid}/sessions")
    res["PUT users/{id} enabled=true"]=call(H,"PUT",f"/{REALM}/users/{uid}",json=dict(enabled=True))
    res["PUT reset-password"]=call(H,"PUT",f"/{REALM}/users/{uid}/reset-password",json=dict(type="password",value="Passw0rd!",temporary=False))
    res["POST users/{id}/logout"]=call(H,"POST",f"/{REALM}/users/{uid}/logout")
    tok().json()
    res["DELETE sessions/{bogus}"]=call(H,"DELETE",f"/{REALM}/sessions/bogus")
    res["POST logout-all (skip effects)"]="skipped"
    res["POST role-mapping realm"]=call(H,"POST",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]])
    res["DELETE role-mapping realm"]=call(H,"DELETE",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]])
    res["PUT users/{id}/groups/{g}"]=call(H,"PUT",f"/{REALM}/users/{uid}/groups/{gid}")
    res["DELETE users/{id}/groups/{g}"]=call(H,"DELETE",f"/{REALM}/users/{uid}/groups/{gid}")
    res["PUT realm notBefore"]=call(H,"PUT",f"/{REALM}",json=dict(notBefore=0))
    res["POST push-revocation"]=call(H,"POST",f"/{REALM}/push-revocation")
    res["GET events"]=call(H,"GET",f"/{REALM}/events?max=1")
    res["GET admin-events"]=call(H,"GET",f"/{REALM}/admin-events?max=1")
    res["GET events/config"]=call(H,"GET",f"/{REALM}/events/config")
    res["DELETE users/{tmp}"]="n/a"
    print(name,rn,json.dumps(res))
kc.a("POST",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]]); kc.a("PUT",f"/{REALM}/users/{uid}/groups/{gid}")
