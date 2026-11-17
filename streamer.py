import requests, re, json, base64
from urllib.parse import quote

# Yeh tumhare JS se nikala hua key aur token hai
XOR_KEY = b"ns-v4-shield-9f2a"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemA... (yahan tumhara pura token paste karna)"

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
        return {"error": str(e)}

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "token": TOKEN,
    "client-type": "WEB",
    "X-Shield-Encode": "1",
    "User-Agent": "Mozilla/5.0 Chrome/120"
}

def api_call(path):
    payload = {"path": path, "method": "GET"}
    encrypted_t = xor_encrypt(json.dumps(payload))
    url = f"https://pw-next.ai.studio/api/q?t={quote(encrypted_t)}"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and "payload" in r.text:
            return xor_decrypt(r.json()["payload"])
    except: pass
    return None

# Tumhare JSON file se first lecture
batch_id = "65d862392b1da90018ad8f3b"
subject_id = "65dc6b432b2f290019d5c69a"
schedule_id = "67f6489a1729f8d024af215e"

print("Fetching video link from GitHub Server...")
res = api_call(f"/api/stream-url?batchId={batch_id}&subjectId={subject_id}&lectureId={schedule_id}&fresh=1")

if res and res.get("data"):
    print("SUCCESS! Video Link found:")
    print(json.dumps(res["data"], indent=2))
    with open("video_link.json", "w") as f:
        json.dump(res["data"], f, indent=2)
else:
    print("Failed to fetch video link.")
