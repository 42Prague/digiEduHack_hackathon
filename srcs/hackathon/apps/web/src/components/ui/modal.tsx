// src/components/ui/Modal.tsx
// This component should NOT be "use client" if it's purely structural, 
// but since it uses children, we'll keep it simple as a functional wrapper.

import React from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title: string;
  // Optional size prop
  size?: 'md' | 'lg' | 'xl'; 
}

export default function Modal({ isOpen, onClose, children, title, size = 'lg' }: ModalProps) {
  if (!isOpen) return null;

  const maxWidthClass = {
    md: 'max-w-xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
  }[size];

  return (
    // Fixed overlay background
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 transition-opacity duration-300">
      
      {/* Modal Container */}
      <div 
        className={`relative w-full rounded-lg bg-background shadow-2xl transition-transform duration-300 transform scale-100 ${maxWidthClass} max-h-[90vh] overflow-y-auto`}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border p-6 sticky top-0 bg-background z-10">
          <h2 className="text-xl font-semibold text-foreground">{title}</h2>
          <button 
            onClick={onClose} 
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close modal"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        {/* Modal Body */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
}