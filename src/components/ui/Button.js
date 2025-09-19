import React from 'react';

export default function Button({ children, className = '', ...props }) {
  return (
    <button
      className={`bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 disabled:opacity-60 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
