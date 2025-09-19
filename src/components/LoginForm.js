import React, { useState } from 'react';

export default function LoginForm({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = e => {
    e.preventDefault();
    onLogin({ email, password });
  };

  return (
    <form className="p-4 max-w-md mx-auto" onSubmit={handleSubmit}>
      <h2 className="text-xl font-semibold mb-4">Login to ClauseCompare</h2>
      
      <input
        type="email"
        placeholder="Email"
        className="w-full border p-2 mb-4"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />

      <input
        type="password"
        placeholder="Password"
        className="w-full border p-2 mb-4"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />

      <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
        Login
      </button>
    </form>
  );
}
