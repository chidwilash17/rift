"""
Agent 4: Aggregator Agent
Merges outputs from Graph Agent, ML Agent, and Quantum Agent.
Produces final JSON output matching the required specification exactly.
Implements weighted ensemble scoring and conflict resolution.
"""

import time
from typing import Dict, List
from collections import defaultdict


class AggregatorAgent:
    """
    Consensus aggregator: merges all agent results into unified output.
    
    Scoring formula:
        final_score = w1 * graph_score + w2 * ml_score + w3 * quantum_score
    
    Weights: Graph=0.40, ML=0.35, Quantum=0.25
    """
    
    WEIGHT_GRAPH = 0.40
    WEIGHT_ML = 0.35
    WEIGHT_QUANTUM = 0.25
    
    def __init__(self, graph_results: Dict, ml_results: Dict, quantum_results: Dict,
                 total_accounts: int, processing_start_time: float):
        self.graph_results = graph_results
        self.ml_results = ml_results
        self.quantum_results = quantum_results
        self.total_accounts = total_accounts
        self.start_time = processing_start_time
    
    def run(self) -> Dict:
        """Produce final output in exact required JSON format."""
        
        # Collect all data per account
        account_data = defaultdict(lambda: {
            "graph_score": 0,
            "ml_score": 0,
            "quantum_score": 0,
            "patterns": [],
            "ring_ids": []
        })
        
        # ── Merge Graph Agent results ──
        graph_suspicious = self.graph_results.get("suspicious_accounts", {})
        for acc_id, data in graph_suspicious.items():
            account_data[acc_id]["graph_score"] = data.get("graph_score", 0)
            account_data[acc_id]["patterns"].extend(data.get("patterns", []))
            account_data[acc_id]["ring_ids"].extend(data.get("ring_ids", []))
        
        # ── Merge ML Agent results ──
        ml_scores = self.ml_results.get("ml_scores", {})
        for acc_id, score in ml_scores.items():
            account_data[acc_id]["ml_score"] = score
        
        # ── Merge Quantum Agent results ──
        quantum_scores = self.quantum_results.get("quantum_scores", {})
        for acc_id, score in quantum_scores.items():
            account_data[acc_id]["quantum_score"] = score
        
        # ── Compute final suspicion scores ──
        suspicious_accounts = []
        for acc_id, data in account_data.items():
            g = data["graph_score"]
            m = data["ml_score"]
            q = data["quantum_score"]
            
            # If quantum didn't analyze this account, redistribute weight
            if q == 0 and (g > 0 or m > 30):
                final_score = (self.WEIGHT_GRAPH + self.WEIGHT_QUANTUM / 2) * g + \
                              (self.WEIGHT_ML + self.WEIGHT_QUANTUM / 2) * m
            else:
                final_score = self.WEIGHT_GRAPH * g + self.WEIGHT_ML * m + self.WEIGHT_QUANTUM * q
            
            # Only flag accounts above threshold
            if final_score < 25:
                continue
            
            # Deduplicate patterns
            patterns = list(dict.fromkeys(data["patterns"]))
            ring_ids = list(dict.fromkeys(data["ring_ids"]))
            
            # Add ML-derived patterns
            if m > 70:
                patterns.append("high_ml_anomaly")
            if m > 50 and "high_velocity" not in patterns:
                features = self.ml_results.get("features", {}).get(acc_id, {})
                if features.get("tx_per_hour", 0) > 1:
                    patterns.append("high_velocity")
                if features.get("burstiness", 0) > 2:
                    patterns.append("temporal_burst")
                if features.get("passthrough_ratio", 0) > 0.8:
                    patterns.append("pass_through")
            
            # If no patterns detected but score is high from ML, add generic
            if not patterns and final_score > 30:
                patterns.append("ml_anomaly_detected")
            
            # Assign to first ring or create standalone
            primary_ring = ring_ids[0] if ring_ids else None
            
            suspicious_accounts.append({
                "account_id": acc_id,
                "suspicion_score": round(min(final_score, 100), 1),
                "detected_patterns": patterns,
                "ring_id": primary_ring if primary_ring else "STANDALONE",
                "component_scores": {
                    "graph": round(g, 1),
                    "ml": round(m, 1),
                    "quantum": round(q, 1)
                }
            })
        
        # Sort by suspicion_score descending
        suspicious_accounts.sort(key=lambda x: x["suspicion_score"], reverse=True)
        
        # ── Build fraud rings ──
        fraud_rings = []
        for ring in self.graph_results.get("rings", []):
            ring_id = ring["ring_id"]
            members = ring["member_accounts"]
            
            # Re-score ring using aggregated member scores
            member_scores = []
            for acc in members:
                for sa in suspicious_accounts:
                    if sa["account_id"] == acc:
                        member_scores.append(sa["suspicion_score"])
                        break
            
            avg_member_score = sum(member_scores) / len(member_scores) if member_scores else ring["risk_score"]
            
            fraud_rings.append({
                "ring_id": ring_id,
                "member_accounts": members,
                "pattern_type": ring["pattern_type"],
                "risk_score": round(min(avg_member_score, 100), 1)
            })
        
        # Sort rings by risk_score descending
        fraud_rings.sort(key=lambda x: x["risk_score"], reverse=True)
        
        # ── Build summary ──
        processing_time = round(time.time() - self.start_time, 2)
        
        summary = {
            "total_accounts_analyzed": self.total_accounts,
            "suspicious_accounts_flagged": len(suspicious_accounts),
            "fraud_rings_detected": len(fraud_rings),
            "processing_time_seconds": processing_time,
            "agents_used": ["graph_detective", "ml_scorer", "quantum_optimizer"],
            "scoring_weights": {
                "graph": self.WEIGHT_GRAPH,
                "ml": self.WEIGHT_ML,
                "quantum": self.WEIGHT_QUANTUM
            }
        }
        
        # ── Build quantum metadata for UI ──
        quantum_metadata = {}
        if self.quantum_results.get("quantum_available"):
            qr = self.quantum_results.get("quantum_results", [])
            quantum_metadata = {
                "available": True,
                "circuits_executed": len(qr),
                "results": qr
            }
        else:
            quantum_metadata = {
                "available": False,
                "message": self.quantum_results.get("message", "Quantum module not available")
            }
        
        return {
            "suspicious_accounts": suspicious_accounts,
            "fraud_rings": fraud_rings,
            "summary": summary,
            "quantum_analysis": quantum_metadata
        }
