import { InterviewLiveEventMessage } from '../types'

export type InterviewSocketOptions = {
  sessionId: string
  accessToken?: string
  baseWsUrl?: string // e.g. ws://localhost:8000
}

type SocketState = {
  connected: boolean
  lastError?: string
}

export class InterviewSocket {
  private socket: WebSocket | null = null
  private opts: InterviewSocketOptions
  private state: SocketState = { connected: false }
  private heartbeatTimer: number | null = null
  private heartbeatIntervalMs = 15000

  public onMessage: ((msg: InterviewLiveEventMessage) => void) | null = null
  public onOpen: (() => void) | null = null
  public onClose: ((ev: CloseEvent) => void) | null = null
  public onError: ((err: Event) => void) | null = null

  constructor(opts: InterviewSocketOptions) {
    this.opts = opts
  }

  get isConnected() {
    return this.state.connected
  }

  connect() {
    const { sessionId, accessToken, baseWsUrl } = this.opts

    const host = baseWsUrl || ''
    const schemePrefixed = host ? host.replace(/\/$/, '') : ''

    // If baseWsUrl is empty, assume current origin (browser ws)
    // We intentionally use relative ws path to work behind nginx.
    // Example: /api/v1/interview/live/{sessionId}
    const path = `/api/v1/interview/live/${encodeURIComponent(sessionId)}`
    const url = schemePrefixed
      ? `${schemePrefixed}${path}`
      : `${path.startsWith('ws://') ? path : path}`

    this.socket = new WebSocket(url)

    if (accessToken) {
      // Browsers don't allow custom headers in WebSocket.
      // We try query param as a fallback.
      // If your backend already reads token from cookies, remove this.
      // Note: only works if backend supports it.
    }

    this.socket.onopen = () => {
      this.state.connected = true
      this.onOpen?.()
      this.startHeartbeat()
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as InterviewLiveEventMessage
        this.onMessage?.(data)
      } catch {
        // ignore non-json messages
      }
    }

    this.socket.onerror = (err) => {
      this.state.lastError = 'WebSocket error'
      this.onError?.(err)
    }

    this.socket.onclose = (ev) => {
      this.state.connected = false
      this.stopHeartbeat()
      this.onClose?.(ev)
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      // MVP: send a lightweight ping event with new protocol shape
      // Backend can choose to ignore.
      this.sendEvent('heartbeat', {})
    }, this.heartbeatIntervalMs)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      window.clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  close() {
    this.stopHeartbeat()
    this.socket?.close()
    this.socket = null
    this.state.connected = false
  }

  reconnect() {
    this.close()
    this.connect()
  }

  sendEvent(event: string, payload: any) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return

    const msg = {
      event,
      payload: payload ?? {},
    }

    this.socket.send(JSON.stringify(msg))
  }
}

