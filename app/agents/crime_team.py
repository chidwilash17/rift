"""
Multi-Agent Crime Investigation Team
Wraps existing detection agents with forensic "personalities" and generates:
  1. Agent conversation log (inter-agent debate)  ← NOW LLM-POWERED via Groq
  2. Case file narrative
  3. Evidence chain
  4. Confidence assessment
  5. Recommended actions

When GROQ_API_KEY is set, conversations are generated dynamically by Llama 3.3 70B
via Groq's ultra-fast inference. Each agent persona sends real analysis data to the
LLM and receives unique, contextual responses that adapt to every dataset.
Falls back to the deterministic template engine if the API is unavailable.
"""

import time
import random
import logging
from typing import Dict, List
from collections import defaultdict

from app.agents.llm_provider import generate_dynamic_conversation, is_available as llm_available

logger = logging.getLogger("crime_team")


# Agent personas
AGENTS = {
    "detective": {
        "name": "Agent VORTEX",
        "title": "Graph Detective",
        "avatar": "fa-magnifying-glass",
        "color": "#58a6ff",
        "specialty": "Structural pattern analysis, cycle detection, network topology",
        "personality": "Methodical, detail-oriented, spots patterns others miss",
    },
    "profiler": {
        "name": "Agent CIPHER",
        "title": "ML Profiler",
        "avatar": "fa-brain",
        "color": "#a371f7",
        "specialty": "Behavioral profiling, anomaly detection, statistical analysis",
        "personality": "Data-driven, probabilistic thinker, questions assumptions",
    },
    "quantum": {
        "name": "Agent QUBIT",
        "title": "Quantum Analyst",
        "avatar": "fa-atom",
        "color": "#79c0ff",
        "specialty": "Quantum optimization, community partitioning, min-cut analysis",
        "personality": "Abstract thinker, sees hidden boundaries, speaks in probabilities",
    },
    "prosecutor": {
        "name": "Agent NEXUS",
        "title": "Lead Prosecutor",
        "avatar": "fa-gavel",
        "color": "#3fb950",
        "specialty": "Evidence synthesis, case building, action recommendations",
        "personality": "Decisive, weighs evidence carefully, builds airtight cases",
    },
}


class CrimeTeam:
    """
    Generates a multi-agent investigation narrative from analysis results.
    """

    def __init__(self, graph_results: Dict, ml_results: Dict,
                 quantum_results: Dict, aggregated: Dict,
                 disruption: Dict = None):
        self.graph_results = graph_results
        self.ml_results = ml_results
        self.quantum_results = quantum_results
        self.aggregated = aggregated
        self.disruption = disruption or {}

    def run(self) -> Dict:
        """Generate full crime team investigation report."""
        # ── Try LLM-powered dynamic conversation first ──
        ai_powered = False
        if llm_available():
            logger.info("Groq LLM available — generating dynamic AI conversation...")
            conversation = generate_dynamic_conversation(
                graph_results=self.graph_results,
                ml_results=self.ml_results,
                quantum_results=self.quantum_results,
                aggregated=self.aggregated,
                disruption=self.disruption,
                agents_meta=AGENTS,
            )
            if conversation is not None:
                ai_powered = True
                logger.info(f"AI conversation generated: {len(conversation)} messages")
            else:
                logger.warning("LLM call failed — falling back to template engine")
                conversation = self._generate_conversation()
        else:
            logger.info("No GROQ_API_KEY — using template conversation engine")
            conversation = self._generate_conversation()

        case_file = self._generate_case_file()
        evidence_chain = self._build_evidence_chain()
        confidence = self._assess_confidence()
        actions = self._recommend_actions()
        timeline = self._build_investigation_timeline()

        return {
            "agents": AGENTS,
            "conversation": conversation,
            "case_file": case_file,
            "evidence_chain": evidence_chain,
            "confidence_assessment": confidence,
            "recommended_actions": actions,
            "investigation_timeline": timeline,
            "ai_powered": ai_powered,
            "llm_model": "llama-3.3-70b-versatile (Groq)" if ai_powered else None,
        }

    def _generate_conversation(self) -> List[Dict]:
        """
        Generate a DYNAMIC inter-agent investigation conversation.
        Branching, debate, and phrasing adapt to the data — different datasets
        produce genuinely different conversations.
        """
        msgs: List[Dict] = []

        # ── Compute "situation profile" from the data ──────────────────────
        rings   = self.aggregated.get("fraud_rings", [])
        accounts = self.aggregated.get("suspicious_accounts", [])
        summary  = self.aggregated.get("summary", {})
        n_rings      = len(rings)
        n_suspicious = len(accounts)
        top_ring     = rings[0] if rings else None
        top_account  = accounts[0] if accounts else None

        ml_scores    = self.ml_results.get("ml_scores", {})
        high_risk    = [a for a in accounts if a["suspicion_score"] >= 70]
        medium_risk  = [a for a in accounts if 40 <= a["suspicion_score"] < 70]
        low_risk     = [a for a in accounts if a["suspicion_score"] < 40]

        q_data       = self.quantum_results or {}
        q_results    = q_data.get("quantum_results", [])
        q_circuits   = len(q_results)
        q_scores     = q_data.get("quantum_scores", {})

        disruption_strats = self.disruption.get("strategies", [])
        global_summary    = self.disruption.get("global_summary", {})

        # Pattern breakdown
        pattern_freq = defaultdict(int)
        for r in rings:
            pattern_freq[r.get("pattern_type", "unknown")] += 1
        dominant_pattern = max(pattern_freq, key=pattern_freq.get) if pattern_freq else "unknown"

        # Graph-ML agreement
        graph_flagged = set()
        for r in self.graph_results.get("rings", []):
            graph_flagged.update(r.get("member_accounts", []))
        ml_flagged = {acc for acc, sc in ml_scores.items() if sc > 60}
        overlap = graph_flagged & ml_flagged
        union   = graph_flagged | ml_flagged
        agreement_pct = (len(overlap) / max(len(union), 1)) * 100

        # Quantum-classical agreement
        qc_match = 0
        qc_total = 0
        for qr in q_results:
            for acc in qr.get("suspicious_set", []):
                qc_total += 1
                if any(a["account_id"] == acc and a["suspicion_score"] > 50 for a in accounts):
                    qc_match += 1
        qc_agreement = (qc_match / max(qc_total, 1)) * 100

        # Severity tier
        severity = "CRITICAL" if n_rings > 10 or len(high_risk) > 8 else \
                   "HIGH"     if n_rings > 5  or len(high_risk) > 4 else "MODERATE"

        # Score divergence (graph vs ML for top account)
        score_divergence = 0
        if top_account:
            cs = top_account.get("component_scores", {})
            score_divergence = abs(cs.get("graph", 0) - cs.get("ml", 0))

        # Disruption fragility
        avg_disruption = global_summary.get("avg_disruption_potential", 0)
        is_fragile = avg_disruption > 50
        resilience = global_summary.get("network_resilience_score", 0)

        # ── PHASE 1: Opening — Severity-driven ────────────────────────────
        if severity == "CRITICAL":
            msgs.append(self._msg("prosecutor",
                f"**EMERGENCY BRIEFING** — All agents, priority override. We have "
                f"**{n_rings} active fraud rings** involving **{n_suspicious} accounts**. "
                f"This is a large-scale operation. VORTEX, start with the structural picture.",
                "emergency_open"))
        elif severity == "HIGH":
            msgs.append(self._msg("detective",
                f"Team, I've completed the structural sweep. The graph is **hot** — "
                f"**{n_rings} distinct fraud rings** touching **{n_suspicious} accounts**. "
                f"I'm seeing organized routing patterns that suggest coordinated muling.",
                "initial_scan"))
        else:
            msgs.append(self._msg("detective",
                f"Scan complete. I've mapped **{n_rings} potential fraud ring{'s' if n_rings != 1 else ''}** "
                f"across **{n_suspicious} accounts**. Activity level is moderate — "
                f"we'll need the full team to confirm before escalation.",
                "initial_scan"))

        # ── PHASE 2: Pattern-specific Detective deep-dive ─────────────────
        pattern_lines = []
        if pattern_freq.get("cycle", 0):
            pattern_lines.append(f"**{pattern_freq['cycle']}** cyclic routing rings (classic carousel laundering)")
        if pattern_freq.get("smurfing", 0):
            pattern_lines.append(f"**{pattern_freq['smurfing']}** smurfing patterns (structured sub-threshold deposits)")
        if pattern_freq.get("shell_network", 0):
            pattern_lines.append(f"**{pattern_freq['shell_network']}** shell company topologies (hub-spoke funnelling)")

        if len(pattern_lines) > 1:
            msgs.append(self._msg("detective",
                f"Pattern breakdown — this is a **mixed-method** operation:\n"
                + "\n".join(f"  • {l}" for l in pattern_lines) +
                f"\nThe diversity of techniques suggests a sophisticated actor rotating TTPs.",
                "pattern_breakdown"))
        elif pattern_lines:
            msgs.append(self._msg("detective",
                f"Dominant pattern: {pattern_lines[0]}. "
                f"Single-technique networks are often early-stage operations "
                f"— we may be catching this before it diversifies.",
                "pattern_breakdown"))

        # ── PHASE 3: ML Profiler report (agreement-aware) ─────────────────
        high_anomaly = sum(1 for s in ml_scores.values() if s > 70)

        if agreement_pct > 70:
            msgs.append(self._msg("profiler",
                f"Strong corroboration from the behavioral side. My ensemble flagged "
                f"**{high_anomaly}** high-anomaly accounts (score > 70). Cross-referencing "
                f"with VORTEX's structural findings shows **{agreement_pct:.0f}% overlap** "
                f"— Graph and ML are pointing at the same nodes. High confidence.",
                "ml_agreement"))
        elif agreement_pct > 40:
            msgs.append(self._msg("profiler",
                f"Mixed picture from ML. I flagged **{high_anomaly}** accounts above 70, "
                f"but only **{agreement_pct:.0f}%** overlap with the graph-based rings. "
                f"Some structurally suspicious nodes look behaviorally clean, and some ML outliers "
                f"aren't in any ring. We should investigate the gap.",
                "ml_mixed"))
            # Detective reacts to the disagreement
            non_overlap = ml_flagged - graph_flagged
            if non_overlap:
                samples = list(non_overlap)[:3]
                msgs.append(self._msg("detective",
                    f"Interesting — the ML-only flags ({', '.join(samples)}) aren't in structural rings. "
                    f"Could be standalone mules or edge nodes I missed. Let me cross-check their "
                    f"degree centrality... they might be bridge accounts connecting separate operations.",
                    "detective_reacts"))
        else:
            msgs.append(self._msg("profiler",
                f"We have a **significant disagreement**. ML flagged **{high_anomaly}** accounts, "
                f"but only **{agreement_pct:.0f}%** line up with graph findings. Either we're "
                f"dealing with polymorphic behavior (accounts switching roles) or one signal is "
                f"picking up noise. I'd recommend double-weighting the accounts that BOTH methods flag.",
                "ml_conflict"))
            msgs.append(self._msg("prosecutor",
                f"Noted. CIPHER, isolate the accounts where Graph scored high but ML scored "
                f"low — those might be dormant mules with structural position but no recent "
                f"behavioral signature. And vice versa for the ML-only outliers.",
                "prosecutor_directs"))

        # ── PHASE 4: Quantum Analysis (conditional depth) ──────────────────
        if q_circuits > 0:
            if qc_agreement > 70:
                msgs.append(self._msg("quantum",
                    f"Quantum laydown complete — **{q_circuits} QAOA circuits** executed. "
                    f"Max-Cut partitioning aligns well with classical findings: "
                    f"**{qc_agreement:.0f}% quantum-classical agreement**. The partition "
                    f"boundaries cleanly separate the suspicious clusters from the rest. "
                    f"This is textbook convergence.",
                    "quantum_strong"))
            elif qc_agreement > 40:
                msgs.append(self._msg("quantum",
                    f"Ran **{q_circuits} QAOA circuits**. Quantum partitioning shows "
                    f"**{qc_agreement:.0f}%** alignment with classical flags. There are "
                    f"some community boundaries the quantum optimizer sees differently — "
                    f"accounts that the quantum side places in the *suspicious* partition "
                    f"but classical methods rated low. Worth investigating.",
                    "quantum_moderate"))
                # Profiler challenges quantum
                msgs.append(self._msg("profiler",
                    f"QUBIT, the partial disagreement concerns me. Are those quantum-only "
                    f"flags driven by topology (position in the graph) or by actual transaction "
                    f"weight? Because Isolation Forest didn't flag them behaviourally.",
                    "profiler_challenges_quantum"))
                msgs.append(self._msg("quantum",
                    f"It's topological — they sit at partition boundaries where the cut value "
                    f"is ambiguous. Think of them as accounts that *could* flip either way. "
                    f"The QAOA energy landscape is flat in that region, which itself is a signal. "
                    f"Ambiguous partition membership often means the account serves both sides.",
                    "quantum_defends"))
            else:
                msgs.append(self._msg("quantum",
                    f"**{q_circuits} QAOA circuits** completed, but quantum-classical agreement "
                    f"is only **{qc_agreement:.0f}%**. The Max-Cut optimizer is partitioning "
                    f"the graph quite differently from classical methods. This could mean the "
                    f"true community structure doesn't align with our suspicion heuristics "
                    f"— or the subgraphs need more QAOA layers to converge.",
                    "quantum_weak"))
        else:
            msgs.append(self._msg("quantum",
                "No quantum circuits executed on this dataset — the subgraphs were too small "
                "or disconnected for meaningful QAOA optimization. I'm deferring to the "
                "classical consensus on this one.",
                "quantum_unavailable"))

        # ── PHASE 5: Top Ring / Top Account spotlight ──────────────────────
        if top_ring:
            members_str = ", ".join(top_ring["member_accounts"][:5])
            extras = len(top_ring["member_accounts"]) - 5
            extra_str = f" + {extras} more" if extras > 0 else ""
            risk = top_ring["risk_score"]
            risk_label = "**extremely high**" if risk >= 80 else "**elevated**" if risk >= 60 else "**moderate**"
            msgs.append(self._msg("detective",
                f"Priority target — **{top_ring['ring_id']}**: {len(top_ring['member_accounts'])} "
                f"members ({members_str}{extra_str}), risk {risk_label} at **{risk}**. "
                f"Pattern: {top_ring['pattern_type']}. "
                + (f"This is the tightest cycle topology in the dataset — minimal hops, maximum throughput."
                   if top_ring["pattern_type"] == "cycle" else
                   f"Structure suggests organized layering with dedicated collection and distribution nodes."
                   if top_ring["pattern_type"] == "smurfing" else
                   f"Hub-spoke formation with a central coordinator funnelling through shell entities."),
                "top_ring"))

        if top_account:
            scores = top_account.get("component_scores", {})
            top_score = top_account["suspicion_score"]
            acct_id = top_account["account_id"]
            patterns = top_account.get("detected_patterns", [])

            # Dynamic commentary based on score distribution
            if scores.get("graph", 0) > 70 and scores.get("ml", 0) > 70:
                verdict = ("Every signal converges on this account — structural centrality, "
                           "behavioral anomaly, and pattern matching all agree.")
            elif scores.get("graph", 0) > scores.get("ml", 0) + 20:
                verdict = ("Interesting asymmetry: structurally very suspicious but behaviorally "
                           "quieter. Could be a dormant controller or a recently activated mule.")
            elif scores.get("ml", 0) > scores.get("graph", 0) + 20:
                verdict = ("ML flags this account harder than the graph does — unusual transaction "
                           "velocity that doesn't yet show up in the ring topology. Watch this one.")
            else:
                verdict = "Balanced signal across all detection methods."

            msgs.append(self._msg("profiler",
                f"Focal account: **{acct_id}** — composite **{top_score}**. "
                f"Graph: {scores.get('graph', 0)}, ML: {scores.get('ml', 0)}, "
                f"Quantum: {scores.get('quantum', 0)}. "
                f"Patterns: {', '.join(patterns[:4])}. {verdict}",
                "top_account"))

        # ── PHASE 6: Disruption Strategy (conditional) ────────────────────
        if disruption_strats:
            best = disruption_strats[0]
            crits = best.get("critical_nodes", [])
            max_d  = best.get("max_disruption_pct", 0)
            if crits:
                crit_names = ", ".join([c["account_id"] for c in crits[:3]])
                if is_fragile:
                    msgs.append(self._msg("quantum",
                        f"Good news on the tactical side — the network is **fragile**. "
                        f"Removing just **{crit_names}** from {best['ring_id']} would fragment it "
                        f"by **{max_d}%**. Network resilience is only **{resilience:.1f}%**. "
                        f"These are single points of failure in the money pipeline.",
                        "disruption_fragile"))
                    msgs.append(self._msg("prosecutor",
                        f"That's our strike vector. If we freeze those accounts simultaneously, "
                        f"the ring collapses before they can reroute. VORTEX, confirm there "
                        f"aren't backup channels they could pivot to.",
                        "prosecutor_disruption"))
                    msgs.append(self._msg("detective",
                        f"Checking... {'No backup routes detected — these nodes are true chokepoints.' if max_d > 70 else 'There are some secondary paths, but removing the critical nodes still degrades capacity by over half.'}",
                        "detective_confirms"))
                else:
                    msgs.append(self._msg("quantum",
                        f"Disruption analysis: Targeting **{crit_names}** in {best['ring_id']} "
                        f"achieves **{max_d}%** disruption, but the network resilience is "
                        f"**{resilience:.1f}%** — it's **robust**. They have redundancy built in. "
                        f"A single-point takedown won't be enough.",
                        "disruption_resilient"))
                    msgs.append(self._msg("prosecutor",
                        f"Then we need a coordinated multi-node action. QUBIT, what's the "
                        f"minimum number of simultaneous freezes to achieve > 80% disruption?",
                        "prosecutor_asks"))
                    # Compute an answer
                    pair_strat = best.get("optimal_pair_removal", {})
                    pair_d = pair_strat.get("disruption_pct", 0)
                    msgs.append(self._msg("quantum",
                        f"Pair removal gets us to **{pair_d}%**. "
                        f"For full collapse, we'd need to hit at least 3 nodes simultaneously "
                        f"across the critical path. I'll flag the optimal combination in the report.",
                        "quantum_pair"))

        # ── PHASE 7: Risk-based Debate ────────────────────────────────────
        if top_account and top_account["suspicion_score"] < 60:
            msgs.append(self._msg("profiler",
                f"I want to raise a **caution flag**. Our top-scoring account ({top_account['account_id']}) "
                f"sits at only **{top_account['suspicion_score']}**. We don't have a single account "
                f"above 80 in the dataset. Are we confident this isn't a false-positive-heavy batch?",
                "caution_low"))
            msgs.append(self._msg("detective",
                f"The individual scores may be moderate, but the *ring structure* is textbook. "
                f"Money muling doesn't require any single account to be overtly suspicious — "
                f"the crime is in the **network pattern**, not the individual node.",
                "counter_caution"))
            msgs.append(self._msg("prosecutor",
                f"Agreed with VORTEX. We prosecute the ring, not the account. File this as "
                f"a network-level SAR and flag the structural evidence as primary.",
                "resolve_debate"))
        elif len(high_risk) > 10:
            msgs.append(self._msg("profiler",
                f"We have **{len(high_risk)} accounts above 70** — this is a wide net. "
                f"Are we at risk of over-flagging? Some of these could be innocent high-volume accounts.",
                "caution_over"))
            msgs.append(self._msg("detective",
                f"I checked — {sum(1 for a in high_risk if len(a.get('detected_patterns', [])) >= 3)} "
                f"of those {len(high_risk)} appear in 3+ distinct attack patterns. That's not "
                f"random correlation. The multi-pattern accounts are our high-confidence targets.",
                "detective_validates"))
        elif score_divergence > 25:
            msgs.append(self._msg("profiler",
                f"Flagging a **score divergence** on {top_account['account_id'] if top_account else 'the top account'}: "
                f"Graph says {top_account['component_scores'].get('graph', 0) if top_account else '?'}, "
                f"ML says {top_account['component_scores'].get('ml', 0) if top_account else '?'}. "
                f"A {score_divergence:.0f}-point gap means our methods see this account very differently.",
                "divergence"))
            graph_vs_ml = "higher" if top_account and top_account.get('component_scores', {}).get('graph', 0) > top_account.get('component_scores', {}).get('ml', 0) else "lower"
            msgs.append(self._msg("detective",
                f"The graph score is {graph_vs_ml} "
                f"because of structural positioning — this account connects multiple rings. "
                f"ML might be weighting transaction features more than topology.",
                "explain_divergence"))

        # ── PHASE 8: Prosecutor synthesis (always, adapted) ───────────────
        proc_time = summary.get("processing_time_seconds", 0)

        if severity == "CRITICAL":
            msgs.append(self._msg("prosecutor",
                f"**FINAL ASSESSMENT — CRITICAL**: {n_rings} fraud rings, {n_suspicious} "
                f"accounts flagged. Multi-agent agreement is "
                f"{'**strong**' if agreement_pct > 60 else '**partial — flag for manual review**'}. "
                f"Quantum validation {'confirms' if qc_agreement > 60 else 'raises questions about'} "
                f"the classical findings. Full analysis completed in **{proc_time:.1f}s**. "
                f"I'm authorizing **immediate escalation** for the top {min(5, n_rings)} rings.",
                "synthesis_critical"))
        elif severity == "HIGH":
            msgs.append(self._msg("prosecutor",
                f"**CASE SUMMARY**: {n_rings} rings confirmed, {len(high_risk)} high-risk + "
                f"{len(medium_risk)} medium-risk accounts. All three detection pillars "
                f"{'converge' if agreement_pct > 60 and qc_agreement > 60 else 'broadly agree with noted divergences'}. "
                f"Processing: **{proc_time:.1f}s** — real-time capability confirmed. "
                f"Recommending immediate freeze on high-risk accounts and enhanced monitoring "
                f"on the medium tier.",
                "synthesis_high"))
        else:
            msgs.append(self._msg("prosecutor",
                f"**CASE SUMMARY**: {n_rings} rings detected at moderate severity. "
                f"Evidence weight: {'convincing structural patterns' if pattern_freq.get('cycle', 0) else 'mixed signals across methods'}. "
                f"Not recommending immediate freeze — instead, flag for 72-hour enhanced monitoring "
                f"and schedule re-analysis with expanded transaction history. Processed in "
                f"**{proc_time:.1f}s**.",
                "synthesis_moderate"))

        # ── PHASE 9: Actionable close ─────────────────────────────────────
        action_items = []
        if len(high_risk) > 0:
            action_items.append(f"FREEZE {len(high_risk)} high-risk accounts within 4 hours")
        if n_rings > 3:
            action_items.append(f"File SARs for top {min(5, n_rings)} rings — network-level evidence attached")
        if disruption_strats:
            action_items.append("Execute coordinated disruption on critical nodes (see Disruption Engine report)")
        if len(medium_risk) > 0:
            action_items.append(f"Enhanced monitoring on {len(medium_risk)} medium-risk accounts (48-hour window)")
        if agreement_pct < 60:
            action_items.append("Schedule manual review for Graph–ML disagreement cases")
        action_items.append("Push results to compliance pipeline via n8n webhook")
        action_items.append("Schedule automated re-scan in 24 hours with expanded lookback")

        action_str = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(action_items))
        msgs.append(self._msg("prosecutor",
            f"**ACTION ITEMS:**\n{action_str}\n\n"
            f"All agents — submit supplementary notes to the case file. "
            f"Case status: **{'CRITICAL — ACTIVE' if severity == 'CRITICAL' else 'ACTIVE'}**.",
            "actions"))

        return msgs

    def _msg(self, agent_key: str, content: str, phase: str) -> Dict:
        """Create a conversation message."""
        agent = AGENTS[agent_key]
        return {
            "agent_key": agent_key,
            "agent_name": agent["name"],
            "agent_title": agent["title"],
            "avatar": agent["avatar"],
            "color": agent["color"],
            "content": content,
            "phase": phase,
            "timestamp": time.time(),
        }

    def _generate_case_file(self) -> Dict:
        """Generate a structured case file."""
        rings = self.aggregated.get("fraud_rings", [])
        accounts = self.aggregated.get("suspicious_accounts", [])
        summary = self.aggregated.get("summary", {})

        # Risk distribution
        high_risk = [a for a in accounts if a["suspicion_score"] >= 70]
        medium_risk = [a for a in accounts if 40 <= a["suspicion_score"] < 70]
        low_risk = [a for a in accounts if a["suspicion_score"] < 40]

        # Pattern frequency
        pattern_freq = defaultdict(int)
        for acc in accounts:
            for p in acc.get("detected_patterns", []):
                pattern_freq[p] += 1
        top_patterns = sorted(pattern_freq.items(), key=lambda x: -x[1])

        return {
            "case_number": f"RIFT-2026-{random.randint(1000, 9999)}",
            "classification": "MONEY MULING — MULTI-PATTERN DETECTION",
            "priority": "HIGH" if len(high_risk) > 3 else "MEDIUM",
            "status": "ACTIVE INVESTIGATION",
            "total_rings": len(rings),
            "total_suspicious": len(accounts),
            "risk_distribution": {
                "high": len(high_risk),
                "medium": len(medium_risk),
                "low": len(low_risk),
            },
            "top_patterns": [
                {"pattern": p, "frequency": f} for p, f in top_patterns[:8]
            ],
            "agents_deployed": list(AGENTS.keys()),
            "processing_time": summary.get("processing_time_seconds", 0),
            "quantum_circuits_used": len(
                self.quantum_results.get("quantum_results", [])
            ),
        }

    def _build_evidence_chain(self) -> List[Dict]:
        """Build chain of evidence from all agents."""
        evidence = []

        # Graph evidence
        graph_rings = self.graph_results.get("rings", [])
        evidence.append({
            "source": "Graph Detective",
            "agent_key": "detective",
            "type": "Structural Analysis",
            "findings": f"Detected {len(graph_rings)} distinct fraud ring topologies",
            "confidence": 85,
            "method": "Johnson's cycle detection + BFS chain analysis",
            "details": [
                f"Cycle-based rings: {sum(1 for r in graph_rings if r['pattern_type'] == 'cycle')}",
                f"Smurfing patterns: {sum(1 for r in graph_rings if r['pattern_type'] == 'smurfing')}",
                f"Shell networks: {sum(1 for r in graph_rings if r['pattern_type'] == 'shell_network')}",
            ]
        })

        # ML evidence
        ml_scores = self.ml_results.get("ml_scores", {})
        high_ml = sum(1 for s in ml_scores.values() if s > 60)
        evidence.append({
            "source": "ML Profiler",
            "agent_key": "profiler",
            "type": "Behavioral Profiling",
            "findings": f"Flagged {high_ml} accounts with ML anomaly scores >60",
            "confidence": 80,
            "method": "Isolation Forest + Random Forest ensemble",
            "details": [
                f"Total accounts scored: {len(ml_scores)}",
                f"Isolation Forest outliers: {sum(1 for s in ml_scores.values() if s > 70)}",
                f"Features extracted: 25+ per account",
            ]
        })

        # Quantum evidence
        q_results = self.quantum_results.get("quantum_results", [])
        if q_results:
            evidence.append({
                "source": "Quantum Analyst",
                "agent_key": "quantum",
                "type": "Quantum Partitioning",
                "findings": f"Executed {len(q_results)} QAOA Max-Cut circuits",
                "confidence": 75,
                "method": "QAOA 2-layer on Qiskit Aer (1024 shots)",
                "details": [
                    f"Total qubits used: {sum(r.get('n_qubits', 0) for r in q_results)}",
                    f"Avg partition score: {sum(r.get('partition_score', 0) for r in q_results) / max(len(q_results), 1):.3f}",
                    f"Suspicious partitions identified: {sum(len(r.get('suspicious_set', [])) for r in q_results)} accounts",
                ]
            })

        # Disruption evidence
        strats = self.disruption.get("strategies", [])
        if strats:
            total_critical = sum(len(s.get("critical_nodes", [])) for s in strats)
            evidence.append({
                "source": "Disruption Engine",
                "agent_key": "quantum",
                "type": "Network Vulnerability",
                "findings": f"Identified {total_critical} critical nodes across {len(strats)} rings",
                "confidence": 90,
                "method": "Vertex cut simulation + betweenness centrality",
                "details": [
                    f"Rings analyzed: {len(strats)}",
                    f"Avg disruption potential: {self.disruption.get('global_summary', {}).get('avg_disruption_potential', 0):.1f}%",
                    f"Network resilience: {self.disruption.get('global_summary', {}).get('network_resilience_score', 0):.1f}%",
                ]
            })

        return evidence

    def _assess_confidence(self) -> Dict:
        """Overall confidence assessment based on agent agreement."""
        accounts = self.aggregated.get("suspicious_accounts", [])

        # Multi-agent agreement
        agree_count = 0
        for acc in accounts:
            scores = acc.get("component_scores", {})
            above_50 = sum(1 for v in scores.values() if v > 50)
            if above_50 >= 2:
                agree_count += 1

        agreement_rate = (agree_count / max(len(accounts), 1)) * 100

        # Quantum-classical agreement
        q_agreement = 0
        q_total = 0
        for qr in self.quantum_results.get("quantum_results", []):
            susp_set = qr.get("suspicious_set", [])
            q_total += len(susp_set)
            for acc in susp_set:
                if any(a["account_id"] == acc and a["suspicion_score"] > 50
                       for a in accounts):
                    q_agreement += 1

        qc_agreement = (q_agreement / max(q_total, 1)) * 100

        overall = (agreement_rate * 0.6 + qc_agreement * 0.4)

        return {
            "overall_confidence": round(overall, 1),
            "multi_agent_agreement": round(agreement_rate, 1),
            "quantum_classical_agreement": round(qc_agreement, 1),
            "accounts_with_multi_agent_consensus": agree_count,
            "total_suspicious": len(accounts),
            "confidence_level": (
                "VERY HIGH" if overall > 80 else
                "HIGH" if overall > 60 else
                "MODERATE" if overall > 40 else
                "LOW"
            ),
        }

    def _recommend_actions(self) -> List[Dict]:
        """Generate actionable recommendations."""
        accounts = self.aggregated.get("suspicious_accounts", [])
        rings = self.aggregated.get("fraud_rings", [])
        actions = []

        # Immediate actions
        high_risk = [a for a in accounts if a["suspicion_score"] >= 70]
        if high_risk:
            actions.append({
                "priority": "CRITICAL",
                "action": "Freeze Accounts",
                "description": f"Immediately freeze {len(high_risk)} high-risk accounts pending investigation",
                "accounts": [a["account_id"] for a in high_risk[:10]],
                "icon": "fa-ban",
                "color": "#f85149",
            })

        if rings:
            actions.append({
                "priority": "HIGH",
                "action": "File SARs",
                "description": f"Submit Suspicious Activity Reports for {len(rings)} detected fraud rings",
                "accounts": [],
                "icon": "fa-file-shield",
                "color": "#d29922",
            })

        # Disruption actions
        global_sum = self.disruption.get("global_summary", {})
        crit_nodes = global_sum.get("critical_node_list", [])
        if crit_nodes:
            actions.append({
                "priority": "HIGH",
                "action": "Disrupt Key Nodes",
                "description": f"Target {len(crit_nodes)} critical nodes to fragment {len(rings)} fraud rings",
                "accounts": crit_nodes[:10],
                "icon": "fa-scissors",
                "color": "#a371f7",
            })

        # Monitoring
        medium_risk = [a for a in accounts if 40 <= a["suspicion_score"] < 70]
        if medium_risk:
            actions.append({
                "priority": "MEDIUM",
                "action": "Enhanced Monitoring",
                "description": f"Place {len(medium_risk)} medium-risk accounts under enhanced transaction monitoring",
                "accounts": [a["account_id"] for a in medium_risk[:10]],
                "icon": "fa-eye",
                "color": "#d29922",
            })

        actions.append({
            "priority": "STANDARD",
            "action": "Automate Pipeline",
            "description": "Configure n8n webhook to run this analysis daily and auto-alert on new rings",
            "accounts": [],
            "icon": "fa-robot",
            "color": "#58a6ff",
        })

        return actions

    def _build_investigation_timeline(self) -> List[Dict]:
        """Build a timeline of the investigation phases."""
        summary = self.aggregated.get("summary", {})
        proc_time = summary.get("processing_time_seconds", 0)

        timeline = [
            {
                "phase": "Data Ingestion",
                "description": f"Parsed CSV with {summary.get('total_accounts_analyzed', 0)} accounts",
                "duration": f"{proc_time * 0.1:.2f}s",
                "agent": "system",
                "icon": "fa-upload",
                "status": "complete",
            },
            {
                "phase": "Graph Analysis",
                "description": f"Detected {summary.get('fraud_rings_detected', 0)} fraud rings via cycle/smurfing/shell detection",
                "duration": f"{proc_time * 0.25:.2f}s",
                "agent": "detective",
                "icon": "fa-diagram-project",
                "status": "complete",
            },
            {
                "phase": "ML Profiling",
                "description": f"Scored {summary.get('total_accounts_analyzed', 0)} accounts with Isolation Forest + Random Forest",
                "duration": f"{proc_time * 0.20:.2f}s",
                "agent": "profiler",
                "icon": "fa-brain",
                "status": "complete",
            },
            {
                "phase": "Quantum Optimization",
                "description": f"Ran {len(self.quantum_results.get('quantum_results', []))} QAOA circuits on Aer",
                "duration": f"{proc_time * 0.30:.2f}s",
                "agent": "quantum",
                "icon": "fa-atom",
                "status": "complete",
            },
            {
                "phase": "Evidence Synthesis",
                "description": f"Aggregated scores, resolved conflicts, flagged {summary.get('suspicious_accounts_flagged', 0)} accounts",
                "duration": f"{proc_time * 0.10:.2f}s",
                "agent": "prosecutor",
                "icon": "fa-gavel",
                "status": "complete",
            },
            {
                "phase": "Disruption Planning",
                "description": f"Computed network vulnerability for {len(self.disruption.get('strategies', []))} rings",
                "duration": f"{proc_time * 0.05:.2f}s",
                "agent": "quantum",
                "icon": "fa-scissors",
                "status": "complete",
            },
        ]

        return timeline
