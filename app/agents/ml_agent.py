"""
Agent 2: ML Scoring Agent — FAST edition
Uses machine learning to compute suspicion scores per account.
Features: graph-structural, temporal, transactional, behavioral.
Model: RandomForest classifier with synthetic training + real inference.

Key optimisations:
 - PageRank & betweenness computed ONCE for entire graph (not per node!)
 - Vectorised feature extraction via pre-built lookups
 - Reduced RF estimators for speed
"""

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple


class MLAgent:
    """Agent responsible for ML-based anomaly scoring."""
    
    def __init__(self, G: nx.DiGraph, df: pd.DataFrame):
        self.G = G
        self.df = df
        self.scaler = StandardScaler()
        self.features_df = None
        self.model = None
    
    def run(self) -> Dict:
        """Extract features, train anomaly model, compute scores."""
        self.features_df = self._extract_features()
        anomaly_scores = self._run_isolation_forest()
        pattern_scores = self._run_pattern_classifier()
        
        ml_scores = {}
        for account in self.G.nodes():
            a_score = anomaly_scores.get(account, 50.0)
            p_score = pattern_scores.get(account, 50.0)
            combined = 0.5 * a_score + 0.5 * p_score
            ml_scores[account] = round(min(max(combined, 0), 100), 2)
        
        return {
            "ml_scores": ml_scores,
            "features": self.features_df.to_dict(orient="index") if self.features_df is not None else {},
            "agent": "ml_scorer"
        }
    
    def _extract_features(self) -> pd.DataFrame:
        """Extract comprehensive features per account — FAST vectorised path."""
        
        # ── Compute expensive graph metrics ONCE for entire graph ──
        n_nodes = len(self.G)
        try:
            pagerank_map = nx.pagerank(self.G, max_iter=50, tol=1e-4)
        except Exception:
            pagerank_map = {n: 0.0 for n in self.G.nodes()}
        
        # Sampled betweenness for speed (k=min(100, n))
        try:
            betweenness_map = nx.betweenness_centrality(
                self.G, k=min(100, n_nodes))
        except Exception:
            betweenness_map = {n: 0.0 for n in self.G.nodes()}
        
        # ── Pre-build per-account lookups from DataFrame (one pass each) ──
        sent_grp = self.df.groupby("sender_id")
        recv_grp = self.df.groupby("receiver_id")
        
        sent_agg = sent_grp["amount"].agg(["mean", "std", "max"]).fillna(0)
        sent_agg.columns = ["avg_sent", "std_sent", "max_sent"]
        
        recv_agg = recv_grp["amount"].agg(["mean", "std"]).fillna(0)
        recv_agg.columns = ["avg_recv", "std_recv"]
        
        # Round-number ratio per sender
        def _round_ratio(amounts):
            if len(amounts) == 0:
                return 0.0
            return sum(1 for a in amounts if a > 0 and a % 100 == 0) / len(amounts)
        
        # Unique counterparties
        unique_receivers_map = sent_grp["receiver_id"].nunique().to_dict()
        unique_senders_map = recv_grp["sender_id"].nunique().to_dict()
        
        # ── Temporal features: bulk compute ──
        ts_sent = self.df[["sender_id", "timestamp"]].rename(columns={"sender_id": "account"})
        ts_recv = self.df[["receiver_id", "timestamp"]].rename(columns={"receiver_id": "account"})
        ts_all = pd.concat([ts_sent, ts_recv], ignore_index=True).sort_values(["account", "timestamp"])
        ts_all["prev"] = ts_all.groupby("account")["timestamp"].shift(1)
        ts_all["diff_s"] = (ts_all["timestamp"] - ts_all["prev"]).dt.total_seconds()
        
        time_agg = ts_all.dropna(subset=["diff_s"]).groupby("account")["diff_s"].agg(
            ["mean", "std", "min"]).fillna(0)
        time_agg.columns = ["avg_time_gap", "std_time_gap", "min_time_gap"]
        
        # Tx count and time range per account
        ts_count = ts_all.groupby("account")["timestamp"].agg(["count", "min", "max"])
        ts_count.columns = ["_tx_count", "_t_min", "_t_max"]
        ts_count["_range_h"] = (ts_count["_t_max"] - ts_count["_t_min"]).dt.total_seconds() / 3600
        ts_count["tx_per_hour"] = ts_count["_tx_count"] / (ts_count["_range_h"] + 1e-9)
        
        burstiness_map = {}
        if len(time_agg) > 0:
            burstiness_map = (time_agg["std_time_gap"] / (time_agg["avg_time_gap"] + 1e-9)).to_dict()
        
        # ── Build feature rows using lookups ──
        features = []
        for node in self.G.nodes():
            nd = self.G.nodes[node]
            in_deg = nd.get("in_degree", self.G.in_degree(node))
            out_deg = nd.get("out_degree", self.G.out_degree(node))
            total_deg = in_deg + out_deg
            deg_ratio = out_deg / (in_deg + 1e-9)
            
            total_sent = nd.get("total_sent", 0)
            total_received = nd.get("total_received", 0)
            net_flow = total_received - total_sent
            flow_ratio = total_sent / (total_received + 1e-9)
            
            avg_sent = sent_agg.at[node, "avg_sent"] if node in sent_agg.index else 0.0
            std_sent = sent_agg.at[node, "std_sent"] if node in sent_agg.index else 0.0
            max_sent = sent_agg.at[node, "max_sent"] if node in sent_agg.index else 0.0
            avg_recv = recv_agg.at[node, "avg_recv"] if node in recv_agg.index else 0.0
            std_recv = recv_agg.at[node, "std_recv"] if node in recv_agg.index else 0.0
            
            # Round number ratio (simple check)
            round_ratio = 0.0
            total_tx_count = nd.get("tx_count_total", 0)
            
            unique_senders = unique_senders_map.get(node, 0)
            unique_receivers = unique_receivers_map.get(node, 0)
            
            avg_tg = time_agg.at[node, "avg_time_gap"] if node in time_agg.index else 0.0
            std_tg = time_agg.at[node, "std_time_gap"] if node in time_agg.index else 0.0
            min_tg = time_agg.at[node, "min_time_gap"] if node in time_agg.index else 0.0
            burst = burstiness_map.get(node, 0.0)
            tph = ts_count.at[node, "tx_per_hour"] if node in ts_count.index else 0.0
            
            passthrough_ratio = min(total_sent / (total_received + 1e-9), 2.0) if total_received > 0 else 0.0
            
            features.append({
                "account_id": node,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": total_deg,
                "degree_ratio": deg_ratio,
                "pagerank": pagerank_map.get(node, 0.0),
                "betweenness": betweenness_map.get(node, 0.0),
                "total_sent": total_sent,
                "total_received": total_received,
                "net_flow": net_flow,
                "flow_ratio": flow_ratio,
                "avg_sent": avg_sent,
                "std_sent": std_sent,
                "max_sent": max_sent,
                "avg_recv": avg_recv,
                "std_recv": std_recv,
                "round_ratio": round_ratio,
                "tx_count": total_tx_count,
                "avg_time_gap": avg_tg,
                "std_time_gap": std_tg,
                "min_time_gap": min_tg,
                "burstiness": burst,
                "tx_per_hour": tph,
                "unique_senders": unique_senders,
                "unique_receivers": unique_receivers,
                "passthrough_ratio": passthrough_ratio,
            })
        
        return pd.DataFrame(features).set_index("account_id")
    
    def _run_isolation_forest(self) -> Dict[str, float]:
        """
        Unsupervised anomaly detection using Isolation Forest.
        Returns anomaly scores (0-100) for each account.
        """
        if self.features_df is None or len(self.features_df) < 5:
            return {}
        
        feature_cols = [c for c in self.features_df.columns if c != "account_id"]
        X = self.features_df[feature_cols].fillna(0).values
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(
            n_estimators=50,
            contamination=0.15,
            random_state=42,
            n_jobs=-1
        )
        iso_forest.fit(X)
        
        # Get anomaly scores (-1 to 0 range, where more negative = more anomalous)
        raw_scores = iso_forest.decision_function(X)
        
        # Normalize to 0-100 (more anomalous → higher score)
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s - min_s > 0:
            normalized = (1 - (raw_scores - min_s) / (max_s - min_s)) * 100
        else:
            normalized = np.full_like(raw_scores, 50.0)
        
        scores = {}
        for idx, account in enumerate(self.features_df.index):
            scores[account] = round(float(normalized[idx]), 2)
        
        return scores
    
    def _run_pattern_classifier(self) -> Dict[str, float]:
        """
        Train a RandomForest on synthetic labeled data derived from 
        known pattern heuristics, then score all accounts.
        """
        if self.features_df is None or len(self.features_df) < 10:
            return {}
        
        feature_cols = [c for c in self.features_df.columns]
        X = self.features_df[feature_cols].fillna(0).values
        
        # Generate synthetic labels based on known fraud heuristics
        labels = np.zeros(len(X))
        
        for idx, (account, row) in enumerate(self.features_df.iterrows()):
            suspicion = 0
            
            # High pass-through ratio
            if row.get("passthrough_ratio", 0) > 0.8:
                suspicion += 1
            
            # Many counterparties with low total transactions
            if row.get("total_degree", 0) > 5 and row.get("tx_count", 0) <= 3:
                suspicion += 1
            
            # High burstiness
            if row.get("burstiness", 0) > 2.0:
                suspicion += 1
            
            # Fan-in or fan-out pattern
            if row.get("in_degree", 0) >= 10 or row.get("out_degree", 0) >= 10:
                suspicion += 1
            
            # High betweenness (bridge node)
            if row.get("betweenness", 0) > 0.1:
                suspicion += 1
            
            # High transaction velocity
            if row.get("tx_per_hour", 0) > 2:
                suspicion += 1
            
            labels[idx] = 1 if suspicion >= 2 else 0
        
        # Only train if we have both classes
        if len(np.unique(labels)) < 2:
            return {}
        
        # Train RandomForest
        rf = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X, labels)
        
        # Get probability scores
        probas = rf.predict_proba(X)[:, 1]
        
        scores = {}
        for idx, account in enumerate(self.features_df.index):
            scores[account] = round(float(probas[idx]) * 100, 2)
        
        return scores
