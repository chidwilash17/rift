import { useState } from 'react'

export default function N8nPanel({ summary }) {
  const [copied, setCopied] = useState(false)

  const webhookUrl = 'https://your-instance.app.n8n.cloud/webhook/muling-detect'

  const downloadWorkflow = () => {
    window.open('/n8n_workflow.json', '_blank')
  }

  const copyWebhook = () => {
    navigator.clipboard.writeText(apiUrl('/api/webhook/n8n'))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const steps = [
    {
      num: 1,
      title: 'Create free n8n account',
      desc: 'Sign up at n8n.io — the free tier includes 2,500 executions/month.',
      action: { label: 'Open n8n.io', url: 'https://n8n.io', icon: 'fa-arrow-up-right-from-square' },
    },
    {
      num: 2,
      title: 'Download our workflow',
      desc: 'Get the pre-built MulingNet fraud detection pipeline — ready to import.',
      action: { label: 'Download JSON', onClick: downloadWorkflow, icon: 'fa-download' },
    },
    {
      num: 3,
      title: 'Import into n8n',
      desc: 'In your n8n dashboard: Workflows → Import from File → select the downloaded JSON.',
      action: { label: 'n8n Docs: Import', url: 'https://docs.n8n.io/workflows/export-import/', icon: 'fa-book' },
    },
    {
      num: 4,
      title: 'Update the API URL',
      desc: 'Edit the "Analyze CSV" node and point it to your deployed MulingNet API endpoint.',
    },
    {
      num: 5,
      title: 'Activate & run',
      desc: 'Toggle the workflow ON. Post a CSV to the webhook trigger and watch the pipeline execute.',
      action: { label: 'Open your n8n', url: 'https://app.n8n.cloud', icon: 'fa-rocket' },
    },
  ]

  return (
    <div className="space-y-5 animate-in">
      {/* Hero Banner */}
      <div className="relative overflow-hidden bg-gradient-to-br from-orange-500/10 via-dark-800 to-amber-500/10 border border-orange-500/20 rounded-2xl p-6">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-orange-500/5 via-transparent to-transparent" />
        <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center shadow-xl shadow-orange-500/20">
              <i className="fas fa-sitemap text-white text-2xl" />
            </div>
            <div>
              <h3 className="text-lg font-black text-white tracking-tight">n8n Cloud Integration</h3>
              <p className="text-sm text-gray-400 mt-0.5">
                Automate fraud detection with <a href="https://n8n.io" target="_blank" rel="noopener" className="text-orange-400 hover:text-orange-300 underline underline-offset-2 font-semibold">n8n.io</a> —
                no local install required
              </p>
            </div>
          </div>
          <a href="https://app.n8n.cloud" target="_blank" rel="noopener"
            className="shrink-0 bg-gradient-to-r from-orange-500 to-red-500 text-white px-5 py-2.5 rounded-xl font-bold text-sm hover:shadow-lg hover:shadow-orange-500/25 transition-all flex items-center gap-2">
            <i className="fas fa-arrow-up-right-from-square" />
            Open n8n Cloud
          </a>
        </div>
      </div>

      {/* Workflow Visual */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-dark-500 bg-dark-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <i className="fas fa-sitemap text-orange-400" />
            <span className="text-sm font-semibold text-white">MulingNet AI — n8n Workflow</span>
          </div>
          <button onClick={downloadWorkflow}
            className="text-xs bg-orange-500/15 text-orange-400 border border-orange-500/25 px-3 py-1.5 rounded-lg hover:bg-orange-500/25 transition font-semibold">
            <i className="fas fa-download mr-1.5" />Download Workflow JSON
          </button>
        </div>

        <div className="p-6">
          {/* Pipeline diagram */}
          <div className="hidden md:flex items-stretch justify-center gap-0">
            <PipelineNode icon="fa-globe" label="Webhook Trigger" color="green" desc="POST /webhook/muling-detect" />
            <PipelineArrow />
            <PipelineNode icon="fa-server" label="MulingNet API" color="blue" desc="Analyze CSV → 7 agents" />
            <PipelineArrow />
            <PipelineNode icon="fa-code-branch" label="If Suspicious?" color="yellow" desc="flagged_accounts ≥ 1" />
            <PipelineArrow />
            <div className="flex flex-col gap-2 justify-center">
              <PipelineNode icon="fa-bell" label="Alert" color="red" desc="Slack / Email / DB" small />
              <PipelineNode icon="fa-archive" label="Archive" color="gray" desc="Log clean result" small />
            </div>
          </div>

          {/* Mobile */}
          <div className="flex md:hidden flex-col items-center gap-2">
            <PipelineNode icon="fa-globe" label="Webhook Trigger" color="green" desc="POST /webhook/muling-detect" />
            <i className="fas fa-arrow-down text-gray-600" />
            <PipelineNode icon="fa-server" label="MulingNet API" color="blue" desc="Analyze CSV → 7 agents" />
            <i className="fas fa-arrow-down text-gray-600" />
            <PipelineNode icon="fa-code-branch" label="If Suspicious?" color="yellow" desc="flagged_accounts ≥ 1" />
            <div className="flex gap-3 mt-1">
              <PipelineNode icon="fa-bell" label="Alert" color="red" desc="Slack/Email" small />
              <PipelineNode icon="fa-archive" label="Archive" color="gray" desc="Log" small />
            </div>
          </div>

          {/* Features row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-6 border-t border-dark-500 pt-5">
            <FeatureCard icon="fa-cloud" title="Cloud-Hosted" desc="Runs on n8n.io — zero infrastructure to manage" />
            <FeatureCard icon="fa-bolt" title="Real-time Triggers" desc="Webhook fires instant analysis on CSV arrival" />
            <FeatureCard icon="fa-share-nodes" title="500+ Integrations" desc="Route alerts to Slack, Teams, email, databases, or any API" />
          </div>
        </div>
      </div>

      {/* Setup Steps */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-dark-500 bg-dark-700/50 flex items-center gap-2">
          <i className="fas fa-list-ol text-orange-400" />
          <span className="text-sm font-semibold text-white">Quick Setup — 5 Minutes</span>
        </div>
        <div className="p-5 space-y-4">
          {steps.map(step => (
            <div key={step.num} className="flex gap-4 items-start group">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white text-xs font-black shrink-0 shadow-lg shadow-orange-500/15">
                {step.num}
              </div>
              <div className="flex-1 pb-4 border-b border-dark-600 last:border-0 group-last:border-0">
                <span className="text-sm font-bold text-white">{step.title}</span>
                <p className="text-xs text-gray-400 mt-0.5">{step.desc}</p>
                {step.action && (
                  step.action.url ? (
                    <a href={step.action.url} target="_blank" rel="noopener"
                      className="inline-flex items-center gap-1.5 mt-2 text-[11px] font-semibold text-orange-400 hover:text-orange-300 transition">
                      <i className={`fas ${step.action.icon}`} />{step.action.label}
                    </a>
                  ) : (
                    <button onClick={step.action.onClick}
                      className="inline-flex items-center gap-1.5 mt-2 text-[11px] font-semibold text-orange-400 hover:text-orange-300 transition">
                      <i className={`fas ${step.action.icon}`} />{step.action.label}
                    </button>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Webhook Info */}
      <div className="bg-dark-800 border border-dark-500 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <i className="fas fa-plug text-accent-blue" />
          <span className="text-sm font-semibold text-white">Your MulingNet Webhook Endpoint</span>
        </div>
        <p className="text-xs text-gray-400 mb-3">
          Point your n8n "Analyze CSV" node to this endpoint. n8n will POST the CSV here and receive the full analysis as JSON.
        </p>
        <div className="flex items-center gap-2">
          <code className="flex-1 bg-dark-900 border border-dark-500 rounded-lg px-4 py-2.5 text-sm text-green-400 font-mono overflow-x-auto">
            {apiUrl('/api/analyze')}
          </code>
          <button onClick={copyWebhook}
            className={`shrink-0 px-3 py-2.5 rounded-lg text-xs font-bold border transition-all ${copied
              ? 'bg-green-500/15 border-green-500/30 text-green-400'
              : 'bg-dark-700 border-dark-500 text-gray-400 hover:text-white hover:border-accent-blue'
              }`}>
            <i className={`fas ${copied ? 'fa-check' : 'fa-copy'} mr-1`} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        {summary && (
          <div className="mt-3 flex flex-wrap gap-2 text-[10px]">
            <span className="px-2 py-1 bg-dark-700 border border-dark-500 rounded text-gray-400">
              Last analysis: <strong className="text-white">{summary.suspicious_accounts_flagged}</strong> flagged, <strong className="text-white">{summary.fraud_rings_detected}</strong> rings
            </span>
            <span className="px-2 py-1 bg-dark-700 border border-dark-500 rounded text-gray-400">
              Processed in <strong className="text-white">{summary.processing_time_seconds}s</strong>
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Sub-components ─────────────────────────────────────────────── */

function PipelineNode({ icon, label, color, desc, small }) {
  const colors = {
    green: { bg: 'from-green-500/20 to-green-600/10', border: 'border-green-500/30', text: 'text-green-400' },
    blue: { bg: 'from-blue-500/20 to-blue-600/10', border: 'border-blue-500/30', text: 'text-blue-400' },
    yellow: { bg: 'from-yellow-500/20 to-yellow-600/10', border: 'border-yellow-500/30', text: 'text-yellow-400' },
    red: { bg: 'from-red-500/20 to-red-600/10', border: 'border-red-500/30', text: 'text-red-400' },
    gray: { bg: 'from-gray-500/20 to-gray-600/10', border: 'border-gray-500/30', text: 'text-gray-400' },
  }
  const c = colors[color] || colors.gray

  return (
    <div className={`bg-gradient-to-b ${c.bg} border ${c.border} rounded-xl flex flex-col items-center justify-center text-center
      ${small ? 'px-3 py-2.5 min-w-[90px]' : 'px-5 py-4 min-w-[140px]'}`}>
      <i className={`fas ${icon} ${c.text} ${small ? 'text-base mb-1' : 'text-xl mb-2'}`} />
      <span className={`font-bold ${c.text} ${small ? 'text-[10px]' : 'text-xs'}`}>{label}</span>
      <span className={`text-gray-500 mt-0.5 ${small ? 'text-[8px]' : 'text-[10px]'}`}>{desc}</span>
    </div>
  )
}

function PipelineArrow() {
  return (
    <div className="flex items-center px-2">
      <div className="w-8 h-px bg-gray-600" />
      <i className="fas fa-chevron-right text-gray-600 text-[8px]" />
    </div>
  )
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-dark-700/50 border border-dark-500 rounded-xl p-3.5 hover:border-orange-500/20 transition">
      <i className={`fas ${icon} text-orange-400 mb-2 block`} />
      <span className="text-xs font-bold text-white block">{title}</span>
      <span className="text-[10px] text-gray-500">{desc}</span>
    </div>
  )
}
