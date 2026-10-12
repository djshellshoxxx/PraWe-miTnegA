from kclab import *
ids=json.load(open("ids.json")); uid=ids["uid"]; gid=ids["gid"]; roles=ids["roles"]
def obs(label,at,rt,do_refresh=True):
    out={}
    out["introspect"]=short(introspect(at))
    out["userinfo"]=short(userinfo(at))
    if do_refresh:
        r=refresh(rt); j=r.json()
        out["refresh"]=(r.status_code, j.get("error_description") or ("ok roles=%s"%jwt_payload(j["access_token"])["realm_access"]["roles"]))
        out["_new"]=j
    print(f"--- {label}")
    for k,v in out.items():
        if not k.startswith("_"): print("   ",k,v)
    return out
def fresh():
    j=tok().json(); return j["access_token"],j["refresh_token"],j
def reset():
    kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=True))
    kc.a("PUT",f"/{REALM}/users/{uid}/groups/{gid}")
    kc.a("POST",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]])
    kc.a("PUT",f"/{REALM}",json=dict(notBefore=0))
    kc.a("POST",f"/{REALM}/users/{uid}/logout")
    kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=True))

print("== E0 baseline"); at,rt,j=fresh(); obs("baseline",at,rt)
print("== E1 disable user (enabled=false)")
reset(); at,rt,j=fresh()
r=kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=False)); print("PUT disable",r.status_code)
o=obs("after disable",at,rt)
print("   new token attempt:",tok().json().get("error_description"))
print("   sessions still listed:",len(kc.a("GET",f"/{REALM}/users/{uid}/sessions").json()))
kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=True))
print("   after re-enable, same AT introspect:",short(introspect(at)),"refresh:",refresh(rt).status_code)

print("== E2 DELETE /sessions/{sid}")
reset(); at,rt,j=fresh(); sid=jwt_payload(at)["sid"]
r=kc.a("DELETE",f"/{REALM}/sessions/{sid}"); print("DELETE session",r.status_code)
obs("after session delete",at,rt)

print("== E3 POST users/{id}/logout")
reset(); at,rt,j=fresh()
r=kc.a("POST",f"/{REALM}/users/{uid}/logout"); print("POST logout",r.status_code)
obs("after user logout",at,rt)
print("   user notBefore:",kc.a("GET",f"/{REALM}/users/{uid}").json().get("notBefore"))
print("   immediately new login+introspect:",short(introspect(tok().json()["access_token"])))
