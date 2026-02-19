import { useState } from 'react'
import { apiUrl } from '../apiClient'

// ── Helpers ───────────────────────────────────────────────────────────────

function IBMBadge({ hardware }) {
  const isReal = hardware === 'real'
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
      isReal
        ? 'bg-cyan-500/10 border-cyan-400/40 text-cyan-300 shadow-[0_0_12px_rgba(34,211,238,0.25)]'
        : 'bg-violet-500/10 border-violet-400/40 text-violet-300'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isReal ? 'bg-cyan-400 animate-pulse' : 'bg-violet-400'}`} />
      {isReal ? '⚛ REAL IBM QUANTUM HARDWARE' : '⚛ Aer Simulator'}
    </span>
  )
}

function AdvantageBar({ value }) {
  const pct = Math.max(0, Math.min(100, value + 50))
  const positive = value >= 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px]">
        <span className="text-gray-500">Classical greedy baseline</span>
        <span className={`font-bold ${positive ? 'text-emerald-400' : 'text-red-400'}`}>
          {positive ? '+' : ''}{value}% quantum advantage
        </span>
      </div>
      <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            positive ? 'bg-gradient-to-r from-cyan-500 to-emerald-400' : 'bg-gradient-to-r from-red-500 to-orange-400'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function NoiseGauge({ value }) {
  const color = value < 0.4 ? '#22d3ee' : value < 0.7 ? '#f59e0b' : '#f87171'
  const angle = Math.round(value * 180)
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-20 h-10 overflow-hidden">
        <svg viewBox="0 0 100 50" className="w-full h-full" fill="none">
          <path d="M5 50 A45 45 0 0 1 95 50" stroke="#334155" strokeWidth="10" strokeLinecap="round" />
          <path d="M5 50 A45 45 0 0 1 95 50" stroke={color} strokeWidth="10" strokeLinecap="round"
            strokeDasharray={`${value * 141.3} 141.3`} />
          <line x1="50" y1="50"
            x2={50 + 38 * Math.cos(Math.PI - (angle * Math.PI / 180))}
            y2={50 - 38 * Math.sin(Math.PI - (angle * Math.PI / 180))}
            stroke="white" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="50" cy="50" r="4" fill="white" />
        </svg>
      </div>
      <span className="text-[10px] text-gray-400 mt-0.5">Noise: <span style={{ color }}>{(value * 100).toFixed(1)}%</span></span>
    </div>
  )
}

function PartitionViz({ group0, group1, ringId }) {
  return (
    <div className="bg-dark-900/60 rounded-xl border border-dark-500 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-gray-300">Quantum Partition — {ringId}</span>
        <span className="text-[10px] text-gray-500">Max-Cut boundary ✂</span>
      </div>
      <div className="flex gap-3">
        <div className="flex-1 bg-dark-700/50 rounded-lg p-3 border border-cyan-500/20">
          <div className="text-[10px] text-cyan-400 font-bold mb-2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
            Partition |0⟩ — {group0?.length ?? 0} accounts
          </div>
          <div className="flex flex-wrap gap-1">
            {(group0 || []).map(acc => (
              <span key={acc} className="text-[9px] bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 px-1.5 py-0.5 rounded font-mono">{acc}</span>
            ))}
            {!group0?.length && <span className="text-[10px] text-gray-600">—</span>}
          </div>
        </div>
        <div className="flex flex-col items-center justify-center text-red-400 text-[9px] font-bold shrink-0 gap-1">
          <div className="w-px flex-1 bg-gradient-to-b from-transparent via-red-400/60 to-transparent" />
          <span>✂</span>
          <div className="w-px flex-1 bg-gradient-to-b from-transparent via-red-400/60 to-transparent" />
        </div>
        <div className="flex-1 bg-dark-700/50 rounded-lg p-3 border border-violet-500/20">
          <div className="text-[10px] text-violet-400 font-bold mb-2 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-violet-400 inline-block" />
            Partition |1⟩ — {group1?.length ?? 0} accounts
          </div>
          <div className="flex flex-wrap gap-1">
            {(group1 || []).map(acc => (
              <span key={acc} className="text-[9px] bg-violet-500/10 text-violet-300 border border-violet-500/20 px-1.5 py-0.5 rounded font-mono">{acc}</span>
            ))}
            {!group1?.length && <span className="text-[10px] text-gray-600">—</span>}
          </div>
        </div>
      </div>
    </div>
  )
}

function MeasurementHistogram({ measurements, nQubits }) {
  if (!measurements?.length) return null
  const max = measurements[0]?.probability ?? 1
  return (
    <div className="space-y-1.5">
      {measurements.map((m, i) => {
        const bits = (m.bitstring || '').padStart(nQubits, '0')
        const isBest = i === 0
        return (
          <div key={i} className={`flex items-center gap-2 rounded-lg px-2 py-1 ${isBest ? 'bg-cyan-500/5 border border-cyan-500/20' : ''}`}>
            <div className="flex gap-0.5 shrink-0">
              {bits.split('').map((bit, j) => (
                <span key={j} className={`w-4 h-4 flex items-center justify-center rounded text-[9px] font-mono font-bold ${
                  bit === '1' ? 'bg-violet-500/30 text-violet-300' : 'bg-dark-600 text-gray-500'
                }`}>{bit}</span>
              ))}
            </div>
            <div className="flex-1 h-3 bg-dark-600 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${
                isBest ? 'bg-gradient-to-r from-cyan-400 to-violet-500 shadow-[0_0_6px_rgba(34,211,238,0.4)]'
                       : 'bg-gradient-to-r from-dark-400 to-dark-300'
              }`} style={{ width: `${(m.probability / max) * 100}%` }} />
            </div>
            <span className="text-[9px] text-gray-400 w-10 text-right font-mono shrink-0">{(m.probability * 100).toFixed(1)}%</span>
            <span className="text-[9px] text-gray-600 w-6 text-right font-mono shrink-0">✂{m.cut_value}</span>
            {isBest && <i className="fas fa-star text-yellow-400 text-[9px] shrink-0" title="Optimal partition" />}
          </div>
        )
      })}
    </div>
  )
}

function IBMResultCard({ ibm }) {
  if (!ibm) return null
  const isReal = ibm.hardware === 'real'
  const partition = ibm.best_partition || {}
  return (
    <div className={`rounded-xl border overflow-hidden ${
      isReal ? 'border-cyan-400/30 bg-gradient-to-br from-dark-800 to-cyan-950/20 shadow-[0_0_30px_rgba(34,211,238,0.08)]'
             : 'border-violet-500/30 bg-dark-800'
    }`}>
      {/* Header */}
      <div className={`px-5 py-4 border-b flex items-center justify-between flex-wrap gap-3 ${
        isReal ? 'border-cyan-400/20 bg-cyan-500/5' : 'border-violet-500/20 bg-violet-500/5'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${
            isReal ? 'bg-cyan-500/15 shadow-[0_0_12px_rgba(34,211,238,0.3)]' : 'bg-violet-500/15'
          }`}>
            <i className={`fas fa-atom text-lg ${isReal ? 'text-cyan-300' : 'text-violet-400'}`} />
          </div>
          <div>
            <IBMBadge hardware={ibm.hardware} />
            <p className="text-[11px] text-gray-400 mt-1">
              {isReal ? `Backend: ${ibm.backend}` : 'Local Aer Simulation'}
              {ibm.ring_id && ` · Ring: ${ibm.ring_id}`}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-gray-500 block">Execution time</span>
          <span className={`text-xl font-extrabold ${isReal ? 'text-cyan-300' : 'text-violet-400'}`}>
            {ibm.execution_time_seconds}s
          </span>
        </div>
      </div>
      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-dark-500 border-b border-dark-500">
        {[
          { label: 'Qubits', val: ibm.n_qubits, icon: 'fa-microchip', color: 'text-cyan-300' },
          { label: 'Shots', val: ibm.shots?.toLocaleString(), icon: 'fa-bullseye', color: 'text-white' },
          { label: 'Edges Cut', val: `${partition.cut_value ?? 0}/${partition.max_possible_cut ?? 0}`, icon: 'fa-scissors', color: 'text-emerald-400' },
          { label: 'Unique States', val: ibm.total_unique_bitstrings, icon: 'fa-wave-square', color: 'text-violet-400' },
        ].map(({ label, val, icon, color }) => (
          <div key={label} className="p-3 text-center">
            <i className={`fas ${icon} text-gray-500 text-[10px] mb-1 block`} />
            <span className={`text-lg font-extrabold ${color}`}>{val ?? '—'}</span>
            <span className="text-[9px] text-gray-500 block">{label}</span>
          </div>
        ))}
      </div>
      {/* Advantage + noise */}
      <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="space-y-2">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Quantum Advantage vs Classical</span>
          <AdvantageBar value={ibm.quantum_advantage_pct ?? 0} />
          <p className="text-[10px] text-gray-500">
            QAOA cut: <span className="text-white font-bold">{partition.cut_value}</span> ·
            Greedy: <span className="text-white font-bold">{ibm.classical_baseline?.cut_value ?? '?'}</span> ·
            Ratio: <span className="text-emerald-400 font-bold">{((partition.cut_ratio ?? 0) * 100).toFixed(1)}%</span>
          </p>
        </div>
        <div className="flex flex-col items-center justify-center">
          <NoiseGauge value={ibm.noise_entropy ?? 0} />
          <p className="text-[10px] text-gray-500 text-center mt-1">
            {isReal ? 'Hardware decoherence' : 'Simulation entropy'}<br />
            γ={ibm.qaoa_gamma?.toFixed(4)} β={ibm.qaoa_beta?.toFixed(4)}
          </p>
        </div>
      </div>
      {/* Partition */}
      <div className="px-5 pb-4">
        <PartitionViz group0={partition.group_0} group1={partition.group_1} ringId={ibm.ring_id} />
      </div>
      {/* Histogram */}
      {ibm.top_measurements?.length > 0 && (
        <div className="px-5 pb-5 border-t border-dark-500 pt-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Quantum Measurement Distribution</span>
            <span className="text-[10px] text-gray-600">{ibm.shots} shots · top 8</span>
          </div>
          <MeasurementHistogram measurements={ibm.top_measurements} nQubits={ibm.n_qubits} />
          <p className="text-[9px] text-gray-600 mt-2">✂ = edges cut · ★ = optimal Max-Cut solution</p>
        </div>
      )}
      {isReal && (
        <div className="mx-5 mb-5 bg-cyan-500/5 border border-cyan-500/20 rounded-lg px-4 py-2.5 text-[10px] text-cyan-400">
          <i className="fas fa-atom mr-1.5" />
          Results obtained on a <strong>real IBM Quantum superconducting processor</strong> ({ibm.backend}).
          Noise is inherent to physical qubits — not a simulation artefact.
        </div>
      )}
    </div>
  )
}

function IBMRerunButton({ ringId, onResult }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const run = async () => {
    setLoading(true); setError(null)
    try {
      const resp = await fetch(apiUrl('/api/quantum/ibm'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ring_id: ringId }),
      })
      if (!resp.ok) throw new Error((await resp.json()).detail || 'Failed')
      onResult(await resp.json())
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <button onClick={run} disabled={loading}
        className="flex items-center gap-2 bg-cyan-500/10 border border-cyan-400/40 text-cyan-300 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-cyan-500/20 hover:border-cyan-400/70 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_10px_rgba(34,211,238,0.1)]">
        <i className={`fas fa-atom ${loading ? 'animate-spin' : ''}`} />
        {loading ? 'Submitting to IBM Quantum…' : '⚛ Run on IBM Quantum'}
      </button>
      {error && <span className="text-red-400 text-xs"><i className="fas fa-exclamation-triangle mr-1" />{error}</span>}
    </div>
  )
}

export default function QuantumPanel({ data, ibmData: initialIBM, topRingId }) {
  const [ibmResult, setIBMResult] = useState(initialIBM || null)

  if (!data?.available) {
    return (
      <div className="bg-dark-800 border border-dark-500 rounded-xl p-8 text-center space-y-3">
        <i className="fas fa-atom text-5xl text-gray-600 mb-4 block animate-pulse" />
        <p className="text-gray-400 text-lg font-semibold">Quantum Analysis Unavailable</p>
        <p className="text-gray-500 text-sm">{data?.message || 'Qiskit not installed — skipping quantum analysis'}</p>
      </div>
    )
  }

  const results = data.results || []

  return (
    <div className="space-y-6">

      {/* ── IBM Quantum Hero Section ── */}
      <div>
        <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <i className="fas fa-atom text-cyan-400" />
              IBM Quantum Hardware Analysis
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              QAOA Max-Cut on real superconducting qubits · Quantum advantage vs classical greedy
            </p>
          </div>
          <IBMRerunButton ringId={topRingId} onResult={setIBMResult} />
        </div>

        {ibmResult
          ? <IBMResultCard ibm={ibmResult} />
          : (
            <div className="bg-dark-800 border border-dashed border-dark-400 rounded-xl p-6 text-center space-y-2">
              <i className="fas fa-atom text-3xl text-gray-600 block" />
              <p className="text-gray-400 text-sm font-semibold">No IBM Quantum result yet</p>
              <p className="text-gray-600 text-xs">
                Set <code className="bg-dark-600 px-1 rounded text-cyan-400">IBM_QUANTUM_TOKEN</code> env var
                and click &ldquo;Run on IBM Quantum&rdquo; above.
              </p>
              <p className="text-gray-600 text-xs">
                Get a free token at{' '}
                <a href="https://quantum.ibm.com" target="_blank" rel="noreferrer" className="text-cyan-500 hover:underline">
                  quantum.ibm.com
                </a>
              </p>
            </div>
          )
        }
      </div>

      {/* ── Aer Local Simulation Section ── */}
      <div>
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <i className="fas fa-laptop-code text-violet-400" />
          <h3 className="text-base font-bold text-white">Local QAOA Simulation (Aer)</h3>
          <span className="text-[10px] text-gray-500 bg-dark-700 px-2 py-0.5 rounded-full">
            {data.circuits_executed} circuits executed &middot; {data.circuits_skipped ?? 0} heuristic fallback
          </span>
        </div>

        {/* Summary strip */}
        <div className="bg-gradient-to-r from-violet-500/10 to-cyan-500/10 border border-violet-500/25 rounded-xl p-4 mb-4">
          <div className="flex flex-wrap gap-6 items-center">
            <div>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Algorithm</span>
              <p className="text-sm font-bold text-violet-400">QAOA Max-Cut p=1</p>
            </div>
            <div>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Max Qubits</span>
              <p className="text-2xl font-extrabold text-white">{data.max_qubits ?? 6}</p>
            </div>
            <div>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Total Shots</span>
              <p className="text-2xl font-extrabold text-white">
                {((data.circuits_executed ?? 0) * 256).toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Rings Analyzed</span>
              <p className="text-2xl font-extrabold text-white">{results.length}</p>
            </div>
          </div>
        </div>

        {/* Circuit cards grid */}
        {results.length > 0
          ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {results.map((r, i) => <CircuitCard key={i} result={r} index={i} />)}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <i className="fas fa-atom text-3xl mb-3 block" />
              No quantum circuits were generated for this dataset.
            </div>
          )
        }
      </div>
    </div>
  )
}

/* ─── Circuit Card ─────────────────────────────────────────── */
function CircuitCard({ result, index }) {
  const [expanded, setExpanded] = useState(false)
  const hasError = !!result.error
  const measurements = result.top_measurements || []
  const suspiciousSet = result.suspicious_set || []

  return (
    <div className={`bg-dark-800 border rounded-xl overflow-hidden transition-all hover:shadow-lg ${
      hasError ? 'border-red-500/40' : 'border-dark-500 hover:border-violet-500/40'
    }`}>
      {/* Header */}
      <div className="px-4 py-2.5 bg-gradient-to-r from-violet-500/10 to-transparent border-b border-dark-500 flex items-center justify-between">
        <span className="text-xs font-bold text-violet-400 flex items-center gap-1.5">
          <i className="fas fa-atom" />Circuit #{index + 1}
        </span>
        <span className="text-[10px] text-gray-400 font-mono bg-dark-600 px-2 py-0.5 rounded">{result.ring_id}</span>
      </div>

      {hasError ? (
        <div className="p-4 text-center">
          <i className="fas fa-exclamation-triangle text-red-400 text-xl mb-2 block" />
          <p className="text-red-400 text-xs">{result.error}</p>
        </div>
      ) : (
        <>
          {/* Circuit image */}
          {result.circuit_image ? (
            <div
              className="p-3 bg-white/95 border-b border-dark-500 cursor-pointer rounded-sm mx-1 mt-1 shadow-inner"
              onClick={() => setExpanded(!expanded)}
            >
              <img
                src={`data:image/png;base64,${result.circuit_image}`}
                alt={`QAOA circuit — ${result.ring_id}`}
                className={`w-full h-auto rounded transition-all ${expanded ? '' : 'max-h-44 object-cover object-left-top'}`}
                loading="lazy"
              />
              {!expanded && (
                <div className="text-center mt-1">
                  <span className="text-[9px] text-gray-500 hover:text-cyan-400 cursor-pointer">
                    <i className="fas fa-expand-alt mr-1" />Click to expand
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 bg-dark-900 border-b border-dark-500 text-center text-gray-600 text-xs">
              <i className="fas fa-image mr-1" />Circuit image not available
            </div>
          )}

          {/* Stats grid */}
          <div className="p-3 grid grid-cols-2 gap-2">
            <StatItem label="Qubits" value={result.n_qubits} icon="fa-microchip" />
            <StatItem label="Gate Count" value={result.gate_count} icon="fa-layer-group" />
            <StatItem label="Depth" value={result.circuit_depth} icon="fa-arrows-left-right" />
            <StatItem label="Partition" value={result.partition_score?.toFixed(3)} icon="fa-cut" color="text-cyan-400" />
          </div>

          {/* Optimal bitstring */}
          {result.optimal_bitstring && (
            <div className="px-3 pb-2">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">Optimal Bitstring</span>
              <div className="flex items-center gap-1 mt-1 flex-wrap">
                {result.optimal_bitstring.split('').map((bit, bi) => (
                  <span key={bi} className={`w-5 h-5 flex items-center justify-center rounded text-[10px] font-bold ${
                    bit === '1'
                      ? 'bg-violet-500/30 text-violet-300 border border-violet-500/40'
                      : 'bg-dark-600 text-gray-500 border border-dark-500'
                  }`}>
                    {bit}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Suspicious set */}
          {suspiciousSet.length > 0 && (
            <div className="px-3 pb-2">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                Suspicious Partition ({suspiciousSet.length} accounts)
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {suspiciousSet.map(acc => (
                  <span key={acc} className="text-[9px] bg-red-500/15 text-red-400 border border-red-500/25 px-1.5 py-0.5 rounded font-mono">
                    {acc}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Measurement histogram */}
          {measurements.length > 0 && (
            <div className="px-3 pb-3 border-t border-dark-500 pt-2">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">Measurement Distribution</span>
              <div className="mt-1.5 space-y-1">
                {measurements.slice(0, 5).map((m, j) => (
                  <div key={j} className="flex items-center gap-2">
                    <span className="font-mono text-[9px] text-cyan-400 w-16 shrink-0 text-right">|{m.bitstring}&#x27E9;</span>
                    <div className="flex-1 h-3 bg-dark-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full transition-all"
                        style={{ width: `${Math.max(m.probability * 100, 2)}%` }}
                      />
                    </div>
                    <span className="text-[9px] text-gray-400 w-12 text-right font-mono">{(m.probability * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatItem({ label, value, icon, color = 'text-white' }) {
  return (
    <div className="flex items-center gap-2 bg-dark-700/50 rounded-lg px-2.5 py-1.5">
      <i className={`fas ${icon} text-[10px] text-gray-500`} />
      <div>
        <span className="text-[9px] text-gray-500 block leading-tight">{label}</span>
        <span className={`text-xs font-bold ${color}`}>{value ?? '—'}</span>
      </div>
    </div>
  )
}
