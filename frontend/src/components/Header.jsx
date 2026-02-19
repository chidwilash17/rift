export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-dark-800/90 backdrop-blur-xl border-b border-dark-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-blue via-accent-purple to-accent-cyan flex items-center justify-center text-white text-sm font-bold shrink-0 shadow-lg shadow-accent-blue/20">
            <i className="fas fa-shield-halved text-lg" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-black leading-tight tracking-tight">
              MulingNet<span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">AI</span>
            </h1>
            <p className="text-[9px] sm:text-[10px] text-gray-500 leading-tight font-medium">Hybrid Classical-ML-Quantum Financial Forensics</p>
          </div>
        </div>

        {/* Badges */}
        <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap justify-end">
          <span className="px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-semibold border border-accent-purple/30 bg-accent-purple/10 text-accent-purple">
            <i className="fas fa-atom mr-1" />Quantum
          </span>
          <span className="px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-semibold border border-accent-blue/30 bg-accent-blue/10 text-accent-blue">
            <i className="fas fa-brain mr-1" />Multi-Agent
          </span>
          <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border border-red-500/30 bg-red-500/10 text-red-400">
            <i className="fas fa-crosshairs mr-1" />Disruption
          </span>
          <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border border-accent-orange/30 bg-accent-orange/10 text-accent-orange">
            <i className="fas fa-link mr-1" />n8n
          </span>
          <span className="px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-semibold border border-accent-green/30 bg-accent-green/10 text-accent-green animate-pulse-green">
            <i className="fas fa-circle text-[5px] mr-1" />RIFT 2026
          </span>
        </div>
      </div>
    </header>
  )
}
