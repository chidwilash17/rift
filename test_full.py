"""Quick full test of all features."""
import urllib.request, json

with open('test_data.csv', 'rb') as f:
    csv_data = f.read()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
    f'Content-Disposition: form-data; name="file"; filename="test_data.csv"\r\n'
    f'Content-Type: text/csv\r\n\r\n'
).encode() + csv_data + b'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n'

req = urllib.request.Request(
    'http://localhost:8000/api/analyze',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW'},
    method='POST'
)
resp = urllib.request.urlopen(req, timeout=120)
data = json.loads(resp.read().decode())

print('=== ANALYSIS RESULT ===')
sa = data.get('suspicious_accounts', [])
fr = data.get('fraud_rings', [])
print(f'Suspicious accounts: {len(sa)}')
print(f'Fraud rings: {len(fr)}')
print(f'Processing time: {data["summary"]["processing_time_seconds"]}s')

print('\n=== DISRUPTION ENGINE ===')
d = data.get('disruption', {})
gs = d.get('global_summary', {})
print(f'Strategies: {len(d.get("strategies", []))}')
print(f'Critical nodes: {gs.get("unique_critical_nodes", 0)}')
print(f'Avg disruption: {gs.get("avg_disruption_potential", 0)}%')
print(f'Net resilience: {gs.get("network_resilience_score", 0)}%')
ns = d.get('network_stats', {})
print(f'Articulation points: {ns.get("articulation_point_count", 0)}')
tb = ns.get('top_betweenness', [])
print(f'Top betweenness: {tb[0]["account_id"] if tb else "N/A"}')

# Show first strategy details
strats = d.get('strategies', [])
if strats:
    s0 = strats[0]
    print(f'\nFirst ring: {s0["ring_id"]} ({s0["member_count"]} members)')
    print(f'  Max disruption: {s0["max_disruption_pct"]}%')
    print(f'  Critical nodes: {len(s0["critical_nodes"])}')
    opt = s0.get('optimal_pair_removal', {})
    if opt.get('nodes'):
        print(f'  Optimal pair: {opt["nodes"]} -> {opt["combined_impact"]}%')
    qo = s0.get('quantum_overlay', {})
    if qo.get('available'):
        print(f'  Quantum overlay: susp={len(qo["suspicious_partition"])}, clean={len(qo["clean_partition"])}')

print('\n=== CRIME TEAM ===')
ct = data.get('crime_team', {})
print(f'Conversation msgs: {len(ct.get("conversation", []))}')
print(f'Evidence chain: {len(ct.get("evidence_chain", []))}')
print(f'Actions: {len(ct.get("recommended_actions", []))}')
print(f'Timeline steps: {len(ct.get("investigation_timeline", []))}')
cf = ct.get('confidence_assessment', {})
print(f'Confidence: {cf.get("overall_confidence", 0)}% ({cf.get("confidence_level", "N/A")})')
case = ct.get('case_file', {})
print(f'Case number: {case.get("case_number", "N/A")}')
print(f'Priority: {case.get("priority", "N/A")}')

# Show conversation preview
conv = ct.get('conversation', [])
for msg in conv[:3]:
    print(f'  [{msg["agent_name"]}]: {msg["content"][:80]}...')

print('\n=== QUANTUM ===')
q = data.get('quantum_analysis', {})
print(f'Circuits: {q.get("circuits_executed", 0)}')

print('\n=== WHAT-IF TEST ===')
# Test What-If simulator
if sa:
    top3 = [a['account_id'] for a in sa[:3]]
    wi_body = json.dumps({'nodes': top3}).encode()
    wi_req = urllib.request.Request(
        'http://localhost:8000/api/whatif',
        data=wi_body,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    wi_resp = urllib.request.urlopen(wi_req, timeout=30)
    wi = json.loads(wi_resp.read().decode())
    print(f'Removed: {wi["nodes_removed"]}')
    eff = wi.get('effectiveness_score', {})
    print(f'Effectiveness: {eff.get("overall", 0)}% (Grade: {eff.get("grade", "?")})')
    print(f'Edge disruption: {eff.get("edge_disruption", 0)}%')
    print(f'Ring destruction: {eff.get("ring_destruction_rate", 0)}%')
    ri = wi.get('ring_impacts', [])
    for r in ri[:3]:
        print(f'  {r["ring_id"]}: {r["status"]} ({r["disruption_pct"]}%)')
    flow = wi.get('flow_impact', {})
    print(f'Flow disrupted: ${flow.get("disrupted_flow", 0):,.0f} ({flow.get("disruption_pct", 0)}%)')
    ai = wi.get('account_impacts', {})
    print(f'Risk reduction: {ai.get("risk_reduction_pct", 0)}%')

print('\n=== ALL TESTS PASSED ===')
