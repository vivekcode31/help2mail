import React, { ButtonHTMLAttributes } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  isLoading = false,
  className = '', 
  disabled, 
  ...props 
}: ButtonProps) {
  
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-black text-white hover:bg-gray-800 border border-transparent shadow-sm',
    secondary: 'bg-gray-100 text-black hover:bg-gray-200 border border-transparent',
    outline: 'bg-transparent text-black border border-gray-300 hover:border-black hover:bg-gray-50',
    ghost: 'bg-transparent text-gray-600 hover:text-black hover:bg-gray-100',
    danger: 'bg-white text-red-600 border border-red-200 hover:bg-red-50 focus:ring-red-500'
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  // Note: Using inline generic classes here representing the CSS we want.
  // To keep it truly standard CSS without Tailwind, we will inject these directly into style or standard CSS if Tailwind isn't available.
  // Wait, I am restricted from Tailwind entirely. I will use standard CSS classes via generic semantic names, and define them in our index.css or write them inline! 
  // Let me switch to purely defined style mappings.
  
  return (
    <button 
      className={`btn btn-${variant} btn-${size} ${className}`}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && <Loader2 size={16} className="btn-spinner" />}
      {!isLoading && children}
      {isLoading && <span style={{marginLeft: '0.5rem'}}>{children}</span>}
    </button>
  );
}
