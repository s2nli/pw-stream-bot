import requests, json, base64
from urllib.parse import quote
import concurrent.futures

# 1. Setup
XOR_KEY = b"ns-v4-shield-9f2a"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMCda8Yhe3iZaWbvV5XKSTbuAn0M"

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
    except: return None

def api_call(path):
    payload = {"path": path, "method": "GET"}
    encrypted_t = xor_encrypt(json.dumps(payload))
    url = f"https://pw-next.ai.studio/api/q?t={quote(encrypted_t)}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and "payload" in r.text:
            return xor_decrypt(r.json()["payload"])
    except: pass
    return None

def get_stream_url(batch_id, subject_id, schedule_id):
    url = f"https://pw-next.ai.studio/api/stream-url?batchId={batch_id}&subjectId={subject_id}&lectureId={schedule_id}&scheduleId={schedule_id}&videoId={schedule_id}&fresh=1"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("directHlsUrl") or data.get("hlsStreamUrl") or data.get("streamUrl")
    except: pass
    return None

# 2. Load Master Data
print("[*] Loading 18k batches...")
try:
    with open("master_batches.json", "r") as f:
        master_batches = json.load(f)
except Exception as e:
    print(f"[-] File not found: {e}")
    exit()

print(f"[+] Total Batches: {len(master_batches)}")

# 3. Process first 100 batches (limit to avoid timeout)
batches_to_process = master_batches[:100] 
print(f"[*] Processing first {len(batches_to_process)} batches...")

final_data = []

for batch in batches_to_process:
    batch_id = batch.get("id")
    batch_name = batch.get("name", "Unknown")
    
    if not batch_id: continue
    
    print(f"\n[2] Fetching Batch: {batch_name}")
    
    details = api_call(f"/v3/batches/{batch_id}/details")
    if not details or "data" not in details:
        continue
        
    subjects = details["data"].get("subjects", [])
    if not subjects: continue
    
    batch_res = {"batch_id": batch_id, "batch_name": batch_name, "subjects": []}
    
    for subj in subjects:
        subj_id = subj.get("_id")
        subj_name = subj.get("name", "Unknown")
        
        schedule_path = f"/batch-service/v3/batch-subject-schedules/{batch_id}/subject/{subj_id}/contents?skip=0&limit=100"
        schedules = api_call(schedule_path)
        
        if not schedules or "data" not in schedules: continue
        
        lectures = schedules["data"]
        subj_res = {"subject_id": subj_id, "subject_name": subj_name, "lectures": []}
        
        for lec in lectures:
            title = lec.get("topic", "Untitled")
            schedule_id = lec.get("_id")
            
            v_url = get_stream_url(batch_id, subj_id, schedule_id)
            subj_res["lectures"].append({
                "title": title,
                "schedule_id": schedule_id,
                "video_url": v_url
            })
        batch_res["subjects"].append(subj_res)
    final_data.append(batch_res)

with open("all_lectures_links.json", "w") as f:
    json.dump(final_data, f, indent=2)

print("\n[🔥 DONE] Saved to all_lectures_links.json")
