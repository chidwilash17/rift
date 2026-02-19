import { useState, useEffect, useRef } from 'react'

export default function CrimeTeamPanel({ data }) {
  const [activeView, setActiveView] = useState('briefing')
  const [visibleMsgs, setVisibleMsgs] = useState(0)
  const chatRef = useRef(null)

  if (!data) {
    return (
      <div className="flex items-center justify-center h-[400px] bg-dark-800 border border-dark-500 rounded-xl text-gray-500">
        <div className="text-center">
          <i className="fas fa-user-secret text-5xl mb-3 block animate-pulse" />
          <p>No investigation data available</p>
        </div>
      </div>
    )
  }

  const { agents, conversation, case_file, evidence_chain, confidence_assessment, recommended_actions, investigation_timeline } = data
  const aiPowered = data.ai_powered || false
  const llmModel = data.llm_model || null

  const views = [
    { id: 'briefing', label: 'Live Briefing', icon: 'fa-comments' },
    { id: 'casefile', label: 'Case File', icon: 'fa-folder-open' },
    { id: 'evidence', label: 'Evidence Chain', icon: 'fa-link' },
    { id: 'actions', label: 'Actions', icon: 'fa-bolt' },
    { id: 'timeline', label: 'Timeline', icon: 'fa-clock-rotate-left' },
  ]

  return (
    <div className="space-y-5 animate-in">
      {/* AI-Powered Banner */}
      {aiPowered && (
        <div className="relative overflow-hidden bg-gradient-to-r from-violet-500/10 via-fuchsia-500/10 to-cyan-500/10 border border-violet-500/25 rounded-xl px-5 py-3">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-violet-500/5 via-transparent to-transparent" />
          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/25">
                <i className="fas fa-microchip text-white text-sm" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black text-white tracking-wide">AI-POWERED INVESTIGATION</span>
                  <span className="px-2 py-0.5 bg-violet-500/20 border border-violet-500/30 rounded-full text-[9px] font-bold text-violet-300 animate-pulse">
                    LIVE
                  </span>
                </div>
                <span className="text-[10px] text-gray-400">
                  Dynamic analysis by <span className="text-violet-300 font-semibold">{llmModel}</span> — 
                  each conversation is unique and adapts to the dataset in real-time
                </span>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-violet-400 animate-ping" />
              <span className="w-1 h-1 rounded-full bg-fuchsia-400 animate-ping" style={{ animationDelay: '150ms' }} />
              <span className="w-1 h-1 rounded-full bg-cyan-400 animate-ping" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
      {/* Agent Roster */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {Object.entries(agents).map(([key, agent]) => (
          <AgentCard key={key} agentKey={key} agent={agent} />
        ))}
      </div>

      {/* Confidence Banner */}
      <ConfidenceBanner confidence={confidence_assessment} />

      {/* View Selector */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {views.map(v => (
          <button
            key={v.id}
            onClick={() => setActiveView(v.id)}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
              activeView === v.id
                ? 'bg-gradient-to-r from-green-500/20 to-blue-500/20 border-green-500/40 text-white shadow-lg shadow-green-500/10'
                : 'border-dark-500 text-gray-400 hover:border-green-500/30 hover:text-gray-200'
            }`}
          >
            <i className={`fas ${v.icon} mr-1.5`} />{v.label}
          </button>
        ))}
      </div>

      {/* View Content */}
      <div className="animate-fade">
        {activeView === 'briefing' && <LiveBriefing conversation={conversation} chatRef={chatRef} />}
        {activeView === 'casefile' && <CaseFile caseFile={case_file} />}
        {activeView === 'evidence' && <EvidenceChain evidence={evidence_chain} />}
        {activeView === 'actions' && <ActionsPanel actions={recommended_actions} />}
        {activeView === 'timeline' && <Timeline timeline={investigation_timeline} />}
      </div>
    </div>
  )
}

function AgentCard({ agentKey, agent }) {
  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl p-4 hover:border-opacity-60 transition-all group relative overflow-hidden"
      style={{ borderColor: `${agent.color}30` }}>
      <div className="absolute inset-0 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity"
        style={{ background: `radial-gradient(circle at top right, ${agent.color}, transparent 70%)` }} />
      <div className="relative z-10">
        <div className="flex items-center gap-2.5 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg"
            style={{ background: `${agent.color}20`, boxShadow: `0 0 20px ${agent.color}15` }}>
            <i className={`fas ${agent.avatar} text-lg`} style={{ color: agent.color }} />
          </div>
          <div>
            <span className="text-xs font-black text-white block leading-tight">{agent.name}</span>
            <span className="text-[10px] font-semibold" style={{ color: agent.color }}>{agent.title}</span>
          </div>
        </div>
        <p className="text-[10px] text-gray-500 leading-relaxed">{agent.specialty}</p>
        <div className="mt-2 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: agent.color }} />
          <span className="text-[9px] text-gray-500 italic">{agent.personality}</span>
        </div>
      </div>
    </div>
  )
}

function ConfidenceBanner({ confidence }) {
  const levelColor = {
    'VERY HIGH': 'from-green-500 to-emerald-500',
    'HIGH': 'from-blue-500 to-cyan-500',
    'MODERATE': 'from-yellow-500 to-orange-500',
    'LOW': 'from-red-500 to-orange-500',
  }
  const gradient = levelColor[confidence.confidence_level] || 'from-gray-500 to-gray-400'

  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl p-5 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1">
        <div className={`h-full bg-gradient-to-r ${gradient} transition-all duration-1000`}
          style={{ width: `${confidence.overall_confidence}%` }} />
      </div>
      <div className="flex flex-wrap items-center gap-6">
        <div>
          <span className="text-[10px] text-gray-500 uppercase tracking-wider block">Overall Confidence</span>
          <span className={`text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r ${gradient}`}>
            {confidence.overall_confidence}%
          </span>
          <span className={`ml-2 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r ${gradient} text-white`}>
            {confidence.confidence_level}
          </span>
        </div>
        <div className="flex gap-6">
          <MiniGauge label="Multi-Agent Agreement" value={confidence.multi_agent_agreement} />
          <MiniGauge label="Quantum-Classical" value={confidence.quantum_classical_agreement} />
          <div>
            <span className="text-[10px] text-gray-500 block">Consensus Accounts</span>
            <span className="text-lg font-bold text-white">
              {confidence.accounts_with_multi_agent_consensus}
              <span className="text-gray-500 text-xs font-normal">/{confidence.total_suspicious}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function MiniGauge({ label, value }) {
  return (
    <div>
      <span className="text-[10px] text-gray-500 block">{label}</span>
      <div className="flex items-center gap-2">
        <div className="w-16 h-2 bg-dark-600 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-accent-blue to-accent-cyan rounded-full transition-all"
            style={{ width: `${value}%` }} />
        </div>
        <span className="text-xs font-bold text-white">{value}%</span>
      </div>
    </div>
  )
}

function LiveBriefing({ conversation, chatRef }) {
  const [revealed, setRevealed] = useState(1)
  const hasAI = conversation.some(m => m.ai_generated)

  useEffect(() => {
    if (revealed < conversation.length) {
      const timer = setTimeout(() => setRevealed(r => r + 1), 600)
      return () => clearTimeout(timer)
    }
  }, [revealed, conversation.length])

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [revealed])

  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
      <div className="px-4 py-2.5 bg-dark-700/50 border-b border-dark-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full animate-pulse ${hasAI ? 'bg-violet-500' : 'bg-red-500'}`} />
          <span className="text-xs font-bold text-gray-300">
            {hasAI ? 'AI LIVE — Dynamic Multi-Agent Investigation' : 'LIVE — Multi-Agent Investigation Briefing'}
          </span>
          {hasAI && (
            <span className="px-1.5 py-0.5 bg-violet-500/15 border border-violet-500/25 rounded text-[8px] font-bold text-violet-400">
              <i className="fas fa-microchip mr-1" />Groq LLM
            </span>
          )}
        </div>
        <button onClick={() => setRevealed(conversation.length)}
          className="text-[10px] text-gray-500 hover:text-white border border-dark-500 px-2 py-0.5 rounded hover:border-accent-blue transition">
          Show All
        </button>
      </div>
      <div ref={chatRef} className="p-4 space-y-3 max-h-[600px] overflow-y-auto scroll-smooth">
        {conversation.slice(0, revealed).map((msg, i) => (
          <ChatMessage key={i} msg={msg} index={i} isNew={i === revealed - 1} />
        ))}
        {revealed < conversation.length && (
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-[10px] text-gray-500 italic">Agent typing...</span>
          </div>
        )}
      </div>
    </div>
  )
}

function ChatMessage({ msg, index, isNew }) {
  const isLeft = ['detective', 'quantum'].includes(msg.agent_key)

  return (
    <div className={`flex gap-3 ${isLeft ? '' : 'flex-row-reverse'} ${isNew ? 'animate-in' : ''}`}>
      {/* Avatar */}
      <div className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center shadow-lg"
        style={{ background: `${msg.color}20`, boxShadow: `0 0 15px ${msg.color}15` }}>
        <i className={`fas ${msg.avatar}`} style={{ color: msg.color, fontSize: '14px' }} />
      </div>
      {/* Bubble */}
      <div className={`max-w-[75%] ${isLeft ? '' : 'text-right'}`}>
        <div className="flex items-center gap-2 mb-0.5" style={{ justifyContent: isLeft ? 'flex-start' : 'flex-end' }}>
          <span className="text-[10px] font-bold" style={{ color: msg.color }}>{msg.agent_name}</span>
          <span className="text-[8px] text-gray-600">{msg.agent_title}</span>
          {msg.ai_generated && (
            <span className="px-1.5 py-0.5 bg-violet-500/15 border border-violet-500/25 rounded text-[7px] font-bold text-violet-400">
              AI
            </span>
          )}
        </div>
        <div className={`bg-dark-700 border border-dark-500 rounded-xl px-3.5 py-2.5 text-xs text-gray-300 leading-relaxed ${
          isLeft ? 'rounded-tl-sm' : 'rounded-tr-sm'
        }`} style={{ borderColor: `${msg.color}15` }}>
          <FormattedText text={msg.content} />
        </div>
        <span className="text-[8px] text-gray-600 mt-0.5 block"
          style={{ textAlign: isLeft ? 'left' : 'right' }}>
          Phase: {msg.phase}
        </span>
      </div>
    </div>
  )
}

function FormattedText({ text }) {
  // Simple markdown: **bold**, numbered lists
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>
        }
        // Handle newlines
        return part.split('\n').map((line, j) => (
          <span key={`${i}-${j}`}>
            {j > 0 && <br />}
            {line}
          </span>
        ))
      })}
    </>
  )
}

function CaseFile({ caseFile }) {
  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-dark-700 to-dark-800 border-b border-dark-500 p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-accent-green/10 flex items-center justify-center">
              <i className="fas fa-folder-open text-accent-green text-xl" />
            </div>
            <div>
              <span className="text-[9px] text-gray-500 uppercase tracking-widest block">Case Number</span>
              <span className="text-lg font-black text-white tracking-wide">{caseFile.case_number}</span>
            </div>
          </div>
          <div className="text-right">
            <span className={`px-3 py-1 rounded-full text-[10px] font-bold border ${
              caseFile.priority === 'HIGH'
                ? 'bg-red-500/15 text-red-400 border-red-500/25'
                : 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25'
            }`}>
              {caseFile.priority} PRIORITY
            </span>
          </div>
        </div>
        <div className="text-xs text-gray-400 font-mono">{caseFile.classification}</div>
        <div className="mt-1 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          <span className="text-[10px] text-green-400 font-semibold">{caseFile.status}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-dark-500">
        <CaseStat label="Fraud Rings" value={caseFile.total_rings} icon="fa-ring" color="text-red-400" />
        <CaseStat label="Suspicious" value={caseFile.total_suspicious} icon="fa-user-shield" color="text-orange-400" />
        <CaseStat label="Quantum Circuits" value={caseFile.quantum_circuits_used} icon="fa-atom" color="text-cyan-400" />
        <CaseStat label="Processing" value={`${caseFile.processing_time}s`} icon="fa-bolt" color="text-yellow-400" />
      </div>

      {/* Risk Distribution */}
      <div className="p-4">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-2">Risk Distribution</span>
        <div className="flex gap-2 items-end h-16">
          <RiskBar label="High" value={caseFile.risk_distribution.high} color="bg-red-500" max={caseFile.total_suspicious} />
          <RiskBar label="Medium" value={caseFile.risk_distribution.medium} color="bg-orange-500" max={caseFile.total_suspicious} />
          <RiskBar label="Low" value={caseFile.risk_distribution.low} color="bg-yellow-500" max={caseFile.total_suspicious} />
        </div>
      </div>

      {/* Top Patterns */}
      <div className="p-4 border-t border-dark-500">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-2">Detected Patterns</span>
        <div className="flex flex-wrap gap-1.5">
          {(caseFile.top_patterns || []).map((p, i) => (
            <span key={i} className="px-2.5 py-1 bg-dark-700 border border-dark-500 rounded-lg text-[10px] text-gray-300 font-mono">
              {p.pattern} <span className="text-accent-blue font-bold">×{p.frequency}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

function CaseStat({ label, value, icon, color }) {
  return (
    <div className="bg-dark-800 p-3 text-center">
      <i className={`fas ${icon} ${color} text-sm mb-1 block`} />
      <span className="text-lg font-extrabold text-white block">{value}</span>
      <span className="text-[9px] text-gray-500 uppercase">{label}</span>
    </div>
  )
}

function RiskBar({ label, value, color, max }) {
  const pct = max > 0 ? (value / max) * 100 : 0
  return (
    <div className="flex-1 flex flex-col items-center gap-1">
      <span className="text-xs font-bold text-white">{value}</span>
      <div className="w-full bg-dark-600 rounded-t-lg overflow-hidden" style={{ height: `${Math.max(pct, 8)}%`, minHeight: '4px' }}>
        <div className={`w-full h-full ${color} rounded-t-lg`} />
      </div>
      <span className="text-[9px] text-gray-500">{label}</span>
    </div>
  )
}

function EvidenceChain({ evidence }) {
  return (
    <div className="space-y-3">
      {evidence.map((e, i) => (
        <div key={i} className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden hover:border-accent-blue/20 transition-all">
          <div className="flex items-center gap-3 px-4 py-3 bg-dark-700/30 border-b border-dark-500">
            <div className="w-8 h-8 rounded-lg bg-accent-blue/10 flex items-center justify-center text-accent-blue text-sm">
              <i className={`fas fa-${e.agent_key === 'detective' ? 'magnifying-glass' : e.agent_key === 'profiler' ? 'brain' : 'atom'}`} />
            </div>
            <div className="flex-1">
              <span className="text-xs font-bold text-white">{e.source}</span>
              <span className="text-[10px] text-gray-500 ml-2">{e.type}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-gray-500">Confidence:</span>
              <div className="w-12 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${
                  e.confidence > 80 ? 'bg-green-500' : e.confidence > 60 ? 'bg-blue-500' : 'bg-yellow-500'
                }`} style={{ width: `${e.confidence}%` }} />
              </div>
              <span className="text-[10px] font-bold text-white">{e.confidence}%</span>
            </div>
          </div>
          <div className="px-4 py-3">
            <p className="text-xs text-gray-300 mb-2">{e.findings}</p>
            <div className="flex items-center gap-1.5 mb-2">
              <i className="fas fa-microscope text-gray-600 text-[10px]" />
              <span className="text-[10px] text-gray-500">{e.method}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {e.details.map((d, j) => (
                <span key={j} className="px-2 py-0.5 bg-dark-700 border border-dark-500 rounded text-[10px] text-gray-400">
                  {d}
                </span>
              ))}
            </div>
          </div>
          {i < evidence.length - 1 && (
            <div className="flex justify-center -mb-3 relative z-10">
              <div className="w-6 h-6 rounded-full bg-dark-700 border border-dark-500 flex items-center justify-center">
                <i className="fas fa-arrow-down text-gray-500 text-[8px]" />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function ActionsPanel({ actions }) {
  const priorityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, STANDARD: 3 }
  const sorted = [...actions].sort((a, b) => (priorityOrder[a.priority] || 9) - (priorityOrder[b.priority] || 9))

  return (
    <div className="space-y-3">
      {sorted.map((action, i) => (
        <div key={i} className="bg-dark-800 border rounded-xl p-4 transition-all hover:shadow-lg group"
          style={{ borderColor: `${action.color}25` }}>
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-lg"
              style={{ background: `${action.color}15`, boxShadow: `0 0 20px ${action.color}10` }}>
              <i className={`fas ${action.icon} text-lg`} style={{ color: action.color }} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${
                  action.priority === 'CRITICAL' ? 'bg-red-500/15 text-red-400 border-red-500/25 animate-pulse' :
                  action.priority === 'HIGH' ? 'bg-orange-500/15 text-orange-400 border-orange-500/25' :
                  action.priority === 'MEDIUM' ? 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25' :
                  'bg-blue-500/15 text-blue-400 border-blue-500/25'
                }`}>{action.priority}</span>
                <span className="text-sm font-bold text-white">{action.action}</span>
              </div>
              <p className="text-xs text-gray-400">{action.description}</p>
              {action.accounts && action.accounts.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {action.accounts.map(acc => (
                    <span key={acc} className="text-[9px] font-mono bg-dark-700 border border-dark-500 text-gray-400 px-1.5 py-0.5 rounded">
                      {acc}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function Timeline({ timeline }) {
  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-dark-500" />

      <div className="space-y-4">
        {timeline.map((step, i) => {
          const agentColors = {
            system: '#8b949e',
            detective: '#58a6ff',
            profiler: '#a371f7',
            quantum: '#79c0ff',
            prosecutor: '#3fb950',
          }
          const color = agentColors[step.agent] || '#8b949e'

          return (
            <div key={i} className="flex gap-4 items-start pl-1 animate-in" style={{ animationDelay: `${i * 100}ms` }}>
              <div className="w-9 h-9 rounded-full border-2 flex items-center justify-center shrink-0 bg-dark-800 z-10"
                style={{ borderColor: color }}>
                <i className={`fas ${step.icon} text-xs`} style={{ color }} />
              </div>
              <div className="flex-1 bg-dark-800 border border-dark-500 rounded-xl p-3 hover:border-opacity-60 transition-all"
                style={{ borderColor: `${color}20` }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">{step.phase}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-gray-500">{step.duration}</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                  </div>
                </div>
                <p className="text-[11px] text-gray-400">{step.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
