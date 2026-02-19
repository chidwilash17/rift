"""Quick integration test for the LLM-powered crime team."""
import urllib.request
import json

boundary = "----FormBoundary123"
csv_path = r"c:\rift\test_data.csv"

with open(csv_path, "rb") as f:
    csv_data = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="test_data.csv"\r\n'
    f"Content-Type: text/csv\r\n\r\n"
).encode() + csv_data + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(
    "http://localhost:8000/api/analyze",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)
resp = urllib.request.urlopen(req, timeout=120)
data = json.loads(resp.read())

ct = data.get("crime_team", {})
print("=== CRIME TEAM ===")
print(f"AI Powered: {ct.get('ai_powered', False)}")
print(f"LLM Model:  {ct.get('llm_model', 'None')}")
print(f"Messages:   {len(ct.get('conversation', []))}")
for m in ct.get("conversation", [])[:3]:
    has_ai = m.get("ai_generated", False)
    tag = " [AI]" if has_ai else ""
    print(f"  [{m['agent_name']}]{tag} ({m['phase']}) {m['content'][:100]}...")
print(f"Evidence:   {len(ct.get('evidence_chain', []))}")
print(f"Actions:    {len(ct.get('recommended_actions', []))}")
conf = ct.get("confidence_assessment", {})
print(f"Confidence: {conf.get('overall_confidence')}% ({conf.get('confidence_level')})")

s = data.get("summary", {})
print(f"\n=== SUMMARY ===")
print(f"Suspicious: {s.get('suspicious_accounts_flagged')}")
print(f"Rings:      {s.get('fraud_rings_detected')}")
print(f"Time:       {s.get('processing_time_seconds')}s")
print("\nDONE")
