"use client";

import React, { useState } from "react";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";

export default function Page() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleSignup = (e) => {
    e.preventDefault();
    // Replace with real signup API call
    setMessage("Signup simulated — check your email for confirmation (demo).");
    setEmail("");
    setPassword("");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow max-w-3xl mx-auto w-full p-6">
        <div className="bg-white border rounded p-6 shadow max-w-md mx-auto">
          <h1 className="text-2xl font-semibold mb-4">Create your ClauseCompare account</h1>
          <p className="text-sm text-gray-500 mb-4">Start with 1 free comparison. No credit card required for the trial.</p>

          {message && <div className="mb-4 text-green-600">{message}</div>}

          <form onSubmit={handleSignup}>
            <label className="block mb-2">
              <span className="text-sm">Email</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border p-2 rounded mt-1"
              />
            </label>

            <label className="block mb-4">
              <span className="text-sm">Password</span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border p-2 rounded mt-1"
              />
            </label>

            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Sign up</button>
          </form>

          <p className="text-sm text-gray-500 mt-4">
            Already have an account? <a href="/login" className="text-blue-600 underline">Login</a>
          </p>
        </div>
      </main>
      <Footer />
    </div>
  );
          }
