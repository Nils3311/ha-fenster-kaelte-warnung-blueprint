#!/usr/bin/env python3
"""Fetch complete map data from iotuserdata/getDeviceData."""
import json, zlib, base64, hashlib, requests

MOVA_B64 = 'H4sIAAAAAAAAA11Sa2/aMBT9K6hS0SYtIQktYar6gYEQ3TRlLdC1nabo4jjEqx+ZbUrZr5+vY7p2+eDcc+772D9OYqZsLNQTRJaSJiZKnHzonaTDbJSjcTM58PvpaS2WX9r8dPUbua8uulwK0LZRgg7S+Dw+/9h7x741StKLHiuWvXQUJxe9JQFOB8M4Sd77omScbIb5ON9k2WiU56MNqcjZOK2HeTWu4SzbQJrAMIF6nMKoqqMUsz6BYaT3sPjM77+n/C6b78ni/rl4nF/fiZvsetFO1un84VY2RTHbXmJGgl+GlrFgdwYtAcZSvWYVgg2T1UwJYBJRq1VLtT2g7cS48iEtB1srLS6vimXfEBdxCZz3txqkLe3BQYzStNbUNKVVj1T23yDvb8GYvdJVf2eoliC6rP6R7pCvBoSonbRIDCpNXWgEO9sMlD99RfS5MGpM+YLftESCPrfMMSUL7i1T3rJU4uTd/qEBDhW5jcPiCFGZAP9pF3wVWPDZ9IkRihZnxt56oZmsVfAVq+lVQMqSo9mCBmGOSR2z9UWEqijvhiVOE/NqQNc4Cg/SUFlNlRDwMl/NuM/HP0p7vEpfADXFf+OaKe2vdkvtzE8+C3uY/4lZ13XiFEe4RnkmW9rdSnDecIIIY5Rmf8AGfVde36h7PFMlnd42WoUpoG05Iz528Mt0CW2JZ3mcTO0lV1CtNQ9MYUxavaZ//gW/B6/rrAMAAA=='
S = json.loads(zlib.decompress(base64.b64decode(MOVA_B64), zlib.MAX_WBITS | 32))

USERNAME, PASSWORD = "JB581668", "Test123!"
BASE = "https://eu.iot.mova-tech.com:13267"
DID = "-113852546"
MODEL = "mova.mower.g2552b"
session = requests.session()

# Login
r = session.post(f"{BASE}/{S[17]}",
    data=f"{S[12]}{S[14]}{USERNAME}{S[15]}{hashlib.md5((PASSWORD + S[2]).encode()).hexdigest()}{S[16]}",
    headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6]}, timeout=10).json()
token, uid = r["access_token"], str(r["u"])
H = {"Content-Type": "application/json", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6], "Dreame-Auth": token}

# Fetch full map data
print("=== Fetching Map Data via iotuserdata/getDeviceData ===\n")
url = f"{BASE}/dreame-user-iot/iotuserdata/getDeviceData"
params = {"did": DID, "uid": uid, "region": "eu"}
r = session.post(url, json=params, headers=H, timeout=30).json()

if r.get("code") == 0:
    data = r.get("data", {})
    print(f"Response has {len(data)} keys:")
    for key in sorted(data.keys()):
        val = str(data[key])
        print(f"  {key:30s}: {val[:120]}{'...' if len(val) > 120 else ''}")

    # Save full data
    with open("mova_full_mapdata.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nFull data saved to mova_full_mapdata.json ({len(json.dumps(data))} bytes)")

    # Analyze MAP keys specifically
    print("\n=== MAP Key Analysis ===\n")
    map_keys = {k: v for k, v in data.items() if k.startswith("MAP")}
    print(f"Found {len(map_keys)} MAP-related keys")

    for key in sorted(map_keys.keys()):
        val = str(map_keys[key])
        # Try to parse as JSON
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                print(f"\n  {key}: JSON array with {len(parsed)} items")
                if parsed:
                    print(f"    First item: {json.dumps(parsed[0], indent=2)[:200]}")
            elif isinstance(parsed, dict):
                print(f"\n  {key}: JSON object with keys: {list(parsed.keys())[:10]}")
                print(f"    Preview: {json.dumps(parsed, indent=2)[:200]}")
            else:
                print(f"\n  {key}: {type(parsed).__name__} = {str(parsed)[:100]}")
        except:
            print(f"\n  {key}: raw string ({len(val)} chars)")
            print(f"    Preview: {val[:200]}")
else:
    print(f"Error: code={r.get('code')} msg={r.get('msg')}")

# Also try setDeviceData to understand what keys the device uses
print("\n=== Try other iotuserdata endpoints ===\n")
for action in ["getDeviceData", "getUserData", "getData"]:
    url = f"{BASE}/dreame-user-iot/iotuserdata/{action}"
    try:
        r = session.post(url, json={"did": DID, "uid": uid, "region": "eu", "model": MODEL}, headers=H, timeout=5).json()
        if r.get("code") == 0:
            keys = list(r.get("data", {}).keys()) if isinstance(r.get("data"), dict) else "non-dict"
            print(f"  ✓ {action}: {keys}")
    except:
        pass

print("\nDone!")
