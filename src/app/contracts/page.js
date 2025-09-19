"use client";

import React, { useState } from "react";
import Navigation from "@/components/Navigation";
import FileUploader from "@/components/FileUploader";
import ReportViewer from "@/components/ReportViewer";
import Footer from "@/components/Footer";

export default function Page() {
  const [report, setReport] = useState(null);

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-grow max-w-6xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Compare Contracts</h1>
          <p className="text-gray-600">Upload two contract versions to see a detailed, plain-English comparison report.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <FileUploader onReport={(r) => setReport(r)} />
          </div>

          <div className="md:col-span-2">
            <ReportViewer report={report} />
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
