export default function TabNav({ tabs, active, onChange }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`
            shrink-0 px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all border
            ${active === t.id
              ? 'bg-accent-blue text-white border-accent-blue'
              : 'border-dark-500 text-gray-400 hover:border-accent-blue/40 hover:text-gray-200'}
          `}
        >
          <i className={`fas ${t.icon} mr-1.5`} />
          <span className="hidden sm:inline">{t.label}</span>
        </button>
      ))}
    </div>
  )
}
