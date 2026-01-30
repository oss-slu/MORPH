import {
  HeadContent,
  Scripts,
  createRootRouteWithContext,
  useNavigate,
} from '@tanstack/react-router'
import { TanStackRouterDevtoolsPanel } from '@tanstack/react-router-devtools'
import { TanStackDevtools } from '@tanstack/react-devtools'

import Header from '../components/Header'

import TanStackQueryDevtools from '../integrations/tanstack-query/devtools'

import appCss from '../styles.css?url'

import type { QueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { socket } from '@/socket'

interface MyRouterContext {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<MyRouterContext>()({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        title: 'TanStack Start Starter',
      },
    ],
    links: [
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),

  shellComponent: RootDocument,
})

function RootDocument({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const [isSocketDisconnected, setIsSocketDisconnected] = useState(false)

  useEffect(() => {
    let redirectTimeout: number | null = null

    const handleDisconnect = () => {
      setIsSocketDisconnected(true)
      redirectTimeout = window.setTimeout(() => {
        navigate({ to: '/' })
      }, 2500)
    }

    const handleConnect = () => {
      setIsSocketDisconnected(false)
      if (redirectTimeout) {
        window.clearTimeout(redirectTimeout)
        redirectTimeout = null
      }
    }

    socket.on('disconnect', handleDisconnect)
    socket.on('connect', handleConnect)

    return () => {
      socket.off('disconnect', handleDisconnect)
      socket.off('connect', handleConnect)
      if (redirectTimeout) {
        window.clearTimeout(redirectTimeout)
      }
    }
  }, [navigate])

  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <div
          className={`fixed top-6 left-1/2 z-50 -translate-x-1/2 transition-all duration-300 ${isSocketDisconnected ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4 pointer-events-none'
            }`}
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center gap-3 rounded-full border border-amber-400/40 bg-amber-500/10 px-5 py-3 text-amber-200 shadow-lg shadow-amber-500/20">
            <span className="inline-flex h-3 w-3 rounded-full bg-amber-400 animate-pulse" />
            <span>Disconnected from server. Reconnecting…</span>
          </div>
        </div>
        <Header />
        {children}
        <TanStackDevtools
          config={{
            position: 'bottom-right',
          }}
          plugins={[
            {
              name: 'Tanstack Router',
              render: <TanStackRouterDevtoolsPanel />,
            },
            TanStackQueryDevtools,
          ]}
        />
        <Scripts />
      </body>
    </html>
  )
}
