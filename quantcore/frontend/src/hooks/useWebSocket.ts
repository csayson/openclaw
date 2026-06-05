import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import { useTradingStore } from '@/store/tradingStore'
import { useAuthStore } from '@/store/authStore'
import type { Trade, TradingState } from '@/types'

let socket: Socket | null = null

export function useWebSocket(accountId: string | undefined) {
  const { setOpenPositions, addPosition, removePosition, updatePosition, setState } =
    useTradingStore()
  const { accessToken } = useAuthStore()
  const mounted = useRef(true)

  useEffect(() => {
    if (!accountId || !accessToken) return

    socket = io('/', {
      auth: { token: accessToken },
      transports: ['websocket'],
    })

    socket.on('connect', () => {
      socket?.emit('subscribe_account', { account_id: accountId })
    })

    socket.on('state_change', (data: { state: TradingState }) => {
      if (mounted.current) setState(data.state)
    })

    socket.on('position_update', (trade: Trade) => {
      if (!mounted.current) return
      updatePosition(trade.id, trade)
    })

    socket.on('position_opened', (trade: Trade) => {
      if (mounted.current) addPosition(trade)
    })

    socket.on('position_closed', ({ trade_id }: { trade_id: string }) => {
      if (mounted.current) {
        // Delay removal by 5s to show final P&L (per Smart Chart spec)
        setTimeout(() => removePosition(trade_id), 5000)
      }
    })

    socket.on('positions_snapshot', (positions: Trade[]) => {
      if (mounted.current) setOpenPositions(positions)
    })

    socket.on('kpi_update', (kpis: any) => {
      if (mounted.current) useTradingStore.getState().updateKPIs(kpis)
    })

    return () => {
      mounted.current = false
      socket?.disconnect()
    }
  }, [accountId, accessToken])

  return socket
}
