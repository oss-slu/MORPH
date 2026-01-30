import { DPad } from '@/components/DPad'
import { socket } from '@/socket'
import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/dashboard')({
    component: RouteComponent,
})

function RouteComponent() {
    const [logs, setLogs] = useState<string[]>([
        '[INFO] Dashboard initialized',
        '[INFO] Ready for commands',
    ])

    const addLog = (message: string) => {
        setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`])
    }

    useEffect(() => {
        socket.on('log', addLog)

        return () => {
            socket.off('log', addLog)
        }
    })

    function directionToCommand(direction: string) {
        switch (direction) {
            case 'up':
                return 'move up'
            case 'down':
                return 'move down'
            case 'left':
                return 'move left'
            case 'right':
                return 'move right'
            case 'center':
                return 'stop'
            default:
                throw new Error(`Unknown direction: ${direction}`)
        }
    }

    function buttonPressed(direction: string) {
        const cmd = directionToCommand(direction)
        socket.emit('send_command', { command: cmd, speed: 100 })
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex">
            {/* Left side - Controls */}
            <div className="w-1/2 flex items-center justify-center p-8 border-r border-slate-700">
                <DPad
                    onUp={() => buttonPressed('up')}
                    onDown={() => buttonPressed('down')}
                    onLeft={() => buttonPressed('left')}
                    onRight={() => buttonPressed('right')}
                    onCenter={() => buttonPressed('center')}
                />
            </div>

            {/* Right side - Displays */}
            <div className="w-1/2 p-8 flex flex-col">
                <h2 className="text-2xl font-bold text-cyan-400 mb-4">Logs</h2>
                <div className="flex-1 bg-slate-900 border border-slate-700 rounded-lg p-4 overflow-y-auto">
                    <div className="space-y-2 font-mono text-sm">
                        {logs.map((log, index) => (
                            <div
                                key={index}
                                className="text-slate-300 hover:text-cyan-300 transition-colors"
                            >
                                {log}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
