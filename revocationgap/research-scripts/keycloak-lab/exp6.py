from kclab import *
import base64
exec(open("exp1.py").read().split('print("== E0')[0])
realm=kc.a("GET",f"/{REALM}").json()
realm.setdefault("attributes",{})["ssf.transmitterEnabled"]="true"
print("enable transmitter",kc.a("PUT",f"/{REALM}",json=realm).status_code)
print(requests.get(f"{BASE}/realms/{REALM}/.well-known/ssf-configuration").status_code)
print(json.dumps(requests.get(f"{BASE}/realms/{REALM}/.well-known/ssf-configuration").json(),indent=1)[:2500])
scopes=[s["name"] for s in kc.a("GET",f"/{REALM}/client-scopes").json()]; print([s for s in scopes if "ssf" in s])
