"""
Generate 10,000-row test CSV for RIFT Money Muling Detection Engine.
Covers ALL detection patterns:
  1. Cycles (length 3, 4, 5) — various risk levels
  2. Fan-in smurfing (10+ senders → 1 aggregator)
  3. Fan-out smurfing (1 disperser → 10+ receivers)
  4. Shell networks (chains through low-activity intermediaries)
  5. Mixed patterns (accounts in multiple rings)
  6. Normal/legitimate noise (merchants, payroll, P2P)
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

rows = []
txn_id = 0

def tid():
    global txn_id
    txn_id += 1
    return f"TXN_{txn_id:05d}"

def ts(base, offset_hours=0, jitter_minutes=0):
    dt = base + timedelta(hours=offset_hours, minutes=random.randint(-jitter_minutes, jitter_minutes) if jitter_minutes else 0)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def acc(prefix, n):
    return f"{prefix}_{n:04d}"

# ═══════════════════════════════════════════════
# PATTERN 1: CYCLES (length 3, 4, 5)
# ~1500 transactions
# ═══════════════════════════════════════════════

# --- High-risk 3-node cycles (fast, high amount) ---
# 20 distinct 3-cycles, each with multiple rounds of transactions
for c in range(20):
    base_time = datetime(2026, 1, 10 + (c % 20), 8, 0)
    a, b, d = acc("CYC3", c*3), acc("CYC3", c*3+1), acc("CYC3", c*3+2)
    for rnd in range(5):  # 5 rounds per cycle
        amt = random.uniform(3000, 15000)
        fee = random.uniform(50, 200)
        rows.append([tid(), a, b, round(amt, 2), ts(base_time, rnd*4)])
        rows.append([tid(), b, d, round(amt - fee, 2), ts(base_time, rnd*4 + 1)])
        rows.append([tid(), d, a, round(amt - fee*2, 2), ts(base_time, rnd*4 + 2)])
# 20 * 5 * 3 = 300 rows

# --- Medium-risk 4-node cycles ---
for c in range(15):
    base_time = datetime(2026, 2, 1 + (c % 15), 9, 0)
    nodes = [acc("CYC4", c*4+i) for i in range(4)]
    for rnd in range(4):
        amt = random.uniform(2000, 8000)
        fee = random.uniform(30, 150)
        for i in range(4):
            rows.append([tid(), nodes[i], nodes[(i+1) % 4], round(amt - fee*i, 2),
                         ts(base_time, rnd*6 + i*1.5)])
# 15 * 4 * 4 = 240 rows

# --- 5-node cycles (lower risk, longer time span) ---
for c in range(12):
    base_time = datetime(2026, 3, 1 + (c % 12), 10, 0)
    nodes = [acc("CYC5", c*5+i) for i in range(5)]
    for rnd in range(3):
        amt = random.uniform(1000, 5000)
        fee = random.uniform(20, 100)
        for i in range(5):
            rows.append([tid(), nodes[i], nodes[(i+1) % 5], round(amt - fee*i, 2),
                         ts(base_time, rnd*24 + i*3, jitter_minutes=30)])
# 12 * 3 * 5 = 180 rows

# --- Ultra-high risk 3-cycles: very fast (<24h), huge amounts ---
for c in range(8):
    base_time = datetime(2026, 1, 5, 2 + c*2, 0)
    a, b, d = acc("UHCYC", c*3), acc("UHCYC", c*3+1), acc("UHCYC", c*3+2)
    for rnd in range(8):
        amt = random.uniform(10000, 50000)
        rows.append([tid(), a, b, round(amt, 2), ts(base_time, rnd*2)])
        rows.append([tid(), b, d, round(amt*0.97, 2), ts(base_time, rnd*2 + 0.5)])
        rows.append([tid(), d, a, round(amt*0.94, 2), ts(base_time, rnd*2 + 1)])
# 8 * 8 * 3 = 192 rows

# --- Slow cycles (spread over weeks, lower risk) ---
for c in range(10):
    base_time = datetime(2026, 4, 1, 10, 0)
    nodes = [acc("SLOWCYC", c*3+i) for i in range(3)]
    for rnd in range(6):
        amt = random.uniform(500, 3000)
        for i in range(3):
            rows.append([tid(), nodes[i], nodes[(i+1) % 3], round(amt, 2),
                         ts(base_time, rnd*72 + i*24)])
# 10 * 6 * 3 = 180 rows

# --- Cross-connected cycles (shared nodes between 2 cycles) ---
for c in range(5):
    base_time = datetime(2026, 5, 1 + c*2, 8, 0)
    shared = acc("XCYC", c*10)
    cycle1 = [shared, acc("XCYC", c*10+1), acc("XCYC", c*10+2)]
    cycle2 = [shared, acc("XCYC", c*10+3), acc("XCYC", c*10+4)]
    for rnd in range(5):
        amt1 = random.uniform(2000, 8000)
        amt2 = random.uniform(3000, 10000)
        for i in range(3):
            rows.append([tid(), cycle1[i], cycle1[(i+1)%3], round(amt1, 2), ts(base_time, rnd*8 + i*2)])
            rows.append([tid(), cycle2[i], cycle2[(i+1)%3], round(amt2, 2), ts(base_time, rnd*8 + i*2 + 1)])
# 5 * 5 * 6 = 150 rows

# Total cycles: ~1242 rows

# ═══════════════════════════════════════════════
# PATTERN 2: SMURFING — FAN-IN
# ~2000 transactions
# ═══════════════════════════════════════════════

# --- Large fan-in hubs (15-25 senders each) ---
for hub_idx in range(8):
    hub = acc("FIHUB", hub_idx)
    n_senders = random.randint(15, 25)
    base_time = datetime(2026, 1, 15 + (hub_idx % 10), 6, 0)
    
    # Each sender sends 3-8 transactions in bursts
    for s in range(n_senders):
        sender = acc("FIS", hub_idx * 100 + s)
        n_tx = random.randint(3, 8)
        for t in range(n_tx):
            amt = random.uniform(100, 500)  # Small amounts (structuring)
            rows.append([tid(), sender, hub, round(amt, 2),
                         ts(base_time, t * 0.5 + s * 0.2, jitter_minutes=10)])
    
    # Hub then sends aggregated amounts out to 2-5 accounts
    out_receivers = random.randint(2, 5)
    total_received = sum(r[3] for r in rows[-n_senders * 5:] if r[2] == hub)
    for r in range(out_receivers):
        rows.append([tid(), hub, acc("FIOUT", hub_idx * 10 + r),
                     round(random.uniform(1000, 5000), 2),
                     ts(base_time, 48 + r*2)])
# Approx 8 * 20 * 5 + 8 * 3 = ~824 rows

# --- Medium fan-in (exactly 10-14 senders) ---
for hub_idx in range(10):
    hub = acc("FIMHUB", hub_idx)
    n_senders = random.randint(10, 14)
    base_time = datetime(2026, 2, 5 + hub_idx, 7, 0)
    
    for s in range(n_senders):
        sender = acc("FIMS", hub_idx * 100 + s)
        n_tx = random.randint(2, 5)
        for t in range(n_tx):
            amt = random.uniform(200, 900)
            rows.append([tid(), sender, hub, round(amt, 2),
                         ts(base_time, t * 1 + s * 0.3, jitter_minutes=15)])
    
    # Hub disperses
    for r in range(3):
        rows.append([tid(), hub, acc("FIMOUT", hub_idx * 10 + r),
                     round(random.uniform(2000, 8000), 2),
                     ts(base_time, 36 + r*3)])
# Approx 10 * 12 * 3.5 + 30 = ~450 rows

# --- High-value fan-in (large individual amounts) ---
for hub_idx in range(6):
    hub = acc("FIVHUB", hub_idx)
    n_senders = random.randint(12, 18)
    base_time = datetime(2026, 3, 10 + hub_idx, 8, 0)
    
    for s in range(n_senders):
        sender = acc("FIVS", hub_idx * 100 + s)
        n_tx = random.randint(2, 4)
        for t in range(n_tx):
            amt = random.uniform(2000, 5000)  # Higher individual amounts
            rows.append([tid(), sender, hub, round(amt, 2),
                         ts(base_time, t * 2 + s * 0.5, jitter_minutes=20)])
    
    for r in range(3):
        rows.append([tid(), hub, acc("FIVOUT", hub_idx * 10 + r),
                     round(random.uniform(10000, 30000), 2),
                     ts(base_time, 48 + r*4)])
# Approx 6 * 15 * 3 + 18 = ~288 rows

# Total fan-in: ~1562 rows

# ═══════════════════════════════════════════════
# PATTERN 3: SMURFING — FAN-OUT
# ~2000 transactions
# ═══════════════════════════════════════════════

# --- Large fan-out hubs (15-25 receivers each) ---
for hub_idx in range(8):
    hub = acc("FOHUB", hub_idx)
    n_receivers = random.randint(15, 25)
    base_time = datetime(2026, 1, 20 + (hub_idx % 8), 9, 0)
    
    # Hub receives from a few sources first
    for s in range(random.randint(2, 4)):
        rows.append([tid(), acc("FOIN", hub_idx * 10 + s), hub,
                     round(random.uniform(5000, 20000), 2),
                     ts(base_time, -24 + s*2)])
    
    # Then disperses to many receivers quickly
    for r in range(n_receivers):
        receiver = acc("FOR", hub_idx * 100 + r)
        n_tx = random.randint(2, 6)
        for t in range(n_tx):
            amt = random.uniform(100, 800)
            rows.append([tid(), hub, receiver, round(amt, 2),
                         ts(base_time, t * 0.3 + r * 0.15, jitter_minutes=5)])
# Approx 8 * (3 + 20*4) = ~664 rows

# --- Medium fan-out ---
for hub_idx in range(10):
    hub = acc("FOMHUB", hub_idx)
    n_receivers = random.randint(10, 14)
    base_time = datetime(2026, 2, 15 + (hub_idx % 10), 10, 0)
    
    for s in range(3):
        rows.append([tid(), acc("FOMIN", hub_idx * 10 + s), hub,
                     round(random.uniform(3000, 10000), 2),
                     ts(base_time, -12 + s)])
    
    for r in range(n_receivers):
        receiver = acc("FOMR", hub_idx * 100 + r)
        n_tx = random.randint(2, 4)
        for t in range(n_tx):
            amt = random.uniform(200, 1000)
            rows.append([tid(), hub, receiver, round(amt, 2),
                         ts(base_time, t * 0.5 + r * 0.3, jitter_minutes=10)])
# Approx 10 * (3 + 12*3) = ~390 rows

# --- Rapid fan-out (all within hours, high risk) ---
for hub_idx in range(6):
    hub = acc("FORPD", hub_idx)
    n_receivers = random.randint(12, 20)
    base_time = datetime(2026, 4, 5 + hub_idx, 14, 0)
    
    rows.append([tid(), acc("FORPIN", hub_idx), hub,
                 round(random.uniform(20000, 50000), 2),
                 ts(base_time, -2)])
    
    for r in range(n_receivers):
        receiver = acc("FORPR", hub_idx * 100 + r)
        n_tx = random.randint(3, 6)
        for t in range(n_tx):
            amt = random.uniform(500, 2000)
            rows.append([tid(), hub, receiver, round(amt, 2),
                         ts(base_time, t * 0.1 + r * 0.05, jitter_minutes=3)])
# Approx 6 * (1 + 16*4.5) = ~438 rows

# Total fan-out: ~1492 rows

# ═══════════════════════════════════════════════
# PATTERN 4: SHELL NETWORKS
# ~1000 transactions
# Shell accounts have exactly 2-3 total transactions
# ═══════════════════════════════════════════════

# --- Long chains (5-6 hops) through dedicated shell accounts ---
for chain_idx in range(20):
    chain_len = random.choice([5, 6])
    base_time = datetime(2026, 1, 25, 8 + chain_idx % 12, 0)
    base_amt = random.uniform(5000, 20000)
    
    nodes = [acc("SHSTART", chain_idx)]
    for i in range(chain_len - 2):
        nodes.append(acc("SHELL", chain_idx * 10 + i))
    nodes.append(acc("SHEND", chain_idx))
    
    for i in range(len(nodes) - 1):
        fee = random.uniform(20, 100)
        rows.append([tid(), nodes[i], nodes[i+1], round(base_amt - fee * i, 2),
                     ts(base_time, i * 4)])
# 20 * ~5 = 100 rows (but shell accounts only get 1 in + 1 out = 2 tx)

# --- Medium chains (3-4 hops) ---
for chain_idx in range(30):
    chain_len = random.choice([3, 4])
    base_time = datetime(2026, 2, 10 + (chain_idx % 15), 9, 0)
    base_amt = random.uniform(3000, 15000)
    
    nodes = [acc("SHMS", chain_idx)]
    for i in range(chain_len - 2):
        nodes.append(acc("SHMED", chain_idx * 10 + i))
    nodes.append(acc("SHME", chain_idx))
    
    for i in range(len(nodes) - 1):
        fee = random.uniform(10, 50)
        rows.append([tid(), nodes[i], nodes[i+1], round(base_amt - fee * i, 2),
                     ts(base_time, i * 6)])
# 30 * ~3 = 90 rows

# --- Shell chains with similar amounts (high CV risk) ---
for chain_idx in range(25):
    chain_len = random.choice([4, 5])
    base_time = datetime(2026, 3, 5 + (chain_idx % 20), 10, 0)
    base_amt = random.uniform(8000, 25000)
    
    nodes = [acc("SHSIM_S", chain_idx)]
    for i in range(chain_len - 2):
        nodes.append(acc("SHSIM", chain_idx * 10 + i))
    nodes.append(acc("SHSIM_E", chain_idx))
    
    # Nearly identical amounts (low CV → high risk)
    for i in range(len(nodes) - 1):
        fee = random.uniform(5, 20)  # Very small fees
        rows.append([tid(), nodes[i], nodes[i+1], round(base_amt - fee * i, 2),
                     ts(base_time, i * 3)])
# 25 * ~4 = 100 rows

# --- Repeated shell usage (same shell accounts for multiple chains) ---
shared_shells = [acc("RSHELL", i) for i in range(15)]
for chain_idx in range(30):
    base_time = datetime(2026, 4, 1 + (chain_idx % 20), 11, 0)
    base_amt = random.uniform(2000, 10000)
    
    start = acc("RSTART", chain_idx)
    # Pick 1-2 shared shell intermediaries (careful: each must stay at 2-3 total tx)
    shell = shared_shells[chain_idx % 15]
    end = acc("REND", chain_idx)
    
    rows.append([tid(), start, shell, round(base_amt, 2), ts(base_time, 0)])
    rows.append([tid(), shell, end, round(base_amt * 0.97, 2), ts(base_time, 3)])
# 30 * 2 = 60 rows

# --- Extra pass-through transactions to give shells exactly 2-3 tx ---
# Add a few extra transactions through some shells to bring tx_count to 3
for i in range(0, 15, 2):
    shell = shared_shells[i]
    rows.append([tid(), acc("REXTRA_S", i), shell, round(random.uniform(1000, 5000), 2),
                 ts(datetime(2026, 4, 25), i)])
# ~8 rows

# --- Branching shell network (one source → multiple shell paths → multiple endpoints) ---
for net_idx in range(10):
    source = acc("BSHSRC", net_idx)
    base_time = datetime(2026, 5, 5 + net_idx, 8, 0)
    n_paths = random.randint(3, 5)
    
    for p in range(n_paths):
        path_len = random.randint(3, 5)
        base_amt = random.uniform(5000, 15000)
        
        nodes = [source]
        for i in range(path_len - 2):
            nodes.append(acc("BSHELL", net_idx * 100 + p * 10 + i))
        nodes.append(acc("BSHEND", net_idx * 100 + p))
        
        for i in range(len(nodes) - 1):
            fee = random.uniform(10, 80)
            rows.append([tid(), nodes[i], nodes[i+1], round(base_amt - fee * i, 2),
                         ts(base_time, p * 12 + i * 2)])
# 10 * 4 * 4 = ~160 rows

# Total shell: ~518 rows

# ═══════════════════════════════════════════════
# PATTERN 5: MIXED / OVERLAPPING PATTERNS
# Accounts that appear in multiple pattern types
# ~500 transactions
# ═══════════════════════════════════════════════

# --- Cycle + Fan-in combo: cycle members also receive from fan-in structure ---
for combo in range(5):
    base_time = datetime(2026, 5, 15 + combo, 8, 0)
    # Create a 3-cycle
    cyc_nodes = [acc("MIX_CYC", combo*3+i) for i in range(3)]
    for rnd in range(4):
        amt = random.uniform(3000, 10000)
        for i in range(3):
            rows.append([tid(), cyc_nodes[i], cyc_nodes[(i+1)%3], round(amt, 2),
                         ts(base_time, rnd*6 + i*1.5)])
    
    # Fan-in to the first cycle node from 12+ accounts
    hub = cyc_nodes[0]
    for s in range(12):
        sender = acc("MIX_FI", combo*20+s)
        for t in range(2):
            rows.append([tid(), sender, hub, round(random.uniform(100, 600), 2),
                         ts(base_time, 48 + s*0.3 + t*0.5)])
# 5 * (4*3 + 12*2) = 5 * 36 = 180 rows

# --- Shell + Cycle combo: shell chain leads into a cycle ---
for combo in range(5):
    base_time = datetime(2026, 6, 1 + combo*2, 9, 0)
    # Shell chain of 3
    shell_start = acc("MSHST", combo)
    shell_mid = acc("MSHMID", combo)
    cycle_entry = acc("MSHCYC", combo*3)
    cyc_b = acc("MSHCYC", combo*3+1)
    cyc_c = acc("MSHCYC", combo*3+2)
    
    base_amt = random.uniform(5000, 15000)
    rows.append([tid(), shell_start, shell_mid, round(base_amt, 2), ts(base_time, 0)])
    rows.append([tid(), shell_mid, cycle_entry, round(base_amt*0.97, 2), ts(base_time, 3)])
    
    for rnd in range(5):
        amt = random.uniform(2000, 8000)
        rows.append([tid(), cycle_entry, cyc_b, round(amt, 2), ts(base_time, 12 + rnd*6)])
        rows.append([tid(), cyc_b, cyc_c, round(amt*0.96, 2), ts(base_time, 12 + rnd*6 + 1.5)])
        rows.append([tid(), cyc_c, cycle_entry, round(amt*0.92, 2), ts(base_time, 12 + rnd*6 + 3)])
# 5 * (2 + 15) = 85 rows

# --- Fan-in → Fan-out combo (classic layering) ---
for combo in range(4):
    hub = acc("LAYER", combo)
    base_time = datetime(2026, 6, 15 + combo*3, 7, 0)
    
    # 12+ senders fan-in
    for s in range(14):
        sender = acc("LAYIN", combo*20+s)
        for t in range(3):
            rows.append([tid(), sender, hub, round(random.uniform(150, 700), 2),
                         ts(base_time, s*0.2 + t*0.4, jitter_minutes=5)])
    
    # 12+ receivers fan-out
    for r in range(14):
        receiver = acc("LAYOUT", combo*20+r)
        for t in range(3):
            rows.append([tid(), hub, receiver, round(random.uniform(150, 700), 2),
                         ts(base_time, 24 + r*0.2 + t*0.4, jitter_minutes=5)])
# 4 * (14*3 + 14*3) = 4 * 84 = 336 rows

# Total mixed: ~601 rows

# ═══════════════════════════════════════════════
# PATTERN 6: NORMAL / LEGITIMATE NOISE
# Fill remaining rows to reach 10,000
# ═══════════════════════════════════════════════

current_count = len(rows)
remaining = 10000 - current_count
print(f"Fraud pattern rows: {current_count}, Need {remaining} normal rows")

# --- Merchant transactions (many senders → 1 merchant, regular amounts, few outgoing) ---
merchants = [acc("MERCH", i) for i in range(15)]
for m_idx, merchant in enumerate(merchants):
    base_time = datetime(2026, 1, 1, 8, 0)
    n_customers = random.randint(30, 50)
    for c in range(n_customers):
        customer = acc("CUST", m_idx * 100 + c)
        base_price = random.choice([9.99, 19.99, 29.99, 49.99, 99.99])
        n_purchases = random.randint(1, 3)
        for p in range(n_purchases):
            # Regular amounts (low CV) — should NOT trigger smurfing
            day_offset = random.randint(0, 90)
            rows.append([tid(), customer, merchant,
                         round(base_price + random.uniform(-2, 2), 2),
                         ts(base_time, day_offset * 24 + random.randint(0, 16))])
    
    # Merchant occasional refunds (out_deg <= 3)
    for r in range(random.randint(1, 3)):
        rows.append([tid(), merchant, acc("CUST", m_idx * 100 + r),
                     round(random.uniform(10, 100), 2),
                     ts(base_time, random.randint(0, 90) * 24)])

# --- Payroll accounts (1-2 sources → 1 payroll → many employees, regular amounts) ---
for p_idx in range(8):
    payroll = acc("PAYROLL", p_idx)
    base_time = datetime(2026, 1, 1, 8, 0)
    
    # Company deposits
    company = acc("COMPANY", p_idx)
    for month in range(3):
        rows.append([tid(), company, payroll,
                     round(random.uniform(50000, 200000), 2),
                     ts(base_time, month * 720)])
    
    # Regular salary payments (similar amounts → should be excluded)
    n_employees = random.randint(25, 40)
    base_salary = random.uniform(2000, 5000)
    for e in range(n_employees):
        employee = acc("EMP", p_idx * 100 + e)
        for month in range(3):
            # Very regular amounts (low CV → should be detected as payroll, not smurfing)
            rows.append([tid(), payroll, employee,
                         round(base_salary + random.uniform(-50, 50), 2),
                         ts(base_time, month * 720 + 24 + e * 0.1)])

# --- Random P2P transactions (noise) ---
p2p_accounts = [acc("P2P", i) for i in range(200)]
current_count = len(rows)
remaining = 10000 - current_count

for _ in range(remaining):
    sender = random.choice(p2p_accounts)
    receiver = random.choice(p2p_accounts)
    while receiver == sender:
        receiver = random.choice(p2p_accounts)
    
    day = random.randint(0, 180)
    hour = random.randint(0, 23)
    base_time = datetime(2026, 1, 1, 0, 0)
    amt = random.choice([
        random.uniform(5, 50),      # Small
        random.uniform(50, 200),     # Medium
        random.uniform(200, 1000),   # Larger
        random.uniform(1000, 5000),  # Occasional big transfer
    ])
    rows.append([tid(), sender, receiver, round(amt, 2),
                 ts(base_time, day * 24 + hour)])

# ═══════════════════════════════════════════════
# WRITE CSV
# ═══════════════════════════════════════════════

# Shuffle to mix fraud and normal transactions
random.shuffle(rows)

output_file = "test_data_10k.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["transaction_id", "sender_id", "receiver_id", "amount", "timestamp"])
    for i, row in enumerate(rows):
        # Re-assign sequential transaction IDs after shuffle
        row[0] = f"TXN_{i+1:05d}"
        writer.writerow(row)

print(f"\nGenerated {len(rows)} transactions → {output_file}")
print(f"Unique accounts: ~{len(set(r[1] for r in rows) | set(r[2] for r in rows))}")

# Print breakdown
cycle_rows = sum(1 for r in rows if any(x in str(r[1]) + str(r[2]) for x in ["CYC3_", "CYC4_", "CYC5_", "UHCYC_", "SLOWCYC_", "XCYC_"]))
fanin_rows = sum(1 for r in rows if any(x in str(r[1]) + str(r[2]) for x in ["FIHUB_", "FIS_", "FIMHUB_", "FIMS_", "FIVHUB_", "FIVS_"]))
fanout_rows = sum(1 for r in rows if any(x in str(r[1]) + str(r[2]) for x in ["FOHUB_", "FOR_", "FOMHUB_", "FOMR_", "FORPD_", "FORPR_"]))
shell_rows = sum(1 for r in rows if any(x in str(r[1]) + str(r[2]) for x in ["SHELL", "SHSTART", "SHEND", "SHMS", "SHME", "BSHELL"]))
mixed_rows = sum(1 for r in rows if any(x in str(r[1]) + str(r[2]) for x in ["MIX_", "MSHST_", "MSHMID_", "MSHCYC_", "LAYER_", "LAYIN_", "LAYOUT_"]))
normal_rows = len(rows) - cycle_rows - fanin_rows - fanout_rows - shell_rows - mixed_rows

print(f"\nBreakdown:")
print(f"  Cycles:          {cycle_rows}")
print(f"  Fan-in:          {fanin_rows}")
print(f"  Fan-out:         {fanout_rows}")
print(f"  Shell networks:  {shell_rows}")
print(f"  Mixed patterns:  {mixed_rows}")
print(f"  Normal/noise:    {normal_rows}")
