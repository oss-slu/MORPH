import { createServerFn } from '@tanstack/react-start'

interface Robot {
    name: string
    host: string
    port: number
}

export const getRobots = createServerFn().handler(
    async (): Promise<Robot[]> => {
        const serverUrl = process.env.SERVER_URL

        const response = await fetch(`${serverUrl}/robots`)
        if (!response.ok) throw new Error('Failed to fetch robots')
        return response.json()
    }
)
