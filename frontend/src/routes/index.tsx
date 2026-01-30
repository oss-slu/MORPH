import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Server, AlertCircle } from 'lucide-react'
import { getRobots } from './index.server'
import { useEffect, useState } from 'react'
import { socket } from '@/socket'

export const Route = createFileRoute('/')({
  component: App
})

interface Robot {
  name: string
  host: string
  port: number
}

function RobotCard({ robot, isSelected, isDisabled, onSelect }: { robot: Robot, isSelected: boolean, isDisabled: boolean, onSelect: () => void }) {
  return (<div
    key={robot.name}
    className={`bg-slate-800 border rounded-lg p-6 transition-all duration-300 ${isSelected
      ? 'border-cyan-400 scale-105 shadow-xl shadow-cyan-400/30 ring-2 ring-cyan-400/50'
      : 'border-slate-700 scale-100'
      } ${isDisabled
        ? 'opacity-50 cursor-not-allowed'
        : 'hover:border-cyan-500 hover:shadow-lg hover:shadow-cyan-500/20 cursor-pointer'
      }`}
    onClick={() => {
      if (isDisabled) return
      onSelect()
    }}
  >
    <div className="flex items-center gap-3 mb-4">
      <Server className={`w-8 h-8 transition-colors duration-300 ${isSelected ? 'text-cyan-300' : 'text-cyan-400'}`} />
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
  </div>)
}

function App() {
  const { data: robots, isLoading, error } = useQuery<Robot[]>({
    queryKey: ['robots'],
    queryFn: getRobots,
  })

  const [selectedRobot, setSelectedRobot] = useState<Robot | null>(null)
  const [connectingToRobot, setConnectingToRobot] = useState(false)
  const navigate = useNavigate()

  function redirectOnConnect() {
    navigate({ to: '/dashboard' })
  }

  useEffect(() => {
    return () => {
      socket.off('connection', redirectOnConnect)
    }
  }, [])

  function connectToRobot() {
    if (!selectedRobot || connectingToRobot) return

    setConnectingToRobot(true)

    socket.connect()

    socket.off('connection', redirectOnConnect)
    socket.on('connection', redirectOnConnect)

    socket.emit("connect_robot", { robot_name: selectedRobot.name }, (response: { success: boolean; message?: string }) => {
      if (response.success) {
        console.log(`Successfully connected to robot: ${selectedRobot.name}`)
      } else {
        console.error(`Failed to connect to robot: ${response.message}`)
      }
      setConnectingToRobot(false)
    })
  }

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
              <RobotCard
                key={robot.name}
                robot={robot}
                isSelected={selectedRobot?.name === robot.name}
                isDisabled={connectingToRobot}
                onSelect={() => setSelectedRobot(robot)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Submit Button - Animated, appears when robot selected */}
      <div className={`fixed bottom-8 left-1/2 -translate-x-1/2 transition-all duration-500 ease-out ${selectedRobot
        ? 'opacity-100 translate-y-0 pointer-events-auto'
        : 'opacity-0 translate-y-20 pointer-events-none'
        }`}>
        <button
          onClick={connectToRobot}
          disabled={connectingToRobot}
          className={`text-white font-bold px-8 py-4 rounded-full transition-all duration-300 flex items-center gap-3 group ${connectingToRobot
            ? 'bg-slate-600 text-slate-300 cursor-not-allowed shadow-none'
            : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 shadow-2xl shadow-cyan-500/50 hover:shadow-cyan-400/60 hover:scale-110'
            }`}
        >
          {connectingToRobot ? (
            <>
              <span className="text-lg">Connecting...</span>
              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border-2 border-slate-200/70 border-t-transparent animate-spin" />
            </>
          ) : (
            <>
              <span className="text-lg">Connect to {selectedRobot?.name}</span>
              <svg
                className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
