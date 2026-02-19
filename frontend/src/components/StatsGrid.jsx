export default function StatsGrid({ summary }) {
  const stats = [
    { value: summary.total_accounts_analyzed, label: 'Accounts Analyzed', icon: 'fa-users', danger: false, gradient: 'from-accent-blue to-accent-cyan' },
    { value: summary.suspicious_accounts_flagged, label: 'Suspicious Flagged', icon: 'fa-user-shield', danger: true, gradient: 'from-accent-red to-accent-orange' },
    { value: summary.fraud_rings_detected, label: 'Fraud Rings', icon: 'fa-ring', danger: true, gradient: 'from-accent-orange to-yellow-500' },
    { value: `${summary.processing_time_seconds}s`, label: 'Processing Time', icon: 'fa-bolt', danger: false, gradient: 'from-accent-purple to-accent-blue' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map((s, i) => (
        <div key={i} className={`relative overflow-hidden bg-dark-700 border rounded-xl p-4 transition-all hover:scale-[1.02] hover:shadow-lg ${
          s.danger ? 'border-red-500/20 hover:border-red-500/40' : 'border-dark-500 hover:border-accent-blue/30'
        }`} style={{ animationDelay: `${i * 100}ms` }}>
          {/* Background icon */}
          <i className={`fas ${s.icon} absolute -right-2 -bottom-2 text-5xl opacity-5`} />
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${s.gradient} flex items-center justify-center bg-opacity-20`}>
              <i className={`fas ${s.icon} text-white text-xs`} />
            </div>
          </div>
          <div className={`text-2xl sm:text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r ${s.gradient} animate-count`}>
            {s.value}
          </div>
          <div className="text-[10px] sm:text-xs text-gray-500 uppercase tracking-wider mt-1">{s.label}</div>
        </div>
      ))}
    </div>
  )
}
