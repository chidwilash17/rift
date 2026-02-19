"""
Quantum Disruption Engine
Identifies critical nodes whose removal maximally fragments fraud rings.
Uses graph theory (vertex cuts, betweenness centrality, articulation points)
combined with quantum partition data to generate optimal disruption strategies.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict


class DisruptionEngine:
    """
    Computes disruption strategies for each fraud ring.
    For each ring, finds the minimum set of nodes whose removal
    maximally fragments the network.
    """

    def __init__(self, G: nx.DiGraph, fraud_rings: List[Dict],
                 suspicious_accounts: List[Dict],
                 quantum_results: Optional[Dict] = None):
        self.G = G
        self.fraud_rings = fraud_rings
        self.suspicious_accounts = suspicious_accounts
        self.quantum_results = quantum_results or {}
        self.score_map = {sa["account_id"]: sa["suspicion_score"]
                         for sa in suspicious_accounts}

    def run(self) -> Dict:
        """Compute disruption analysis for top rings only (capped at 30)."""
        strategies = []
        network_stats = self._compute_network_stats()

        # Only analyze top 30 rings by risk score (rest are low priority)
        sorted_rings = sorted(self.fraud_rings, key=lambda r: r.get("risk_score", 0), reverse=True)
        rings_to_analyze = sorted_rings[:30]

        for ring in rings_to_analyze:
            strategy = self._analyze_ring(ring)
            strategies.append(strategy)

        # Global disruption summary
        all_critical = set()
        total_impact = 0
        for s in strategies:
            for n in s.get("critical_nodes", []):
                all_critical.add(n["account_id"])
            total_impact += s.get("max_disruption_pct", 0)

        avg_impact = total_impact / len(strategies) if strategies else 0

        return {
            "strategies": strategies,
            "network_stats": network_stats,
            "global_summary": {
                "total_rings_analyzed": len(strategies),
                "unique_critical_nodes": len(all_critical),
                "critical_node_list": sorted(all_critical),
                "avg_disruption_potential": round(avg_impact, 1),
                "network_resilience_score": round(100 - avg_impact, 1),
            }
        }

    def _compute_network_stats(self) -> Dict:
        """Compute global network statistics — sampled for speed."""
        undirected = self.G.to_undirected()
        n = len(self.G)

        # Sampled betweenness for speed (k = min(50, n))
        betweenness = nx.betweenness_centrality(self.G, k=min(50, n))
        top_betweenness = sorted(betweenness.items(), key=lambda x: -x[1])[:10]

        # Degree centrality (O(n) — fast)
        degree_cent = nx.degree_centrality(self.G)
        top_degree = sorted(degree_cent.items(), key=lambda x: -x[1])[:10]

        # Skip closeness centrality entirely (O(n^2) — too slow on 3K nodes)
        top_closeness = top_degree[:10]  # Reuse degree as proxy

        # Connected components
        components = list(nx.connected_components(undirected))
        largest_cc = max(components, key=len) if components else set()

        # Articulation points
        try:
            artic_points = list(nx.articulation_points(undirected))
        except Exception:
            artic_points = []

        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "connected_components": len(components),
            "largest_component_size": len(largest_cc),
            "articulation_points": artic_points[:20],
            "articulation_point_count": len(artic_points),
            "density": round(nx.density(self.G), 4),
            "top_betweenness": [
                {"account_id": n, "score": round(s, 4)} for n, s in top_betweenness
            ],
            "top_degree_centrality": [
                {"account_id": n, "score": round(s, 4)} for n, s in top_degree
            ],
            "top_closeness": [
                {"account_id": n, "score": round(s, 4)} for n, s in top_closeness
            ],
        }

    def _analyze_ring(self, ring: Dict) -> Dict:
        """Analyze a single fraud ring for disruption opportunities."""
        ring_id = ring["ring_id"]
        members = ring["member_accounts"]
        n_members = len(members)

        if n_members < 2:
            return {
                "ring_id": ring_id,
                "members": members,
                "critical_nodes": [],
                "max_disruption_pct": 0,
                "resilience_score": 100,
                "removal_simulations": [],
            }

        # Build undirected subgraph of the ring
        subG = nx.Graph()
        for u in members:
            for v in members:
                if u != v:
                    weight = 0
                    if self.G.has_edge(u, v):
                        weight += self.G[u][v].get("total_amount", 1)
                    if self.G.has_edge(v, u):
                        weight += self.G[v][u].get("total_amount", 1)
                    if weight > 0:
                        subG.add_edge(u, v, weight=weight)

        # Add isolated members
        for m in members:
            if m not in subG:
                subG.add_node(m)

        # Original connectivity
        orig_components = nx.number_connected_components(subG)
        orig_edges = subG.number_of_edges()

        # Simulate removal of each node
        removal_sims = []
        for node in members:
            sim = self._simulate_removal(subG, node, members, orig_components, orig_edges)
            removal_sims.append(sim)

        # Sort by impact (highest first)
        removal_sims.sort(key=lambda x: -x["impact_score"])

        # Critical nodes = top nodes that cause maximum fragmentation
        critical_nodes = []
        for sim in removal_sims:
            if sim["impact_score"] > 20:
                critical_nodes.append({
                    "account_id": sim["removed_node"],
                    "impact_score": sim["impact_score"],
                    "fragments_created": sim["new_components"],
                    "edges_severed": sim["edges_lost"],
                    "suspicion_score": self.score_map.get(sim["removed_node"], 0),
                    "is_articulation_point": sim["is_articulation_point"],
                })

        # If no node has >20 impact, take top 3
        if not critical_nodes and removal_sims:
            for sim in removal_sims[:3]:
                critical_nodes.append({
                    "account_id": sim["removed_node"],
                    "impact_score": sim["impact_score"],
                    "fragments_created": sim["new_components"],
                    "edges_severed": sim["edges_lost"],
                    "suspicion_score": self.score_map.get(sim["removed_node"], 0),
                    "is_articulation_point": sim["is_articulation_point"],
                })

        max_disruption = removal_sims[0]["impact_score"] if removal_sims else 0

        # Multi-node removal: find optimal pair
        optimal_pair = self._find_optimal_pair(subG, members, orig_components, orig_edges)

        # Quantum partition overlay
        quantum_overlay = self._get_quantum_overlay(ring_id, members)

        return {
            "ring_id": ring_id,
            "members": members,
            "member_count": n_members,
            "original_edges": orig_edges,
            "original_components": orig_components,
            "critical_nodes": critical_nodes,
            "max_disruption_pct": round(max_disruption, 1),
            "resilience_score": round(100 - max_disruption, 1),
            "removal_simulations": removal_sims,
            "optimal_pair_removal": optimal_pair,
            "quantum_overlay": quantum_overlay,
            "risk_score": ring.get("risk_score", 0),
        }

    def _simulate_removal(self, subG: nx.Graph, node: str,
                          members: List[str], orig_components: int,
                          orig_edges: int) -> Dict:
        """Simulate removing a single node and measure impact."""
        test_G = subG.copy()
        edges_incident = list(test_G.edges(node))
        edge_count = len(edges_incident)

        test_G.remove_node(node)
        new_components = nx.number_connected_components(test_G)
        remaining_edges = test_G.number_of_edges()

        # Component sizes after removal
        comp_sizes = sorted(
            [len(c) for c in nx.connected_components(test_G)],
            reverse=True
        )

        # Impact score: combination of fragmentation + edge loss + centrality
        fragmentation = ((new_components - orig_components) / max(len(members) - 1, 1)) * 50
        edge_loss = (edge_count / max(orig_edges, 1)) * 30
        degree_impact = (subG.degree(node) / max(len(members) - 1, 1)) * 20
        impact = min(fragmentation + edge_loss + degree_impact, 100)

        # Check if it's an articulation point
        is_artic = new_components > orig_components

        return {
            "removed_node": node,
            "edges_lost": edge_count,
            "new_components": new_components,
            "component_sizes": comp_sizes,
            "impact_score": round(impact, 1),
            "is_articulation_point": is_artic,
            "suspicion_score": self.score_map.get(node, 0),
        }

    def _find_optimal_pair(self, subG: nx.Graph, members: List[str],
                           orig_components: int, orig_edges: int) -> Dict:
        """Find the optimal pair of nodes to remove for maximum disruption."""
        best_pair = None
        best_impact = 0
        best_info = {}

        # Only try pairs for small rings (avoid O(n^2) for large)
        if len(members) > 10:
            # Use heuristic: top 3 by degree
            degrees = sorted(
                [(n, subG.degree(n)) for n in members if n in subG],
                key=lambda x: -x[1]
            )
            candidates = [d[0] for d in degrees[:3]]
        else:
            candidates = members

        for i, n1 in enumerate(candidates):
            for n2 in candidates[i + 1:]:
                test_G = subG.copy()
                if n1 in test_G:
                    test_G.remove_node(n1)
                if n2 in test_G:
                    test_G.remove_node(n2)

                new_comps = nx.number_connected_components(test_G)
                remaining = test_G.number_of_edges()
                frag = ((new_comps - orig_components) / max(len(members) - 2, 1)) * 60
                edge_loss = ((orig_edges - remaining) / max(orig_edges, 1)) * 40
                impact = min(frag + edge_loss, 100)

                if impact > best_impact:
                    best_impact = impact
                    best_pair = (n1, n2)
                    best_info = {
                        "new_components": new_comps,
                        "edges_remaining": remaining,
                    }

        if best_pair:
            return {
                "nodes": list(best_pair),
                "combined_impact": round(best_impact, 1),
                "new_components": best_info.get("new_components", 0),
                "edges_remaining": best_info.get("edges_remaining", 0),
            }
        return {"nodes": [], "combined_impact": 0}

    def _get_quantum_overlay(self, ring_id: str, members: List[str]) -> Dict:
        """Overlay quantum partition data on disruption analysis."""
        qr_list = self.quantum_results.get("quantum_results", [])
        for qr in qr_list:
            if qr.get("ring_id") == ring_id:
                susp_set = qr.get("suspicious_set", [])
                partition_score = qr.get("partition_score", 0)
                return {
                    "available": True,
                    "suspicious_partition": susp_set,
                    "clean_partition": [m for m in members if m not in susp_set],
                    "partition_score": partition_score,
                    "quantum_agreement": self._quantum_agreement(susp_set, members),
                }
        return {"available": False}

    def _quantum_agreement(self, susp_set: List[str], members: List[str]) -> float:
        """How much quantum partition agrees with classical risk scores."""
        if not susp_set:
            return 0.0
        quantum_flagged = set(susp_set)
        classical_flagged = {m for m in members if self.score_map.get(m, 0) > 50}
        if not classical_flagged:
            return 50.0
        overlap = quantum_flagged & classical_flagged
        return round(len(overlap) / max(len(quantum_flagged | classical_flagged), 1) * 100, 1)
