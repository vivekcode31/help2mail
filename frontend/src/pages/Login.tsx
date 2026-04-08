import React, { useState, useEffect } from 'react';
import { Send, AlertCircle } from 'lucide-react';
import { api } from '../api';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { useSearchParams } from 'react-router-dom';

export function Login() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { authError, clearError } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Pick up error from URL query (set by backend callback redirect)
  useEffect(() => {
    const urlError = searchParams.get('auth_error');
    if (urlError) {
      setError(urlError);
      // Clean the URL so refreshing doesn't re-show
      searchParams.delete('auth_error');
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Also surface context-level errors
  useEffect(() => {
    if (authError) {
      setError(authError);
      clearError();
    }
  }, [authError, clearError]);

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await api.get('/auth/login');
      if (res.data.auth_url) {
        window.location.href = res.data.auth_url;
      } else {
        setError('Could not get authorization URL. Please try again.');
        setIsLoading(false);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to connect to server. Please try again.';
      setError(msg);
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page animate-fade-in">
      <div className="login-card">
        {/* Brand Section */}
        <div className="login-brand">
          <div className="login-icon-wrapper">
            <Send size={32} />
          </div>
          <h1 className="login-title">Help2Mail</h1>
          <p className="login-subtitle">
            Bulk-send personalized emails from your own Gmail — no SMTP hassle.
          </p>
        </div>

        {/* Divider */}
        <div className="login-divider" />

        {/* Error Display */}
        {error && (
          <div className="login-error animate-fade-in" role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Google Sign-In Button */}
        <button
          id="google-login-btn"
          className="google-btn"
          onClick={handleLogin}
          disabled={isLoading}
          type="button"
        >
          {isLoading ? (
            <div className="google-btn-spinner" />
          ) : (
            <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
          )}
          <span>{isLoading ? 'Redirecting…' : 'Sign in with Google'}</span>
        </button>

        <p className="login-footer-text">
          We only request basic profile access — your data stays yours.
        </p>
      </div>
    </div>
  );
}
