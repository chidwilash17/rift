/**
 * Vercel Serverless Proxy
 * =======================
 * Catches every /api/* request made to the Vercel-hosted frontend and
 * forwards it transparently to the real backend (ngrok / Render / local).
 *
 * Why this exists:
 *   • Browser never talks to ngrok directly → no mixed-cert / CORS block
 *   • ngrok "browser warning" page is bypassed via the skip header
 *   • Works for JSON endpoints AND multipart file uploads (raw body streaming)
 *
 * Configuration:
 *   Set BACKEND_URL in the Vercel project dashboard → Environment Variables
 *   e.g.  BACKEND_URL = https://unheaved-elina-roughly.ngrok-free.dev
 *
 *   For local Vite dev server, the vite.config.js proxy to localhost:8000
 *   handles /api/* so this file is never used locally.
 */

export const config = {
  api: {
    bodyParser: false,      // stream raw bytes — needed for multipart/file uploads
    responseLimit: '50mb',  // allow large CSV uploads & JSON responses
  },
}

export default async function handler(req, res) {
  // ── 1. Resolve backend origin ──────────────────────────────────────────
  const BACKEND = (process.env.BACKEND_URL || 'https://unheaved-elina-roughly.ngrok-free.dev').replace(/\/$/, '')

  // ── 2. Reconstruct the target URL ─────────────────────────────────────
  //   req.url is the full path as seen by Vercel, e.g. /api/analyze?foo=bar
  //   We simply append it to the backend origin.
  const targetUrl = `${BACKEND}${req.url}`

  // ── 3. Collect raw request body (works for JSON + multipart) ──────────
  const bodyChunks = []
  for await (const chunk of req) {
    bodyChunks.push(chunk)
  }
  const rawBody = Buffer.concat(bodyChunks)

  // ── 4. Build forwarded headers ─────────────────────────────────────────
  const forwardHeaders = {}
  const skipRequestHeaders = new Set(['host', 'connection', 'transfer-encoding'])
  for (const [key, value] of Object.entries(req.headers)) {
    if (!skipRequestHeaders.has(key.toLowerCase())) {
      forwardHeaders[key] = value
    }
  }
  // Override host to match the backend
  forwardHeaders['host'] = new URL(BACKEND).host
  // Bypass ngrok's browser-interstitial page for API calls
  forwardHeaders['ngrok-skip-browser-warning'] = 'true'
  forwardHeaders['User-Agent'] = 'rift-vercel-proxy/1.0'

  // ── 5. Forward the request ─────────────────────────────────────────────
  let upstream
  try {
    upstream = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body: rawBody.length > 0 ? rawBody : undefined,
      // Don't follow redirects — pass them through to the browser
      redirect: 'manual',
    })
  } catch (err) {
    console.error('[proxy] fetch error:', err)
    res.status(502).json({
      error: 'Bad Gateway',
      detail: `Proxy could not reach backend at ${BACKEND}`,
      message: String(err),
    })
    return
  }

  // ── 6. Stream the response back ────────────────────────────────────────
  const skipResponseHeaders = new Set(['transfer-encoding', 'connection', 'keep-alive'])
  for (const [key, value] of upstream.headers.entries()) {
    if (!skipResponseHeaders.has(key.toLowerCase())) {
      res.setHeader(key, value)
    }
  }
  // Allow the Vercel frontend origin to read the response
  res.setHeader('Access-Control-Allow-Origin', '*')

  res.status(upstream.status)

  const responseBuffer = Buffer.from(await upstream.arrayBuffer())
  res.end(responseBuffer)
}
