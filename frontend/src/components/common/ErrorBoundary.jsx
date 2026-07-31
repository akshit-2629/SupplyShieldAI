import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          background: '#F9FAFB',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
          textAlign: 'center',
        }}>
          <div style={{
            width: 56,
            height: 56,
            background: '#FEE2E2',
            border: '1px solid #FCA5A5',
            borderRadius: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 16,
          }}>
            <AlertTriangle size={28} color="#DC2626" />
          </div>

          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#111827', marginBottom: 8 }}>
            Something went wrong
          </h2>

          <p style={{ fontSize: 14, color: '#6B7280', maxWidth: 460, marginBottom: 20, lineHeight: 1.5 }}>
            An unexpected error occurred while rendering this page. Our team has been notified.
          </p>

          {this.state.error?.message && (
            <div style={{
              background: '#FFFFFF',
              border: '1px solid #E5E7EB',
              borderRadius: 8,
              padding: '10px 16px',
              fontSize: 12,
              fontFamily: 'monospace',
              color: '#991B1B',
              marginBottom: 20,
              maxWidth: 500,
              wordBreak: 'break-word',
            }}>
              {this.state.error.message}
            </div>
          )}

          <button
            onClick={this.handleReset}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              background: '#2563EB',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: 8,
              padding: '10px 20px',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={15} /> Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
