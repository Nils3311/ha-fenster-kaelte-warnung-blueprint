#!/usr/bin/env python3
"""Direct Mova 600 Plus cloud API test — all endpoints."""
import json, zlib, base64, hashlib, requests, time

MOVA_B64 = 'H4sIAAAAAAAAA11Sa2/aMBT9K6hS0SYtIQktYar6gYEQ3TRlLdC1nabo4jjEqx+ZbUrZr5+vY7p2+eDcc+772D9OYqZsLNQTRJaSJiZKnHzonaTDbJSjcTM58PvpaS2WX9r8dPUbua8uulwK0LZRgg7S+Dw+/9h7x741StKLHiuWvXQUJxe9JQFOB8M4Sd77omScbIb5ON9k2WiU56MNqcjZOK2HeTWu4SzbQJrAMIF6nMKoqqMUsz6BYaT3sPjM77+n/C6b78ni/rl4nF/fiZvsetFO1un84VY2RTHbXmJGgl+GlrFgdwYtAcZSvWYVgg2T1UwJYBJRq1VLtT2g7cS48iEtB1srLS6vimXfEBdxCZz3txqkLe3BQYzStNbUNKVVj1T23yDvb8GYvdJVf2eoliC6rP6R7pCvBoSonbRIDCpNXWgEO9sMlD99RfS5MGpM+YLftESCPrfMMSUL7i1T3rJU4uTd/qEBDhW5jcPiCFGZAP9pF3wVWPDZ9IkRihZnxt56oZmsVfAVq+lVQMqSo9mCBmGOSR2z9UWEqijvhiVOE/NqQNc4Cg/SUFlNlRDwMl/NuM/HP0p7vEpfADXFf+OaKe2vdkvtzE8+C3uY/4lZ13XiFEe4RnkmW9rdSnDecIIIY5Rmf8AGfVde36h7PFMlnd42WoUpoG05Iz528Mt0CW2JZ3mcTO0lV1CtNQ9MYUxavaZ//gW/B6/rrAMAAA=='
S = json.loads(zlib.decompress(base64.b64decode(MOVA_B64), zlib.MAX_WBITS | 32))

USERNAME, PASSWORD = "JB581668", "Test123!"
BASE = "https://eu.iot.mova-tech.com:13267"
session = requests.session()

print(f"=== MOVA Cloud API Full Test ===\n")

# 1. Login
login_data = f"{S[12]}{S[14]}{USERNAME}{S[15]}{hashlib.md5((PASSWORD + S[2]).encode()).hexdigest()}{S[16]}"
login_headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6]}
r = session.post(f"{BASE}/{S[17]}", data=login_data, headers=login_headers, timeout=10).json()
token = r.get("access_token")
uid = r.get("u")
print(f"[1] Login: {'OK' if token else 'FAILED'} (uid={uid})")
if not token: exit(1)

# Auth headers for all API calls
H = {"Content-Type": "application/json", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6], "Dreame-Auth": token}

# 2. Device list via /dreame-user-iot/iotuserbind/device/listV2
print("\n[2] Device list...")
for endpoint in [
    f"{S[23]}/{S[24]}/{S[27]}/{S[28]}",  # iotuserbind/device/listV2
    f"{S[23]}/{S[24]}/{S[27]}/list",       # iotuserbind/device/list
    f"{S[23]}/{S[24]}/list",               # iotuserbind/list
]:
    url = f"{BASE}/{endpoint}"
    try:
        r = session.get(url, headers=H, timeout=10).json()
        print(f"  GET {endpoint}: code={r.get('code')}")
        if r.get("code") == 0:
            data = r.get("data", {})
            if isinstance(data, dict):
                devs = data.get("list", data.get("devices", data.get(S[36], [])))  # records
            else:
                devs = data
            if devs:
                print(f"  Found {len(devs)} device(s)")
                for d in devs:
                    print(f"    {json.dumps(d, indent=2)[:400]}")
                break
    except Exception as e:
        print(f"  GET {endpoint}: {e}")

    # Try POST
    try:
        r = session.post(url, json={}, headers=H, timeout=10).json()
        print(f"  POST {endpoint}: code={r.get('code')}")
        if r.get("code") == 0:
            data = r.get("data", {})
            if isinstance(data, dict):
                devs = data.get("list", data.get("devices", data.get(S[36], [])))
            else:
                devs = data
            if devs:
                print(f"  Found {len(devs)} device(s)")
                for d in devs:
                    print(f"    {json.dumps(d, indent=2)[:400]}")
                break
    except Exception as e:
        print(f"  POST {endpoint}: {e}")

# Use known DID
did = -113852546
print(f"\n[3] Using known DID: {did}")

# 3. sendCommand with correct auth
print("\n[4] sendCommand (get_properties)...")
cmd_url = f"{BASE}/{S[37]}/{S[27]}/{S[38]}"  # dreame-iot-com/device/sendCommand
props = [{"did": str(did), "siid": 2, "piid": 1}, {"did": str(did), "siid": 3, "piid": 1}]
payload = json.dumps({"did": str(did), "id": 1, "data": {"did": str(did), "id": 1, "method": "get_properties", "params": props}})
r = session.post(cmd_url, data=payload, headers=H, timeout=10).json()
print(f"  POST {S[37]}/{S[27]}/{S[38]}: code={r.get('code')}")
if r.get("code") == 0:
    print(f"  Result: {json.dumps(r.get('data', {}).get('result', []), indent=2)[:400]}")
else:
    print(f"  Response: {json.dumps(r, indent=2)[:300]}")

# 4. iotstatus/props - alternative property endpoint
print("\n[5] iotstatus/props...")
props_url = f"{BASE}/{S[23]}/{S[25]}/{S[41]}"  # dreame-user-iot/iotstatus/props
for siid, piid, name in [(2,1,"STATE"), (3,1,"BATTERY"), (6,8,"MAP_LIST"), (6,1,"OBJ_NAME"), (6,2,"MAP_DATA")]:
    params = {"uid": str(uid), "did": str(did), "siid": siid, "piid": piid, S[21]: "eu", S[42]: 3}
    try:
        r = session.post(props_url, json=params, headers=H, timeout=10).json()
        if r.get("code") == 0:
            val = r.get("data", {})
            print(f"  ✓ {name:12s} ({siid},{piid}): {str(val)[:150]}")
        else:
            print(f"  ✗ {name:12s} ({siid},{piid}): code={r.get('code')} msg={r.get('msg','')[:80]}")
    except Exception as e:
        print(f"  ✗ {name:12s} ({siid},{piid}): {e}")
    # Also try GET
    try:
        r = session.get(props_url, params=params, headers=H, timeout=10).json()
        if r.get("code") == 0:
            print(f"  ✓ {name:12s} (GET): {str(r.get('data',{}))[:150]}")
    except: pass

# 5. iotstatus/history - time-series data
print("\n[6] iotstatus/history...")
hist_url = f"{BASE}/{S[23]}/{S[25]}/{S[43]}"  # dreame-user-iot/iotstatus/history
for siid, piid, name in [(2,1,"STATE"), (6,2,"MAP_DATA"), (6,1,"OBJ_NAME"), (6,8,"MAP_LIST")]:
    params = {"uid": str(uid), "did": str(did), "siid": siid, "piid": piid, "from": 1, "limit": 5, S[21]: "eu", S[42]: 3}
    try:
        r = session.post(hist_url, json=params, headers=H, timeout=10).json()
        if r.get("code") == 0:
            data = r.get("data", {})
            lst = data.get(S[33], [])  # "list"
            print(f"  ✓ {name:12s} ({siid},{piid}): {len(lst)} entries")
            if lst:
                print(f"    Sample: {str(lst[0])[:200]}")
        else:
            print(f"  ✗ {name:12s} ({siid},{piid}): code={r.get('code')} msg={r.get('msg','')[:80]}")
    except Exception as e:
        print(f"  ✗ {name:12s} ({siid},{piid}): {e}")

# 6. File URL endpoints
print("\n[7] File URL endpoints...")
for ep_name, ep_idx in [("getDownloadUrl", 55), ("getOss1dDownloadUrl", 56)]:
    url = f"{BASE}/{S[23]}/{S[39]}/{S[ep_idx]}"
    params = {"did": str(did), "uid": str(uid), S[35]: "mova.mower.g2552b", "filename": "test", S[21]: "eu"}
    try:
        r = session.post(url, json=params, headers=H, timeout=10).json()
        print(f"  {ep_name}: code={r.get('code')}, data={str(r.get('data',''))[:200]}")
    except Exception as e:
        print(f"  {ep_name}: {e}")

print("\nDone!")
