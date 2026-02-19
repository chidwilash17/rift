import { useState, useEffect, useRef, useMemo } from 'react'

/* ═══════════════════════════════════════════════════════════════
   FRAUD RINGS TABLE — with expandable detail dropdowns
   ═══════════════════════════════════════════════════════════════ */

export default function RingsTable({ rings, graphData, accounts }) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState('risk_score')
  const [sortDir, setSortDir] = useState('desc')
  const [expandedRing, setExpandedRing] = useState(null)

  /* Build lookup maps */
  const accountMap = useMemo(() => {
    const m = {}
    ;(accounts || []).forEach(a => { m[a.account_id] = a })
    return m
  }, [accounts])

  /* Filter + sort */
  const filtered = useMemo(() => {
    let list = [...(rings || [])]
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(r =>
        r.ring_id.toLowerCase().includes(q) ||
        r.pattern_type.toLowerCase().includes(q) ||
        r.member_accounts.some(a => a.toLowerCase().includes(q))
      )
    }
    list.sort((a, b) => {
      let av, bv
      if (sortKey === 'members') { av = a.member_accounts.length; bv = b.member_accounts.length }
      else if (sortKey === 'risk_score') { av = a.risk_score; bv = b.risk_score }
      else if (sortKey === 'ring_id') { av = a.ring_id; bv = b.ring_id }
      else if (sortKey === 'pattern_type') { av = a.pattern_type; bv = b.pattern_type }
      else { av = a[sortKey]; bv = b[sortKey] }
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })
    return list
  }, [rings, search, sortKey, sortDir])

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  if (!rings?.length) return <Empty msg="No fraud rings detected" />

  return (
    <div className="space-y-3">
      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <div className="relative">
            <i className="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-xs" />
            <input type="text" placeholder="Search rings, patterns, accounts…"
              value={search} onChange={e => setSearch(e.target.value)}
              className="pl-8 pr-4 py-2 rounded-lg bg-dark-700 border border-dark-500 text-sm text-gray-200 placeholder-gray-600
                         focus:border-violet-500/50 focus:outline-none focus:ring-1 focus:ring-violet-500/20 transition-all w-72" />
          </div>
          <span className="text-xs text-gray-500">
            {filtered.length} of {rings.length} rings
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-gray-500">
          <span>Click any row to expand details</span>
          <i className="fas fa-chevron-down text-violet-400" />
        </div>
      </div>

      {/* ── Table ── */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-dark-700 text-gray-400 text-xs uppercase tracking-wider">
                <th className="w-8 px-2 py-3" />
                <SortHeader label="Ring ID" sortKey="ring_id" current={sortKey} dir={sortDir} onClick={toggleSort} />
                <SortHeader label="Pattern" sortKey="pattern_type" current={sortKey} dir={sortDir} onClick={toggleSort} />
                <SortHeader label="Members" sortKey="members" current={sortKey} dir={sortDir} onClick={toggleSort} center />
                <SortHeader label="Risk Score" sortKey="risk_score" current={sortKey} dir={sortDir} onClick={toggleSort} center />
                <th className="px-4 py-3 text-left hidden sm:table-cell">Account IDs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-500">
              {filtered.map((ring) => (
                <RingRow key={ring.ring_id} ring={ring}
                  expanded={expandedRing === ring.ring_id}
                  onToggle={() => setExpandedRing(expandedRing === ring.ring_id ? null : ring.ring_id)}
                  graphData={graphData} accountMap={accountMap} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

/* ─── Sort Header ─── */
function SortHeader({ label, sortKey, current, dir, onClick, center }) {
  const active = current === sortKey
  return (
    <th className={`px-4 py-3 ${center ? 'text-center' : 'text-left'} cursor-pointer select-none hover:text-gray-200 transition-colors group`}
        onClick={() => onClick(sortKey)}>
      <span className="inline-flex items-center gap-1">
        {label}
        <i className={`fas fa-sort${active ? (dir === 'asc' ? '-up' : '-down') : ''} text-[9px] ${active ? 'text-violet-400' : 'text-gray-600 group-hover:text-gray-400'}`} />
      </span>
    </th>
  )
}

/* ─── Ring Row ─── */
function RingRow({ ring, expanded, onToggle, graphData, accountMap }) {
  return (
    <>
      <tr className={`cursor-pointer transition-all ${expanded ? 'bg-dark-700' : 'hover:bg-dark-700/50'}`}
          onClick={onToggle}>
        <td className="px-2 py-3 text-center">
          <i className={`fas fa-chevron-right text-[10px] text-gray-500 transition-transform duration-300 ${expanded ? 'rotate-90 text-violet-400' : ''}`} />
        </td>
        <td className="px-4 py-3 font-mono text-accent-blue text-xs font-bold">{ring.ring_id}</td>
        <td className="px-4 py-3"><PatternBadge pattern={ring.pattern_type} /></td>
        <td className="px-4 py-3 text-center font-bold">{ring.member_accounts.length}</td>
        <td className="px-4 py-3 text-center"><ScorePill score={ring.risk_score} /></td>
        <td className="px-4 py-3 hidden sm:table-cell">
          <div className="flex flex-wrap gap-1 max-w-sm">
            {ring.member_accounts.map(a => (
              <span key={a} className="text-[10px] bg-dark-600 px-1.5 py-0.5 rounded font-mono text-gray-300">{a}</span>
            ))}
          </div>
        </td>
      </tr>

      {/* ── Expanded Detail Panel ── */}
      {expanded && (
        <tr>
          <td colSpan={6} className="p-0">
            <RingDetail ring={ring} graphData={graphData} accountMap={accountMap} />
          </td>
        </tr>
      )}
    </>
  )
}

/* ═══════════════════ RING DETAIL PANEL ═══════════════════ */
function RingDetail({ ring, graphData, accountMap }) {
  const members = ring.member_accounts
  const memberSet = useMemo(() => new Set(members), [members])

  /* Extract this ring's edges + transactions from graph data */
  const { ringEdges, ringTransactions, totalAmount, totalTxCount } = useMemo(() => {
    const edgesArr = []
    const txArr = []
    let amount = 0
    let txCount = 0
    if (graphData?.edges) {
      graphData.edges.forEach(e => {
        if (memberSet.has(e.from) && memberSet.has(e.to)) {
          edgesArr.push(e)
          amount += e.total_amount || 0
          txCount += e.tx_count || 0
          ;(e.transactions || []).forEach(tx => {
            txArr.push({ ...tx, sender: e.from, receiver: e.to })
          })
        }
      })
    }
    txArr.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    return { ringEdges: edgesArr, ringTransactions: txArr, totalAmount: amount, totalTxCount: txCount }
  }, [graphData, memberSet])

  /* Member account details */
  const memberDetails = useMemo(() =>
    members.map(id => {
      const acct = accountMap[id] || {}
      const node = graphData?.nodes?.find(n => n.id === id)
      return {
        id,
        score: acct.suspicion_score || 0,
        patterns: acct.detected_patterns || [],
        componentScores: acct.component_scores || {},
        totalSent: node?.title?.match(/Sent: ([\d.]+)/)?.[1] || '0',
        totalReceived: node?.title?.match(/Received: ([\d.]+)/)?.[1] || '0',
      }
    }),
  [members, accountMap, graphData])

  return (
    <div className="bg-dark-800/80 border-t border-dark-500 animate-in">
      {/* ── Stats Bar ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 border-b border-dark-500">
        <MiniStat icon="fa-users" label="Members" value={members.length} gradient="from-blue-400 to-cyan-400" />
        <MiniStat icon="fa-exchange-alt" label="Transactions" value={totalTxCount} gradient="from-purple-400 to-violet-400" />
        <MiniStat icon="fa-dollar-sign" label="Total Amount" value={`$${totalAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} gradient="from-amber-400 to-orange-400" />
        <MiniStat icon="fa-exclamation-triangle" label="Risk Score" value={ring.risk_score} gradient={ring.risk_score >= 70 ? 'from-red-400 to-pink-400' : ring.risk_score >= 50 ? 'from-orange-400 to-amber-400' : 'from-yellow-400 to-lime-400'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
        {/* ── Left: Mini Graph ── */}
        <div className="border-b lg:border-b-0 lg:border-r border-dark-500 p-4">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <i className="fas fa-diagram-project text-violet-400" />Ring Network Topology
          </h4>
          <MiniGraph members={members} edges={ringEdges} graphData={graphData} ringId={ring.ring_id} />
        </div>

        {/* ── Right: Member Details ── */}
        <div className="p-4">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <i className="fas fa-user-shield text-red-400" />Member Accounts
          </h4>
          <div className="space-y-2 max-h-[280px] overflow-y-auto custom-scroll">
            {memberDetails.map(m => (
              <div key={m.id} className="bg-dark-700 rounded-lg p-3 border border-dark-500 hover:border-gray-600 transition-all">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-xs text-accent-blue font-bold">{m.id}</span>
                  <ScorePill score={m.score} />
                </div>
                <div className="grid grid-cols-3 gap-2 text-[10px]">
                  <div>
                    <span className="text-gray-500">Graph</span>
                    <div className="text-emerald-400 font-bold">{m.componentScores.graph || 0}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">ML</span>
                    <div className="text-sky-400 font-bold">{m.componentScores.ml || 0}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Quantum</span>
                    <div className="text-violet-400 font-bold">{m.componentScores.quantum || 0}</div>
                  </div>
                </div>
                {m.patterns.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {m.patterns.map((p, i) => (
                      <span key={i} className="text-[9px] px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
                        {p.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Transaction Log ── */}
      <div className="border-t border-dark-500 p-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <i className="fas fa-list-alt text-amber-400" />
          Transaction Log
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-dark-600 text-gray-500">
            {ringTransactions.length} transactions
          </span>
        </h4>
        {ringTransactions.length > 0 ? (
          <div className="overflow-x-auto max-h-[250px] overflow-y-auto custom-scroll">
            <table className="w-full text-xs">
              <thead className="sticky top-0 z-10">
                <tr className="bg-dark-700 text-gray-500 uppercase text-[10px] tracking-wider">
                  <th className="px-3 py-2 text-left">TX ID</th>
                  <th className="px-3 py-2 text-left">Sender</th>
                  <th className="px-3 py-2 text-center"><i className="fas fa-arrow-right" /></th>
                  <th className="px-3 py-2 text-left">Receiver</th>
                  <th className="px-3 py-2 text-right">Amount</th>
                  <th className="px-3 py-2 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-600">
                {ringTransactions.map((tx, i) => (
                  <tr key={`${tx.transaction_id}-${i}`} className="hover:bg-dark-700/50 transition-colors">
                    <td className="px-3 py-2 font-mono text-gray-400">{tx.transaction_id}</td>
                    <td className="px-3 py-2 font-mono text-accent-blue">{tx.sender}</td>
                    <td className="px-3 py-2 text-center text-gray-600"><i className="fas fa-arrow-right text-[8px]" /></td>
                    <td className="px-3 py-2 font-mono text-accent-blue">{tx.receiver}</td>
                    <td className="px-3 py-2 text-right font-bold text-amber-400">
                      ${typeof tx.amount === 'number' ? tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : tx.amount}
                    </td>
                    <td className="px-3 py-2 text-right text-gray-400">
                      {formatTimestamp(tx.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-gray-600 text-xs py-6">
            <i className="fas fa-database mr-1" />No transaction data available for this ring
          </div>
        )}
      </div>
    </div>
  )
}

/* ─── Mini Graph (vis.js) ─── */
function MiniGraph({ members, edges, graphData, ringId }) {
  const containerRef = useRef(null)
  const networkRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !graphData) return
    let destroyed = false

    const init = async () => {
      const vis = await import('vis-network/standalone')
      if (destroyed) return

      const memberSet = new Set(members)

      /* Nodes for this ring */
      const ringNodes = graphData.nodes
        .filter(n => memberSet.has(n.id))
        .map(n => ({
          ...n,
          size: 22,
          font: { color: '#e6edf3', size: 12, bold: { color: '#ffffff' } },
          borderWidth: 3,
          shadow: { enabled: true, color: 'rgba(139,92,246,0.3)', size: 8 },
        }))

      /* Edges for ring */
      const ringEdges = edges.map(e => ({
        ...e,
        width: 2.5,
        color: { color: '#f85149', opacity: 0.9 },
        font: { color: '#fbbf24', size: 10, strokeWidth: 3, strokeColor: '#0d1117' },
      }))

      const options = {
        physics: {
          stabilization: { iterations: 50, fit: true },
          barnesHut: { gravitationalConstant: -2000, springLength: 120, damping: 0.5 },
        },
        interaction: { hover: true, tooltipDelay: 150, zoomView: true, dragView: true },
        nodes: { font: { color: '#c9d1d9', size: 11 } },
        edges: { font: { color: '#8b949e', size: 9 } },
      }

      if (networkRef.current) networkRef.current.destroy()
      networkRef.current = new vis.Network(
        containerRef.current,
        { nodes: new vis.DataSet(ringNodes), edges: new vis.DataSet(ringEdges) },
        options
      )
    }

    init()
    return () => { destroyed = true; networkRef.current?.destroy() }
  }, [members, edges, graphData])

  return (
    <div className="relative">
      <div ref={containerRef} className="w-full h-[260px] rounded-lg bg-dark-900/50 border border-dark-500" />
      <div className="absolute top-2 right-2 flex gap-1">
        <button onClick={() => networkRef.current?.fit()}
          className="text-[10px] text-gray-400 hover:text-white px-2 py-1 rounded bg-dark-700/80 border border-dark-500 hover:border-violet-500/50 transition backdrop-blur">
          <i className="fas fa-expand mr-1" />Fit
        </button>
      </div>
      <div className="absolute bottom-2 left-2 text-[10px] text-gray-500 bg-dark-700/80 px-2 py-0.5 rounded backdrop-blur">
        {ringId} &bull; {members.length} nodes &bull; {edges.length} edges
      </div>
    </div>
  )
}

/* ─── Mini Stat Card ─── */
function MiniStat({ icon, label, value, gradient }) {
  return (
    <div className="bg-dark-700 rounded-lg p-3 border border-dark-500">
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-6 h-6 rounded-md bg-gradient-to-br ${gradient} flex items-center justify-center`}>
          <i className={`fas ${icon} text-white text-[9px]`} />
        </div>
        <span className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-lg font-extrabold bg-clip-text text-transparent bg-gradient-to-r ${gradient}`}>
        {value}
      </div>
    </div>
  )
}

/* ─── Helpers ─── */
function PatternBadge({ pattern }) {
  const colors = {
    cycle: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
    cyclic_flow: 'text-red-400 bg-red-500/10 border-red-500/30',
    smurfing_fan_in: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
    smurfing_fan_out: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
    shell_network: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    shell_chain: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  }
  const cls = colors[pattern] || 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full border text-[10px] font-semibold ${cls}`}>
      {pattern?.replace(/_/g, ' ')}
    </span>
  )
}

function ScorePill({ score }) {
  const bg = score >= 70 ? 'bg-red-500' : score >= 40 ? 'bg-orange-500' : 'bg-yellow-500'
  return (
    <span className={`inline-flex items-center justify-center text-xs font-bold text-white rounded-full w-10 h-6 ${bg}`}>
      {score}
    </span>
  )
}

function formatTimestamp(ts) {
  if (!ts) return '—'
  try {
    const d = new Date(ts)
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
  } catch { return ts }
}

function Empty({ msg }) {
  return (
    <div className="flex items-center justify-center h-40 bg-dark-800 border border-dark-500 rounded-xl text-gray-500 text-sm">
      <i className="fas fa-ring mr-2" />{msg}
    </div>
  )
}
