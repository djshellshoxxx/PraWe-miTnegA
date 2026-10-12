from kclab import *
def mk(path,body):
    r=kc.a("POST",path,json=body); print(path,r.status_code,r.text[:150]); return r
mk(f"/{REALM}/clients",dict(clientId="tester",secret="tester-secret",publicClient=False,directAccessGrantsEnabled=True,standardFlowEnabled=True,redirectUris=["http://localhost:9999/*"],attributes={"backchannel.logout.url":"","post.logout.redirect.uris":"+"}))
mk(f"/{REALM}/clients",dict(clientId="rs",secret="rs-secret",publicClient=False,serviceAccountsEnabled=True,directAccessGrantsEnabled=False,standardFlowEnabled=False))
mk(f"/{REALM}/roles",dict(name="r-direct"))
mk(f"/{REALM}/roles",dict(name="r-group"))
mk(f"/{REALM}/groups",dict(name="g1"))
r=mk(f"/{REALM}/users",dict(username="alice",enabled=True,email="alice@example.test",firstName="A",lastName="L",emailVerified=True,credentials=[dict(type="password",value="Passw0rd!",temporary=False)]))
uid=r.headers["Location"].rsplit("/",1)[1]; print("uid",uid)
roles={x["name"]:x for x in kc.a("GET",f"/{REALM}/roles").json()}
print(kc.a("POST",f"/{REALM}/users/{uid}/role-mappings/realm",json=[roles["r-direct"]]).status_code)
gid=[g for g in kc.a("GET",f"/{REALM}/groups").json() if g["name"]=="g1"][0]["id"]
print(kc.a("POST",f"/{REALM}/groups/{gid}/role-mappings/realm",json=[roles["r-group"]]).status_code)
print(kc.a("PUT",f"/{REALM}/users/{uid}/groups/{gid}").status_code)
json.dump(dict(uid=uid,gid=gid,roles=roles),open("ids.json","w"))
r=tok(); print(r.status_code); j=r.json(); print({k:(v if not k.endswith('token') else v[:20]) for k,v in j.items()})
print(json.dumps(jwt_payload(j["access_token"]),indent=1))
print(r.headers)
