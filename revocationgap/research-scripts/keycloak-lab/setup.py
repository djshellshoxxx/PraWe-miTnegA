from kclab import *
r=kc.a("POST","",json=dict(realm=REALM,enabled=True,accessTokenLifespan=3600,ssoSessionIdleTimeout=1800,eventsEnabled=True,adminEventsEnabled=True,adminEventsDetailsEnabled=True,enabledEventTypes=[]))
print("realm",r.status_code,r.text[:200])
# default realm values check (separate realm with no overrides)
r=kc.a("POST","",json=dict(realm="defaults",enabled=True)); print(r.status_code)
d=kc.a("GET","/defaults").json()
keys=["accessTokenLifespan","accessTokenLifespanForImplicitFlow","ssoSessionIdleTimeout","ssoSessionMaxLifespan","ssoSessionIdleTimeoutRememberMe","ssoSessionMaxLifespanRememberMe","offlineSessionIdleTimeout","offlineSessionMaxLifespan","offlineSessionMaxLifespanEnabled","clientSessionIdleTimeout","clientSessionMaxLifespan","clientOfflineSessionIdleTimeout","clientOfflineSessionMaxLifespan","accessCodeLifespan","accessCodeLifespanLogin","accessCodeLifespanUserAction","actionTokenGeneratedByAdminLifespan","actionTokenGeneratedByUserLifespan","revokeRefreshToken","refreshTokenMaxReuse","notBefore","bruteForceProtected","eventsEnabled","adminEventsEnabled","eventsExpiration","sslRequired","passwordPolicy","defaultSignatureAlgorithm"]
print(json.dumps({k:d.get(k) for k in keys},indent=1))
print("attributes",d.get("attributes"))
