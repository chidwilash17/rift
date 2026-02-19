/**
 * Vercel Serverless Proxy — forwards every /api/* hit to the ngrok backend.
 * Browser only ever talks to Vercel (trusted cert, no CORS / cert errors).
 * Set BACKEND_URL in Vercel → Settings → Environment Variables.
 */

module.exports = async function handler(req, res) {
  // ── CORS pre-flight ────────────────────────────────────────────────────
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH')
  res.setHeader('Access-Control-Allow-Headers', '*')
  if (req.method === 'OPTIONS') { res.status(200).end(); return }

  // ── Resolve backend ────────────────────────────────────────────────────
  const BACKEND = (process.env.BACKEND_URL || 'https://unheaved-elina-roughly.ngrok-free.dev').replace(/\/$/, '')
  const targetUrl = `${BACKEND}${req.url}`

  // ── Collect raw body (works for JSON + multipart) ──────────────────────
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  const rawBody = Buffer.concat(chunks)

  // ── Forward headers ────────────────────────────────────────────────────
  const skip = new Set(['host', 'connection', 'transfer-encoding'])
  const headers = {}
  for (const [k, v] of Object.entries(req.headers)) {
    if (!skip.has(k.toLowerCase())) headers[k] = v
  }
  headers['host'] = new URL(BACKEND).host
  headers['ngrok-skip-browser-warning'] = 'true'
  headers['User-Agent'] = 'rift-vercel-proxy/1.0'

  // ── Proxy ──────────────────────────────────────────────────────────────
  let upstream
  try {
    upstream = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: rawBody.length > 0 ? rawBody : undefined,
      redirect: 'manual',
    })
  } catch (err) {
    console.error('[proxy] fetch error:', err)
    return res.status(502).json({ error: 'Bad Gateway', detail: String(err) })
  }

  // ── Stream response back ───────────────────────────────────────────────
  const skipRes = new Set(['transfer-encoding', 'connection', 'keep-alive'])
  for (const [k, v] of upstream.headers.entries()) {
    if (!skipRes.has(k.toLowerCase())) res.setHeader(k, v)
  }
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.status(upstream.status)
  res.end(Buffer.from(await upstream.arrayBuffer()))
}

module.exports.config = {
  api: { bodyParser: false, responseLimit: '50mb' },
}
