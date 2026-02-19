import { useState } from 'react'

export default function AccountsTable({ accounts }) {
  const [search, setSearch] = useState('')

  if (!accounts?.length) return <Empty />

  const filtered = accounts.filter(a =>
    a.account_id.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
      {/* Search */}
      <div className="px-4 py-3 border-b border-dark-500 flex items-center gap-2">
        <i className="fas fa-search text-gray-500 text-xs" />
        <input
          type="text"
          placeholder="Search accounts…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="bg-transparent text-sm text-gray-200 outline-none flex-1 placeholder:text-gray-600"
        />
        <span className="text-xs text-gray-500">{filtered.length} of {accounts.length}</span>
      </div>

      <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-dark-700 z-10">
            <tr className="text-gray-400 text-xs uppercase tracking-wider">
              <th className="px-4 py-3 text-left">Account</th>
              <th className="px-4 py-3 text-center">Score</th>
              <th className="px-4 py-3 text-left">Patterns</th>
              <th className="px-4 py-3 text-center hidden sm:table-cell">Graph</th>
              <th className="px-4 py-3 text-center hidden sm:table-cell">ML</th>
              <th className="px-4 py-3 text-center hidden sm:table-cell">Quantum</th>
              <th className="px-4 py-3 text-left hidden md:table-cell">Ring</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-500">
            {filtered.map(a => {
              const cs = a.component_scores || {}
              return (
                <tr key={a.account_id} className="hover:bg-dark-700/50 transition">
                  <td className="px-4 py-3 font-mono text-accent-blue text-xs">{a.account_id}</td>
                  <td className="px-4 py-3 text-center">
                    <ScorePill score={a.suspicion_score} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(a.detected_patterns || []).map((p, i) => (
                        <span key={i} className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded-full font-medium">
                          {p.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center hidden sm:table-cell text-xs font-mono">{cs.graph ?? '—'}</td>
                  <td className="px-4 py-3 text-center hidden sm:table-cell text-xs font-mono">{cs.ml ?? '—'}</td>
                  <td className="px-4 py-3 text-center hidden sm:table-cell text-xs font-mono">{cs.quantum ?? '—'}</td>
                  <td className="px-4 py-3 hidden md:table-cell text-xs font-mono text-gray-400">{a.ring_id || '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
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

function Empty() {
  return (
    <div className="flex items-center justify-center h-40 bg-dark-800 border border-dark-500 rounded-xl text-gray-500 text-sm">
      <i className="fas fa-user-shield mr-2" />No suspicious accounts detected
    </div>
  )
}
