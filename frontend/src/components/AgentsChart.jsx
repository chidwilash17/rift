import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

export default function AgentsChart({ accounts }) {
  if (!accounts?.length) {
    return (
      <div className="flex items-center justify-center h-40 bg-dark-800 border border-dark-500 rounded-xl text-gray-500 text-sm">
        <i className="fas fa-chart-bar mr-2" />No data available
      </div>
    )
  }

  // Show top 15 accounts sorted by score
  const top = accounts.slice(0, 15)
  const labels = top.map(a => a.account_id)

  const data = {
    labels,
    datasets: [
      {
        label: 'Graph',
        data: top.map(a => a.component_scores?.graph || 0),
        backgroundColor: 'rgba(88, 166, 255, 0.7)',
        borderColor: 'rgba(88, 166, 255, 1)',
        borderWidth: 1,
      },
      {
        label: 'ML',
        data: top.map(a => a.component_scores?.ml || 0),
        backgroundColor: 'rgba(163, 113, 247, 0.7)',
        borderColor: 'rgba(163, 113, 247, 1)',
        borderWidth: 1,
      },
      {
        label: 'Quantum',
        data: top.map(a => a.component_scores?.quantum || 0),
        backgroundColor: 'rgba(121, 192, 255, 0.7)',
        borderColor: 'rgba(121, 192, 255, 1)',
        borderWidth: 1,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#8b949e', font: { size: 11 }, padding: 16 },
      },
      title: {
        display: true,
        text: 'Agent Score Breakdown (Top 15 Accounts)',
        color: '#c9d1d9',
        font: { size: 14, weight: 'bold' },
        padding: { bottom: 16 },
      },
      tooltip: {
        backgroundColor: '#161b22',
        titleColor: '#c9d1d9',
        bodyColor: '#c9d1d9',
        borderColor: '#30363d',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: { color: '#8b949e', font: { size: 9 }, maxRotation: 45, minRotation: 45 },
        grid: { color: 'rgba(48,54,61,0.4)' },
      },
      y: {
        ticks: { color: '#8b949e' },
        grid: { color: 'rgba(48,54,61,0.4)' },
        beginAtZero: true,
        max: 100,
      },
    },
  }

  return (
    <div className="bg-dark-800 border border-dark-500 rounded-xl p-4">
      <div className="h-[300px] sm:h-[400px]">
        <Bar data={data} options={options} />
      </div>
    </div>
  )
}
