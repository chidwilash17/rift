"""
Agent 3: Quantum Agent
Uses Qiskit Aer simulator to run QAOA for community detection on suspicious subgraphs.
Generates quantum circuits, measurement histograms, and quantum-enhanced scores.
"""

import os
import numpy as np
import networkx as nx
import base64
import io
from typing import Dict, List, Optional

# Qiskit imports (with graceful fallback)
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


class QuantumAgent:
    """Agent responsible for quantum-enhanced fraud community detection."""
    
    MAX_QUBITS = 6    # Reduced from 8 — cuts circuit size, big speed win on free tier
    QAOA_LAYERS = 1   # Single layer is enough for partitioning
    SHOTS = 256       # Halved again — still statistically meaningful
    
    def __init__(self, G: nx.DiGraph, suspicious_subgraphs: List[Dict] = None):
        self.G = G
        self.suspicious_subgraphs = suspicious_subgraphs or []
        self.simulator = AerSimulator() if QISKIT_AVAILABLE else None
    
    # Env-configurable: set MAX_QUANTUM_RINGS=0 in Render to skip all circuits
    TOP_RINGS_LIMIT = int(os.getenv("MAX_QUANTUM_RINGS", "5"))  # default 5 (was 10)

    def run(self) -> Dict:
        """Run quantum analysis on the top-N most critical rings only."""
        if not QISKIT_AVAILABLE:
            return {
                "quantum_available": False,
                "agent": "quantum_optimizer",
                "message": "Qiskit not installed — skipping quantum analysis"
            }

        quantum_results = []
        all_quantum_scores = {}

        # Sort rings by risk_score descending and split into top-N vs rest
        sorted_rings = sorted(
            self.suspicious_subgraphs,
            key=lambda r: r.get("risk_score", 0),
            reverse=True,
        )
        top_rings = sorted_rings[:self.TOP_RINGS_LIMIT]
        remaining_rings = sorted_rings[self.TOP_RINGS_LIMIT:]

        # ── Full QAOA circuits for critical top rings ──
        image_budget = 3  # Only render circuit PNGs for top 3 rings (expensive)
        for ring_info in top_rings:
            members = ring_info.get("member_accounts", [])
            ring_id = ring_info.get("ring_id", "UNKNOWN")

            if len(members) < 2:
                continue

            members_subset = members[:self.MAX_QUBITS]
            render_image = image_budget > 0

            result = self._run_qaoa_maxcut(members_subset, ring_id, render_image=render_image)
            if result:
                quantum_results.append(result)
                if render_image:
                    image_budget -= 1
                for acc, score in result.get("quantum_scores", {}).items():
                    if acc not in all_quantum_scores:
                        all_quantum_scores[acc] = score
                    else:
                        all_quantum_scores[acc] = max(all_quantum_scores[acc], score)

        # ── Heuristic-only scores for the remaining rings (no circuit) ──
        for ring_info in remaining_rings:
            members = ring_info.get("member_accounts", [])
            ring_id = ring_info.get("ring_id", "UNKNOWN")
            risk = ring_info.get("risk_score", 0)

            if len(members) < 2:
                continue

            # Approximate quantum scores from the classical risk score
            approx_scores = {}
            for acc in members:
                approx_scores[acc] = round(min(risk * 0.85, 100.0), 2)

            quantum_results.append({
                "ring_id": ring_id,
                "n_qubits": 0,
                "qaoa_layers": 0,
                "shots": 0,
                "optimal_bitstring": None,
                "top_measurements": [],
                "quantum_scores": approx_scores,
                "circuit_image": None,
                "circuit_depth": 0,
                "gate_count": 0,
                "partition_score": 0,
                "suspicious_set": members,
                "skipped": True,
                "skip_reason": f"Ring below top-{self.TOP_RINGS_LIMIT} threshold — heuristic score used",
            })

            for acc, score in approx_scores.items():
                if acc not in all_quantum_scores:
                    all_quantum_scores[acc] = score
                else:
                    all_quantum_scores[acc] = max(all_quantum_scores[acc], score)

        return {
            "quantum_available": True,
            "quantum_results": quantum_results,
            "quantum_scores": all_quantum_scores,
            "circuits_executed": len(top_rings),
            "circuits_skipped": len(remaining_rings),
            "agent": "quantum_optimizer"
        }
    
    def _run_qaoa_maxcut(self, members: List[str], ring_id: str, render_image: bool = True) -> Optional[Dict]:
        """
        Run QAOA Max-Cut on a subgraph of suspicious accounts.
        Partitions accounts into fraud (1) vs uncertain (0).
        """
        try:
            n_qubits = len(members)
            if n_qubits < 2:
                return None
            
            # Build subgraph (undirected for Max-Cut)
            subG = nx.Graph()
            for i, u in enumerate(members):
                for j, v in enumerate(members):
                    if i < j:
                        # Check if edge exists in either direction
                        weight = 0
                        if self.G.has_edge(u, v):
                            weight += self.G[u][v].get("total_amount", 1)
                        if self.G.has_edge(v, u):
                            weight += self.G[v][u].get("total_amount", 1)
                        if weight > 0:
                            # Normalize weight to [0, 1]
                            subG.add_edge(i, j, weight=min(weight / 10000, 1.0))
            
            if subG.number_of_edges() == 0:
                # Add default connections for fully disconnected sets
                for i in range(n_qubits - 1):
                    subG.add_edge(i, i + 1, weight=0.5)
            
            # Build QAOA circuit
            qc = self._build_qaoa_circuit(n_qubits, subG)
            
            # Execute on Aer
            result = self.simulator.run(qc, shots=self.SHOTS).result()
            counts = result.get_counts()
            
            # Find optimal bitstring
            best_bitstring = max(counts, key=counts.get)
            
            # Calculate quantum scores per account
            quantum_scores = {}
            for idx in range(n_qubits):
                account = members[idx]
                # Probability of being in partition '1' (suspicious)
                prob_1 = sum(
                    count for bs, count in counts.items()
                    if len(bs) > idx and bs[-(idx + 1)] == '1'
                ) / self.SHOTS
                quantum_scores[account] = round(prob_1 * 100, 2)
            
            # Generate circuit diagram as base64 image (only when requested)
            circuit_image_b64 = self._circuit_to_base64(qc) if render_image else None
            
            # Top measurement results as structured list
            total_shots = sum(counts.values())
            sorted_measurements = sorted(counts.items(), key=lambda x: -x[1])[:10]
            top_measurements = [
                {"bitstring": bs, "count": cnt, "probability": round(cnt / total_shots, 4)}
                for bs, cnt in sorted_measurements
            ]
            
            # Partition score: Max-Cut value of best bitstring
            partition_score = self._compute_cut_value(best_bitstring, subG, n_qubits)
            
            # Suspicious set: accounts where qubit measured '1' in best bitstring
            suspicious_set = [
                members[idx] for idx in range(n_qubits)
                if len(best_bitstring) > idx and best_bitstring[-(idx + 1)] == '1'
            ]
            
            return {
                "ring_id": ring_id,
                "n_qubits": n_qubits,
                "qaoa_layers": self.QAOA_LAYERS,
                "shots": self.SHOTS,
                "optimal_bitstring": best_bitstring,
                "top_measurements": top_measurements,
                "quantum_scores": quantum_scores,
                "circuit_image": circuit_image_b64,
                "circuit_depth": qc.depth(),
                "gate_count": qc.size(),
                "partition_score": partition_score,
                "suspicious_set": suspicious_set
            }
        except Exception as e:
            return {
                "ring_id": ring_id,
                "error": str(e),
                "quantum_scores": {}
            }
    
    @staticmethod
    def _compute_cut_value(bitstring: str, subG: nx.Graph, n_qubits: int) -> float:
        """Compute the Max-Cut value for a given bitstring."""
        cut_val = 0.0
        for u, v, data in subG.edges(data=True):
            w = data.get("weight", 1.0)
            bu = int(bitstring[-(u + 1)]) if len(bitstring) > u else 0
            bv = int(bitstring[-(v + 1)]) if len(bitstring) > v else 0
            if bu != bv:
                cut_val += w
        return round(cut_val, 4)

    def _build_qaoa_circuit(self, n_qubits: int, subG: nx.Graph) -> "QuantumCircuit":
        """Build a QAOA circuit for Max-Cut."""
        qc = QuantumCircuit(n_qubits, n_qubits)
        
        # Optimized parameters (pre-tuned for typical fraud subgraphs)
        gammas = [0.75, 1.15]
        betas = [0.45, 0.65]
        
        # Initial superposition
        for i in range(n_qubits):
            qc.h(i)
        
        # QAOA layers
        for layer in range(self.QAOA_LAYERS):
            # Cost unitary (ZZ interactions for edges)
            for (u, v, data) in subG.edges(data=True):
                weight = data.get("weight", 1.0)
                gamma = gammas[layer] * weight
                
                qc.cx(u, v)
                qc.rz(2 * gamma, v)
                qc.cx(u, v)
            
            # Mixer unitary (X rotations)
            for i in range(n_qubits):
                qc.rx(2 * betas[layer], i)
        
        # Measurement
        qc.measure(range(n_qubits), range(n_qubits))
        
        return qc
    
    def _circuit_to_base64(self, qc: "QuantumCircuit") -> str:
        """Render quantum circuit as a high-contrast, publication-quality PNG."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            # Premium light-on-dark style: crisp white bg, vivid gate colors
            premium_style = {
                'backgroundcolor': '#ffffff',
                'textcolor':       '#1b1f23',
                'subtextcolor':    '#586069',
                'linecolor':       '#24292e',
                'creglinecolor':   '#6f42c1',
                'gatetextcolor':   '#ffffff',
                'gatefacecolor':   '#4f46e5',       # Indigo gates
                'barrierfacecolor':'#d1d5db',
                'fontsize':        14,
                'subfontsize':     11,
                'displaycolor': {
                    'h':    ('#6366f1', '#ffffff'),   # Indigo-500
                    'x':    ('#ef4444', '#ffffff'),   # Red-500
                    'y':    ('#22c55e', '#ffffff'),   # Green-500
                    'z':    ('#3b82f6', '#ffffff'),   # Blue-500
                    'cx':   ('#8b5cf6', '#ffffff'),   # Violet-500
                    'cz':   ('#0ea5e9', '#ffffff'),   # Sky-500
                    'rx':   ('#f97316', '#ffffff'),   # Orange-500
                    'ry':   ('#14b8a6', '#ffffff'),   # Teal-500
                    'rz':   ('#a855f7', '#ffffff'),   # Purple-500
                    'swap': ('#ec4899', '#ffffff'),   # Pink-500
                    'id':   ('#94a3b8', '#1e293b'),   # Slate
                    'u':    ('#e11d48', '#ffffff'),   # Rose-600
                    'measure': ('#0d9488', '#ffffff'), # Teal-600
                    'reset': ('#64748b', '#ffffff'),  # Slate-500
                    'target': ('#6366f1', '#ffffff'),
                },
            }

            # Wider figure for deeper circuits
            n_qubits = qc.num_qubits
            fig_w = max(12, min(20, qc.depth() * 1.4))
            fig_h = max(3, n_qubits * 0.7 + 1)

            fig = qc.draw(
                output='mpl',
                style=premium_style,
                fold=-1,                    # no folding — show full width
                initial_state=True,
            )
            # Override figure size after draw
            fig.set_size_inches(fig_w, fig_h)

            buf = io.BytesIO()
            fig.savefig(
                buf, format='png', dpi=200,
                bbox_inches='tight', pad_inches=0.15,
                facecolor='#ffffff', edgecolor='none',
            )
            plt.close(fig)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode('utf-8')

        except Exception as e:
            # Fallback: text circuit rendered as high-contrast PNG
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt

                text_repr = str(qc.draw(output='text'))
                lines = text_repr.split('\n')
                fig_h = max(3, len(lines) * 0.22 + 0.5)
                fig, ax = plt.subplots(figsize=(14, fig_h), facecolor='#ffffff')
                ax.set_facecolor('#ffffff')
                ax.text(
                    0.02, 0.95, text_repr,
                    transform=ax.transAxes,
                    fontfamily='monospace', fontsize=9, color='#1b1f23',
                    verticalalignment='top',
                )
                ax.axis('off')
                buf = io.BytesIO()
                fig.savefig(
                    buf, format='png', dpi=200,
                    bbox_inches='tight', facecolor='#ffffff', edgecolor='none',
                )
                plt.close(fig)
                buf.seek(0)
                return base64.b64encode(buf.read()).decode('utf-8')
            except Exception:
                return None
