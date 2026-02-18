import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';

/**
 * Global Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      retryCount: 0,
      isRetrying: false
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({ errorInfo });
    
    // You could also log to an error reporting service here
    // Example: logErrorToService(error, errorInfo);
  }

  handleRetry = async () => {
    this.setState({ isRetrying: true });
    
    // Wait a bit before retrying
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1,
      isRetrying: false
    }));
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleRefreshPage = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error, retryCount, isRetrying } = this.state;
      
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
          <Card className="max-w-lg w-full shadow-xl border-0">
            <CardHeader className="text-center pb-2">
              <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="w-8 h-8 text-amber-600" />
              </div>
              <CardTitle className="text-2xl font-bold text-slate-800">
                Something went wrong
              </CardTitle>
              <CardDescription className="text-slate-600 mt-2">
                {retryCount > 2 
                  ? "We're having trouble loading this page. Please try again later or contact support."
                  : "Don't worry, we're working on it. Try refreshing or click retry below."
                }
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Error Details (collapsible in production) */}
              {process.env.NODE_ENV === 'development' && error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm font-mono text-red-800 break-all">
                    {error.toString()}
                  </p>
                </div>
              )}
              
              {/* Retry Status */}
              {retryCount > 0 && (
                <div className="text-center text-sm text-slate-500">
                  Retry attempt: {retryCount}/3
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button 
                  onClick={this.handleRetry}
                  disabled={isRetrying || retryCount >= 3}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700"
                  data-testid="error-boundary-retry-btn"
                >
                  {isRetrying ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Retrying...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Try Again
                    </>
                  )}
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={this.handleGoHome}
                  className="flex-1"
                  data-testid="error-boundary-home-btn"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
              </div>
              
              {/* Hard Refresh Option */}
              {retryCount >= 2 && (
                <Button 
                  variant="ghost" 
                  onClick={this.handleRefreshPage}
                  className="w-full text-slate-500"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh Page
                </Button>
              )}
              
              {/* Support Link */}
              <p className="text-center text-xs text-slate-400 pt-2">
                If this problem persists, please contact support.
              </p>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * API Error Handler Component
 * Shows a retry-able error state for API failures
 */
export const APIErrorState = ({ 
  message = "Failed to load data", 
  onRetry, 
  isRetrying = false 
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <AlertTriangle className="w-6 h-6 text-red-600" />
      </div>
      <h3 className="text-lg font-semibold text-slate-800 mb-2">
        Connection Error
      </h3>
      <p className="text-slate-600 mb-4 max-w-sm">
        {message}
      </p>
      {onRetry && (
        <Button 
          onClick={onRetry} 
          disabled={isRetrying}
          variant="outline"
          data-testid="api-error-retry-btn"
        >
          {isRetrying ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Retrying...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </>
          )}
        </Button>
      )}
    </div>
  );
};

/**
 * Loading State with Connection Status
 */
export const LoadingWithRetry = ({ 
  message = "Loading...", 
  showRetry = false,
  onRetry 
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
      <p className="text-slate-600">{message}</p>
      {showRetry && onRetry && (
        <Button 
          onClick={onRetry}
          variant="ghost"
          className="mt-4 text-sm"
        >
          Taking too long? Click to retry
        </Button>
      )}
    </div>
  );
};

export default ErrorBoundary;
