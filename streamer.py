import requests, re, json, base64
from urllib.parse import quote

# 1. Setup (Key & Token)
XOR_KEY = b"ns-v4-shield-9f2a"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMCda8Yhe3iZaWbvV5XKSTbuAn0M"

def xor_encrypt(payload_str):
    data = payload_str.encode('utf-8')
    encrypted = bytearray()
    for i, b in enumerate(data):
        encrypted.append(b ^ XOR_KEY[i % len(XOR_KEY)])
    return base64.b64encode(encrypted).decode('utf-8').replace('+', '-').replace('/', '_').replace('=', '')

def xor_decrypt(encoded_str):
    encoded_str = encoded_str.replace('-', '+').replace('_', '/')
    padding = '=' * (-len(encoded_str) % 4)
    encoded_str += padding
    try:
        data = base64.b64decode(encoded_str)
        decrypted = bytearray()
        for i, b in enumerate(data):
            decrypted.append(b ^ XOR_KEY[i % len(XOR_KEY)])
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        return {"error": "Decryption failed: " + str(e)}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Authorization": f"Bearer {TOKEN}",
    "token": TOKEN,
    "client-type": "WEB",
    "X-Shield-Encode": "1",
    "Origin": "https://pw-next.ai.studio",
    "Referer": "https://pw-next.ai.studio/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"
}

def api_proxy_call(path):
    payload = {"path": path, "method": "GET"}
    encrypted_t = xor_encrypt(json.dumps(payload))
    url = f"https://pw-next.ai.studio/api/q?t={quote(encrypted_t)}"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print(f"  Proxy Status: {r.status_code}")
        if r.status_code == 200 and "payload" in r.text:
            return xor_decrypt(r.json()["payload"])
        else:
            print(f"  Proxy Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Proxy Error: {e}")
    return None

def direct_stream_call():
    url = "https://pw-next.ai.studio/api/stream-url?batchId=65d862392b1da90018ad8f3b&subjectId=65dc6b432b2f290019d5c69a&lectureId=67f6489a1729f8d024af215e&scheduleId=67f6489a1729f8d024af215e&videoId=67f6489a1729f8d024af215e&fresh=1"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print(f"  Direct Status: {r.status_code}")
        if r.status_code == 200:
            if "payload" in r.text:
                return xor_decrypt(r.json()["payload"])
            else:
                return r.json()
        else:
            print(f"  Direct Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Direct Error: {e}")
    return None

print("=== TRYING METHOD 1: PROXY ===")
res1 = api_proxy_call("/api/stream-url?batchId=65d862392b1da90018ad8f3b&subjectId=65dc6b432b2f290019d5c69a&lectureId=67f6489a1729f8d024af215e&fresh=1")

print("\n=== TRYING METHOD 2: DIRECT ===")
res2 = direct_stream_call()

final_res = res1 if res1 and res1.get("data") else res2

if final_res and final_res.get("data"):
    print("\n[🔥 SUCCESS] Video Link Found:")
    print(json.dumps(final_res["data"], indent=2))
else:
    print("\n[-] Still failed. Data received:")
    print(res1)
    print(res2)

print("###_VIDEO_LINK_START_###", json.dumps(final_res.get("data") if final_res else {}) , "###_VIDEO_LINK_END_###")
