import { useState, useCallback } from 'react'
import { apiUrl } from '../apiClient'

export default function WhatIfSimulator({ graphData, accounts, rings }) {
  const [selectedNodes, setSelectedNodes] = useState(new Set())
  const [simResult, setSimResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  if (!accounts || accounts.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] bg-dark-800 border border-dark-500 rounded-xl text-gray-500">
        <div className="text-center">
          <i className="fas fa-flask-vial text-5xl mb-3 block animate-pulse" />
          <p>No accounts available for simulation</p>
        </div>
      </div>
    )
  }

  const toggleNode = (nodeId) => {
    setSelectedNodes(prev => {
      const next = new Set(prev)
      if (next.has(nodeId)) next.delete(nodeId)
      else next.add(nodeId)
      return next
    })
    setSimResult(null) // Reset when selection changes
  }

  const runSimulation = async () => {
    if (selectedNodes.size === 0) return
    setLoading(true)
    setError(null)

    try {
      const resp = await fetch('/api/whatif', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes: [...selectedNodes] }),
      })
      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || 'Simulation failed')
      }
      const data = await resp.json()
      setSimResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const clearSelection = () => {
    setSelectedNodes(new Set())
    setSimResult(null)
  }

  return (
    <div className="space-y-5 animate-in">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-900/20 via-dark-800 to-cyan-900/15 border border-blue-500/20 p-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(88,166,255,0.06),transparent_60%)]" />
        <div className="absolute top-3 right-4 opacity-[0.03]">
          <i className="fas fa-flask-vial text-[120px] text-blue-400" />
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <i className="fas fa-flask-vial text-blue-400 text-sm" />
            </div>
            <h2 className="text-lg font-black text-white tracking-tight">What-If Simulator</h2>
            <span className="ml-auto px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/25">
              INTERACTIVE
            </span>
          </div>
          <p className="text-xs text-gray-400 max-w-2xl">
            Select accounts to remove and simulate the impact on the fraud network in real-time.
            Click accounts below to build your removal strategy, then hit "Run Simulation".
          </p>
        </div>
      </div>

      {/* Selection Panel */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
        <div className="px-4 py-2.5 bg-dark-700/50 border-b border-dark-500 flex items-center justify-between">
          <span className="text-xs font-bold text-gray-300">
            <i className="fas fa-hand-pointer mr-1.5 text-blue-400" />
            Select Accounts to Remove
          </span>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-500">
              {selectedNodes.size} selected
            </span>
            {selectedNodes.size > 0 && (
              <button onClick={clearSelection}
                className="text-[10px] text-gray-500 hover:text-white border border-dark-500 px-2 py-0.5 rounded hover:border-red-500/40 transition">
                <i className="fas fa-times mr-1" />Clear
              </button>
            )}
          </div>
        </div>

        {/* Account grid */}
        <div className="p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 max-h-[280px] overflow-y-auto">
          {accounts.map((acc) => {
            const isSelected = selectedNodes.has(acc.account_id)
            return (
              <button
                key={acc.account_id}
                onClick={() => toggleNode(acc.account_id)}
                className={`relative px-3 py-2.5 rounded-xl text-left transition-all border group ${isSelected
                  ? 'bg-red-500/10 border-red-500/40 shadow-lg shadow-red-500/10 scale-[0.98]'
                  : 'bg-dark-700 border-dark-500 hover:border-blue-500/30 hover:bg-dark-700/80'
                  }`}
              >
                {isSelected && (
                  <div className="absolute top-1.5 right-1.5">
                    <i className="fas fa-circle-xmark text-red-400 text-xs" />
                  </div>
                )}
                <span className={`text-[10px] font-mono font-bold block truncate ${isSelected ? 'text-red-400' : 'text-gray-300'
                  }`}>{acc.account_id}</span>
                <div className="flex items-center gap-1.5 mt-1">
                  <div className={`w-8 h-1.5 rounded-full overflow-hidden ${isSelected ? 'bg-red-800' : 'bg-dark-600'}`}>
                    <div
                      className={`h-full rounded-full ${acc.suspicion_score >= 70 ? 'bg-red-500' :
                        acc.suspicion_score >= 40 ? 'bg-orange-500' : 'bg-yellow-500'
                        }`}
                      style={{ width: `${acc.suspicion_score}%` }}
                    />
                  </div>
                  <span className={`text-[9px] font-bold ${acc.suspicion_score >= 70 ? 'text-red-400' :
                    acc.suspicion_score >= 40 ? 'text-orange-400' : 'text-yellow-400'
                    }`}>{acc.suspicion_score}</span>
                </div>
              </button>
            )
          })}
        </div>

        {/* Selected summary & Run button */}
        {selectedNodes.size > 0 && (
          <div className="px-4 py-3 border-t border-dark-500 bg-dark-700/30 flex flex-wrap items-center gap-3">
            <div className="flex flex-wrap gap-1 flex-1">
              {[...selectedNodes].map(n => (
                <span key={n} className="px-2 py-0.5 text-[9px] font-mono font-bold bg-red-500/15 text-red-400 border border-red-500/25 rounded flex items-center gap-1">
                  {n}
                  <i className="fas fa-times text-[7px] cursor-pointer hover:text-white" onClick={(e) => { e.stopPropagation(); toggleNode(n) }} />
                </span>
              ))}
            </div>
            <button
              onClick={runSimulation}
              disabled={loading}
              className="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-bold text-xs hover:shadow-lg hover:shadow-blue-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <><i className="fas fa-spinner fa-spin mr-1.5" />Simulating...</>
              ) : (
                <><i className="fas fa-play mr-1.5" />Run Simulation</>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-3 text-red-400 text-xs">
          <i className="fas fa-exclamation-triangle mr-2" />{error}
        </div>
      )}

      {/* Results */}
      {simResult && <SimulationResults result={simResult} />}
    </div>
  )
}

function SimulationResults({ result }) {
  const { before, after, delta, ring_impacts, account_impacts, flow_impact, cascade_effects, effectiveness_score } = result

  return (
    <div className="space-y-4 animate-in">
      {/* Effectiveness Score */}
      <div className="relative overflow-hidden bg-dark-800 border border-dark-500 rounded-2xl p-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(88,166,255,0.04),transparent_60%)]" />
        <div className="relative z-10 text-center">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-2">Removal Effectiveness</span>
          <div className="inline-flex items-center gap-4">
            <div className={`text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r ${effectiveness_score.overall > 60 ? 'from-green-400 to-emerald-400' :
              effectiveness_score.overall > 30 ? 'from-yellow-400 to-orange-400' :
                'from-red-400 to-orange-400'
              }`}>
              {effectiveness_score.grade}
            </div>
            <div className="text-left">
              <span className="text-3xl font-extrabold text-white">{effectiveness_score.overall}%</span>
              <div className="flex gap-3 mt-1">
                <MicroStat label="Edge Disruption" value={`${effectiveness_score.edge_disruption}%`} />
                <MicroStat label="Ring Destruction" value={`${effectiveness_score.ring_destruction_rate}%`} />
                <MicroStat label="Fragmentation" value={`${effectiveness_score.fragmentation_increase}%`} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Before / After Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StateCard state={before} label="Before Removal" color="text-gray-400" borderColor="border-dark-500" />
        <StateCard state={after} label="After Removal" color="text-blue-400" borderColor="border-blue-500/30" />
      </div>

      {/* Delta Metrics */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl p-4">
        <span className="text-xs font-bold text-gray-300 block mb-3">
          <i className="fas fa-arrow-right-arrow-left mr-1.5 text-accent-cyan" />Impact Delta
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(delta).map(([key, d]) => (
            <DeltaCard key={key} label={key.replace(/_/g, ' ')} delta={d} />
          ))}
        </div>
      </div>

      {/* Ring Impacts */}
      {ring_impacts && ring_impacts.length > 0 && (
        <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-dark-700/50 border-b border-dark-500 flex items-center gap-2">
            <i className="fas fa-ring text-orange-400 text-sm" />
            <span className="text-xs font-bold text-gray-300">Ring Impact Analysis</span>
          </div>
          <div className="p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {ring_impacts.map((ri, i) => (
              <RingImpactCard key={ri.ring_id} impact={ri} />
            ))}
          </div>
        </div>
      )}

      {/* Flow Disruption */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <i className="fas fa-money-bill-wave text-green-400 text-sm" />
          <span className="text-xs font-bold text-gray-300">Money Flow Disruption</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <FlowStat label="Total Flow" value={`$${flow_impact.total_flow.toLocaleString()}`} icon="fa-dollar-sign" />
          <FlowStat label="Disrupted" value={`$${flow_impact.disrupted_flow.toLocaleString()}`} icon="fa-ban" color="text-red-400" />
          <FlowStat label="Flow Disruption" value={`${flow_impact.disruption_pct}%`} icon="fa-chart-pie" color="text-orange-400" />
          <FlowStat label="Txns Disrupted" value={`${flow_impact.disrupted_transactions}/${flow_impact.total_transactions}`} icon="fa-exchange-alt" />
        </div>
        {/* Visual bar */}
        <div className="mt-3 w-full h-3 bg-dark-600 rounded-full overflow-hidden relative">
          <div className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full absolute left-0"
            style={{ width: `${100 - flow_impact.disruption_pct}%` }} />
          <div className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full absolute right-0"
            style={{ width: `${flow_impact.disruption_pct}%` }} />
        </div>
        <div className="flex justify-between text-[9px] text-gray-500 mt-1">
          <span>Remaining Flow</span>
          <span>Disrupted Flow</span>
        </div>
      </div>

      {/* Risk Reduction */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <i className="fas fa-shield-halved text-accent-purple text-sm" />
          <span className="text-xs font-bold text-gray-300">Risk Reduction</span>
        </div>
        <div className="flex items-center gap-6">
          <div>
            <span className="text-[10px] text-gray-500 block">Risk Removed</span>
            <span className="text-xl font-extrabold text-green-400">{account_impacts.total_risk_removed}</span>
          </div>
          <div className="text-4xl text-gray-600">→</div>
          <div>
            <span className="text-[10px] text-gray-500 block">Risk Remaining</span>
            <span className="text-xl font-extrabold text-orange-400">{account_impacts.total_risk_remaining}</span>
          </div>
          <div className="ml-auto">
            <span className="text-[10px] text-gray-500 block">Reduction</span>
            <span className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-cyan-400">
              {account_impacts.risk_reduction_pct}%
            </span>
          </div>
        </div>
      </div>

      {/* Cascade Effects */}
      {cascade_effects && cascade_effects.length > 0 && (
        <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-dark-700/50 border-b border-dark-500 flex items-center gap-2">
            <i className="fas fa-wave-square text-accent-cyan text-sm" />
            <span className="text-xs font-bold text-gray-300">Cascade Effects — Most Impacted Remaining Accounts</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="text-gray-500 uppercase text-[9px] tracking-wider border-b border-dark-500">
                  <th className="px-4 py-2 text-left">Account</th>
                  <th className="px-3 py-2 text-center">Connections Lost</th>
                  <th className="px-3 py-2 text-center">In Lost</th>
                  <th className="px-3 py-2 text-center">Out Lost</th>
                  <th className="px-3 py-2 text-right">Flow Disrupted</th>
                  <th className="px-3 py-2 text-center">Suspicious?</th>
                </tr>
              </thead>
              <tbody>
                {cascade_effects.slice(0, 10).map((c, i) => (
                  <tr key={c.account_id} className="border-b border-dark-600/50 hover:bg-dark-700/30 transition-colors">
                    <td className="px-4 py-2 font-mono font-bold text-gray-300">{c.account_id}</td>
                    <td className="px-3 py-2 text-center font-bold text-orange-400">{c.connections_lost}</td>
                    <td className="px-3 py-2 text-center text-gray-400">{c.incoming_lost}</td>
                    <td className="px-3 py-2 text-center text-gray-400">{c.outgoing_lost}</td>
                    <td className="px-3 py-2 text-right font-mono text-accent-cyan">${c.flow_disrupted.toLocaleString()}</td>
                    <td className="px-3 py-2 text-center">
                      {c.is_suspicious
                        ? <span className="px-1.5 py-0.5 bg-red-500/15 text-red-400 rounded text-[9px] font-bold">YES</span>
                        : <span className="text-gray-600">—</span>
                      }
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

function MicroStat({ label, value }) {
  return (
    <div>
      <span className="text-[9px] text-gray-500 block">{label}</span>
      <span className="text-xs font-bold text-gray-300">{value}</span>
    </div>
  )
}

function StateCard({ state, label, color, borderColor }) {
  return (
    <div className={`bg-dark-800 border ${borderColor} rounded-xl p-4`}>
      <span className={`text-xs font-bold ${color} block mb-3`}>
        <i className={`fas fa-${label.includes('After') ? 'arrow-right' : 'arrow-left'} mr-1.5`} />{label}
      </span>
      <div className="grid grid-cols-2 gap-2">
        <StatBox label="Nodes" value={state.nodes} />
        <StatBox label="Edges" value={state.edges} />
        <StatBox label="Components" value={state.components} />
        <StatBox label="Largest CC" value={state.largest_component} />
        <StatBox label="Density" value={state.density.toFixed(4)} />
        <StatBox label="Avg Degree" value={state.avg_degree} />
      </div>
    </div>
  )
}

function StatBox({ label, value }) {
  return (
    <div className="bg-dark-700/50 rounded-lg px-2.5 py-1.5">
      <span className="text-[9px] text-gray-500 block">{label}</span>
      <span className="text-sm font-bold text-white">{value}</span>
    </div>
  )
}

function DeltaCard({ label, delta }) {
  const isPositive = delta.change > 0
  const isNegative = delta.change < 0
  return (
    <div className="bg-dark-700/50 rounded-xl p-2.5">
      <span className="text-[9px] text-gray-500 uppercase block mb-1">{label}</span>
      <div className="flex items-center gap-1.5">
        <span className={`text-xs font-bold ${isNegative ? 'text-red-400' : isPositive ? 'text-green-400' : 'text-gray-400'
          }`}>
          {isPositive ? '+' : ''}{typeof delta.change === 'number' && delta.change % 1 !== 0 ? delta.change.toFixed(4) : delta.change}
        </span>
        <span className={`text-[9px] ${isNegative ? 'text-red-400/60' : isPositive ? 'text-green-400/60' : 'text-gray-500'
          }`}>
          ({delta.change_pct > 0 ? '+' : ''}{delta.change_pct}%)
        </span>
      </div>
    </div>
  )
}

function RingImpactCard({ impact }) {
  const statusColors = {
    DESTROYED: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/25', icon: 'fa-skull-crossbones' },
    CRITICALLY_DAMAGED: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/25', icon: 'fa-heart-crack' },
    FRAGMENTED: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', border: 'border-yellow-500/25', icon: 'fa-puzzle-piece' },
    WEAKENED: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/25', icon: 'fa-shield-virus' },
    INTACT: { bg: 'bg-gray-500/15', text: 'text-gray-400', border: 'border-gray-500/25', icon: 'fa-shield' },
  }
  const style = statusColors[impact.status] || statusColors.INTACT

  return (
    <div className={`${style.bg} border ${style.border} rounded-xl p-3`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-white">{impact.ring_id}</span>
        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${style.bg} ${style.text} border ${style.border}`}>
          <i className={`fas ${style.icon} mr-1`} />{impact.status.replace('_', ' ')}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-1.5 text-[10px]">
        <div>
          <span className="text-gray-500">Original</span>
          <span className="block font-bold text-gray-300">{impact.original_size} members</span>
        </div>
        <div>
          <span className="text-gray-500">Surviving</span>
          <span className="block font-bold text-gray-300">{impact.surviving_members} members</span>
        </div>
      </div>
      <div className="mt-2 w-full h-2 bg-dark-600/50 rounded-full overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r from-red-500 to-orange-500 transition-all`}
          style={{ width: `${impact.disruption_pct}%` }} />
      </div>
      <span className="text-[9px] text-gray-500 mt-1 block text-right">{impact.disruption_pct}% disrupted</span>
    </div>
  )
}

function FlowStat({ label, value, icon, color = 'text-gray-300' }) {
  return (
    <div className="bg-dark-700/50 rounded-xl p-2.5">
      <div className="flex items-center gap-1.5 mb-1">
        <i className={`fas ${icon} text-[10px] text-gray-500`} />
        <span className="text-[9px] text-gray-500">{label}</span>
      </div>
      <span className={`text-sm font-bold ${color}`}>{value}</span>
    </div>
  )
}
