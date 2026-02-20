"""
Money Muling Detection Engine — FastAPI Application
RIFT 2026 Hackathon | Graph Theory Track

Multi-Agent Hybrid Classical-Quantum Financial Forensics Engine.
"""

import os
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from typing import Dict

# Production tuning env vars
MAX_GRAPH_VIZ_NODES = int(os.getenv("MAX_GRAPH_VIZ_NODES", "800"))   # cap nodes in response
MAX_GRAPH_VIZ_EDGES = int(os.getenv("MAX_GRAPH_VIZ_EDGES", "2000"))  # cap edges in response

# Load .env before any agent imports (so GROQ_API_KEY is available)
load_dotenv(Path(__file__).parent.parent / ".env")

from app.utils.csv_parser import parse_csv
from app.agents.graph_agent import GraphAgent
from app.agents.ml_agent import MLAgent
from app.agents.quantum_agent import QuantumAgent
from app.agents.aggregator import AggregatorAgent
from app.agents.disruption_engine import DisruptionEngine
from app.agents.ibm_quantum_agent import IBMQuantumAgent
from app.agents.crime_team import CrimeTeam
from app.agents.whatif_simulator import WhatIfSimulator

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("muling_engine")

# App
app = FastAPI(
    title="Money Muling Detection Engine",
    description="Hybrid Classical-ML-Quantum Financial Forensics System",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files — prefer React build, fallback to legacy
REACT_DIST = Path(__file__).parent.parent / "frontend" / "dist"
STATIC_DIR = Path(__file__).parent / "static"

if REACT_DIST.exists() and (REACT_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(REACT_DIST / "assets")), name="assets")
elif STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Store latest results in memory (for demo purposes)
latest_results = {}
latest_graph = None
latest_df = None
latest_intermediate = {}  # Store intermediate agent results
@app.head("/", include_in_schema=False)
async def homepage_head():
    """HEAD / — satisfies Render's port-detection health probe."""
    return JSONResponse(content=None, status_code=200)


@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Serve the main application page (React build or legacy).
    When deployed as a pure API backend (e.g. Render + Vercel split),
    no static directory exists — return a friendly JSON status instead.
    """
    if REACT_DIST.exists():
        index_path = REACT_DIST / "index.html"
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        index_path = STATIC_DIR / "index.html"
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    # Pure API mode — no frontend bundled on this server
    return JSONResponse(content={
        "service": "Money Muling Detection Engine API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    })


@app.post("/api/analyze")
async def analyze_csv(file: UploadFile = File(...)):
    """
    Main analysis endpoint.
    Accepts CSV upload, runs all 4 agents, returns unified results.
    """
    global latest_results, latest_graph, latest_df, latest_intermediate
    start_time = time.time()
    
    try:
        # ── Step 1: Read & parse CSV ──
        logger.info(f"Received file: {file.filename}")
        content = await file.read()
        csv_text = content.decode("utf-8")
        
        df, G, metadata = parse_csv(csv_text)
        logger.info(f"Parsed {metadata['total_transactions']} transactions, "
                     f"{metadata['total_accounts']} accounts")
        
        # Store for What-If simulator
        latest_graph = G
        latest_df = df
        
        # ── Steps 2-4: Run Agents 1-3 in PARALLEL ──
        logger.info("Running GraphAgent, MLAgent, QuantumAgent in parallel...")
        graph_results = None
        ml_results = None
        quantum_results = None

        def _run_graph():
            ga = GraphAgent(G, df)
            return ga.run()

        def _run_ml():
            ma = MLAgent(G, df)
            return ma.run()

        # Placeholder so quantum can reference graph rings after parallel step
        _graph_tmp = {"rings": []}

        with ThreadPoolExecutor(max_workers=3) as exe:
            f_graph = exe.submit(_run_graph)
            f_ml    = exe.submit(_run_ml)
            # Quantum needs rings — submit with empty rings first, update after
            f_quantum = exe.submit(lambda: QuantumAgent(G, []).run())

            graph_results  = f_graph.result()
            ml_results     = f_ml.result()
            quantum_results = f_quantum.result()

        # Re-run quantum scoring with actual rings (heuristic pass only, fast)
        if graph_results.get("rings"):
            logger.info("Enriching quantum scores with detected rings (fast-pass)...")
            qa2 = QuantumAgent(G, graph_results["rings"])
            # Only do the heuristic re-score (no new circuits) - use result directly
            # Override quantum scores for rings that weren't in the parallel run
            q2 = qa2.run()
            # Merge: prefer full circuit results from parallel run; add heuristic-only entries
            existing_ring_ids = {r["ring_id"] for r in quantum_results.get("quantum_results", [])}
            for qr in q2.get("quantum_results", []):
                if qr["ring_id"] not in existing_ring_ids and qr.get("n_qubits", 0) == 0:
                    quantum_results["quantum_results"].append(qr)
                    existing_ring_ids.add(qr["ring_id"])
            # Merge quantum scores
            for acc, sc in q2.get("quantum_scores", {}).items():
                if acc not in quantum_results.get("quantum_scores", {}):
                    quantum_results.setdefault("quantum_scores", {})[acc] = sc

        logger.info(f"Graph Agent found {len(graph_results['rings'])} rings, "
                     f"{len(graph_results['suspicious_accounts'])} suspicious accounts")
        logger.info(f"ML Agent scored {len(ml_results.get('ml_scores', {}))} accounts")
        q_avail = quantum_results.get("quantum_available", False)
        logger.info(f"Quantum Agent: available={q_avail}")
        
        # ── Step 5: Run Agent 4 — Aggregator ──
        logger.info("Running Aggregator Agent...")
        aggregator = AggregatorAgent(
            graph_results=graph_results,
            ml_results=ml_results,
            quantum_results=quantum_results,
            total_accounts=metadata["total_accounts"],
            processing_start_time=start_time
        )
        final_output = aggregator.run()
        
        # ── Step 6: Run Disruption Engine ──
        logger.info("Running Disruption Engine...")
        disruption = DisruptionEngine(
            G=G,
            fraud_rings=final_output["fraud_rings"],
            suspicious_accounts=final_output["suspicious_accounts"],
            quantum_results=quantum_results,
        )
        disruption_results = disruption.run()
        final_output["disruption"] = disruption_results
        logger.info(f"Disruption Engine: {len(disruption_results['strategies'])} strategies, "
                     f"{disruption_results['global_summary']['unique_critical_nodes']} critical nodes")
        
        # ── Step 7: Run Crime Team ──
        logger.info("Running Crime Team...")
        crime_team = CrimeTeam(
            graph_results=graph_results,
            ml_results=ml_results,
            quantum_results=quantum_results,
            aggregated=final_output,
            disruption=disruption_results,
        )
        crime_team_results = crime_team.run()
        final_output["crime_team"] = crime_team_results
        logger.info("Crime Team report generated")
        
        # ── Step 8: Run IBM Quantum on top ring (async, non-blocking) ──
        ibm_result = None
        top_rings = final_output.get("fraud_rings", [])
        ibm_token = os.getenv("IBM_QUANTUM_TOKEN", "").strip()
        if top_rings and ibm_token:
            logger.info("Running IBM Quantum agent on top ring...")
            try:
                ibm_agent = IBMQuantumAgent(G, top_rings[0])
                ibm_result = ibm_agent.run()
                hw = ibm_result.get("hardware", "none")
                logger.info(f"IBM Quantum: hardware={hw}, "
                            f"backend={ibm_result.get('backend')}, "
                            f"advantage={ibm_result.get('quantum_advantage_pct')}%")
            except Exception as e:
                logger.error(f"IBM Quantum step failed: {e}")
        elif top_rings and not ibm_token:
            logger.info("IBM_QUANTUM_TOKEN not set — skipping real hardware run")
        final_output["ibm_quantum"] = ibm_result

        # ── Step 9: Build graph data for visualization ──
        graph_viz_data = _build_graph_viz_data(G, final_output)
        final_output["graph_data"] = graph_viz_data
        final_output["metadata"] = metadata
        
        # Store for download
        latest_results = final_output
        
        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Analysis complete in {elapsed}s — "
                     f"{final_output['summary']['suspicious_accounts_flagged']} suspicious, "
                     f"{final_output['summary']['fraud_rings_detected']} rings")
        
        return JSONResponse(content=final_output)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.get("/api/download")
async def download_json():
    """Download the latest analysis results as JSON file."""
    if not latest_results:
        raise HTTPException(status_code=404, detail="No analysis results available. Upload a CSV first.")
    
    # Build clean output matching exact required format
    clean_output = {
        "suspicious_accounts": [
            {
                "account_id": sa["account_id"],
                "suspicion_score": sa["suspicion_score"],
                "detected_patterns": sa["detected_patterns"],
                "ring_id": sa["ring_id"]
            }
            for sa in latest_results.get("suspicious_accounts", [])
        ],
        "fraud_rings": [
            {
                "ring_id": ring["ring_id"],
                "member_accounts": ring["member_accounts"],
                "pattern_type": ring["pattern_type"],
                "risk_score": ring["risk_score"]
            }
            for ring in latest_results.get("fraud_rings", [])
        ],
        "summary": {
            "total_accounts_analyzed": latest_results["summary"]["total_accounts_analyzed"],
            "suspicious_accounts_flagged": latest_results["summary"]["suspicious_accounts_flagged"],
            "fraud_rings_detected": latest_results["summary"]["fraud_rings_detected"],
            "processing_time_seconds": latest_results["summary"]["processing_time_seconds"]
        }
    }
    
    return JSONResponse(
        content=clean_output,
        headers={
            "Content-Disposition": "attachment; filename=fraud_analysis_results.json"
        }
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    ibm_token_set = bool(os.getenv("IBM_QUANTUM_TOKEN", "").strip())
    return {
        "status": "healthy",
        "engine": "Money Muling Detection Engine v1.0",
        "ibm_quantum_configured": ibm_token_set,
    }


@app.post("/api/quantum/ibm")
async def run_ibm_quantum(request: Request):
    """
    On-demand IBM Quantum run on a specific ring.
    Body: { "ring_id": "RING_001" }   (optional — defaults to top ring)
    Returns real quantum hardware results or simulator fallback.
    """
    if not latest_results:
        raise HTTPException(status_code=400, detail="No analysis results. Upload a CSV first.")

    body = await request.json()
    ring_id = body.get("ring_id")
    rings = latest_results.get("fraud_rings", [])

    if not rings:
        raise HTTPException(status_code=400, detail="No fraud rings detected in last analysis.")

    # Find requested ring or use top ring
    target_ring = next((r for r in rings if r["ring_id"] == ring_id), rings[0])

    ibm_agent = IBMQuantumAgent(latest_graph, target_ring)
    result = ibm_agent.run()
    return JSONResponse(content=result)


@app.post("/api/webhook/n8n")
async def n8n_webhook(request: Request):
    """
    Webhook endpoint for n8n integration.
    n8n can trigger analysis and receive results.
    """
    body = await request.json()
    action = body.get("action", "check_status")
    
    if action == "get_results" and latest_results:
        return JSONResponse(content={
            "status": "success",
            "summary": latest_results.get("summary", {}),
            "suspicious_accounts": latest_results.get("suspicious_accounts", []),
            "fraud_rings": latest_results.get("fraud_rings", []),
        })
    
    return JSONResponse(content={
        "status": "received",
        "message": "n8n webhook processed",
        "action": action,
        "latest_results_available": bool(latest_results),
        "summary": latest_results.get("summary") if latest_results else None
    })


@app.get("/n8n_workflow.json")
async def get_n8n_workflow():
    """Serve the n8n importable workflow JSON."""
    workflow_path = Path(__file__).parent.parent / "n8n_workflow.json"
    if not workflow_path.exists():
        raise HTTPException(status_code=404, detail="Workflow file not found")
    content = json.loads(workflow_path.read_text(encoding="utf-8"))
    return JSONResponse(content=content, headers={
        "Content-Disposition": "attachment; filename=mulingnet_n8n_workflow.json"
    })


@app.post("/api/whatif")
async def whatif_simulate(request: Request):
    """
    What-If Simulator endpoint.
    Accepts a list of nodes to remove and returns impact analysis.
    """
    if not latest_graph or not latest_results:
        raise HTTPException(status_code=400, detail="No analysis results. Upload a CSV first.")
    
    body = await request.json()
    nodes_to_remove = body.get("nodes", [])
    
    if not nodes_to_remove:
        raise HTTPException(status_code=400, detail="No nodes specified. Provide 'nodes' array.")
    
    simulator = WhatIfSimulator(
        G=latest_graph,
        df=latest_df,
        fraud_rings=latest_results.get("fraud_rings", []),
        suspicious_accounts=latest_results.get("suspicious_accounts", []),
    )
    
    result = simulator.simulate(nodes_to_remove)
    return JSONResponse(content=result)
    
def _build_graph_viz_data(G, results: Dict) -> Dict:
    """Build graph data in vis.js compatible format.

    For large graphs (10K+ transactions) we cap the visualisation to
    MAX_GRAPH_VIZ_NODES / MAX_GRAPH_VIZ_EDGES to avoid generating a
    multi-megabyte JSON payload that would time-out on Render free tier.

    Priority: suspicious nodes > their direct neighbours > benign nodes.
    """
    suspicious_ids = {sa["account_id"] for sa in results.get("suspicious_accounts", [])}
    suspicious_map = {
        sa["account_id"]: sa for sa in results.get("suspicious_accounts", [])
    }
    
    # Ring membership lookup
    ring_colors = {}
    color_palette = [
        "#ff4444", "#ff8800", "#ffcc00", "#44ff44", 
        "#4488ff", "#aa44ff", "#ff44aa", "#44ffcc",
        "#ff6644", "#66ccff", "#cc44ff", "#ffaa44"
    ]
    for idx, ring in enumerate(results.get("fraud_rings", [])):
        color = color_palette[idx % len(color_palette)]
        for member in ring["member_accounts"]:
            ring_colors[member] = color

    # ── Build the node subset (suspicious first, then neighbours) ──
    include_nodes: set = set(suspicious_ids)
    # Add direct neighbours of suspicious nodes until cap reached
    if len(include_nodes) < MAX_GRAPH_VIZ_NODES:
        for node in list(suspicious_ids):
            if len(include_nodes) >= MAX_GRAPH_VIZ_NODES:
                break
            for nb in list(G.predecessors(node)) + list(G.successors(node)):
                include_nodes.add(nb)
                if len(include_nodes) >= MAX_GRAPH_VIZ_NODES:
                    break

    # If still under cap, fill with remaining nodes
    if len(include_nodes) < MAX_GRAPH_VIZ_NODES:
        for node in G.nodes():
            if node not in include_nodes:
                include_nodes.add(node)
            if len(include_nodes) >= MAX_GRAPH_VIZ_NODES:
                break

    nodes = []
    for node in include_nodes:
        is_suspicious = node in suspicious_ids
        node_data = G.nodes[node]
        
        sa = suspicious_map.get(node, {})
        score = sa.get("suspicion_score", 0)
        patterns = sa.get("detected_patterns", [])
        ring_id = sa.get("ring_id", None)
        
        # Node styling based on suspicion
        if is_suspicious and score >= 70:
            color = ring_colors.get(node, "#ff2222")
            size = 25 + score * 0.3
            border_width = 4
            shape = "dot"
        elif is_suspicious and score >= 40:
            color = ring_colors.get(node, "#ff8800")
            size = 20 + score * 0.2
            border_width = 3
            shape = "dot"
        elif is_suspicious:
            color = ring_colors.get(node, "#ffcc00")
            size = 18
            border_width = 2
            shape = "dot"
        else:
            color = "#336699"
            size = 12
            border_width = 1
            shape = "dot"
        
        nodes.append({
            "id": node,
            "label": node,
            "color": {
                "background": color,
                "border": "#ffffff" if is_suspicious else "#224466",
                "highlight": {"background": "#ffffff", "border": color}
            },
            "size": size,
            "borderWidth": border_width,
            "shape": shape,
            "title": (
                f"<b>{node}</b><br>"
                f"Score: {score}<br>"
                f"Patterns: {', '.join(patterns) if patterns else 'None'}<br>"
                f"Ring: {ring_id or 'N/A'}<br>"
                f"Sent: {node_data.get('total_sent', 0):.2f}<br>"
                f"Received: {node_data.get('total_received', 0):.2f}<br>"
                f"Transactions: {node_data.get('tx_count_total', 0)}"
            ),
            "suspicious": is_suspicious,
            "score": score,
            "patterns": patterns,
            "ring_id": ring_id
        })
    
    edges = []
    edge_count = 0
    for u, v, data in G.edges(data=True):
        if u not in include_nodes or v not in include_nodes:
            continue
        if edge_count >= MAX_GRAPH_VIZ_EDGES:
            break
        is_suspicious_edge = u in suspicious_ids and v in suspicious_ids
        amount = data.get("total_amount", 0)
        tx_count = data.get("tx_count", 0)
        
        edges.append({
            "from": u,
            "to": v,
            "arrows": "to",
            "label": f"${amount:,.0f}" if amount > 0 else "",
            "title": f"{u} → {v}<br>Amount: ${amount:,.2f}<br>Transactions: {tx_count}",
            "color": {
                "color": "#ff4444" if is_suspicious_edge else "#556677",
                "opacity": 0.8 if is_suspicious_edge else 0.4
            },
            "width": max(1, min(5, amount / 5000)) if is_suspicious_edge else 1,
            "smooth": {"type": "curvedCW", "roundness": 0.2}
        })
        edge_count += 1
    
    total_nodes = len(G.nodes())
    total_edges = G.number_of_edges()
    return {
        "nodes": nodes,
        "edges": edges,
        "truncated": total_nodes > MAX_GRAPH_VIZ_NODES or total_edges > MAX_GRAPH_VIZ_EDGES,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
    }


