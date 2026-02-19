"""Benchmark: full pipeline on test_data_10k.csv"""
import time
import sys

start = time.time()

def t():
    return f"[{time.time()-start:5.1f}s]"

print(f"{t()} Reading CSV...")
with open("test_data_10k.csv", "r") as f:
    csv_text = f.read()

from app.utils.csv_parser import parse_csv
print(f"{t()} Parsing CSV...")
df, G, meta = parse_csv(csv_text)
print(f"{t()} Parsed: {meta['total_transactions']} txns, {meta['total_accounts']} accts, {meta['total_edges']} edges")

from app.agents.graph_agent import GraphAgent
print(f"{t()} Running Graph Agent...")
ga = GraphAgent(G, df)
gr = ga.run()
print(f"{t()} Graph: {len(gr['rings'])} rings, {len(gr['suspicious_accounts'])} suspicious")

from app.agents.ml_agent import MLAgent
print(f"{t()} Running ML Agent...")
ml = MLAgent(G, df)
mr = ml.run()
print(f"{t()} ML: scored {len(mr['ml_scores'])} accounts")

from app.agents.quantum_agent import QuantumAgent
print(f"{t()} Running Quantum Agent...")
qa = QuantumAgent(G, gr.get("rings", []))
qr = qa.run()
exec_count = qr.get("circuits_executed", 0)
skip_count = qr.get("circuits_skipped", 0)
print(f"{t()} Quantum: executed={exec_count}, skipped={skip_count}")

from app.agents.aggregator import AggregatorAgent
print(f"{t()} Running Aggregator...")
agg = AggregatorAgent(gr, mr, qr, meta["total_accounts"], start)
out = agg.run()
print(f"{t()} Aggregated: {out['summary']['suspicious_accounts_flagged']} suspicious, {out['summary']['fraud_rings_detected']} rings")

from app.agents.disruption_engine import DisruptionEngine
print(f"{t()} Running Disruption Engine...")
de = DisruptionEngine(G, out["fraud_rings"], out["suspicious_accounts"], qr)
dr = de.run()
print(f"{t()} Disruption: {len(dr['strategies'])} strategies")

from app.agents.crime_team import CrimeTeam
print(f"{t()} Running Crime Team...")
ct = CrimeTeam(gr, mr, qr, out, dr)
cr = ct.run()
print(f"{t()} Crime Team: done")

elapsed = time.time() - start
print(f"\n{'='*50}")
print(f"  TOTAL: {elapsed:.2f}s")
if elapsed <= 30:
    print(f"  PASS: Under 30 seconds!")
else:
    print(f"  FAIL: {elapsed:.1f}s > 30s target")
print(f"{'='*50}")
