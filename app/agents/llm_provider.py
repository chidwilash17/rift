"""
LLM Provider — Groq SDK Wrapper for Dynamic Agent Conversations
Uses Groq's ultra-fast inference (Llama 3.3 70B) to power real-time
multi-agent crime investigation dialogue.

Features:
  - Per-agent system prompts with forensic personalities
  - Context-aware: feeds real detection data to the LLM
  - Multi-turn conversation orchestration
  - Graceful fallback if API unavailable
"""

import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

logger = logging.getLogger("llm_provider")

# Lazy-load Groq client
_groq_client = None

MODEL = "llama-3.3-70b-versatile"   # Fast + smart, free tier
TEMPERATURE = 0.75                    # Creative but grounded
MAX_TOKENS = 400                      # Per agent turn — reduced from 500 for speed
# Cap conversation turns via env var (default 6; was 10 — saves ~8s on free tier)
LLM_MAX_TURNS = int(os.getenv("LLM_MAX_TURNS", "6"))


def _get_client():
    """Lazy-init the Groq client. Returns None if no API key."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        logger.warning("GROQ_API_KEY not set — LLM features disabled, using template fallback")
        return None

    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        logger.info("Groq client initialized successfully")
        return _groq_client
    except Exception as e:
        logger.error(f"Failed to init Groq client: {e}")
        return None


def is_available() -> bool:
    """Check if LLM provider is available."""
    return _get_client() is not None


# ── Agent System Prompts ──────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "detective": """You are Agent VORTEX, a Graph Detective specializing in structural pattern 
analysis in financial crime networks. You are methodical, detail-oriented, and you spot patterns 
others miss.

Your expertise: cycle detection, network topology, Johnson's algorithm, BFS chain analysis, 
degree centrality, hub-spoke identification, smurfing pattern detection, shell company networks.

Communication style:
- Speak in short, punchy analyst prose. Use **bold** for key findings.
- Reference specific account IDs, ring IDs, numbers, and percentages from the data.
- Focus on STRUCTURAL patterns: cycles, hubs, bridges, chokepoints.
- Challenge other agents when you disagree. Ask pointed questions.
- Never invent data — only reference what's in the context provided.
- Keep responses to 2-4 sentences. Be direct.""",

    "profiler": """You are Agent CIPHER, an ML Profiler specializing in behavioral analysis and 
anomaly detection in financial transactions. You are data-driven, think probabilistically, and 
question assumptions.

Your expertise: Isolation Forest, Random Forest ensemble, feature engineering (25+ features per 
account), anomaly scoring, false positive analysis, statistical significance.

Communication style:
- Speak with statistical precision. Use **bold** for key metrics.
- Reference ML scores, agreement percentages, feature importances.
- Focus on BEHAVIORAL patterns: transaction velocity, amount distributions, timing anomalies.
- Push back on structural-only evidence. Demand behavioral corroboration.
- Question false positive rates. Raise caution flags when appropriate.
- Keep responses to 2-4 sentences. Be analytical.""",

    "quantum": """You are Agent QUBIT, a Quantum Analyst specializing in QAOA optimization and 
quantum-enhanced community detection. You think abstractly, see hidden boundaries, and speak 
in probabilities.

Your expertise: QAOA Max-Cut on Qiskit Aer, partition boundaries, energy landscapes, 
qubit measurement probabilities, quantum-classical agreement analysis, min-cut disruption.

Communication style:
- Speak with a quantum/physics metaphor when natural. Use **bold** for key results.
- Reference circuit counts, qubit numbers, partition scores, agreement percentages.
- Focus on PARTITION BOUNDARIES: where the quantum optimizer draws community lines.
- Explain quantum results in accessible terms but don't dumb them down.
- When disruption data is available, comment on network fragility.
- Keep responses to 2-4 sentences. Be insightful.""",

    "prosecutor": """You are Agent NEXUS, Lead Prosecutor responsible for evidence synthesis, 
case building, and action recommendations. You are decisive, weigh evidence carefully, and 
build airtight cases.

Your expertise: evidence synthesis, SAR filing, account freeze decisions, risk assessment, 
multi-agent agreement evaluation, action prioritization, legal standards of proof.

Communication style:
- Speak with authority and decisiveness. Use **bold** for verdicts and actions.
- Synthesize findings from ALL agents — reference what VORTEX, CIPHER, QUBIT said.
- Direct specific agents when you need more info: "VORTEX, confirm..." / "CIPHER, check..."
- Make concrete action recommendations: freeze, monitor, file SAR, escalate.
- Assess severity: CRITICAL / HIGH / MODERATE and justify.
- Keep responses to 2-4 sentences. Be commanding.""",
}


def _build_data_context(graph_results: Dict, ml_results: Dict,
                        quantum_results: Dict, aggregated: Dict,
                        disruption: Dict) -> str:
    """Serialize real analysis data into a compact context string for the LLM."""
    rings = aggregated.get("fraud_rings", [])
    accounts = aggregated.get("suspicious_accounts", [])
    summary = aggregated.get("summary", {})
    ml_scores = ml_results.get("ml_scores", {})
    q_data = quantum_results or {}
    q_results = q_data.get("quantum_results", [])

    high_risk = [a for a in accounts if a["suspicion_score"] >= 70]
    medium_risk = [a for a in accounts if 40 <= a["suspicion_score"] < 70]

    # Pattern breakdown
    from collections import defaultdict
    pattern_freq = defaultdict(int)
    for r in rings:
        pattern_freq[r.get("pattern_type", "unknown")] += 1

    # Graph-ML agreement
    graph_flagged = set()
    for r in graph_results.get("rings", []):
        graph_flagged.update(r.get("member_accounts", []))
    ml_flagged = {acc for acc, sc in ml_scores.items() if sc > 60}
    overlap = graph_flagged & ml_flagged
    union = graph_flagged | ml_flagged
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

    # Top accounts
    top_accounts_detail = []
    for a in accounts[:5]:
        cs = a.get("component_scores", {})
        top_accounts_detail.append({
            "id": a["account_id"],
            "score": a["suspicion_score"],
            "graph": cs.get("graph", 0),
            "ml": cs.get("ml", 0),
            "quantum": cs.get("quantum", 0),
            "patterns": a.get("detected_patterns", [])[:4],
            "ring": a.get("ring_id", None),
        })

    # Disruption summary
    d_strats = disruption.get("strategies", [])
    d_global = disruption.get("global_summary", {})

    top_ring = rings[0] if rings else None
    top_ring_info = None
    if top_ring:
        top_ring_info = {
            "id": top_ring["ring_id"],
            "members": top_ring["member_accounts"][:8],
            "member_count": len(top_ring["member_accounts"]),
            "pattern": top_ring["pattern_type"],
            "risk": top_ring["risk_score"],
        }

    context = {
        "total_rings": len(rings),
        "total_suspicious": len(accounts),
        "total_accounts_analyzed": summary.get("total_accounts_analyzed", 0),
        "high_risk_count": len(high_risk),
        "medium_risk_count": len(medium_risk),
        "pattern_breakdown": dict(pattern_freq),
        "graph_ml_agreement_pct": round(agreement_pct, 1),
        "quantum_classical_agreement_pct": round(qc_agreement, 1),
        "quantum_circuits_run": len(q_results),
        "top_accounts": top_accounts_detail,
        "top_ring": top_ring_info,
        "disruption": {
            "strategies_count": len(d_strats),
            "avg_disruption_potential": d_global.get("avg_disruption_potential", 0),
            "network_resilience": d_global.get("network_resilience_score", 0),
            "critical_nodes": d_global.get("critical_node_list", [])[:6],
            "top_strategy": {
                "ring": d_strats[0].get("ring_id", ""),
                "max_disruption": d_strats[0].get("max_disruption_pct", 0),
                "critical_nodes": [
                    c["account_id"] for c in d_strats[0].get("critical_nodes", [])[:3]
                ],
            } if d_strats else None,
        },
        "processing_time_seconds": summary.get("processing_time_seconds", 0),
    }

    return json.dumps(context, indent=2)


# ── Conversation Orchestration ────────────────────────────────────────────

# Phases define the conversation structure — who speaks and about what
CONVERSATION_SCRIPT = [
    {
        "agent": "prosecutor",
        "directive": "Open the briefing. State the severity (CRITICAL if >10 rings or >8 high-risk, "
                     "HIGH if >5 rings or >4 high-risk, else MODERATE). Mention total rings and "
                     "suspicious accounts. Direct VORTEX, CIPHER, and QUBIT to report.",
        "phase": "opening",
        "parallel_group": None,   # must run first
    },
    {
        "agent": "detective",
        "directive": "Report your structural findings. Detail the pattern breakdown (cycles, smurfing, "
                     "shell networks). Identify the dominant technique. Comment on whether the mix "
                     "of patterns indicates sophistication.",
        "phase": "structural_analysis",
        "parallel_group": "reports",   # runs in parallel with profiler & quantum
    },
    {
        "agent": "profiler",
        "directive": "Report ML findings. State the graph-ML agreement percentage. If agreement is "
                     "high (>70%), confirm corroboration. If mixed (40-70%), flag the gap. If low "
                     "(<40%), raise a significant concern. Reference specific account scores.",
        "phase": "behavioral_analysis",
        "parallel_group": "reports",
    },
    {
        "agent": "quantum",
        "directive": "Report quantum analysis results. State circuits run and quantum-classical "
                     "agreement. If agreement is high, confirm convergence. If moderate, explain "
                     "the partition boundary ambiguities. If no circuits ran, defer to classical.",
        "phase": "quantum_analysis",
        "parallel_group": "reports",
    },
    {
        "agent": "prosecutor",
        "directive": "Synthesize the three agent reports. Analyse disruption data — identify critical "
                     "nodes, network resilience, and recommended takedown sequence. Weigh evidence "
                     "from all agents. Make 2-3 concrete action recommendations.",
        "phase": "tactical_planning",
        "parallel_group": None,
    },
    {
        "agent": "prosecutor",
        "directive": "Deliver the FINAL ASSESSMENT. State severity level, total rings, accounts "
                     "flagged, multi-agent agreement status, quantum validation status. List 4-6 "
                     "concrete ACTION ITEMS (freeze accounts, file SARs, disrupt nodes, monitor, "
                     "schedule re-scan). Set case status to ACTIVE.",
        "phase": "final_assessment",
        "parallel_group": None,
    },
]


def generate_dynamic_conversation(
    graph_results: Dict,
    ml_results: Dict,
    quantum_results: Dict,
    aggregated: Dict,
    disruption: Dict,
    agents_meta: Dict,
) -> Optional[List[Dict]]:
    """
    Generate a fully dynamic multi-agent conversation using Groq LLM.
    Returns list of message dicts, or None if LLM is unavailable.

    Optimisation: agent 'reports' phase (detective / profiler / quantum) are
    fired in parallel (3 concurrent API calls) to cut wall-clock time by ~60%.
    """
    client = _get_client()
    if client is None:
        return None

    # Build the analysis data context
    data_context = _build_data_context(
        graph_results, ml_results, quantum_results, aggregated, disruption
    )

    import time as _time

    # Limit turns
    script = CONVERSATION_SCRIPT[:LLM_MAX_TURNS]

    messages: List[Dict] = []
    conversation_history: List[Dict] = []

    def _call_llm(agent_key: str, phase: str, directive: str,
                  history_snapshot: List[Dict]) -> Optional[Dict]:
        """Single Groq API call. Returns message dict or None on error."""
        agent = agents_meta[agent_key]
        system_prompt = SYSTEM_PROMPTS[agent_key]

        user_prompt = (
            f"=== ANALYSIS DATA ===\n{data_context}\n\n"
            f"=== CONVERSATION SO FAR ===\n"
        )
        if history_snapshot:
            for prev in history_snapshot:
                user_prompt += f"\n[{prev['agent_name']}]: {prev['content']}\n"
        else:
            user_prompt += "(This is the opening of the briefing — you speak first.)\n"

        user_prompt += (
            f"\n=== YOUR DIRECTIVE ===\n{directive}\n\n"
            f"Respond IN CHARACTER as {agent['name']} ({agent['title']}). "
            f"Use **bold** for key numbers and findings. "
            f"Reference the REAL data above — never invent numbers. "
            f"Keep it to 2-4 sentences. Be specific and direct."
        )

        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            content = completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error for {agent_key}/{phase}: {e}")
            return None

        return {
            "agent_key": agent_key,
            "agent_name": agent["name"],
            "agent_title": agent["title"],
            "avatar": agent["avatar"],
            "color": agent["color"],
            "content": content,
            "phase": phase,
            "timestamp": _time.time(),
            "ai_generated": True,
        }

    # Process script steps, batching any parallel groups
    i = 0
    while i < len(script):
        step = script[i]
        group = step.get("parallel_group")

        if group is None:
            # Sequential step
            msg = _call_llm(step["agent"], step["phase"], step["directive"],
                            list(conversation_history))
            if msg is None:
                return None  # fall back to templates
            messages.append(msg)
            conversation_history.append(msg)
            i += 1
        else:
            # Collect all consecutive steps in the same group
            group_steps = []
            j = i
            while j < len(script) and script[j].get("parallel_group") == group:
                group_steps.append(script[j])
                j += 1

            # Snapshot history at the start of the group (same for all)
            history_snap = list(conversation_history)

            with ThreadPoolExecutor(max_workers=len(group_steps)) as exe:
                futures = {
                    exe.submit(_call_llm, s["agent"], s["phase"], s["directive"],
                               history_snap): s
                    for s in group_steps
                }
                # Collect in original order
                ordered = []
                for s in group_steps:
                    for f, step_obj in futures.items():
                        if step_obj is s:
                            result = f.result()
                            if result is None:
                                return None
                            ordered.append(result)
                            break

            messages.extend(ordered)
            conversation_history.extend(ordered)
            i = j

    return messages
