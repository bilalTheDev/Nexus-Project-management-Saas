import { Component } from 'react'

/**
 * Catches render errors in the tree and offers a simple retry.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: error?.message || 'Something went wrong.',
    }
  }

  componentDidCatch(error, info) {
    if (typeof console !== 'undefined') {
      console.error('ErrorBoundary caught', error, info?.componentStack)
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, message: '' })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          style={{
            minHeight: '100vh',
            display: 'grid',
            placeItems: 'center',
            padding: '2rem',
            fontFamily: 'var(--font-sans, system-ui, sans-serif)',
            background: 'var(--bg, #0c0c0c)',
            color: 'var(--fg, #f5f5f5)',
          }}
        >
          <div style={{ maxWidth: '28rem', textAlign: 'center' }}>
            <h1 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
              This view hit an error
            </h1>
            <p style={{ opacity: 0.75, marginBottom: '1.25rem', fontSize: '0.95rem' }}>
              {this.state.message}
            </p>
            <button
              type="button"
              onClick={this.handleRetry}
              style={{
                padding: '0.6rem 1.1rem',
                borderRadius: '0.5rem',
                border: '1px solid currentColor',
                background: 'transparent',
                color: 'inherit',
                cursor: 'pointer',
                fontSize: '0.95rem',
              }}
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
