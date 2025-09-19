"use client";

import React from "react";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import useAuth from "@/hooks/useAuth";

export default function Page() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow max-w-4xl mx-auto p-6">
        <div className="bg-white border rounded p-6 shadow">
          <h1 className="text-2xl font-bold mb-4">My Profile</h1>

          {!user ? (
            <p className="text-gray-600">You are not logged in. <a href="/login" className="text-blue-600 underline">Login</a></p>
          ) : (
            <>
              <div className="mb-4">
                <p className="text-sm text-gray-500">Email</p>
                <p className="font-medium">{user.email}</p>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-500">Account</p>
                <p className="font-medium">Free / Demo</p>
              </div>

              <button onClick={logout} className="bg-red-600 text-white px-3 py-2 rounded">Logout</button>
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
