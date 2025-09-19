import React from "react";

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t mt-12">
      <div className="max-w-6xl mx-auto px-4 py-6 text-sm text-gray-600 flex justify-between items-center">
        <div>© {new Date().getFullYear()} ClauseCompare</div>
        <div className="space-x-4">
          <a href="/privacy" className="underline">Privacy</a>
          <a href="/terms" className="underline">Terms</a>
        </div>
      </div>
    </footer>
  );
}
