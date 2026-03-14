#!/usr/bin/env python3
"""Scan ALL possible siid.piid combinations for Mova 600 Plus."""
import json, zlib, base64, hashlib, requests, time

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

# Scan siid 1-15, piid 1-30
print("=== Full Property Scan (siid 1-15, piid 1-30) ===\n")
all_keys = []
for siid in range(1, 16):
    keys = ",".join(f"{siid}.{piid}" for piid in range(1, 31))
    all_keys.append(keys)

# Batch request all keys at once
all_flat = ",".join(all_keys)
params = {"did": str(did), "keys": all_flat}
payload = json.dumps(params, separators=(",", ":"))
r = session.post(props_url, data=payload, headers=H, timeout=30).json()

if r.get("code") == 0:
    results = r.get("data", [])
    with_value = [p for p in results if "value" in p]
    without_value = [p for p in results if "value" not in p and "key" in p]

    print(f"Total keys found: {len(results)}")
    print(f"With values: {len(with_value)}")
    print(f"Without values (registered but empty): {len(without_value)}")

    print(f"\n--- Properties WITH values ---")
    for p in sorted(with_value, key=lambda x: [int(n) for n in x["key"].split(".")]):
        val = str(p.get("value", ""))
        ts = p.get("updateDate", 0)
        age = (time.time() * 1000 - ts) / 1000 if ts else 0
        print(f"  {p['key']:8s} = {val[:120]:120s} (updated {age:.0f}s ago)")

    print(f"\n--- Keys registered but NO value ---")
    for p in sorted(without_value, key=lambda x: [int(n) for n in x["key"].split(".")]):
        print(f"  {p['key']}")

    # Save full results
    with open("mova_all_props.json", "w") as f:
        json.dump({"with_value": with_value, "without_value": [p["key"] for p in without_value]}, f, indent=2)
    print(f"\nSaved to mova_all_props.json")
else:
    print(f"Error: {r.get('code')} {r.get('msg')}")

print("\nDone!")
