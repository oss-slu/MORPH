import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Server, AlertCircle } from 'lucide-react'
import { getRobots } from './index.server'

export const Route = createFileRoute('/')({
  component: App
})

interface Robot {
  name: string
  host: string
  port: number
}

function App() {
  const { data: robots, isLoading, error } = useQuery<Robot[]>({
    queryKey: ['robots'],
    queryFn: getRobots,
  })

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Header with logo */}
      <div className="flex justify-center pt-12 pb-2">
        <img
          src="/logo.svg"
          alt="MORPH Logo"
          className="h-40 w-100 opacity-90 hover:opacity-100 transition-opacity"
        />
      </div>

      {/* Robots section */}
      <div className="max-w-6xl mx-auto px-6 py-2">
        <h1 className="text-4xl font-bold text-white text-center mb-12">Available Robots</h1>

        {isLoading && (
          <div className="flex justify-center">
            <div className="text-cyan-400">Loading robots...</div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center gap-3 bg-red-900/30 border border-red-600 rounded-lg p-6">
            <AlertCircle className="w-6 h-6 text-red-400" />
            <span className="text-red-200">Failed to load robots</span>
          </div>
        )}

        {robots && robots.length === 0 && (
          <div className="flex justify-center">
            <div className="text-slate-300">No robots available</div>
          </div>
        )}

        {robots && robots.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {robots.map((robot) => (
              <div
                key={robot.name}
                className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-cyan-500 transition-colors hover:shadow-lg hover:shadow-cyan-500/20 cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-4">
                  <Server className="w-8 h-8 text-cyan-400" />
                  <h2 className="text-xl font-semibold text-white">{robot.name}</h2>
                </div>
                <div className="space-y-2 text-slate-300">
                  <p>
                    <span className="text-slate-400">Host:</span> {robot.host}
                  </p>
                  <p>
                    <span className="text-slate-400">Port:</span> {robot.port}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
