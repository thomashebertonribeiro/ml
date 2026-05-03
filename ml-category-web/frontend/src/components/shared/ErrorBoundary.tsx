import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean; message: string }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', color: '#e74c3c' }}>
          <h2>Algo deu errado</h2>
          <p>{this.state.message}</p>
          <button onClick={() => this.setState({ hasError: false, message: '' })}>
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
