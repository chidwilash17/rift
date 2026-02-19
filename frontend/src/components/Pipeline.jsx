const steps = [
  { icon: 'fa-file-csv', label: 'CSV Parse' },
  { icon: 'fa-diagram-project', label: 'Graph Agent' },
  { icon: 'fa-robot', label: 'ML Agent' },
  { icon: 'fa-atom', label: 'Quantum Agent' },
  { icon: 'fa-layer-group', label: 'Aggregator' },
  { icon: 'fa-crosshairs', label: 'Disruption' },
  { icon: 'fa-user-secret', label: 'Crime Team' },
]

export default function Pipeline({ step }) {
  if (step < 0) return null

  return (
    <div className="flex items-center gap-2 p-3 bg-dark-800/60 rounded-xl overflow-x-auto">
      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-2 shrink-0">
          <div className={`
            flex items-center gap-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all duration-300
            ${i < step ? 'border border-accent-green/40 bg-accent-green/10 text-accent-green' : ''}
            ${i === step ? 'border border-accent-blue/50 bg-accent-blue/10 text-accent-blue shadow-[0_0_12px_rgba(88,166,255,0.2)]' : ''}
            ${i > step ? 'border border-dark-500 text-gray-500' : ''}
          `}>
            <i className={`fas ${s.icon}`} />
            <span className="hidden sm:inline">{s.label}</span>
            {i < step && <i className="fas fa-check text-[10px]" />}
            {i === step && <div className="w-2 h-2 bg-accent-blue rounded-full animate-pulse" />}
          </div>
          {i < steps.length - 1 && (
            <i className={`fas fa-arrow-right text-xs ${i < step ? 'text-accent-green/50' : 'text-gray-600'}`} />
          )}
        </div>
      ))}
    </div>
  )
}
