import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (err: Error, reset: () => void) => React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error({
      event: "react_error_boundary_caught",
      error_type: error.name,
      error_message: error.message,
      component_stack: info.componentStack,
    });
  }

  reset = (): void => {
    this.setState({ error: null });
  };

  render(): React.ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    if (this.props.fallback) {
      return this.props.fallback(error, this.reset);
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="max-w-lg w-full">
          <CardContent className="p-6 sm:p-8">
            <h1 className="text-page-heading uppercase tracking-tight text-foreground mb-3">
              Something went wrong
            </h1>
            <p className="text-sm text-muted-foreground mb-4">
              An unexpected error occurred while rendering the page.
            </p>
            <pre className="text-xs font-[var(--font-mono)] bg-muted text-foreground p-3 rounded-md overflow-auto whitespace-pre-wrap break-words mb-4 max-h-48">
              {error.message}
            </pre>
            <Button onClick={() => window.location.reload()}>Reload</Button>
          </CardContent>
        </Card>
      </div>
    );
  }
}

export default ErrorBoundary;
