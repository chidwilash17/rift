import { useState, useCallback, useEffect } from 'react'
import { apiUrl, warmupBackend } from './apiClient'
import Header from './components/Header'
import UploadSection from './components/UploadSection'
import Pipeline from './components/Pipeline'
import StatsGrid from './components/StatsGrid'
import TabNav from './components/TabNav'
import GraphView from './components/GraphView'
import RingsTable from './components/RingsTable'
import AccountsTable from './components/AccountsTable'
import QuantumPanel from './components/QuantumPanel'
import AgentsChart from './components/AgentsChart'
import N8nPanel from './components/N8nPanel'
import DisruptionPanel from './components/DisruptionPanel'
import CrimeTeamPanel from './components/CrimeTeamPanel'
import WhatIfSimulator from './components/WhatIfSimulator'
import JsonOutputPanel from './components/JsonOutputPanel'
import Footer from './components/Footer'

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pipelineStep, setPipelineStep] = useState(-1)
  const [activeTab, setActiveTab] = useState('graph')
  const [error, setError] = useState(null)

  // Wake up the Render free-tier backend as early as possible
  useEffect(() => { warmupBackend() }, [])

  const handleUpload = useCallback(async (file) => {
    setLoading(true)
    setError(null)
    setResults(null)

    // Animate pipeline
    const steps = [0, 1, 2, 3, 4, 5, 6]
    for (const s of steps) {
      setPipelineStep(s)
      await new Promise(r => setTimeout(r, 600))
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const resp = await fetch(apiUrl('/api/analyze'), { method: 'POST', body: formData })
      if (!resp.ok) {
        const err = await resp.json()
        throw new Error(err.detail || 'Analysis failed')
      }
      const data = await resp.json()
      setResults(data)
      setPipelineStep(7) // all done
    } catch (e) {
      setError(e.message)
      setPipelineStep(-1)
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = () => {
    setResults(null)
    setPipelineStep(-1)
    setActiveTab('graph')
    setError(null)
  }

  const downloadJSON = () => window.open(apiUrl('/api/download'), '_blank')

  const tabs = [
    { id: 'graph', label: 'Graph View', icon: 'fa-diagram-project' },
    { id: 'rings', label: 'Fraud Rings', icon: 'fa-ring' },
    { id: 'accounts', label: 'Suspicious Accounts', icon: 'fa-user-shield' },
    { id: 'quantum', label: 'Quantum Analysis', icon: 'fa-atom' },
    { id: 'disruption', label: 'Disruption Engine', icon: 'fa-crosshairs' },
    { id: 'crimeteam', label: 'Crime Team', icon: 'fa-user-secret' },
    { id: 'whatif', label: 'What-If Simulator', icon: 'fa-flask-vial' },
    { id: 'agents', label: 'Agent Scores', icon: 'fa-robot' },
    { id: 'n8n', label: 'n8n Pipeline', icon: 'fa-link' },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Upload */}
        <UploadSection onUpload={handleUpload} loading={loading} />

        {/* Pipeline */}
        <Pipeline step={pipelineStep} />

        {/* Error */}
        {error && (
          <div className="bg-red-900/30 border border-red-500/40 rounded-xl p-4 text-red-400 text-sm">
            <i className="fas fa-exclamation-triangle mr-2" />{error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-6 animate-in">
            <StatsGrid summary={results.summary} />

            {/* Action buttons */}
            <div className="flex flex-wrap gap-3">
              <button onClick={reset}
                className="bg-dark-600 border border-dark-500 text-gray-300 px-5 py-2.5 rounded-lg font-semibold text-sm hover:border-accent-blue transition-all">
                <i className="fas fa-rotate mr-2" />New Analysis
              </button>
            </div>

            {/* JSON Output Panel */}
            <JsonOutputPanel results={results} onDownload={downloadJSON} />

            {/* Tabs */}
            <TabNav tabs={tabs} active={activeTab} onChange={setActiveTab} />

            {/* Tab content */}
            <div className="min-h-[400px]">
              {activeTab === 'graph' && <GraphView data={results.graph_data} />}
              {activeTab === 'rings' && <RingsTable rings={results.fraud_rings} graphData={results.graph_data} accounts={results.suspicious_accounts} />}
              {activeTab === 'accounts' && <AccountsTable accounts={results.suspicious_accounts} />}
              {activeTab === 'quantum' && (
                <QuantumPanel
                  data={results.quantum_analysis}
                  ibmData={results.ibm_quantum}
                  topRingId={results.fraud_rings?.[0]?.ring_id}
                />
              )}
              {activeTab === 'disruption' && <DisruptionPanel data={results.disruption} />}
              {activeTab === 'crimeteam' && <CrimeTeamPanel data={results.crime_team} />}
              {activeTab === 'whatif' && <WhatIfSimulator graphData={results.graph_data} accounts={results.suspicious_accounts} rings={results.fraud_rings} />}
              {activeTab === 'agents' && <AgentsChart accounts={results.suspicious_accounts} />}
              {activeTab === 'n8n' && <N8nPanel summary={results.summary} />}
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
