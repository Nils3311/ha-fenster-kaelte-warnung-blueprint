#!/usr/bin/env python3
"""Analyze Mova 600 Plus telemetry byte arrays and find map data."""
import json, zlib, base64, hashlib, requests, time, struct

MOVA_B64 = 'H4sIAAAAAAAAA11Sa2/aMBT9K6hS0SYtIQktYar6gYEQ3TRlLdC1nabo4jjEqx+ZbUrZr5+vY7p2+eDcc+772D9OYqZsLNQTRJaSJiZKnHzonaTDbJSjcTM58PvpaS2WX9r8dPUbua8uulwK0LZRgg7S+Dw+/9h7x741StKLHiuWvXQUJxe9JQFOB8M4Sd77omScbIb5ON9k2WiU56MNqcjZOK2HeTWu4SzbQJrAMIF6nMKoqqMUsz6BYaT3sPjM77+n/C6b78ni/rl4nF/fiZvsetFO1un84VY2RTHbXmJGgl+GlrFgdwYtAcZSvWYVgg2T1UwJYBJRq1VLtT2g7cS48iEtB1srLS6vimXfEBdxCZz3txqkLe3BQYzStNbUNKVVj1T23yDvb8GYvdJVf2eoliC6rP6R7pCvBoSonbRIDCpNXWgEO9sMlD99RfS5MGpM+YLftESCPrfMMSUL7i1T3rJU4uTd/qEBDhW5jcPiCFGZAP9pF3wVWPDZ9IkRihZnxt56oZmsVfAVq+lVQMqSo9mCBmGOSR2z9UWEqijvhiVOE/NqQNc4Cg/SUFlNlRDwMl/NuM/HP0p7vEpfADXFf+OaKe2vdkvtzE8+C3uY/4lZ13XiFEe4RnkmW9rdSnDecIIIY5Rmf8AGfVde36h7PFMlnd42WoUpoG05Iz528Mt0CW2JZ3mcTO0lV1CtNQ9MYUxavaZ//gW/B6/rrAMAAA=='
S = json.loads(zlib.decompress(base64.b64decode(MOVA_B64), zlib.MAX_WBITS | 32))

USERNAME, PASSWORD = "JB581668", "Test123!"
BASE = "https://eu.iot.mova-tech.com:13267"
session = requests.session()

# Login
r = session.post(f"{BASE}/{S[17]}",
    data=f"{S[12]}{S[14]}{USERNAME}{S[15]}{hashlib.md5((PASSWORD + S[2]).encode()).hexdigest()}{S[16]}",
    headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6]}, timeout=10).json()
token, uid = r["access_token"], r["u"]
H = {"Content-Type": "application/json", "User-Agent": S[3], "Authorization": S[5], "Tenant-Id": S[6], "Dreame-Auth": token}
did = -113852546

props_url = f"{BASE}/dreame-user-iot/iotstatus/props"
hist_url = f"{BASE}/dreame-user-iot/iotstatus/history"

# 1. Get the byte arrays from 1.1 and 1.4
print("=== Byte Array Analysis ===\n")
for key in ["1.1", "1.4"]:
    params = {"did": str(did), "keys": key}
    r = session.post(props_url, data=json.dumps(params, separators=(",", ":")), headers=H, timeout=10).json()
    if r.get("code") == 0:
        for p in r["data"]:
            if "value" in p:
                val = p["value"]
                print(f"Key {key}:")
                print(f"  Type: {type(val).__name__}")
                if isinstance(val, str):
                    print(f"  String value: {val[:200]}")
                    # Try JSON parse
                    try:
                        parsed = json.loads(val)
                        print(f"  JSON parsed: {json.dumps(parsed, indent=2)[:300]}")
                    except:
                        # Try base64
                        try:
                            decoded = base64.b64decode(val)
                            print(f"  Base64 decoded ({len(decoded)} bytes): {decoded[:50]}")
                        except:
                            print(f"  Not JSON or base64")
                elif isinstance(val, list):
                    print(f"  Array length: {len(val)}")
                    print(f"  Raw bytes: {val}")
                    # Try to decode as bytes
                    try:
                        raw = bytes(val)
                        print(f"  As bytes ({len(raw)}): {raw[:50]}")
                        # Try zlib decompress
                        try:
                            decompressed = zlib.decompress(raw)
                            print(f"  Zlib decompressed ({len(decompressed)} bytes): {decompressed[:200]}")
                        except:
                            try:
                                decompressed = zlib.decompress(raw, zlib.MAX_WBITS | 32)
                                print(f"  Gzip decompressed ({len(decompressed)} bytes): {decompressed[:200]}")
                            except:
                                print(f"  Not zlib/gzip compressed")
                    except:
                        pass
                print()

# 2. Check history for siid=1 (might have map frames)
print("=== History for siid=1 ===\n")
for piid in [1, 2, 3, 4]:
    params = {"did": str(did), "uid": str(uid), "siid": 1, "piid": piid, "from": 1, "limit": 3, "region": "eu", "type": 3}
    r = session.post(hist_url, json=params, headers=H, timeout=10).json()
    if r.get("code") == 0:
        lst = r.get("data", {}).get("list", [])
        print(f"  1.{piid}: {len(lst)} history entries")
        if lst:
            for entry in lst[:2]:
                print(f"    Time: {entry.get('time', '?')}, Value: {str(entry.get('value', ''))[:100]}")

# 3. Sample 1.4 multiple times to see what changes (position data?)
print("\n=== 1.4 Telemetry Sampling (3 samples, 2s apart) ===\n")
for i in range(3):
    params = {"did": str(did), "keys": "1.4"}
    r = session.post(props_url, data=json.dumps(params, separators=(",", ":")), headers=H, timeout=10).json()
    if r.get("code") == 0:
        for p in r["data"]:
            if "value" in p:
                val = p["value"]
                ts = p.get("updateDate", 0)
                print(f"  Sample {i+1} (ts={ts}): {val}")
    if i < 2:
        time.sleep(2)

# 4. Try to get the device info to see model capabilities
print("\n=== Device Info ===\n")
info_url = f"{BASE}/dreame-user-iot/iotuserbind/device/info"
r = session.post(info_url, json={"did": str(did)}, headers=H, timeout=10).json()
print(f"  Code: {r.get('code')}")
if r.get("code") == 0:
    data = r.get("data", {})
    print(f"  Model: {data.get('model')}")
    print(f"  BindDomain: {data.get('bindDomain')}")
    print(f"  Property: {str(data.get('property', ''))[:200]}")
    # Save full device info
    with open("mova_device_info.json", "w") as f:
        json.dump(data, f, indent=2)
    print("  Saved to mova_device_info.json")

print("\nDone!")
