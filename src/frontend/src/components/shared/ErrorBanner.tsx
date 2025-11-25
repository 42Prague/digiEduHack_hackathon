import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { AlertCircle, X } from 'lucide-react';
import { Button } from '../ui/button';

interface ErrorBannerProps {
  error: Error | string;
  onDismiss?: () => void;
  onRetry?: () => void;
}

export function ErrorBanner({ error, onDismiss, onRetry }: ErrorBannerProps) {
  const message = typeof error === 'string' ? error : error.message;
  const errorType = typeof error === 'object' && 'type' in error ? (error as any).type : 'Error';

  return (
    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-start gap-3">
        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-medium text-red-900 mb-1">{errorType}</h4>
          <p className="text-sm text-red-700">{message}</p>
          {(onRetry || onDismiss) && (
            <div className="flex gap-2 mt-3">
              {onRetry && (
                <Button variant="outline" size="sm" onClick={onRetry}>
                  Retry
                </Button>
              )}
              {onDismiss && (
                <Button variant="ghost" size="sm" onClick={onDismiss}>
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

