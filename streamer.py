import requests, re, json, base64
from urllib.parse import quote
import concurrent.futures

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
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "token": TOKEN,
    "client-type": "WEB",
    "X-Shield-Encode": "1",
    "Origin": "https://pw-next.ai.studio",
    "Referer": "https://pw-next.ai.studio/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"
}

batch_id = "65d862392b1da90018ad8f3b" # Lakshya JEE 2025

# 2. Hum pehle apne save kiye hue JSON se saare lectures nikalte hain
# Par GitHub pe wo JSON nahi hai, isliye hum direct API se subjects aur lectures mangayenge.
# Wait, Github pe JSON nahi hai, par humare paas IDs hain. 
# Hum subject list fetch karte hain pehle.

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

def get_stream_url(schedule_id, subject_id):
    url = f"https://pw-next.ai.studio/api/stream-url?batchId={batch_id}&subjectId={subject_id}&lectureId={schedule_id}&scheduleId={schedule_id}&videoId={schedule_id}&fresh=1"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data.get("directHlsUrl") or data.get("hlsStreamUrl") or data.get("streamUrl")
    except: pass
    return None

print("[1] Fetching Batch Details...")
details = api_call(f"/v3/batches/{batch_id}/details")
if not details:
    print("[-] Failed to get details.")
    exit()

subjects = details.get("data", {}).get("subjects", [])
print(f"[+] Found {len(subjects)} Subjects.")

all_lectures = []

for subj in subjects:
    subj_id = subj.get("_id")
    subj_name = subj.get("name", "Unknown")
    print(f"\n[2] Processing Subject: {subj_name}")
    
    schedule_path = f"/batch-service/v3/batch-subject-schedules/{batch_id}/subject/{subj_id}/contents?skip=0&limit=100"
    schedules = api_call(schedule_path)
    
    if schedules and "data" in schedules:
        lectures = schedules["data"]
        print(f"    [+] Found {len(lectures)} Lectures.")
        
        for lec in lectures:
            title = lec.get("topic", "Untitled")
            schedule_id = lec.get("_id")
            
            # Direct stream URL fetch karo (parallel)
            all_lectures.append({
                "title": title,
                "subject": subj_name,
                "subject_id": subj_id,
                "schedule_id": schedule_id
            })

print(f"\n[3] Resolving Video Links for {len(all_lectures)} lectures...")

def resolve_lec(lec):
    url = get_stream_url(lec["schedule_id"], lec["subject_id"])
    if url:
        lec["video_url"] = url
        print(f"  [+] {lec['title'][:40]}... -> FOUND")
    else:
        lec["video_url"] = None
        print(f"  [-] {lec['title'][:40]}... -> FAILED")
    return lec

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    all_lectures = list(executor.map(resolve_lec, all_lectures))

# Save to file
with open("all_lectures_links.json", "w") as f:
    json.dump(all_lectures, f, indent=2)

print("\n[🔥 DONE] All lectures resolved. Check 'all_lectures_links.json'")
