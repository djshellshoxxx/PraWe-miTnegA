from kclab import *
exec(open("exp1.py").read().split('print("== E0')[0])
print("== E9 refresh-token rotation (revokeRefreshToken=true, maxReuse=0)")
kc.a("PUT",f"/{REALM}",json=dict(revokeRefreshToken=True,refreshTokenMaxReuse=0))
reset(); at,rt0,j=fresh()
r1=refresh(rt0); print(" refresh#1 with RT0:",r1.status_code); rt1=r1.json()["refresh_token"]
r2=refresh(rt0); print(" replay RT0:",r2.status_code,r2.json())
r3=refresh(rt1); print(" RT1 after replay of RT0 (does reuse kill family?):",r3.status_code,r3.json().get("error_description"))
print(" session still exists:",len(kc.a("GET",f"/{REALM}/users/{uid}/sessions").json()))
kc.a("PUT",f"/{REALM}",json=dict(revokeRefreshToken=True,refreshTokenMaxReuse=2))
reset(); at,rt0,j=fresh()
print(" maxReuse=2: ",[refresh(rt0).status_code for _ in range(4)])
kc.a("PUT",f"/{REALM}",json=dict(revokeRefreshToken=False,refreshTokenMaxReuse=0))
print("== E10 offline tokens")
reset(); j=tok(scope="openid offline_access").json(); at,rt=j["access_token"],j["refresh_token"]
print(" offline RT type:",jwt_payload(rt)["typ"],"refresh_expires_in:",j.get("refresh_expires_in"), "exp-iat", jwt_payload(rt).get("exp"))
print(" offline sessions listed (client):",len(kc.a("GET",f"/{REALM}/users/{uid}/offline-sessions/"+[c for c in kc.a("GET",f"/{REALM}/clients?clientId=tester").json()][0]["id"]).json()))
kc.a("POST",f"/{REALM}/users/{uid}/logout")
print(" after POST users/{id}/logout (online sessions only):")
o=obs("offline after user logout",at,rt)
j=refresh(rt).json(); print("   new RT type",jwt_payload(j["refresh_token"])["typ"]); at,rt=j["access_token"],j["refresh_token"]
print("   introspect new AT:",short(introspect(at))[1].get("active"))
# disable user
kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=False)); o=obs("offline after disable",at,rt); kc.a("PUT",f"/{REALM}/users/{uid}",json=dict(enabled=True))
# DELETE /sessions/{sid}?isOffline=true
sid=jwt_payload(at)["sid"]
print(" DELETE offline session:",kc.a("DELETE",f"/{REALM}/sessions/{sid}?isOffline=true").status_code)
obs("offline after offline-session delete",at,rt)
print(" -- offline + realm notBefore")
j=tok(scope="openid offline_access").json(); at,rt=j["access_token"],j["refresh_token"]; time.sleep(1.1)
kc.a("PUT",f"/{REALM}",json=dict(notBefore=int(time.time()))); obs("offline after realm NB",at,rt); kc.a("PUT",f"/{REALM}",json=dict(notBefore=0))
print(" -- offline: revoke consent endpoint DELETE users/{id}/consents/tester")
j=tok(scope="openid offline_access").json(); at,rt=j["access_token"],j["refresh_token"]
print("   ",kc.a("DELETE",f"/{REALM}/users/{uid}/consents/tester").status_code); obs("offline after consent revoke",at,rt)
print("== E11 delete user")
reset(); j=tok().json(); at,rt=j["access_token"],j["refresh_token"]
r=kc.a("POST",f"/{REALM}/users",json=dict(username="bob",enabled=True,credentials=[dict(type="password",value="Passw0rd!",temporary=False)],email="bob@e.test",firstName="b",lastName="b",emailVerified=True)); bid=r.headers["Location"].rsplit("/",1)[1]
jb=tok(user="bob").json(); atb,rtb=jb["access_token"],jb["refresh_token"]
print(" DELETE user:",kc.a("DELETE",f"/{REALM}/users/{bid}").status_code)
obs("bob after delete",atb,rtb)
print("== E12 client_credentials token (no session)")
r=requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token",data=dict(grant_type="client_credentials",client_id="rs",client_secret="rs-secret")); jj=r.json()
cat=jj["access_token"]; p=jwt_payload(cat); print(" claims sid?",p.get("sid"),"aud",p.get("aud"),"azp",p.get("azp"),"refresh_token in resp?","refresh_token" in jj)
print(" introspect:",short(introspect(cat)))
cid=[c for c in kc.a("GET",f"/{REALM}/clients?clientId=rs").json()][0]["id"]
su=kc.a("GET",f"/{REALM}/clients/{cid}/service-account-user").json()["id"]
print(" disable service account user:",kc.a("PUT",f"/{REALM}/users/{su}",json=dict(enabled=False)).status_code)
print(" introspect after disable SA:",short(introspect(cat)))
print(" new cc token:",requests.post(f"{BASE}/realms/{REALM}/protocol/openid-connect/token",data=dict(grant_type="client_credentials",client_id="rs",client_secret="rs-secret")).json())
print(" POST users/{id}/logout for SA:",kc.a("POST",f"/{REALM}/users/{su}/logout").status_code,"-> introspect",short(introspect(cat)))
kc.a("PUT",f"/{REALM}/users/{su}",json=dict(enabled=True))
print(" disable client rs:"); kc.a("PUT",f"/{REALM}/clients/{cid}",json=dict(enabled=False)); print(short(introspect(cat,"tester","tester-secret"))); kc.a("PUT",f"/{REALM}/clients/{cid}",json=dict(enabled=True))
