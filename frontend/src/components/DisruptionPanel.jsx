import { useState } from 'react'

export default function DisruptionPanel({ data }) {
  const [selectedRing, setSelectedRing] = useState(0)

  if (!data || !data.strategies) {
    return (
      <div className="flex items-center justify-center h-[400px] bg-dark-800 border border-dark-500 rounded-xl text-gray-500">
        <div className="text-center">
          <i className="fas fa-shield-virus text-5xl mb-3 block animate-pulse" />
          <p>No disruption data available</p>
        </div>
      </div>
    )
  }

  const { strategies, network_stats, global_summary } = data
  const strat = strategies[selectedRing] || null

  return (
    <div className="space-y-5 animate-in">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-900/30 via-dark-800 to-purple-900/20 border border-red-500/20 p-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(248,81,73,0.08),transparent_60%)]" />
        <div className="absolute top-3 right-4 opacity-[0.03]">
          <i className="fas fa-crosshairs text-[120px] text-red-400" />
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
              <i className="fas fa-crosshairs text-red-400 text-sm" />
            </div>
            <h2 className="text-lg font-black text-white tracking-tight">Quantum Disruption Engine</h2>
            <span className="ml-auto px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-500/15 text-red-400 border border-red-500/25 animate-pulse">
              LIVE ANALYSIS
            </span>
          </div>
          <p className="text-xs text-gray-400 max-w-2xl">
            Identifies critical nodes whose removal maximally fragments fraud networks.
            Combines graph vertex-cut simulation with quantum partition data.
          </p>

          {/* Global KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
            <KPI label="Rings Analyzed" value={global_summary.total_rings_analyzed} gradient="from-red-500 to-orange-500" icon="fa-ring" />
            <KPI label="Critical Nodes" value={global_summary.unique_critical_nodes} gradient="from-orange-500 to-yellow-500" icon="fa-bullseye" />
            <KPI label="Avg Disruption" value={`${global_summary.avg_disruption_potential}%`} gradient="from-purple-500 to-pink-500" icon="fa-explosion" />
            <KPI label="Net Resilience" value={`${global_summary.network_resilience_score}%`} gradient="from-cyan-500 to-blue-500" icon="fa-shield-halved" />
          </div>
        </div>
      </div>

      {/* Network Centrality Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CentralityCard
          title="Betweenness Centrality"
          icon="fa-arrows-split-up-and-left"
          color="text-red-400"
          bgColor="bg-red-500/10"
          borderColor="border-red-500/20"
          items={network_stats.top_betweenness}
          description="Nodes that control the most information flow"
        />
        <CentralityCard
          title="Degree Centrality"
          icon="fa-circle-nodes"
          color="text-orange-400"
          bgColor="bg-orange-500/10"
          borderColor="border-orange-500/20"
          items={network_stats.top_degree_centrality}
          description="Most connected nodes in the network"
        />
        <CentralityCard
          title="Closeness Centrality"
          icon="fa-arrows-to-dot"
          color="text-cyan-400"
          bgColor="bg-cyan-500/10"
          borderColor="border-cyan-500/20"
          items={network_stats.top_closeness}
          description="Nodes that can reach all others fastest"
        />
      </div>

      {/* Articulation Points */}
      {network_stats.articulation_point_count > 0 && (
        <div className="bg-dark-800 border border-yellow-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-triangle-exclamation text-yellow-400 text-sm" />
            <span className="text-sm font-bold text-yellow-400">
              {network_stats.articulation_point_count} Articulation Points Detected
            </span>
            <span className="text-[10px] text-gray-500 ml-2">
              Removing these disconnects the network
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {network_stats.articulation_points.map(ap => (
              <span key={ap} className="px-2 py-0.5 text-[10px] font-mono font-bold bg-yellow-500/10 text-yellow-400 border border-yellow-500/25 rounded">
                {ap}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Ring Selector */}
      {strategies.length > 0 && (
        <>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {strategies.map((s, i) => (
              <button
                key={s.ring_id}
                onClick={() => setSelectedRing(i)}
                className={`shrink-0 px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                  selectedRing === i
                    ? 'bg-gradient-to-r from-red-500/20 to-purple-500/20 border-red-500/40 text-white shadow-lg shadow-red-500/10'
                    : 'border-dark-500 text-gray-400 hover:border-red-500/30 hover:text-gray-200'
                }`}
              >
                <i className="fas fa-ring mr-1.5" />
                {s.ring_id}
                <span className={`ml-2 px-1.5 py-0.5 rounded text-[9px] ${
                  s.max_disruption_pct > 60 ? 'bg-red-500/20 text-red-400' :
                  s.max_disruption_pct > 30 ? 'bg-orange-500/20 text-orange-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {s.max_disruption_pct}%
                </span>
              </button>
            ))}
          </div>

          {/* Selected Ring Detail */}
          {strat && <RingDisruptionDetail strategy={strat} />}
        </>
      )}
    </div>
  )
}

function KPI({ label, value, gradient, icon }) {
  return (
    <div className="bg-dark-700/60 rounded-xl p-3 border border-dark-500/50 relative overflow-hidden group hover:scale-[1.02] transition-transform">
      <i className={`fas ${icon} absolute -right-1 -bottom-1 text-4xl opacity-[0.04] group-hover:opacity-[0.08] transition-opacity`} />
      <span className="text-[9px] text-gray-500 uppercase tracking-wider block">{label}</span>
      <span className={`text-xl sm:text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r ${gradient}`}>
        {value}
      </span>
    </div>
  )
}

function CentralityCard({ title, icon, color, bgColor, borderColor, items, description }) {
  return (
    <div className={`bg-dark-800 border ${borderColor} rounded-xl overflow-hidden`}>
      <div className={`px-4 py-2.5 ${bgColor} border-b ${borderColor} flex items-center gap-2`}>
        <i className={`fas ${icon} ${color} text-sm`} />
        <span className="text-xs font-bold text-white">{title}</span>
      </div>
      <div className="p-3">
        <p className="text-[10px] text-gray-500 mb-2">{description}</p>
        <div className="space-y-1.5">
          {(items || []).slice(0, 5).map((item, i) => (
            <div key={item.account_id} className="flex items-center gap-2">
              <span className={`w-4 h-4 rounded flex items-center justify-center text-[9px] font-bold ${
                i === 0 ? 'bg-red-500/20 text-red-400' : 'bg-dark-600 text-gray-500'
              }`}>{i + 1}</span>
              <span className="text-[10px] font-mono text-gray-300 flex-1 truncate">{item.account_id}</span>
              <div className="w-16 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${
                    i === 0 ? 'from-red-500 to-orange-500' : 'from-gray-500 to-gray-400'
                  }`}
                  style={{ width: `${Math.max(item.score * 100, 5)}%` }}
                />
              </div>
              <span className="text-[9px] text-gray-500 w-10 text-right font-mono">{(item.score * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function RingDisruptionDetail({ strategy }) {
  const { critical_nodes, removal_simulations, optimal_pair_removal, quantum_overlay } = strategy

  return (
    <div className="space-y-4 animate-fade">
      {/* Ring Overview */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl p-5">
        <div className="flex flex-wrap items-center gap-6 mb-4">
          <div>
            <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Ring</span>
            <span className="text-lg font-black text-white">{strategy.ring_id}</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Members</span>
            <span className="text-lg font-extrabold text-accent-blue">{strategy.member_count}</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Edges</span>
            <span className="text-lg font-extrabold text-accent-cyan">{strategy.original_edges}</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Risk Score</span>
            <span className="text-lg font-extrabold text-red-400">{strategy.risk_score}</span>
          </div>
          <div className="ml-auto">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Max Disruption</span>
            <DisruptionMeter value={strategy.max_disruption_pct} />
          </div>
        </div>

        {/* Resilience gauge */}
        <div className="w-full h-3 bg-dark-600 rounded-full overflow-hidden relative">
          <div
            className="h-full rounded-full bg-gradient-to-r from-red-500 via-orange-500 to-green-500 transition-all duration-1000"
            style={{ width: `${strategy.resilience_score}%` }}
          />
          <span className="absolute inset-0 flex items-center justify-center text-[8px] font-bold text-white drop-shadow">
            Resilience: {strategy.resilience_score}%
          </span>
        </div>
      </div>

      {/* Critical Nodes - The Targets */}
      {critical_nodes.length > 0 && (
        <div className="bg-dark-800 border border-red-500/20 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-red-500/5 border-b border-red-500/20 flex items-center gap-2">
            <i className="fas fa-crosshairs text-red-400 text-sm animate-pulse" />
            <span className="text-sm font-bold text-red-400">Critical Nodes — Priority Targets</span>
          </div>
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {critical_nodes.map((node, i) => (
              <div key={node.account_id} className="bg-dark-700 border border-dark-500 rounded-xl p-3 hover:border-red-500/30 transition-all group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-red-500/[0.02] to-transparent group-hover:from-red-500/[0.05] transition-all" />
                <div className="relative z-10">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      i === 0 ? 'bg-red-500 text-white' : 'bg-red-500/20 text-red-400'
                    }`}>{i + 1}</span>
                    <span className="text-xs font-mono font-bold text-white truncate">{node.account_id}</span>
                    {node.is_articulation_point && (
                      <span className="ml-auto px-1.5 py-0.5 rounded text-[8px] font-bold bg-yellow-500/15 text-yellow-400 border border-yellow-500/25">
                        BRIDGE
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                    <div className="bg-dark-600/50 rounded px-2 py-1">
                      <span className="text-gray-500 block">Impact</span>
                      <span className="font-bold text-red-400">{node.impact_score}%</span>
                    </div>
                    <div className="bg-dark-600/50 rounded px-2 py-1">
                      <span className="text-gray-500 block">Edges Cut</span>
                      <span className="font-bold text-orange-400">{node.edges_severed}</span>
                    </div>
                    <div className="bg-dark-600/50 rounded px-2 py-1">
                      <span className="text-gray-500 block">Fragments</span>
                      <span className="font-bold text-accent-cyan">{node.fragments_created}</span>
                    </div>
                    <div className="bg-dark-600/50 rounded px-2 py-1">
                      <span className="text-gray-500 block">Suspicion</span>
                      <span className="font-bold text-accent-purple">{node.suspicion_score}</span>
                    </div>
                  </div>
                  {/* Impact bar */}
                  <div className="mt-2 w-full h-1.5 bg-dark-600 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full transition-all duration-700"
                      style={{ width: `${node.impact_score}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Optimal Pair Removal */}
      {optimal_pair_removal && optimal_pair_removal.nodes && optimal_pair_removal.nodes.length === 2 && (
        <div className="bg-gradient-to-r from-purple-900/20 to-dark-800 border border-purple-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-user-minus text-purple-400 text-sm" />
            <span className="text-sm font-bold text-purple-400">Optimal Pair Removal Strategy</span>
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 bg-purple-500/15 text-purple-300 border border-purple-500/25 rounded-lg text-xs font-mono font-bold">
                {optimal_pair_removal.nodes[0]}
              </span>
              <span className="text-gray-500 text-xs">+</span>
              <span className="px-3 py-1.5 bg-purple-500/15 text-purple-300 border border-purple-500/25 rounded-lg text-xs font-mono font-bold">
                {optimal_pair_removal.nodes[1]}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <i className="fas fa-arrow-right text-gray-500 text-xs" />
              <span className="text-sm font-bold text-purple-400">{optimal_pair_removal.combined_impact}% disruption</span>
            </div>
            <div className="text-[10px] text-gray-500">
              → {optimal_pair_removal.new_components} fragments, {optimal_pair_removal.edges_remaining} edges remaining
            </div>
          </div>
        </div>
      )}

      {/* Quantum Overlay */}
      {quantum_overlay && quantum_overlay.available && (
        <div className="bg-dark-800 border border-accent-cyan/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-atom text-accent-cyan text-sm animate-spin-slow" />
            <span className="text-sm font-bold text-accent-cyan">Quantum Partition Overlay</span>
            <span className="ml-auto text-[10px] bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/25 px-2 py-0.5 rounded">
              Agreement: {quantum_overlay.quantum_agreement}%
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <span className="text-[10px] text-red-400 uppercase tracking-wider block mb-1.5">
                <i className="fas fa-exclamation-circle mr-1" />Suspicious Partition ({quantum_overlay.suspicious_partition.length})
              </span>
              <div className="flex flex-wrap gap-1">
                {quantum_overlay.suspicious_partition.map(acc => (
                  <span key={acc} className="text-[9px] bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded font-mono">
                    {acc}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <span className="text-[10px] text-green-400 uppercase tracking-wider block mb-1.5">
                <i className="fas fa-check-circle mr-1" />Clean Partition ({quantum_overlay.clean_partition.length})
              </span>
              <div className="flex flex-wrap gap-1">
                {quantum_overlay.clean_partition.map(acc => (
                  <span key={acc} className="text-[9px] bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded font-mono">
                    {acc}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Impact Simulation Table */}
      {removal_simulations && removal_simulations.length > 0 && (
        <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-dark-700/50 border-b border-dark-500 flex items-center gap-2">
            <i className="fas fa-flask text-gray-400 text-sm" />
            <span className="text-xs font-bold text-gray-300">Node Removal Simulations</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-gray-500 uppercase tracking-wider border-b border-dark-500">
                  <th className="px-4 py-2 text-left">Node</th>
                  <th className="px-3 py-2 text-center">Impact</th>
                  <th className="px-3 py-2 text-center">Edges Lost</th>
                  <th className="px-3 py-2 text-center">Fragments</th>
                  <th className="px-3 py-2 text-center">Bridge?</th>
                  <th className="px-3 py-2 text-left w-32">Impact Bar</th>
                </tr>
              </thead>
              <tbody>
                {removal_simulations.slice(0, 10).map((sim, i) => (
                  <tr key={sim.removed_node} className="border-b border-dark-600/50 hover:bg-dark-700/30 transition-colors">
                    <td className="px-4 py-2 font-mono font-bold text-gray-300">{sim.removed_node}</td>
                    <td className="px-3 py-2 text-center">
                      <span className={`font-bold ${
                        sim.impact_score > 50 ? 'text-red-400' : sim.impact_score > 25 ? 'text-orange-400' : 'text-gray-400'
                      }`}>{sim.impact_score}%</span>
                    </td>
                    <td className="px-3 py-2 text-center text-gray-400">{sim.edges_lost}</td>
                    <td className="px-3 py-2 text-center text-accent-cyan">{sim.new_components}</td>
                    <td className="px-3 py-2 text-center">
                      {sim.is_articulation_point
                        ? <i className="fas fa-check-circle text-yellow-400" />
                        : <i className="fas fa-minus text-gray-600" />
                      }
                    </td>
                    <td className="px-3 py-2">
                      <div className="w-full h-2 bg-dark-600 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            sim.impact_score > 50 ? 'bg-gradient-to-r from-red-500 to-red-400' :
                            sim.impact_score > 25 ? 'bg-gradient-to-r from-orange-500 to-yellow-500' :
                            'bg-gradient-to-r from-gray-500 to-gray-400'
                          }`}
                          style={{ width: `${sim.impact_score}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function DisruptionMeter({ value }) {
  const color = value > 60 ? 'text-red-400' : value > 30 ? 'text-orange-400' : 'text-yellow-400'
  return (
    <div className="flex items-center gap-2">
      <span className={`text-2xl font-extrabold ${color}`}>{value}%</span>
      <div className="flex gap-0.5">
        {[...Array(5)].map((_, i) => (
          <div key={i} className={`w-1.5 rounded-full transition-all ${
            i < Math.ceil(value / 20)
              ? `${value > 60 ? 'bg-red-500' : value > 30 ? 'bg-orange-500' : 'bg-yellow-500'} h-${3 + i}`
              : 'bg-dark-600 h-3'
          }`} style={{ height: `${8 + (i < Math.ceil(value / 20) ? i * 3 : 0)}px` }} />
        ))}
      </div>
    </div>
  )
}
