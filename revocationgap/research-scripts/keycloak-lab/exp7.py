from kclab import *
exec(open("exp1.py").read().split('print("== E0')[0])
kc.a("PUT",f"/{REALM}",json=dict(accessTokenLifespan=10,ssoSessionIdleTimeout=60,ssoSessionMaxLifespan=36000))
reset(); j=tok().json(); at,rt=j["access_token"],j["refresh_token"]; p=jwt_payload(at); t0=time.time()
print("iat",p["iat"],"exp",p["exp"],"expires_in",j["expires_in"],"refresh_expires_in",j["refresh_expires_in"],"rt exp-iat",jwt_payload(rt)["exp"]-jwt_payload(rt)["iat"],"auth_time",p.get("auth_time"))
for dt in [5,9,11,12,30,55,59,61,63,65,70,80]:
    time.sleep(max(0,t0+dt-time.time()))
    i=introspect(at)[1].get("active"); u=userinfo(at)[0]
    print(f"t+{dt}s local_exp_remaining={p['exp']-time.time():.1f} introspect={i} userinfo={u}")
    if dt in (30,55): print("   (no refresh)")
r=refresh(rt); print("refresh after idle:",r.status_code,r.json().get("error_description"))
kc.a("PUT",f"/{REALM}",json=dict(accessTokenLifespan=3600,ssoSessionIdleTimeout=1800))
