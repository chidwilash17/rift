"""
PythonAnywhere WSGI entry point
================================
PythonAnywhere serves Python web apps via Apache + mod_wsgi (WSGI protocol).
FastAPI is an ASGI framework, so we use `a2wsgi` to bridge the gap.

Setup steps on PythonAnywhere:
  1. Upload / clone this repo to /home/<username>/rift
  2. Create a virtualenv (Python 3.11) and install requirements.txt
     (also install: pip install a2wsgi)
  3. Go to Web tab → Add new web app → Manual configuration → Python 3.11
  4. Set "Source code" to /home/<username>/rift
  5. Set "WSGI configuration file" path, then paste this file's contents there
     (or just point it at this file)
  6. Set working directory to /home/<username>/rift
  7. Add environment variables in the Web tab → Env vars section:
       GROQ_API_KEY=<your key>
       MAX_QUANTUM_RINGS=3
       MAX_GRAPH_VIZ_NODES=600
       MAX_GRAPH_VIZ_EDGES=1500
       LLM_MAX_TURNS=6
  8. Reload the web app

NOTE: PythonAnywhere FREE tier blocks outbound HTTP to non-whitelisted domains.
      Groq API (api.groq.com) works on the PAID tier ("Hacker" plan, $5/mo).
      On the free tier the LLM crime-team falls back to the template engine.
      Qiskit simulation also uses significant RAM — recommend Hacker plan (3 GB RAM).
"""

import sys
import os

# ── Make sure the project root is on the Python path ──────────────────────
# Change this path to match your PythonAnywhere username / folder.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Load .env if present ───────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ── Wrap FastAPI (ASGI) with a2wsgi so Apache mod_wsgi can call it ─────────
from a2wsgi import ASGIMiddleware
from app.main import app as _asgi_app

# `application` is the name mod_wsgi looks for
application = ASGIMiddleware(_asgi_app)
