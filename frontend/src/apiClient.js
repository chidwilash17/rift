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

// Empty BASE = relative paths → same-origin on Vercel/Netlify, proxied by Vite locally
const BASE = 'https://unheaved-elina-roughly.ngrok-free.dev'

/**
 * Prepend the backend base URL to a path.
 * @param {string} path  Must start with '/'
 * @returns {string}
 */
export function apiUrl(path) {
    return `${BASE}${path}`
}

/**
 * Default headers for all API requests.
 * ngrok-skip-browser-warning bypasses ngrok's interstitial page.
 */
export const API_HEADERS = {
    'ngrok-skip-browser-warning': 'true',
    'User-Agent': 'rift-frontend/1.0',
}

/**
 * Ping the backend health endpoint to warm up the instance.
 */
export async function warmupBackend() {
    try {
        await fetch(apiUrl('/api/health'), {
            method: 'GET',
            cache: 'no-store',
            headers: API_HEADERS,
        })
    } catch (_) {
        // Ignore — warmup is best-effort
    }
}
