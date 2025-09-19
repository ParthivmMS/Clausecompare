import React from 'react';

export default function ReportViewer({ report }) {
  if (!report) return <p>No report available</p>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Comparison Report</h2>

      <div>
        <h3 className="font-semibold">Risk Score: {report.riskScore}</h3>

        {report.diffs.map((diff, idx) => (
          <div key={idx} className="border p-2 my-2">
            <p><strong>Clause:</strong> {diff.clause}</p>
            <p><strong>Old Text:</strong> {diff.oldText}</p>
            <p><strong>New Text:</strong> {diff.newText}</p>
            <p><strong>Severity:</strong> {diff.severity}</p>
            <p><strong>Suggestion:</strong> {diff.explanation}</p>
          </div>
        ))}

        <a
          href={report.pdfUrl}
          className="mt-4 inline-block bg-green-500 text-white px-4 py-2 rounded"
          target="_blank"
        >
          Download PDF Report
        </a>
      </div>
    </div>
  );
}
