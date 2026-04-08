import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { LogOut, Send, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/Button';

export function Layout() {
  const { userEmail, logout } = useAuth();

  return (
    <div className="layout-wrapper">
      <header className="layout-header">
        <div className="container flex justify-between items-center">
          <Link to="/" className="flex items-center gap-2">
            <Send size={24} />
            <h2>Help2Mail</h2>
          </Link>
          <nav className="flex items-center gap-6">
            <Link to="/" className="text-sm border-b hover:border-black">New Campaign</Link>
            <Link to="/history" className="text-sm flex items-center gap-2 hover:text-black text-light transition-colors">
              <Clock size={16} /> History
            </Link>
            <div className="flex items-center gap-4 border-l border-gray-200 pl-4 ml-2">
              <span className="text-sm text-light">{userEmail}</span>
              <Button variant="ghost" size="sm" onClick={logout} title="Sign Out">
                <LogOut size={16} />
              </Button>
            </div>
          </nav>
        </div>
      </header>
      <main className="layout-main">
        <div className="container">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
