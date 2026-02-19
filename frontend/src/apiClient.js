/**
 * API routing via Vercel proxy.
 *
 * In production (Vercel): all /api/* requests are intercepted by
 *   frontend/api/[...path].js which forwards them to the ngrok/Render backend.
 *   The browser only ever talks to Vercel (trusted cert, no CORS issues).
 *
 * In local dev (Vite): vite.config.js proxies /api/* to localhost:8000
 *   so this file doesn't need to change between environments.
 *
 * To point to a different backend, set BACKEND_URL in the Vercel dashboard:
 *   Project → Settings → Environment Variables → BACKEND_URL
 *   e.g.  https://unheaved-elina-roughly.ngrok-free.dev
 *         https://rift-a9qf.onrender.com
 */

// Empty BASE = relative paths → same-origin on Vercel, proxied by Vite locally
const BASE = ''

/**
 * Prepend the backend base URL to a path.
 * @param {string} path  Must start with '/'
 * @returns {string}
 */
export function apiUrl(path) {
    return `${BASE}${path}`
}

/**
 * Ping the backend health endpoint to warm up the instance.
 * PythonAnywhere and Render free-tier instances can have cold starts.
 * Call this as early as possible (e.g. on app mount) so the server is warm
 * by the time the user uploads a file.
 */
export async function warmupBackend() {
    try {
        await fetch(apiUrl('/api/health'), { method: 'GET', cache: 'no-store' })
    } catch (_) {
        // Ignore — warmup is best-effort
    }
}
