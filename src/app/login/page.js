"use client";

import React from "react";
import Navigation from "@/components/Navigation";
import LoginForm from "@/components/LoginForm";
import Footer from "@/components/Footer";

export default function Page() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow max-w-4xl mx-auto w-full p-6">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div className="hidden md:block">
            <h1 className="text-3xl font-bold mb-4">Welcome back</h1>
            <p className="text-gray-600">
              Login to ClauseCompare to run contract comparisons, download reports, and manage your account.
            </p>
            <img src="/images/login-illus.svg" alt="login" className="mt-6 w-full" />
          </div>

          <div className="bg-white border rounded p-6 shadow">
            <LoginForm />
            <p className="text-sm text-gray-500 mt-4">
              Don’t have an account? <a href="/signup" className="text-blue-600 underline">Sign up</a>
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
