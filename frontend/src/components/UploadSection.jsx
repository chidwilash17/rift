import { useRef, useState } from 'react'

export default function UploadSection({ onUpload, loading }) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file?.name.endsWith('.csv')) onUpload(file)
  }

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) onUpload(file)
  }

  return (
    <div
      onClick={() => !loading && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-300
        ${loading ? 'border-accent-purple/50 animate-glow cursor-wait' : ''}
        ${dragOver ? 'border-accent-blue bg-accent-blue/5 shadow-[0_0_20px_rgba(88,166,255,0.15)]' : 'border-dark-500 bg-dark-800/40 hover:border-accent-blue/50 hover:bg-accent-blue/5'}
      `}
    >
      {loading ? (
        <>
          <div className="w-10 h-10 mx-auto border-3 border-dark-500 border-t-accent-purple rounded-full animate-spin mb-4" />
          <p className="text-gray-400 text-sm">Running multi-agent pipeline...</p>
        </>
      ) : (
        <>
          <i className="fas fa-cloud-arrow-up text-4xl sm:text-5xl text-accent-blue mb-4 block" />
          <h2 className="text-lg sm:text-xl font-bold mb-2">Upload Transaction CSV</h2>
          <p className="text-gray-400 text-sm mb-2">
            Drag & drop or click — CSV with transaction_id, sender_id, receiver_id, amount, timestamp
          </p>
          <p className="text-gray-500 text-xs font-mono">Supports datasets up to 10,000+ transactions</p>
        </>
      )}
      <input ref={inputRef} type="file" accept=".csv" className="hidden" onChange={handleChange} />
    </div>
  )
}
