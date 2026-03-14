#!/usr/bin/env python3
"""Find the map data for Mova 600 Plus — try everything."""
import json, zlib, base64, hashlib, requests, time, ssl, threading

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
print(f"Logged in: uid={uid}\n")

# ============================================================
# ATTACK 1: Try common filename patterns with getOss1dDownloadUrl
# ============================================================
print("=" * 60)
print("ATTACK 1: Brute-force OSS filenames")
print("=" * 60)

file_url_endpoint = f"{BASE}/{S[23]}/{S[39]}/{S[56]}"  # getOss1dDownloadUrl

# object_name pattern from protocol.py: f"{self._model}/{self._uid}/{str(self._did)}/0"
base_path = f"{MODEL}/{uid}/{DID}"

patterns = [
    # From protocol.py object_name pattern
    f"{base_path}/0",
    f"{base_path}/1",
    f"{base_path}/map",
    f"{base_path}/map_0",
    f"{base_path}/map_1",
    f"{base_path}/map_current",
    f"{base_path}/saved_map",
    f"{base_path}/map.bin",
    f"{base_path}/mapData",
    f"{base_path}/mapdata",
    # Without model prefix
    f"{uid}/{DID}/0",
    f"{uid}/{DID}/map",
    # Dreame vacuum style
    f"/{MODEL}/{uid}/{DID}/0",
    f"/{uid}/{DID}/0",
    # Direct patterns
    f"map_{DID}",
    f"{DID}/map",
    f"{DID}/0",
    # Try with leading slash removed (filename param strips first char in protocol.py!)
    f"/{base_path}/0",  # becomes base_path/0 after [1:]
]

for pattern in patterns:
    # protocol.py get_file_url strips first char: object_name[1:]
    params = {"did": DID, "uid": uid, S[35]: MODEL, "filename": pattern, S[21]: "eu"}
    try:
        r = session.post(file_url_endpoint, json=params, headers=H, timeout=5).json()
        if r.get("code") == 0:
            url = r.get("data", "")
            # Try to download it
            try:
                dl = session.get(url, timeout=5)
                if dl.status_code == 200 and len(dl.content) > 0:
                    print(f"  ✓✓✓ FOUND: {pattern} -> {len(dl.content)} bytes!")
                    with open(f"mova_map_{pattern.replace('/', '_')}.bin", "wb") as f:
                        f.write(dl.content)
                    print(f"      Saved! First bytes: {dl.content[:50]}")
                else:
                    print(f"  ✗ {pattern}: URL works but download {dl.status_code} ({len(dl.content)}b)")
            except Exception as e:
                print(f"  ⚠ {pattern}: URL works, download error: {e}")
        else:
            pass  # Silently skip non-working patterns
    except:
        pass

# ============================================================
# ATTACK 2: Scan higher SIIDs (16-50) for hidden properties
# ============================================================
print(f"\n{'=' * 60}")
print("ATTACK 2: Scan SIIDs 16-50")
print("=" * 60)

props_url = f"{BASE}/dreame-user-iot/iotstatus/props"
for siid_start in range(16, 51, 10):
    keys = ",".join(f"{s}.{p}" for s in range(siid_start, min(siid_start+10, 51)) for p in range(1, 16))
    params = {"did": DID, "keys": keys}
    r = session.post(props_url, data=json.dumps(params, separators=(",", ":")), headers=H, timeout=10).json()
    if r.get("code") == 0:
        with_value = [p for p in r.get("data", []) if "value" in p]
        if with_value:
            print(f"  SIID {siid_start}-{siid_start+9}: {len(with_value)} properties with values!")
            for p in with_value:
                print(f"    {p['key']}: {str(p['value'])[:100]}")

# ============================================================
# ATTACK 3: Try the interim file URL (getDownloadUrl) with different params
# ============================================================
print(f"\n{'=' * 60}")
print("ATTACK 3: getDownloadUrl variations")
print("=" * 60)

interim_url = f"{BASE}/{S[23]}/{S[39]}/{S[55]}"  # getDownloadUrl

for fn in [f"{base_path}/0", f"/{base_path}/0", "map", f"{DID}"]:
    params = {"did": DID, S[35]: MODEL, S[40]: fn, S[21]: "eu"}  # S[40] = "filename"
    try:
        r = session.post(interim_url, json=params, headers=H, timeout=5).json()
        code = r.get("code")
        if code == 0:
            print(f"  ✓ {fn}: {r.get('data', '')[:200]}")
        else:
            print(f"  ✗ {fn}: code={code}")
    except Exception as e:
        print(f"  ✗ {fn}: {e}")

# ============================================================
# ATTACK 4: Check iotuserdata endpoint
# ============================================================
print(f"\n{'=' * 60}")
print("ATTACK 4: iotuserdata endpoint")
print("=" * 60)

# S[26] = "iotuserdata"
for action in ["getDeviceData", "list", "get", "query"]:
    url = f"{BASE}/{S[23]}/{S[26]}/{action}"
    params = {"did": DID, "uid": uid, "region": "eu"}
    try:
        r = session.post(url, json=params, headers=H, timeout=5).json()
        code = r.get("code")
        if code == 0:
            print(f"  ✓ {action}: {json.dumps(r.get('data', {}), indent=2)[:300]}")
        else:
            print(f"  ✗ {action}: code={code} msg={r.get('msg','')[:80]}")
    except Exception as e:
        print(f"  ✗ {action}: {e}")

# ============================================================
# ATTACK 5: MQTT listener — capture messages for 15 seconds
# ============================================================
print(f"\n{'=' * 60}")
print("ATTACK 5: MQTT listener (15 seconds)")
print("=" * 60)

from paho.mqtt import client as mqtt_client
import random

mqtt_messages = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        topic = f"/{S[7]}/{DID}/{uid}/{MODEL}/eu/"
        print(f"  Connected! Subscribing to: {topic}")
        client.subscribe(topic)
        # Also try wildcard
        client.subscribe(f"/{S[7]}/{DID}/#")
        print(f"  Also subscribing to: /{S[7]}/{DID}/#")
    else:
        print(f"  Connection failed: rc={rc}")

def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8", errors="replace")
    mqtt_messages.append({"topic": message.topic, "payload": payload[:500]})
    print(f"  MSG [{message.topic}]: {payload[:200]}")

try:
    # MQTT broker from device info
    mqtt_host = "20000.mt.eu.iot.mova-tech.com"
    mqtt_port = 19974

    # Generate client ID like protocol.py
    agent_id = "".join(random.choice("ABCDEF") for _ in range(13))
    client_id = f"p_{uid}_{agent_id}_{mqtt_host.split('.')[0]}"

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id, clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(r.get("uid", uid), token)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    print(f"  Connecting to {mqtt_host}:{mqtt_port}...")
    client.connect(mqtt_host, mqtt_port, 50)
    client.loop_start()

    time.sleep(15)
    client.loop_stop()
    client.disconnect()

    print(f"\n  Captured {len(mqtt_messages)} messages")
    if mqtt_messages:
        with open("mova_mqtt_messages.json", "w") as f:
            json.dump(mqtt_messages, f, indent=2)
        print("  Saved to mova_mqtt_messages.json")
except Exception as e:
    print(f"  MQTT failed: {e}")

# ============================================================
# ATTACK 6: Try device-specific API endpoints
# ============================================================
print(f"\n{'=' * 60}")
print("ATTACK 6: Device-specific endpoints")
print("=" * 60)

for endpoint in [
    f"dreame-user-iot/iotstatus/getMapData",
    f"dreame-user-iot/iotstatus/map",
    f"dreame-user-iot/iotmap/get",
    f"dreame-user-iot/iotmap/list",
    f"dreame-user-iot/iotmap/getMapList",
    f"dreame-iot-com/device/getMapData",
    f"dreame-iot-com/map/get",
    f"dreame-user-iot/device/getMapData",
    f"dreame-user-iot/iotstatus/getDeviceData",
]:
    url = f"{BASE}/{endpoint}"
    params = {"did": DID, "uid": uid, "region": "eu", "model": MODEL}
    try:
        r = session.post(url, json=params, headers=H, timeout=5).json()
        code = r.get("code")
        if code == 0:
            print(f"  ✓ {endpoint}: {json.dumps(r.get('data', {}), indent=2)[:300]}")
        elif code != 404:
            print(f"  ? {endpoint}: code={code} msg={r.get('msg','')[:80]}")
    except:
        pass

print("\nDone!")
