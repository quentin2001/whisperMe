import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-red-50 text-red-800 min-h-screen flex flex-col items-center justify-center">
          <div className="max-w-2xl bg-white p-6 rounded-lg shadow-lg border border-red-200">
            <h1 className="text-2xl font-bold mb-4 flex items-center">
              <svg className="w-8 h-8 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              Something went wrong.
            </h1>
            <p className="mb-4 text-gray-700">The application encountered an unexpected error.</p>
            <details className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded overflow-auto max-h-96">
              <summary className="cursor-pointer font-bold mb-2">Error Details</summary>
              <div className="mt-2 text-red-600 font-semibold">{this.state.error && this.state.error.toString()}</div>
              <div className="mt-2 text-gray-600 text-xs">{this.state.errorInfo && this.state.errorInfo.componentStack}</div>
            </details>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children; 
  }
}

export default ErrorBoundary;
