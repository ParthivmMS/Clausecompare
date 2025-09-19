"use client";

import React from "react";
import Navigation from "@/components/Navigation";
import Dashboard from "@/components/Dashboard";
import Footer from "@/components/Footer";

export default function Page() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow">
        <Dashboard />
      </main>
      <Footer />
    </div>
  );
}
