"""
What-If Simulator
Interactive network simulation: remove nodes and see real-time impact on
fraud rings, risk scores, and network connectivity.
"""

import networkx as nx
import pandas as pd
from typing import Dict, List, Set
from collections import defaultdict


class WhatIfSimulator:
    """
    Simulates the effect of removing accounts from the transaction network.
    Returns before/after comparison of all key metrics.
    """

    def __init__(self, G: nx.DiGraph, df: pd.DataFrame,
                 fraud_rings: List[Dict],
                 suspicious_accounts: List[Dict]):
        self.G = G
        self.df = df
        self.fraud_rings = fraud_rings
        self.suspicious_accounts = suspicious_accounts
        self.score_map = {sa["account_id"]: sa for sa in suspicious_accounts}

    def simulate(self, nodes_to_remove: List[str]) -> Dict:
        """
        Simulate removing specified nodes and return impact analysis.
        """
        if not nodes_to_remove:
            return {"error": "No nodes specified for removal"}

        # Validate nodes exist
        valid_nodes = [n for n in nodes_to_remove if n in self.G]
        invalid = [n for n in nodes_to_remove if n not in self.G]

        # Before state
        before = self._compute_state(self.G, "before")

        # Create modified graph
        G_modified = self.G.copy()
        for node in valid_nodes:
            if node in G_modified:
                G_modified.remove_node(node)

        # After state
        after = self._compute_state(G_modified, "after")

        # Ring impact analysis
        ring_impacts = self._analyze_ring_impacts(valid_nodes)

        # Account impact (remaining suspicious accounts)
        account_impacts = self._analyze_account_impacts(valid_nodes)

        # Flow disruption
        flow_impact = self._analyze_flow_disruption(valid_nodes)

        # Cascade analysis: who becomes safer after removal?
        cascade = self._cascade_analysis(valid_nodes)

        return {
            "nodes_removed": valid_nodes,
            "invalid_nodes": invalid,
            "before": before,
            "after": after,
            "delta": self._compute_delta(before, after),
            "ring_impacts": ring_impacts,
            "account_impacts": account_impacts,
            "flow_impact": flow_impact,
            "cascade_effects": cascade,
            "effectiveness_score": self._effectiveness_score(before, after, ring_impacts),
        }

    def _compute_state(self, G: nx.DiGraph, label: str) -> Dict:
        """Compute network state metrics."""
        undirected = G.to_undirected()
        components = list(nx.connected_components(undirected))
        largest_cc = max(components, key=len) if components else set()

        # Degree stats
        degrees = [d for _, d in G.degree()]
        avg_degree = sum(degrees) / max(len(degrees), 1)

        # Flow volume
        total_flow = sum(
            data.get("total_amount", 0)
            for _, _, data in G.edges(data=True)
        )

        return {
            "label": label,
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "components": len(components),
            "largest_component": len(largest_cc),
            "density": round(nx.density(G), 6),
            "avg_degree": round(avg_degree, 2),
            "total_flow": round(total_flow, 2),
            "max_degree": max(degrees) if degrees else 0,
        }

    def _compute_delta(self, before: Dict, after: Dict) -> Dict:
        """Compute the change between before and after states."""
        delta = {}
        for key in ["nodes", "edges", "components", "largest_component",
                     "density", "avg_degree", "total_flow"]:
            b = before.get(key, 0)
            a = after.get(key, 0)
            if isinstance(b, (int, float)) and isinstance(a, (int, float)):
                change = a - b
                pct = ((change / b) * 100) if b != 0 else 0
                delta[key] = {
                    "before": b,
                    "after": a,
                    "change": round(change, 4),
                    "change_pct": round(pct, 1),
                }
        return delta

    def _analyze_ring_impacts(self, removed: List[str]) -> List[Dict]:
        """Analyze how removal affects each fraud ring."""
        removed_set = set(removed)
        impacts = []

        for ring in self.fraud_rings:
            members = ring["member_accounts"]
            removed_members = [m for m in members if m in removed_set]
            surviving = [m for m in members if m not in removed_set]

            if not removed_members:
                impacts.append({
                    "ring_id": ring["ring_id"],
                    "status": "INTACT",
                    "original_size": len(members),
                    "surviving_members": len(surviving),
                    "removed_members": [],
                    "disruption_pct": 0,
                    "risk_change": 0,
                })
                continue

            # Check if ring is broken (no cycle possible in surviving members)
            disruption_pct = (len(removed_members) / len(members)) * 100

            # Check surviving connectivity
            if len(surviving) < 3:
                status = "DESTROYED"
                disruption_pct = 100
            elif len(surviving) < len(members) * 0.5:
                status = "CRITICALLY_DAMAGED"
            else:
                # Check if surviving members still form a connected subgraph
                subG = nx.Graph()
                for u in surviving:
                    for v in surviving:
                        if u != v and (self.G.has_edge(u, v) or self.G.has_edge(v, u)):
                            subG.add_edge(u, v)
                n_comps = nx.number_connected_components(subG) if subG.nodes() else 0
                status = "FRAGMENTED" if n_comps > 1 else "WEAKENED"

            impacts.append({
                "ring_id": ring["ring_id"],
                "status": status,
                "original_size": len(members),
                "surviving_members": len(surviving),
                "removed_members": removed_members,
                "surviving_list": surviving,
                "disruption_pct": round(disruption_pct, 1),
                "original_risk": ring.get("risk_score", 0),
                "pattern_type": ring.get("pattern_type", "unknown"),
            })

        # Sort by disruption impact
        impacts.sort(key=lambda x: -x["disruption_pct"])
        return impacts

    def _analyze_account_impacts(self, removed: List[str]) -> Dict:
        """How removal affects remaining suspicious accounts."""
        removed_set = set(removed)

        removed_accounts = []
        surviving_accounts = []

        for acc in self.suspicious_accounts:
            aid = acc["account_id"]
            if aid in removed_set:
                removed_accounts.append({
                    "account_id": aid,
                    "suspicion_score": acc["suspicion_score"],
                    "status": "REMOVED",
                })
            else:
                # Check if any connections to removed nodes
                connected_to_removed = any(
                    self.G.has_edge(aid, r) or self.G.has_edge(r, aid)
                    for r in removed_set
                )
                surviving_accounts.append({
                    "account_id": aid,
                    "suspicion_score": acc["suspicion_score"],
                    "connected_to_removed": connected_to_removed,
                    "status": "ISOLATED" if connected_to_removed else "UNAFFECTED",
                })

        total_risk_removed = sum(a["suspicion_score"] for a in removed_accounts)
        total_risk_remaining = sum(a["suspicion_score"] for a in surviving_accounts)

        return {
            "removed": removed_accounts,
            "surviving": surviving_accounts,
            "total_risk_removed": round(total_risk_removed, 1),
            "total_risk_remaining": round(total_risk_remaining, 1),
            "risk_reduction_pct": round(
                total_risk_removed / max(total_risk_removed + total_risk_remaining, 1) * 100, 1
            ),
        }

    def _analyze_flow_disruption(self, removed: List[str]) -> Dict:
        """Analyze how much money flow is disrupted."""
        removed_set = set(removed)

        disrupted_flow = 0
        disrupted_txs = 0
        total_flow = 0
        total_txs = 0

        for u, v, data in self.G.edges(data=True):
            amount = data.get("total_amount", 0)
            tx_count = data.get("tx_count", 0)
            total_flow += amount
            total_txs += tx_count

            if u in removed_set or v in removed_set:
                disrupted_flow += amount
                disrupted_txs += tx_count

        return {
            "total_flow": round(total_flow, 2),
            "disrupted_flow": round(disrupted_flow, 2),
            "disruption_pct": round(
                disrupted_flow / max(total_flow, 1) * 100, 1
            ),
            "total_transactions": total_txs,
            "disrupted_transactions": disrupted_txs,
        }

    def _cascade_analysis(self, removed: List[str]) -> List[Dict]:
        """Accounts most impacted by the removal (cascade effect)."""
        removed_set = set(removed)
        cascade = []

        for node in self.G.nodes():
            if node in removed_set:
                continue

            # Count connections to removed nodes
            in_from_removed = sum(
                1 for r in removed_set if self.G.has_edge(r, node)
            )
            out_to_removed = sum(
                1 for r in removed_set if self.G.has_edge(node, r)
            )
            total_connections = in_from_removed + out_to_removed

            if total_connections > 0:
                # Calculate flow impact
                flow_lost = 0
                for r in removed_set:
                    if self.G.has_edge(r, node):
                        flow_lost += self.G[r][node].get("total_amount", 0)
                    if self.G.has_edge(node, r):
                        flow_lost += self.G[node][r].get("total_amount", 0)

                score = self.score_map.get(node, {})
                susp_score = score.get("suspicion_score", 0) if isinstance(score, dict) else 0

                cascade.append({
                    "account_id": node,
                    "connections_lost": total_connections,
                    "incoming_lost": in_from_removed,
                    "outgoing_lost": out_to_removed,
                    "flow_disrupted": round(flow_lost, 2),
                    "suspicion_score": susp_score,
                    "is_suspicious": node in self.score_map,
                })

        cascade.sort(key=lambda x: -x["connections_lost"])
        return cascade[:20]

    def _effectiveness_score(self, before: Dict, after: Dict,
                            ring_impacts: List[Dict]) -> Dict:
        """Calculate an overall effectiveness score for the removal."""
        # Edge reduction
        edge_reduction = 1 - (after["edges"] / max(before["edges"], 1))

        # Ring destruction rate
        destroyed = sum(1 for r in ring_impacts
                       if r["status"] in ("DESTROYED", "CRITICALLY_DAMAGED"))
        ring_rate = destroyed / max(len(ring_impacts), 1)

        # Fragmentation increase
        frag_increase = (after["components"] - before["components"]) / max(before["nodes"], 1)

        # Combined score
        score = (edge_reduction * 30 + ring_rate * 50 + frag_increase * 20) * 100
        score = min(max(score, 0), 100)

        return {
            "overall": round(score, 1),
            "edge_disruption": round(edge_reduction * 100, 1),
            "ring_destruction_rate": round(ring_rate * 100, 1),
            "fragmentation_increase": round(frag_increase * 100, 1),
            "grade": (
                "A+" if score > 90 else
                "A" if score > 80 else
                "B+" if score > 70 else
                "B" if score > 60 else
                "C" if score > 40 else
                "D" if score > 20 else "F"
            ),
        }
