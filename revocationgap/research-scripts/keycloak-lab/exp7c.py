from kclab import *
exec(open("exp1.py").read().split('print("== E0')[0])
kc.a("PUT",f"/{REALM}",json=dict(accessTokenLifespan=3600,ssoSessionIdleTimeout=60,ssoSessionMaxLifespan=36000))
print("realm idle now:",kc.a("GET",f"/{REALM}").json()["ssoSessionIdleTimeout"])
reset(); j=tok().json(); at,rt=j["access_token"],j["refresh_token"]; t0=time.time(); sid=jwt_payload(at)["sid"]
for dt in [10,65,75,90,150,200]:
    time.sleep(max(0,t0+dt-time.time()))
    ss=kc.a("GET",f"/{REALM}/users/{uid}/sessions").json()
    mine=[s for s in ss if s["id"]==sid]
    print(f"t+{dt}s now={int(time.time()*1000)} introspect={introspect(at)[1].get('active')} mySession={[(s['start'],s['lastAccess']) for s in mine]}")
r=refresh(rt); print("refresh:",r.status_code,r.json())
kc.a("PUT",f"/{REALM}",json=dict(accessTokenLifespan=3600,ssoSessionIdleTimeout=1800))
