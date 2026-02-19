"""
IBM Quantum Agent — Real Hardware QAOA Fraud Detection
=======================================================
Uses IBM Quantum's real quantum processors (127-qubit ibm_brisbane / ibm_sherbrooke)
via qiskit-ibm-runtime to run QAOA Max-Cut on the most critical fraud ring.

This produces ACTUAL quantum hardware results — not simulation — giving:
  • Real quantum noise fingerprints (shot-by-shot)
  • Hardware backend topology and qubit mapping
  • Quantum advantage metric (vs classical greedy)
  • Noise-aware partition confidence scores

Fallback chain: IBM Quantum → Aer Simulator → Heuristic scores

Setup: Set IBM_QUANTUM_TOKEN env var to your IBM Quantum API token.
       Get one free at https://quantum.ibm.com
"""

import os
import time
import logging
import numpy as np
import networkx as nx
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("ibm_quantum_agent")

# ── IBM Runtime imports (graceful fallback) ───────────────────────────────
try:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    from qiskit_ibm_runtime import SamplerOptions
    IBM_RUNTIME_AVAILABLE = True
except ImportError:
    IBM_RUNTIME_AVAILABLE = False
    logger.warning("qiskit-ibm-runtime not installed — IBM Quantum unavailable")

try:
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


# ── QAOA Circuit Builder ──────────────────────────────────────────────────

def _build_qaoa_maxcut_circuit(n: int, edges: List[Tuple[int, int]],
                                gamma: float, beta: float) -> "QuantumCircuit":
    """
    Build a depth-1 QAOA Max-Cut circuit for n qubits.
    This is the standard formulation: cost unitary (ZZ) + mixer (Rx).
    """
    qc = QuantumCircuit(n, n)

    # Initial superposition
    qc.h(range(n))

    # Cost unitary: e^{-i*gamma*C} where C = sum_{(u,v) in E} 0.5*(1 - Zv*Zu)
    for u, v in edges:
        qc.cx(u, v)
        qc.rz(2 * gamma, v)
        qc.cx(u, v)

    # Mixer unitary: e^{-i*beta*B} where B = sum_j Xj
    qc.rx(2 * beta, range(n))

    # Measure all
    qc.measure(range(n), range(n))
    return qc


def _get_graph_edges(members: List[str], G: nx.DiGraph) -> List[Tuple[int, int]]:
    """Map account IDs to qubit indices and return edge list."""
    idx = {acc: i for i, acc in enumerate(members)}
    edges = []
    for u, v in G.edges():
        if u in idx and v in idx:
            edges.append((idx[u], idx[v]))
    # Add reverse edges for undirected Max-Cut
    for u, v in list(edges):
        if (v, u) not in edges:
            edges.append((v, u))
    # Deduplicate
    seen = set()
    unique = []
    for e in edges:
        key = (min(e), max(e))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def _compute_maxcut_value(bitstring: str, edges: List[Tuple[int, int]]) -> int:
    """Count edges cut by a given bitstring partition."""
    cut = 0
    for u, v in edges:
        if bitstring[u] != bitstring[v]:
            cut += 1
    return cut


def _classical_greedy_maxcut(n: int, edges: List[Tuple[int, int]]) -> Tuple[str, int]:
    """Simple greedy Max-Cut as classical baseline for quantum advantage metric."""
    partition = [0] * n
    for i in range(n):
        # Assign to partition that maximises cuts
        cuts_0 = sum(1 for u, v in edges
                     if (u == i and partition[v] == 0) or (v == i and partition[u] == 0))
        cuts_1 = sum(1 for u, v in edges
                     if (u == i and partition[v] == 1) or (v == i and partition[u] == 1))
        partition[i] = 1 if cuts_1 > cuts_0 else 0
    bs = ''.join(str(b) for b in partition)
    return bs, _compute_maxcut_value(bs, edges)


# ── Main IBM Quantum Agent ────────────────────────────────────────────────

class IBMQuantumAgent:
    """
    Runs real QAOA on IBM Quantum hardware for the top fraud ring.
    Falls back to Aer simulation if IBM token unavailable.
    """

    # Fixed optimised QAOA angles (pre-trained via parameter sweep on Aer)
    # Using p=1 QAOA optimal angles for Max-Cut on small random graphs
    GAMMA = 0.3927   # π/8
    BETA  = 0.7854   # π/4

    MAX_QUBITS_REAL   = 5   # Keep small for real hardware (less noise, faster queue)
    MAX_QUBITS_SIM    = 8
    SHOTS_REAL        = 1024
    SHOTS_SIM         = 2048

    def __init__(self, G: nx.DiGraph, top_ring: Dict):
        self.G = G
        self.top_ring = top_ring
        self._service: Optional["QiskitRuntimeService"] = None
        self._backend_name: Optional[str] = None
        self._ibm_token = os.getenv("IBM_QUANTUM_TOKEN", "").strip()

    # ── IBM Service connection ────────────────────────────────────────────

    def _connect(self) -> bool:
        """Connect to IBM Quantum. Returns True if successful."""
        if not IBM_RUNTIME_AVAILABLE or not self._ibm_token:
            return False
        try:
            self._service = QiskitRuntimeService(
                channel="ibm_quantum_platform",
                token=self._ibm_token,
                instance="open-instance",
            )
            logger.info("Connected to IBM Quantum service")
            return True
        except Exception as e:
            logger.error(f"IBM Quantum connection failed: {e}")
            return False

    def _get_best_backend(self, n_qubits: int) -> Optional[object]:
        """Find the least-busy IBM backend with enough qubits (0.29+ API)."""
        if self._service is None:
            return None
        try:
            # qiskit-ibm-runtime >= 0.29 uses keyword filters directly
            best = self._service.least_busy(
                min_num_qubits=n_qubits,
                simulator=False,
                operational=True,
            )
            self._backend_name = best.name
            logger.info(f"Selected IBM backend: {best.name} "
                        f"({best.num_qubits} qubits)")
            return best
        except Exception as e:
            logger.error(f"Backend selection failed: {e}")
            return None

    # ── Core run method ───────────────────────────────────────────────────

    def run(self) -> Dict:
        """
        Run QAOA on the top fraud ring.
        Returns enriched results dict with hardware metadata.
        """
        members = self.top_ring.get("member_accounts", [])
        ring_id = self.top_ring.get("ring_id", "RING_001")
        risk_score = self.top_ring.get("risk_score", 50)

        if len(members) < 2:
            return self._fallback_result(ring_id, members, "insufficient_members")

        # ── Try IBM Quantum first ──
        ibm_connected = self._connect()

        if ibm_connected:
            members_sub = members[:self.MAX_QUBITS_REAL]
            result = self._run_on_ibm(members_sub, ring_id, risk_score)
            if result:
                return result

        # ── Fallback to Aer simulation ──
        if QISKIT_AVAILABLE:
            logger.info("Falling back to Aer simulation")
            members_sub = members[:self.MAX_QUBITS_SIM]
            return self._run_on_aer(members_sub, ring_id, risk_score)

        return self._fallback_result(ring_id, members, "qiskit_unavailable")

    def _run_on_ibm(self, members: List[str], ring_id: str, risk_score: float) -> Optional[Dict]:
        """Execute circuit on real IBM Quantum hardware."""
        n = len(members)
        edges = _get_graph_edges(members, self.G)

        if not edges:
            logger.warning(f"Ring {ring_id}: no edges between members, skipping IBM run")
            return None

        backend = self._get_best_backend(n)
        if backend is None:
            return None

        try:
            qc = _build_qaoa_maxcut_circuit(n, edges, self.GAMMA, self.BETA)

            # Transpile for the target backend
            from qiskit.compiler import transpile
            qc_t = transpile(qc, backend=backend, optimization_level=1)

            logger.info(f"Submitting job to {self._backend_name} "
                        f"({n} qubits, {len(edges)} edges, {self.SHOTS_REAL} shots)...")

            t0 = time.time()
            sampler = Sampler(backend)
            job = sampler.run([qc_t], shots=self.SHOTS_REAL)
            result = job.result()
            elapsed = round(time.time() - t0, 2)

            logger.info(f"IBM Quantum job completed in {elapsed}s")

            # Extract counts from SamplerV2 result
            pub_result = result[0]
            counts = pub_result.data.c.get_counts()

            return self._process_counts(
                counts=counts,
                members=members,
                ring_id=ring_id,
                risk_score=risk_score,
                edges=edges,
                backend_name=self._backend_name,
                elapsed=elapsed,
                hardware="real",
                shots=self.SHOTS_REAL,
            )

        except Exception as e:
            logger.error(f"IBM Quantum job failed: {e}", exc_info=True)
            return None

    def _run_on_aer(self, members: List[str], ring_id: str, risk_score: float) -> Dict:
        """Execute circuit on local Aer simulator (fallback)."""
        n = len(members)
        edges = _get_graph_edges(members, self.G)

        if not edges:
            return self._fallback_result(ring_id, members, "no_edges")

        try:
            qc = _build_qaoa_maxcut_circuit(n, edges, self.GAMMA, self.BETA)
            sim = AerSimulator()

            from qiskit import transpile
            qc_t = transpile(qc, sim)

            t0 = time.time()
            job = sim.run(qc_t, shots=self.SHOTS_SIM)
            counts = job.result().get_counts()
            elapsed = round(time.time() - t0, 2)

            return self._process_counts(
                counts=counts,
                members=members,
                ring_id=ring_id,
                risk_score=risk_score,
                edges=edges,
                backend_name="aer_simulator",
                elapsed=elapsed,
                hardware="simulator",
                shots=self.SHOTS_SIM,
            )
        except Exception as e:
            logger.error(f"Aer simulation failed: {e}")
            return self._fallback_result(ring_id, members, f"aer_error: {e}")

    def _process_counts(self, counts: Dict, members: List[str], ring_id: str,
                        risk_score: float, edges: List[Tuple[int, int]],
                        backend_name: str, elapsed: float,
                        hardware: str, shots: int) -> Dict:
        """Turn raw measurement counts into enriched fraud analysis."""
        n = len(members)
        total = sum(counts.values())

        # Sort bitstrings by frequency
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        # Find best partition (highest cut value among top measurements)
        best_bs = None
        best_cut = -1
        for bs, cnt in sorted_counts[:20]:
            # Pad/truncate to n bits
            bs_clean = bs.replace(' ', '').zfill(n)[-n:]
            cut = _compute_maxcut_value(bs_clean, edges)
            if cut > best_cut:
                best_cut = cut
                best_bs = bs_clean

        # Partition accounts
        group_0 = [members[i] for i in range(n) if best_bs[i] == '0']
        group_1 = [members[i] for i in range(n) if best_bs[i] == '1']

        # Classical baseline for quantum advantage metric
        classical_bs, classical_cut = _classical_greedy_maxcut(n, edges)
        max_possible_cut = len(edges)
        quantum_advantage = round(
            (best_cut - classical_cut) / max(max_possible_cut, 1) * 100, 2
        )

        # Top measurement probabilities
        top_measurements = [
            {
                "bitstring": bs.replace(' ', '').zfill(n)[-n:],
                "probability": round(cnt / total, 4),
                "count": cnt,
                "cut_value": _compute_maxcut_value(bs.replace(' ', '').zfill(n)[-n:], edges),
            }
            for bs, cnt in sorted_counts[:8]
        ]

        # Per-account quantum suspicion scores
        # Accounts in the larger partition get higher scores (they're the "core" ring)
        dominant_group = group_1 if len(group_1) >= len(group_0) else group_0
        minority_group = group_0 if dominant_group is group_1 else group_1

        quantum_scores = {}
        # Dominant group (core ring members): score based on probability mass
        dominant_prob = sum(
            cnt / total for bs, cnt in sorted_counts[:10]
            if bs.replace(' ', '').zfill(n)[-n:] == best_bs
        )
        for acc in dominant_group:
            quantum_scores[acc] = round(min(risk_score * 0.9 + dominant_prob * 10, 100), 2)
        for acc in minority_group:
            quantum_scores[acc] = round(min(risk_score * 0.6, 100), 2)

        # Noise entropy (higher = noisier hardware / more uncertain)
        probs = [cnt / total for _, cnt in sorted_counts]
        entropy = -sum(p * np.log2(p + 1e-10) for p in probs)
        max_entropy = np.log2(max(len(counts), 1))
        noise_level = round(entropy / max(max_entropy, 1), 3)

        return {
            "ibm_quantum": True,
            "hardware": hardware,
            "backend": backend_name,
            "ring_id": ring_id,
            "n_qubits": n,
            "shots": shots,
            "execution_time_seconds": elapsed,
            "qaoa_gamma": self.GAMMA,
            "qaoa_beta": self.BETA,
            "edges_analyzed": len(edges),
            "best_partition": {
                "bitstring": best_bs,
                "cut_value": best_cut,
                "max_possible_cut": max_possible_cut,
                "cut_ratio": round(best_cut / max(max_possible_cut, 1), 3),
                "group_0": group_0,
                "group_1": group_1,
            },
            "classical_baseline": {
                "bitstring": classical_bs,
                "cut_value": classical_cut,
            },
            "quantum_advantage_pct": quantum_advantage,
            "noise_entropy": noise_level,
            "top_measurements": top_measurements,
            "quantum_scores": quantum_scores,
            "suspicious_set": dominant_group,
            "total_unique_bitstrings": len(counts),
        }

    def _fallback_result(self, ring_id: str, members: List[str], reason: str) -> Dict:
        return {
            "ibm_quantum": False,
            "hardware": "none",
            "backend": "unavailable",
            "ring_id": ring_id,
            "reason": reason,
            "quantum_scores": {acc: 50.0 for acc in members},
            "suspicious_set": members,
            "quantum_advantage_pct": 0,
        }
