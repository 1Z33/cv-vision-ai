import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']

export default function ScoreChart({ structure, content, keywords, overall }) {
  const data = [
    { name: 'Structure', value: structure, color: COLORS[0] },
    { name: 'Contenu', value: content, color: COLORS[1] },
    { name: 'Mots-clés', value: keywords, color: COLORS[2] },
  ]

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#fff'
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="text-center -mt-32 mb-8">
        <span className="text-3xl font-bold text-white">{overall}</span>
        <span className="text-sm text-dark-400 block">/100</span>
      </div>
    </div>
  )
}