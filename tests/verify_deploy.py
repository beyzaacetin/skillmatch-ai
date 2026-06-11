import requests
import time

base_url = "https://skillmatch-ai-production-042a.up.railway.app"

print("Waiting for deployment to go live (checking for 'is_deleted' field)...")
for i in range(30):
    try:
        res = requests.get(f"{base_url}/api/candidates/", headers={"Cache-Control": "no-cache"})
        if res.status_code == 200:
            candidates = res.json()
            if candidates and "is_deleted" in candidates[0]:
                print("New deployment is LIVE!")
                break
        print(f"[{i+1}/30] Not live yet... status: {res.status_code}")
    except Exception as e:
        print(f"[{i+1}/30] Connection error: {e}")
    time.sleep(15)
else:
    print("Timed out waiting for deployment to go live.")
    exit(1)

# Now run the test
candidate_id = 3 # Erkut Oğuz
print(f"\n--- SOFT DELETING CANDIDATE {candidate_id} ---")
res = requests.delete(f"{base_url}/api/candidates/{candidate_id}")
print(f"Status (Expected 200): {res.status_code}")
print(f"Response: {res.json()}")

print(f"\n--- VERIFYING DETAIL IS HIDDEN (404) ---")
res = requests.get(f"{base_url}/api/candidates/{candidate_id}")
print(f"Status (Expected 404): {res.status_code}")

print(f"\n--- VERIFYING ABSENT FROM LISTING ---")
res = requests.get(f"{base_url}/api/candidates/")
candidates_after = res.json()
print("Candidate IDs in list:", [c["id"] for c in candidates_after])
assert candidate_id not in [c["id"] for c in candidates_after], "Candidate still in list!"

print(f"\n--- RESTORING CANDIDATE {candidate_id} ---")
res = requests.put(f"{base_url}/api/candidates/{candidate_id}/restore")
print(f"Status (Expected 200): {res.status_code}")
print(f"Response: {res.json()}")

print(f"\n--- VERIFYING DETAIL IS VISIBLE AGAIN (200) ---")
res = requests.get(f"{base_url}/api/candidates/{candidate_id}")
print(f"Status (Expected 200): {res.status_code}")
if res.status_code == 200:
    name_clean = res.json()['name'].encode('ascii', errors='ignore').decode()
    print(f"Name (clean): {name_clean}")
