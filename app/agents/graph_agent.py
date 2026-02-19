"""
Agent 1: Graph Detective Agent — FAST edition
Detects money muling patterns using graph theory:
  1. Circular Fund Routing (cycles of length 3-5)
  2. Smurfing Patterns (fan-in/fan-out with temporal analysis)
  3. Layered Shell Networks (chains through low-activity intermediaries)

Performance: Scoped cycle search, capped shell BFS, early exits.
"""

import networkx as nx
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Set, Tuple
import itertools
import time


class GraphAgent:
    """Agent responsible for structural graph-based fraud detection."""
    
    def __init__(self, G: nx.DiGraph, df: pd.DataFrame):
        self.G = G
        self.df = df
        self.rings = []          # Detected fraud rings
        self.suspicious = {}     # account_id -> {patterns, ring_ids, scores}
        self._ring_counter = 0
    
    def _next_ring_id(self) -> str:
        self._ring_counter += 1
        return f"RING_{self._ring_counter:03d}"
    
    def run(self) -> Dict:
        """Execute all detection algorithms and return results."""
        self.detect_cycles()
        self.detect_smurfing()
        self.detect_shell_networks()
        
        return {
            "rings": self.rings,
            "suspicious_accounts": self.suspicious,
            "agent": "graph_detective"
        }
    
    # ─────────────────────────────────────────────
    # Pattern 1: Circular Fund Routing (Cycles)
    # ─────────────────────────────────────────────
    MAX_CYCLES = 500          # Hard cap on cycles to process
    CYCLE_TIME_LIMIT = 6.0    # Seconds before aborting cycle search

    def detect_cycles(self):
        """Detect cycles of length 3-5, time-bounded for large graphs."""
        found_cycles: set = set()
        deadline = time.time() + self.CYCLE_TIME_LIMIT

        # Only search within Strongly Connected Components (huge speed win)
        sccs = [s for s in nx.strongly_connected_components(self.G) if len(s) >= 3]

        for scc_nodes in sccs:
            if time.time() > deadline or len(found_cycles) >= self.MAX_CYCLES:
                break
            subG = self.G.subgraph(scc_nodes)
            try:
                for cycle in nx.simple_cycles(subG, length_bound=5):
                    if time.time() > deadline or len(found_cycles) >= self.MAX_CYCLES:
                        break
                    if len(cycle) < 3:
                        continue
                    canonical = self._canonical_cycle(cycle)
                    cycle_key = tuple(canonical)
                    if cycle_key in found_cycles:
                        continue
                    found_cycles.add(cycle_key)

                    risk_score = self._cycle_risk_score(cycle)
                    ring_id = self._next_ring_id()
                    ring = {
                        "ring_id": ring_id,
                        "member_accounts": list(cycle),
                        "pattern_type": "cycle",
                        "cycle_length": len(cycle),
                        "risk_score": round(risk_score, 2)
                    }
                    self.rings.append(ring)

                    for account in cycle:
                        if account not in self.suspicious:
                            self.suspicious[account] = {
                                "patterns": [], "ring_ids": [], "graph_score": 0
                            }
                        self.suspicious[account]["patterns"].append(f"cycle_length_{len(cycle)}")
                        self.suspicious[account]["ring_ids"].append(ring_id)
                        self.suspicious[account]["graph_score"] = max(
                            self.suspicious[account]["graph_score"], risk_score)
            except Exception:
                # Fallback on error — just continue to next SCC
                continue
    
    def _dfs_cycles(self) -> List[List[str]]:
        """Fallback DFS-based cycle detection for cycles of length 3-5."""
        cycles = []
        nodes = list(self.G.nodes())
        
        for start in nodes:
            visited = {start}
            stack = [(start, [start])]
            
            while stack:
                node, path = stack.pop()
                
                if len(path) > 5:
                    continue
                
                for neighbor in self.G.successors(node):
                    if neighbor == start and len(path) >= 3:
                        cycles.append(list(path))
                    elif neighbor not in visited and len(path) < 5:
                        visited.add(neighbor)
                        stack.append((neighbor, path + [neighbor]))
            
        return cycles
    
    def _canonical_cycle(self, cycle: List[str]) -> List[str]:
        """Normalize cycle to canonical form (start from min element)."""
        if not cycle:
            return cycle
        min_idx = cycle.index(min(cycle))
        return cycle[min_idx:] + cycle[:min_idx]
    
    def _cycle_risk_score(self, cycle: List[str]) -> float:
        """Score a cycle based on amounts, velocity, and structure."""
        score = 50.0  # Base score for being in a cycle
        
        total_amount = 0
        tx_count = 0
        timestamps = []
        
        for i in range(len(cycle)):
            sender = cycle[i]
            receiver = cycle[(i + 1) % len(cycle)]
            if self.G.has_edge(sender, receiver):
                edge_data = self.G[sender][receiver]
                total_amount += edge_data.get("total_amount", 0)
                tx_count += edge_data.get("tx_count", 0)
                for tx in edge_data.get("transactions", []):
                    try:
                        timestamps.append(pd.Timestamp(tx["timestamp"]))
                    except (ValueError, KeyError):
                        pass
        
        # Higher amounts → higher risk
        if total_amount > 10000:
            score += 15
        elif total_amount > 5000:
            score += 10
        elif total_amount > 1000:
            score += 5
        
        # Fast cycling (all within 72h) → higher risk
        if timestamps:
            timestamps.sort()
            time_span = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
            if time_span <= 24:
                score += 20
            elif time_span <= 72:
                score += 15
            elif time_span <= 168:
                score += 10
        
        # Shorter cycles are more suspicious
        if len(cycle) == 3:
            score += 5
        
        return min(score, 100.0)
    
    # ─────────────────────────────────────────────
    # Pattern 2: Smurfing (Fan-in / Fan-out)
    # ─────────────────────────────────────────────
    def detect_smurfing(self):
        """Detect fan-in and fan-out smurfing patterns with temporal analysis."""
        
        # --- Fan-in detection ---
        for node in self.G.nodes():
            in_edges = list(self.G.in_edges(node, data=True))
            
            if len(in_edges) < 10:
                continue
            
            # Check if this is a legitimate high-volume account (merchant/payroll)
            if self._is_likely_merchant(node):
                continue
            
            # Temporal clustering: check for bursts within 72h windows
            all_timestamps = []
            senders = set()
            total_in_amount = 0
            
            for sender, _, data in in_edges:
                senders.add(sender)
                total_in_amount += data.get("total_amount", 0)
                for tx in data.get("transactions", []):
                    try:
                        all_timestamps.append((pd.Timestamp(tx["timestamp"]), sender, tx["amount"]))
                    except (ValueError, KeyError):
                        pass
            
            # Find 72h windows with high activity
            temporal_clusters = self._find_temporal_clusters(all_timestamps, hours=72)
            
            if len(senders) >= 10:
                risk_score = self._smurfing_risk_score(
                    node, senders, total_in_amount, temporal_clusters, "fan_in"
                )
                
                # Get fan-out from this aggregator
                out_receivers = set(self.G.successors(node))
                member_accounts = list(senders | {node} | out_receivers)
                
                ring_id = self._next_ring_id()
                ring = {
                    "ring_id": ring_id,
                    "member_accounts": member_accounts,
                    "pattern_type": "fan_in",
                    "aggregator": node,
                    "sender_count": len(senders),
                    "risk_score": round(risk_score, 2)
                }
                self.rings.append(ring)
                
                for account in member_accounts:
                    if account not in self.suspicious:
                        self.suspicious[account] = {
                            "patterns": [],
                            "ring_ids": [],
                            "graph_score": 0
                        }
                    self.suspicious[account]["patterns"].append("smurfing_fan_in")
                    self.suspicious[account]["ring_ids"].append(ring_id)
                    self.suspicious[account]["graph_score"] = max(
                        self.suspicious[account]["graph_score"], risk_score
                    )
        
        # --- Fan-out detection ---
        for node in self.G.nodes():
            out_edges = list(self.G.out_edges(node, data=True))
            
            if len(out_edges) < 10:
                continue
            
            if self._is_likely_payroll(node):
                continue
            
            receivers = set()
            total_out_amount = 0
            all_timestamps = []
            
            for _, receiver, data in out_edges:
                receivers.add(receiver)
                total_out_amount += data.get("total_amount", 0)
                for tx in data.get("transactions", []):
                    try:
                        all_timestamps.append((pd.Timestamp(tx["timestamp"]), receiver, tx["amount"]))
                    except (ValueError, KeyError):
                        pass
            
            temporal_clusters = self._find_temporal_clusters(all_timestamps, hours=72)
            
            if len(receivers) >= 10:
                risk_score = self._smurfing_risk_score(
                    node, receivers, total_out_amount, temporal_clusters, "fan_out"
                )
                
                in_senders = set(self.G.predecessors(node))
                member_accounts = list(in_senders | {node} | receivers)
                
                ring_id = self._next_ring_id()
                ring = {
                    "ring_id": ring_id,
                    "member_accounts": member_accounts,
                    "pattern_type": "fan_out",
                    "disperser": node,
                    "receiver_count": len(receivers),
                    "risk_score": round(risk_score, 2)
                }
                self.rings.append(ring)
                
                for account in member_accounts:
                    if account not in self.suspicious:
                        self.suspicious[account] = {
                            "patterns": [],
                            "ring_ids": [],
                            "graph_score": 0
                        }
                    self.suspicious[account]["patterns"].append("smurfing_fan_out")
                    self.suspicious[account]["ring_ids"].append(ring_id)
                    self.suspicious[account]["graph_score"] = max(
                        self.suspicious[account]["graph_score"], risk_score
                    )
    
    def _is_likely_merchant(self, node: str) -> bool:
        """
        Heuristic to detect legitimate high-volume merchants.
        Merchants: receive from many, send to few; stable amounts; regular timing.
        """
        data = self.G.nodes[node]
        in_deg = data.get("in_degree", 0)
        out_deg = data.get("out_degree", 0)
        
        if in_deg == 0:
            return False
        
        # Merchants receive from many but send to very few (refunds only)
        if out_deg <= 3 and in_deg > 20:
            return True
        
        # Check amount regularity: merchants have similar transaction amounts
        in_amounts = []
        for pred in self.G.predecessors(node):
            edge = self.G[pred][node]
            for tx in edge.get("transactions", []):
                in_amounts.append(tx["amount"])
        
        if len(in_amounts) > 10:
            cv = np.std(in_amounts) / (np.mean(in_amounts) + 1e-9)
            # Low coefficient of variation → regular payments → likely merchant
            if cv < 0.3:
                return True
        
        return False
    
    def _is_likely_payroll(self, node: str) -> bool:
        """
        Heuristic to detect legitimate payroll accounts.
        Payroll: sends to many, receives from few; regular amounts; monthly timing.
        """
        data = self.G.nodes[node]
        in_deg = data.get("in_degree", 0)
        out_deg = data.get("out_degree", 0)
        
        if out_deg == 0:
            return False
        
        # Payroll: receives from 1–2 accounts (company), sends to many
        if in_deg <= 2 and out_deg > 20:
            # Check if amounts are regular
            out_amounts = []
            for succ in self.G.successors(node):
                edge = self.G[node][succ]
                for tx in edge.get("transactions", []):
                    out_amounts.append(tx["amount"])
            
            if len(out_amounts) > 10:
                cv = np.std(out_amounts) / (np.mean(out_amounts) + 1e-9) 
                if cv < 0.4:
                    return True
        
        return False
    
    def _find_temporal_clusters(self, timestamps_data: List, hours: int = 72) -> List:
        """Find clusters of transactions within a time window."""
        if not timestamps_data:
            return []
        
        timestamps_data.sort(key=lambda x: x[0])
        clusters = []
        current_cluster = [timestamps_data[0]]
        
        for item in timestamps_data[1:]:
            if (item[0] - current_cluster[0][0]).total_seconds() <= hours * 3600:
                current_cluster.append(item)
            else:
                if len(current_cluster) >= 5:
                    clusters.append(current_cluster)
                current_cluster = [item]
        
        if len(current_cluster) >= 5:
            clusters.append(current_cluster)
        
        return clusters
    
    def _smurfing_risk_score(self, hub: str, connected: set, 
                              total_amount: float, clusters: list, 
                              pattern: str) -> float:
        """Score smurfing patterns based on multiple factors."""
        score = 40.0  # Base score
        
        # More connections → more suspicious
        n = len(connected)
        if n >= 20:
            score += 20
        elif n >= 15:
            score += 15
        elif n >= 10:
            score += 10
        
        # Temporal clustering (bursts within 72h)
        if clusters:
            max_cluster_size = max(len(c) for c in clusters)
            if max_cluster_size >= 15:
                score += 20
            elif max_cluster_size >= 10:
                score += 15
            elif max_cluster_size >= 5:
                score += 10
        
        # High velocity (lots of money moved)
        if total_amount > 50000:
            score += 15
        elif total_amount > 20000:
            score += 10
        elif total_amount > 10000:
            score += 5
        
        return min(score, 100.0)
    
    # ─────────────────────────────────────────────
    # Pattern 3: Layered Shell Networks
    # ─────────────────────────────────────────────
    MAX_SHELL_RINGS = 100       # Cap on shell rings to avoid explosion
    SHELL_TIME_LIMIT = 3.0      # Seconds

    def detect_shell_networks(self):
        """
        Detect chains of 3+ hops through shell accounts
        (intermediaries with only 2-3 total transactions).
        Time-bounded and capped.
        """
        shell_accounts = set()
        for node in self.G.nodes():
            total_tx = self.G.nodes[node].get("tx_count_total", 0)
            if 2 <= total_tx <= 3:
                shell_accounts.add(node)

        if not shell_accounts:
            return

        visited_chains: set = set()
        deadline = time.time() + self.SHELL_TIME_LIMIT
        shell_ring_count = 0

        for shell in shell_accounts:
            if time.time() > deadline or shell_ring_count >= self.MAX_SHELL_RINGS:
                break

            chains = self._find_shell_chains(shell, shell_accounts)

            for chain in chains:
                if shell_ring_count >= self.MAX_SHELL_RINGS:
                    break
                if len(chain) < 3:
                    continue

                chain_key = tuple(sorted(chain))
                if chain_key in visited_chains:
                    continue
                visited_chains.add(chain_key)

                shells_in_chain = [n for n in chain if n in shell_accounts]
                if len(shells_in_chain) < 1:
                    continue

                risk_score = self._shell_risk_score(chain, shells_in_chain)
                ring_id = self._next_ring_id()
                ring = {
                    "ring_id": ring_id,
                    "member_accounts": chain,
                    "pattern_type": "shell_network",
                    "chain_length": len(chain),
                    "shell_accounts": shells_in_chain,
                    "risk_score": round(risk_score, 2)
                }
                self.rings.append(ring)
                shell_ring_count += 1

                for account in chain:
                    if account not in self.suspicious:
                        self.suspicious[account] = {
                            "patterns": [], "ring_ids": [], "graph_score": 0
                        }
                    if account in shell_accounts:
                        self.suspicious[account]["patterns"].append("shell_intermediary")
                    else:
                        self.suspicious[account]["patterns"].append("shell_network_endpoint")
                    self.suspicious[account]["ring_ids"].append(ring_id)
                    self.suspicious[account]["graph_score"] = max(
                        self.suspicious[account]["graph_score"], risk_score)
    
    def _find_shell_chains(self, start: str, shell_accounts: set, max_depth: int = 6) -> List[List[str]]:
        """Find chains passing through shell accounts via BFS."""
        chains = []
        queue = [(start, [start])]
        
        while queue:
            node, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for successor in self.G.successors(node):
                if successor in path:
                    continue
                
                new_path = path + [successor]
                
                # If chain has 3+ hops, save it
                if len(new_path) >= 3:
                    # Check if intermediaries are shell accounts
                    intermediaries = new_path[1:-1]
                    shell_intermediaries = [n for n in intermediaries if n in shell_accounts]
                    if shell_intermediaries:
                        chains.append(new_path)
                
                # Continue searching through shell accounts
                if successor in shell_accounts and len(new_path) < max_depth:
                    queue.append((successor, new_path))
        
        return chains
    
    def _shell_risk_score(self, chain: List[str], shells: List[str]) -> float:
        """Score shell network chains."""
        score = 35.0  # Base
        
        # More shell intermediaries → more suspicious
        score += len(shells) * 10
        
        # Longer chains → more suspicious
        if len(chain) >= 5:
            score += 15
        elif len(chain) >= 4:
            score += 10
        elif len(chain) >= 3:
            score += 5
        
        # Check if amounts are similar through the chain (pass-through)
        amounts = []
        for i in range(len(chain) - 1):
            if self.G.has_edge(chain[i], chain[i+1]):
                amounts.append(self.G[chain[i]][chain[i+1]].get("total_amount", 0))
        
        if len(amounts) >= 2:
            mean_amt = np.mean(amounts)
            if mean_amt > 0:
                cv = np.std(amounts) / mean_amt
                # Similar amounts through chain → likely layering
                if cv < 0.2:
                    score += 15
                elif cv < 0.4:
                    score += 10
        
        return min(score, 100.0)
