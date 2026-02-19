"""Quick test script for the analysis endpoint."""
import urllib.request
import json

csv_path = r"c:\rift\test_data.csv"

with open(csv_path, "rb") as f:
    csv_data = f.read()

boundary = "----TestBoundary1234"
body_parts = []
body_parts.append(f"------TestBoundary1234\r\nContent-Disposition: form-data; name=\"file\"; filename=\"test.csv\"\r\nContent-Type: text/csv\r\n\r\n")
body = body_parts[0].encode("utf-8") + csv_data + b"\r\n------TestBoundary1234--\r\n"

headers = {
    "Content-Type": f"multipart/form-data; boundary=----TestBoundary1234"
}

req = urllib.request.Request("http://localhost:8000/api/analyze", data=body, headers=headers)

try:
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    
    print("STATUS:", resp.status)
    print("\n=== SUMMARY ===")
    print(json.dumps(result.get("summary", {}), indent=2))
    
    print("\n=== FRAUD RINGS ===")
    for r in result.get("fraud_rings", []):
        print(f"  {r['ring_id']}: {r['pattern_type']} | members={len(r['member_accounts'])} | risk={r['risk_score']}")
        print(f"    accounts: {r['member_accounts']}")
    
    print(f"\n=== SUSPICIOUS ACCOUNTS ({len(result.get('suspicious_accounts', []))}) ===")
    for s in result.get("suspicious_accounts", [])[:10]:
        cs = s.get("component_scores", {})
        print(f"  {s['account_id']}: score={s['suspicion_score']} | graph={cs.get('graph',0)} ml={cs.get('ml',0)} quantum={cs.get('quantum',0)}")
        print(f"    patterns: {s['detected_patterns']} | ring: {s['ring_id']}")
    
    qa = result.get("quantum_analysis", {})
    print(f"\n=== QUANTUM ===")
    print(f"  Available: {qa.get('available', False)}")
    print(f"  Circuits: {qa.get('circuits_executed', 0)}")
    for qr in qa.get("results", []):
        if "error" not in qr:
            print(f"  {qr.get('ring_id')}: {qr.get('n_qubits')} qubits, depth={qr.get('circuit_depth')}, gates={qr.get('gate_count')}")
            print(f"    optimal: {qr.get('optimal_bitstring')}")
            print(f"    partition_score: {qr.get('partition_score')}")
            print(f"    suspicious_set: {qr.get('suspicious_set')}")
            tm = qr.get('top_measurements', [])
            print(f"    measurements: {len(tm)} entries")
            if tm:
                print(f"    top: |{tm[0]['bitstring']}> p={tm[0]['probability']}")
            img = qr.get('circuit_image', '')
            print(f"    circuit_image: {'YES' if img else 'NO'} ({len(img)} chars)")
            print(f"    scores: {qr.get('quantum_scores', {})}")
        else:
            print(f"  {qr.get('ring_id')}: ERROR - {qr.get('error')}")
    
    print("\n=== GRAPH VIZ DATA ===")
    gd = result.get("graph_data", {})
    print(f"  Nodes: {len(gd.get('nodes', []))}, Edges: {len(gd.get('edges', []))}")
    
    print("\nSUCCESS!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
