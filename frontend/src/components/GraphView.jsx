import { useEffect, useRef, useState, useMemo, useCallback } from 'react'

export default function GraphView({ data }) {
  const containerRef = useRef(null)
  const networkRef = useRef(null)
  const nodesRef = useRef(null)
  const edgesRef = useRef(null)
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showResults, setShowResults] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [highlightedNodes, setHighlightedNodes] = useState(new Set())
  const searchBoxRef = useRef(null)

  /* Build searchable index */
  const searchIndex = useMemo(() => {
    if (!data) return []
    const items = []
    /* Nodes */
    data.nodes.forEach(n => {
      items.push({
        type: 'account', id: n.id, label: n.id,
        score: n.score, ringId: n.ring_id, suspicious: n.suspicious,
        patterns: n.patterns || [],
        desc: `Score: ${n.score} | Ring: ${n.ring_id || 'N/A'} | ${n.suspicious ? 'Suspicious' : 'Normal'}`,
        icon: n.suspicious ? 'fa-user-shield' : 'fa-user',
        color: n.suspicious ? 'text-red-400' : 'text-gray-400',
      })
    })
    /* Group by ring */
    const rings = {}
    data.nodes.forEach(n => {
      if (n.ring_id && n.ring_id !== 'N/A' && n.ring_id !== 'STANDALONE') {
        if (!rings[n.ring_id]) rings[n.ring_id] = { members: [], scores: [] }
        rings[n.ring_id].members.push(n.id)
        rings[n.ring_id].scores.push(n.score)
      }
    })
    Object.entries(rings).forEach(([rid, r]) => {
      items.push({
        type: 'ring', id: rid, label: rid,
        members: r.members,
        desc: `${r.members.length} members | Avg score: ${(r.scores.reduce((a,b) => a+b, 0) / r.scores.length).toFixed(1)}`,
        icon: 'fa-ring', color: 'text-orange-400',
      })
    })
    /* Patterns */
    const patternSet = new Set()
    data.nodes.forEach(n => (n.patterns || []).forEach(p => patternSet.add(p)))
    patternSet.forEach(p => {
      const nodesWithPattern = data.nodes.filter(n => (n.patterns || []).includes(p))
      items.push({
        type: 'pattern', id: p, label: p.replace(/_/g, ' '),
        members: nodesWithPattern.map(n => n.id),
        desc: `${nodesWithPattern.length} accounts with this pattern`,
        icon: 'fa-fingerprint', color: 'text-violet-400',
      })
    })
    return items
  }, [data])

  /* Search filter */
  const doSearch = useCallback((q) => {
    setSearch(q)
    if (!q.trim()) { setSearchResults([]); setShowResults(false); return }
    const lower = q.toLowerCase()
    const results = searchIndex.filter(item =>
      item.label.toLowerCase().includes(lower) ||
      item.id.toLowerCase().includes(lower) ||
      (item.desc || '').toLowerCase().includes(lower) ||
      (item.members || []).some(m => m.toLowerCase().includes(lower))
    ).slice(0, 12)
    setSearchResults(results)
    setShowResults(true)
  }, [searchIndex])

  /* Highlight node(s) on graph */
  const focusNodes = useCallback((nodeIds) => {
    if (!networkRef.current || !nodesRef.current) return
    const idSet = new Set(nodeIds)
    setHighlightedNodes(idSet)

    /* Dim all, highlight selected */
    const updates = data.nodes.map(n => {
      if (idSet.has(n.id)) {
        return {
          id: n.id,
          opacity: 1,
          borderWidth: 5,
          shadow: { enabled: true, color: 'rgba(139,92,246,0.6)', size: 15 },
          size: (n.size || 15) * 1.4,
        }
      }
      return {
        id: n.id,
        opacity: 0.15,
        borderWidth: n.borderWidth || 1,
        shadow: false,
        size: n.size || 12,
      }
    })
    nodesRef.current.update(updates)

    /* Dim edges not involving highlighted nodes */
    const edgeUpdates = data.edges.map(e => {
      if (idSet.has(e.from) && idSet.has(e.to)) {
        return { id: e.id, hidden: false, color: { color: '#f85149', opacity: 1 }, width: 3 }
      }
      return { id: e.id, hidden: false, color: { ...e.color, opacity: 0.05 }, width: 0.5 }
    })
    edgesRef.current.update(edgeUpdates)

    /* Zoom to highlighted */
    if (nodeIds.length > 0) {
      networkRef.current.fit({ nodes: nodeIds, animation: { duration: 600, easingFunction: 'easeInOutQuad' } })
    }

    setShowResults(false)
  }, [data])

  /* Reset highlights */
  const resetHighlights = useCallback(() => {
    if (!nodesRef.current || !edgesRef.current || !data) return
    setHighlightedNodes(new Set())
    setSelectedNode(null)
    setSearch('')
    setShowResults(false)

    const nodeResets = data.nodes.map(n => ({
      id: n.id, opacity: 1, borderWidth: n.borderWidth || 1,
      shadow: false, size: n.size || 12,
    }))
    nodesRef.current.update(nodeResets)

    const edgeResets = data.edges.map(e => ({
      id: e.id, hidden: false, color: e.color, width: e.width || 1,
    }))
    edgesRef.current.update(edgeResets)

    networkRef.current?.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } })
  }, [data])

  /* Select a search result */
  const selectResult = useCallback((item) => {
    setSelectedNode(item)
    if (item.type === 'account') {
      focusNodes([item.id])
    } else if (item.type === 'ring' || item.type === 'pattern') {
      focusNodes(item.members || [])
    }
  }, [focusNodes])

  /* Init vis.js network */
  useEffect(() => {
    if (!data || !containerRef.current) return
    let destroyed = false

    const init = async () => {
      const vis = await import('vis-network/standalone')
      if (destroyed) return

      /* Add stable IDs to edges for updates */
      const edgesWithIds = data.edges.map((e, i) => ({ ...e, id: e.id || `e-${i}` }))

      const nodes = new vis.DataSet(data.nodes)
      const edges = new vis.DataSet(edgesWithIds)
      nodesRef.current = nodes
      edgesRef.current = edges

      const options = {
        physics: {
          stabilization: { iterations: 80, fit: true },
          barnesHut: { gravitationalConstant: -3000, springLength: 150, damping: 0.4 },
        },
        interaction: { hover: true, tooltipDelay: 200, zoomView: true, dragView: true },
        nodes: { font: { color: '#c9d1d9', size: 10 } },
        edges: { font: { color: '#8b949e', size: 8 } },
        layout: { improvedLayout: data.nodes.length < 80 },
      }

      if (networkRef.current) networkRef.current.destroy()
      networkRef.current = new vis.Network(containerRef.current, { nodes, edges }, options)

      /* Click node to show info */
      networkRef.current.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0]
          const nodeData = data.nodes.find(n => n.id === nodeId)
          if (nodeData) {
            setSelectedNode({
              type: 'account', id: nodeId, label: nodeId,
              score: nodeData.score, ringId: nodeData.ring_id,
              suspicious: nodeData.suspicious, patterns: nodeData.patterns || [],
              desc: `Score: ${nodeData.score}`,
              icon: 'fa-user-shield', color: 'text-accent-blue',
            })
          }
        }
      })
    }

    init()
    return () => { destroyed = true; networkRef.current?.destroy() }
  }, [data])

  /* Close dropdown on outside click */
  useEffect(() => {
    const handler = (e) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target)) setShowResults(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  if (!data) return <Placeholder text="No graph data available" />

  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl overflow-hidden">
      {/* Truncation notice for large datasets */}
      {data.truncated && (
        <div className="bg-amber-900/30 border-b border-amber-500/30 px-4 py-2 text-amber-400 text-xs flex items-center gap-2">
          <i className="fas fa-triangle-exclamation" />
          Large dataset — showing {data.nodes.length} of {data.total_nodes} nodes and {data.edges.length} of {data.total_edges} edges (suspicious nodes + neighbours prioritised).
        </div>
      )}
      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-dark-500 bg-dark-700/50 gap-3 flex-wrap">
        <span className="text-xs text-gray-400 shrink-0">
          <i className="fas fa-circle-nodes mr-1" />
          {data.nodes.length} nodes &middot; {data.edges.length} edges
        </span>

        {/* Search */}
        <div className="relative flex-1 max-w-md" ref={searchBoxRef}>
          <i className="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-xs" />
          <input type="text" placeholder="Search accounts, rings, patterns…"
            value={search}
            onChange={e => doSearch(e.target.value)}
            onFocus={() => { if (searchResults.length) setShowResults(true) }}
            className="w-full pl-8 pr-10 py-1.5 rounded-lg bg-dark-600 border border-dark-400 text-xs text-gray-200 placeholder-gray-600
                       focus:border-violet-500/50 focus:outline-none focus:ring-1 focus:ring-violet-500/20 transition-all" />
          {search && (
            <button onClick={resetHighlights}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 text-xs">
              <i className="fas fa-times-circle" />
            </button>
          )}

          {/* Search Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-dark-700 border border-dark-400 rounded-lg shadow-xl z-50 max-h-72 overflow-y-auto custom-scroll">
              {searchResults.map((item, i) => (
                <button key={`${item.type}-${item.id}-${i}`}
                  onClick={() => selectResult(item)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-dark-600 transition-colors text-left border-b border-dark-600 last:border-0">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                    item.type === 'ring' ? 'bg-orange-500/10' : item.type === 'pattern' ? 'bg-violet-500/10' : item.suspicious ? 'bg-red-500/10' : 'bg-gray-500/10'
                  }`}>
                    <i className={`fas ${item.icon} text-xs ${item.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-gray-200 truncate">{item.label}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-semibold uppercase ${
                        item.type === 'ring' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                        : item.type === 'pattern' ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20'
                        : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      }`}>{item.type}</span>
                    </div>
                    <span className="text-[10px] text-gray-500 truncate block">{item.desc}</span>
                  </div>
                  <i className="fas fa-crosshairs text-[10px] text-gray-600" />
                </button>
              ))}
            </div>
          )}
          {showResults && search && searchResults.length === 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-dark-700 border border-dark-400 rounded-lg shadow-xl z-50 p-4 text-center">
              <span className="text-xs text-gray-500"><i className="fas fa-search mr-1" />No results for "{search}"</span>
            </div>
          )}
        </div>

        {/* Buttons */}
        <div className="flex gap-2 shrink-0">
          {highlightedNodes.size > 0 && (
            <button onClick={resetHighlights}
              className="text-xs text-violet-400 hover:text-white px-2.5 py-1 rounded border border-violet-500/30 hover:border-violet-500 bg-violet-500/10 transition flex items-center gap-1">
              <i className="fas fa-eye" />Show All
            </button>
          )}
          <button onClick={() => networkRef.current?.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } })}
            className="text-xs text-gray-400 hover:text-white px-2.5 py-1 rounded border border-dark-500 hover:border-accent-blue transition">
            <i className="fas fa-expand mr-1" />Fit
          </button>
        </div>
      </div>

      {/* ── Selected Node Info Bar ── */}
      {selectedNode && (
        <div className="flex items-center gap-3 px-4 py-2 border-b border-dark-500 bg-dark-700/30 animate-fade">
          <div className={`w-6 h-6 rounded-md flex items-center justify-center ${
            selectedNode.type === 'ring' ? 'bg-orange-500/20' : selectedNode.type === 'pattern' ? 'bg-violet-500/20' : 'bg-blue-500/20'
          }`}>
            <i className={`fas ${selectedNode.icon} text-[10px] ${selectedNode.color}`} />
          </div>
          <span className="text-xs font-mono font-bold text-gray-200">{selectedNode.label}</span>
          <span className="text-[10px] text-gray-500">{selectedNode.desc}</span>
          {selectedNode.patterns?.length > 0 && (
            <div className="flex gap-1">
              {selectedNode.patterns.slice(0, 3).map((p, i) => (
                <span key={i} className="text-[9px] px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
                  {p.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
          <button onClick={() => { resetHighlights() }} className="ml-auto text-gray-500 hover:text-gray-300 text-xs">
            <i className="fas fa-times" />
          </button>
        </div>
      )}

      {/* ── Graph container ── */}
      <div ref={containerRef} className="w-full h-[400px] sm:h-[500px] lg:h-[600px]" />

      {/* ── Legend ── */}
      <div className="flex flex-wrap gap-3 px-4 py-2 border-t border-dark-500 text-[10px] text-gray-400">
        <span><span className="inline-block w-2 h-2 rounded-full bg-[#ff2222] mr-1" /> High Risk</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-[#ff8800] mr-1" /> Medium Risk</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-[#ffcc00] mr-1" /> Low Risk</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-[#336699] mr-1" /> Normal</span>
        {highlightedNodes.size > 0 && (
          <span className="ml-auto text-violet-400"><i className="fas fa-crosshairs mr-1" />{highlightedNodes.size} highlighted</span>
        )}
      </div>
    </div>
  )
}

function Placeholder({ text }) {
  return (
    <div className="flex items-center justify-center h-[400px] bg-dark-800 border border-dark-500 rounded-xl text-gray-500 text-sm">
      {text}
    </div>
  )
}
