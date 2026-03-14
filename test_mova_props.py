#!/usr/bin/env python3
"""Test iotstatus/props endpoint with correct keys parameter."""
import json, zlib, base64, hashlib, requests

MOVA_B64 = 'H4sIAAAAAAAAA11Sa2/aMBT9K6hS0SYtIQktYar6gYEQ3TRlLdC1nabo4jjEqx+ZbUrZr5+vY7p2+eDcc+772D9OYqZsLNQTRJaSJiZKnHzonaTDbJSjcTM58PvpaS2WX9r8dPUbua8uulwK0LZRgg7S+Dw+/9h7x741StKLHiuWvXQUJxe9JQFOB8M4Sd77omScbIb5ON9k2WiU56MNqcjZOK2HeTWu4SzbQJrAMIF6nMKoqqMUsz6BYaT3sPjM77+n/C6b78ni/rl4nF/fiZvsetFO1un84VY2RTHbXmJGgl+GlrFgdwYtAcZSvWYVgg2T1UwJYBJRq1VLtT2g7cS48iEtB1srLS6vimXfEBdxCZz3txqkLe3BQYzStNbUNKVVj1T23yDvb8GYvdJVf2eoliC6rP6R7pCvBoSonbRIDCpNXWgEO9sMlD99RfS5MGpM+YLftESCPrfMMSUL7i1T3rJU4uTd/qEBDhW5jcPiCFGZAP9pF3wVWPDZ9IkRihZnxt56oZmsVfAVq+lVQMqSo9mCBmGOSR2z9UWEqijvhiVOE/NqQNc4Cg/SUFlNlRDwMl/NuM/HP0p7vEpfADXFf+OaKe2vdkvtzE8+C3uY/4lZ13XiFEe4RnkmW9rdSnDecIIIY5Rmf8AGfVde36h7PFMlnd42WoUpoG05Iz528Mt0CW2JZ3mcTO0lV1CtNQ9MYUxavaZ//gW/B6/rrAMAAA=='
S = json.loads(zlib.decompress(base64.b64decode(MOVA_B64), zlib.MAX_WBITS | 32))

USERNAME, PASSWORD = "JB581668", "Test123!"
BASE = "https://eu.iot.mova-tech.com:13267"
session = requests.session()

# Login
login_data = f"{S[12]}{S[14]}{USERNAME}{S[15]}{hashlib.md5((PASSWORD + S[2]).encode()).hexdigest()}{S[16]}"
r = session.post(f"{BASE}/{S[17]}", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6]}, timeout=10).json()
token = r["access_token"]
uid = r["u"]
H = {"Content-Type": "application/json", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6], "Dreame-Auth": token}
did = -113852546

print("=== iotstatus/props variations ===\n")
props_url = f"{BASE}/dreame-user-iot/iotstatus/props"

# Try different "keys" formats
test_keys = [
    # Format 1: Simple key string "siid.piid"
    {"did": str(did), "keys": "2.1", "region": "eu", "type": 3},
    # Format 2: JSON array of keys
    {"did": str(did), "keys": json.dumps([{"siid": 2, "piid": 1}]), "region": "eu", "type": 3},
    # Format 3: Comma-separated
    {"did": str(did), "keys": "2.1,3.1,6.8", "region": "eu", "type": 3},
    # Format 4: With uid
    {"did": str(did), "uid": str(uid), "keys": "2.1", "region": "eu", "type": 3},
    # Format 5: keys as list
    {"did": str(did), "uid": str(uid), "keys": ["2.1", "3.1", "6.8"], "region": "eu", "type": 3},
    # Format 6: array of objects
    {"did": str(did), "uid": str(uid), "keys": [{"siid": 2, "piid": 1}, {"siid": 3, "piid": 1}, {"siid": 6, "piid": 8}], "region": "eu"},
]

for i, params in enumerate(test_keys):
    try:
        r = session.post(props_url, json=params, headers=H, timeout=10).json()
        code = r.get("code")
        if code == 0:
            print(f"[{i+1}] ✓ code=0: {json.dumps(r.get('data', {}), indent=2)[:400]}")
        else:
            print(f"[{i+1}] ✗ code={code}: {r.get('msg', '')[:100]}")
    except Exception as e:
        print(f"[{i+1}] ERROR: {e}")

# Also try GET with keys
print("\n=== GET variations ===")
for keys_val in ["2.1", "2.1,3.1,6.8"]:
    params = {"did": str(did), "uid": str(uid), "keys": keys_val, "region": "eu", "type": "3"}
    try:
        r = session.get(props_url, params=params, headers=H, timeout=10).json()
        code = r.get("code")
        if code == 0:
            print(f"  GET keys={keys_val}: ✓ {json.dumps(r.get('data', {}), indent=2)[:400]}")
        else:
            print(f"  GET keys={keys_val}: ✗ code={code} msg={r.get('msg', '')[:100]}")
    except Exception as e:
        print(f"  GET keys={keys_val}: {e}")

# Try the protocol.py get_properties endpoint (line 521)
print("\n=== get_properties via props endpoint ===")
# In protocol.py line 521-527:
# def get_properties(self, keys):
#     params = {"did": str(self._did), "keys": keys}
#     return self._api_call(f"{self._strings[23]}/{self._strings[25]}/{self._strings[41]}", params)
# Keys format from protocol.py is the raw keys parameter
for keys_val in [
    [{"siid": 2, "piid": 1, "did": str(did)}, {"siid": 3, "piid": 1, "did": str(did)}],
    [{"siid": 2, "piid": 1}, {"siid": 3, "piid": 1}],
    "2.1,3.1",
]:
    params = {"did": str(did), "keys": keys_val}
    try:
        payload = json.dumps(params, separators=(",", ":"))
        r = session.post(props_url, data=payload, headers=H, timeout=10).json()
        code = r.get("code")
        if code == 0:
            print(f"  keys={str(keys_val)[:50]}: ✓ {json.dumps(r.get('data', {}), indent=2)[:400]}")
        else:
            print(f"  keys={str(keys_val)[:50]}: ✗ code={code} msg={r.get('msg', '')[:100]}")
    except Exception as e:
        print(f"  keys={str(keys_val)[:50]}: {e}")

print("\nDone!")
