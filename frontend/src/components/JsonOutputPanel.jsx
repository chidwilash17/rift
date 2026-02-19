import { useState, useMemo, useCallback, useRef } from 'react'

/* ─── Syntax-highlighted JSON renderer ─── */
function SyntaxJson({ json }) {
  /* Tokenise JSON string into coloured spans */
  const tokens = useMemo(() => {
    const parts = []
    // Match strings, numbers, booleans, null, structural chars
    const rx = /("(?:\\.|[^"\\])*")\s*(:)?|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|(\btrue\b|\bfalse\b)|(\bnull\b)|([{}\[\],])/g
    let m
    let last = 0
    while ((m = rx.exec(json)) !== null) {
      // whitespace between tokens
      if (m.index > last) parts.push({ type: 'ws', text: json.slice(last, m.index) })
      if (m[1] !== undefined) {
        if (m[2]) {
          // key
          parts.push({ type: 'key', text: m[1] })
          parts.push({ type: 'punct', text: ':' })
        } else {
          parts.push({ type: 'string', text: m[1] })
        }
      } else if (m[3] !== undefined) {
        parts.push({ type: 'number', text: m[3] })
      } else if (m[4] !== undefined) {
        parts.push({ type: 'bool', text: m[4] })
      } else if (m[5] !== undefined) {
        parts.push({ type: 'null', text: m[5] })
      } else if (m[6] !== undefined) {
        parts.push({ type: 'punct', text: m[6] })
      }
      last = m.index + m[0].length
    }
    if (last < json.length) parts.push({ type: 'ws', text: json.slice(last) })
    return parts
  }, [json])

  const colorMap = {
    key: 'text-violet-400',
    string: 'text-emerald-400',
    number: 'text-amber-400',
    bool: 'text-sky-400',
    null: 'text-gray-500 italic',
    punct: 'text-gray-500',
    ws: '',
  }

  return (
    <code>
      {tokens.map((t, i) => (
        <span key={i} className={colorMap[t.type] || ''}>{t.text}</span>
      ))}
    </code>
  )
}

/* ═══════════════════ Main Export ═══════════════════ */
export default function JsonOutputPanel({ results, onDownload }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const timerRef = useRef(null)

  /* Build the output object in the required format */
  const outputJson = useMemo(() => {
    if (!results) return null
    return {
      suspicious_accounts: (results.suspicious_accounts || []).map(a => ({
        account_id: a.account_id,
        suspicion_score: a.suspicion_score ?? a.score ?? 0,
        detected_patterns: a.detected_patterns || a.patterns || [],
        ring_id: a.ring_id || null,
      })),
      fraud_rings: (results.fraud_rings || []).map(r => ({
        ring_id: r.ring_id,
        member_accounts: r.member_accounts || r.accounts || [],
        pattern_type: r.pattern_type || r.type || 'unknown',
        risk_score: r.risk_score ?? r.score ?? 0,
      })),
      summary: {
        total_accounts_analyzed: results.summary?.total_accounts_analyzed ?? 0,
        suspicious_accounts_flagged: results.summary?.suspicious_accounts_flagged ?? (results.suspicious_accounts || []).length,
        fraud_rings_detected: results.summary?.fraud_rings_detected ?? (results.fraud_rings || []).length,
        processing_time_seconds: results.summary?.processing_time_seconds ?? 0,
      },
    }
  }, [results])

  const rawJson = useMemo(() => outputJson ? JSON.stringify(outputJson, null, 2) : '', [outputJson])
  const lineCount = useMemo(() => rawJson.split('\n').length, [rawJson])

  const jsonSize = useMemo(() => {
    const bytes = new Blob([rawJson]).size
    return bytes > 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${(bytes / 1024).toFixed(1)} KB`
  }, [rawJson])

  const copyAll = useCallback(() => {
    navigator.clipboard.writeText(rawJson)
    setCopied(true)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setCopied(false), 2000)
  }, [rawJson])

  if (!results) return null

  const acctCount = outputJson.suspicious_accounts.length
  const ringCount = outputJson.fraud_rings.length

  return (
    <div className="bg-dark-700 border border-dark-500 rounded-xl overflow-hidden transition-all duration-300">
      {/* ─ Clickable Header ─ */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-dark-800/50 hover:bg-dark-700 transition-all text-left group"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <i className="fas fa-code text-white text-sm" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-100 flex items-center gap-2">
              JSON Output
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {acctCount} accounts &middot; {ringCount} rings
              </span>
            </h3>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="text-[10px] text-gray-500 font-mono">{lineCount} lines</span>
              <span className="text-[10px] text-gray-600">&bull;</span>
              <span className="text-[10px] text-gray-500 font-mono">{jsonSize}</span>
              <span className="text-[10px] text-gray-600">&bull;</span>
              <span className="text-[10px] text-gray-500 font-mono">3 sections</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
          {/* Copy — always visible */}
          <button onClick={copyAll}
            className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all flex items-center gap-1.5 ${
              copied
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-dark-600 text-gray-400 border border-dark-400 hover:text-gray-200 hover:border-gray-500'
            }`}>
            <i className={`fas ${copied ? 'fa-check' : 'fa-clipboard'}`} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
          {/* Download — always visible */}
          <button onClick={onDownload}
            className="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-gradient-to-r from-accent-blue to-accent-purple text-white
                       hover:shadow-lg hover:shadow-accent-blue/20 transition-all flex items-center gap-1.5">
            <i className="fas fa-download" />Download
          </button>
          <i className={`fas fa-chevron-down text-xs text-gray-500 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* ─ Collapsible JSON Body ─ */}
      {open && (
        <div className="border-t border-dark-500">
          {/* Action bar */}
          <div className="flex items-center justify-end gap-2 px-4 py-2 bg-dark-800/30 border-b border-dark-600">
            {/* Copy */}
            <button onClick={(e) => { e.stopPropagation(); copyAll() }}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all flex items-center gap-1.5 ${
                copied
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-dark-600 text-gray-400 border border-dark-400 hover:text-gray-200 hover:border-gray-500'
              }`}>
              <i className={`fas ${copied ? 'fa-check' : 'fa-clipboard'}`} />
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {/* Download */}
            <button onClick={(e) => { e.stopPropagation(); onDownload() }}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-gradient-to-r from-accent-blue to-accent-purple text-white
                         hover:shadow-lg hover:shadow-accent-blue/20 transition-all flex items-center gap-1.5">
              <i className="fas fa-download" />Download
            </button>
          </div>

          {/* JSON with line numbers */}
          <div className="flex max-h-[500px] overflow-auto custom-scroll">
            <div className="sticky left-0 bg-dark-800 border-r border-dark-600 px-2 py-3 select-none shrink-0 z-10">
              {rawJson.split('\n').map((_, i) => (
                <div key={i} className="text-[10px] text-gray-600 text-right font-mono leading-5 h-5 w-6">{i + 1}</div>
              ))}
            </div>
            <pre className="flex-1 p-3 text-xs font-mono leading-5 overflow-x-auto whitespace-pre select-all">
              <SyntaxJson json={rawJson} />
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
