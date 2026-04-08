import React from 'react';

export function Card({ children, className = '' }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={`card ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ title, description }: { title: string, description?: string }) {
  return (
    <div className="card-header">
      <h3 className="card-title">{title}</h3>
      {description && <p className="card-desc text-light">{description}</p>}
    </div>
  );
}

export function CardContent({ children, className = '' }: { children: React.ReactNode, className?: string }) {
  return <div className={`card-content ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }: { children: React.ReactNode, className?: string }) {
  return <div className={`card-footer ${className}`}>{children}</div>;
}
