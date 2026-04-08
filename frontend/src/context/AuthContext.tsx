import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { api } from '../api';

interface AuthContextType {
  isAuthenticated: boolean;
  userEmail: string | null;
  isLoading: boolean;
  authError: string | null;
  checkAuth: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const checkAuth = useCallback(async () => {
    try {
      const res = await api.get('/auth/me');
      if (res.data.user_email) {
        setIsAuthenticated(true);
        setUserEmail(res.data.user_email);
        setAuthError(null);
      } else {
        setIsAuthenticated(false);
        setUserEmail(null);
      }
    } catch (err: any) {
      setIsAuthenticated(false);
      setUserEmail(null);
      if (err.response?.status === 401) {
        setAuthError('Session expired. Please sign in again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.error('Logout failed', err);
    } finally {
      setIsAuthenticated(false);
      setUserEmail(null);
      setAuthError(null);
    }
  }, []);

  const clearError = useCallback(() => {
    setAuthError(null);
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, userEmail, isLoading, authError, checkAuth, logout, clearError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
