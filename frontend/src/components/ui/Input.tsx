import React, { InputHTMLAttributes, TextareaHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, className = '', id, ...props }: InputProps) {
  const inputId = id || Array.from({length: 8}, () => Math.random().toString(36)[2]).join('');
  
  return (
    <div className={`mb-4 w-full ${className}`}>
      <label htmlFor={inputId} className="label">
        {label}
      </label>
      <input 
        id={inputId}
        className="input-field" 
        {...props} 
      />
      {error && <p className="text-xs text-error mt-1">{error}</p>}
    </div>
  );
}

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export function TextArea({ label, error, className = '', id, ...props }: TextAreaProps) {
  const inputId = id || Array.from({length: 8}, () => Math.random().toString(36)[2]).join('');
  
  return (
    <div className={`mb-4 w-full ${className}`}>
      <label htmlFor={inputId} className="label">
        {label}
      </label>
      <textarea 
        id={inputId}
        className="input-field" 
        style={{ resize: 'vertical', minHeight: '100px' }}
        {...props} 
      />
      {error && <p className="text-xs text-error mt-1">{error}</p>}
    </div>
  );
}
