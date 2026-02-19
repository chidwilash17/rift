export default function Footer() {
  return (
    <footer className="border-t border-dark-500 mt-8 py-4 px-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500">
        <span>
          <i className="fas fa-shield-halved mr-1 text-accent-blue" />
          MulingNet<span className="text-accent-blue">AI</span> — RIFT 2026 Hackathon · Graph Theory Track
        </span>
        <span className="flex items-center gap-3">
          <span><i className="fas fa-diagram-project mr-1" />Graph · NetworkX</span>
          <span><i className="fas fa-robot mr-1" />ML · scikit-learn</span>
          <span><i className="fas fa-atom mr-1" />Quantum · Qiskit Aer</span>
        </span>
      </div>
    </footer>
  )
}
