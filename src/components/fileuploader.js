import React, { useState } from 'react';

export default function FileUploader({ onFilesSelected }) {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);

  const handleUpload = () => {
    if (fileA && fileB) {
      onFilesSelected({ fileA, fileB });
    }
  };

  return (
    <div className="p-4 border rounded shadow">
      <h2 className="text-lg font-semibold mb-4">Upload Contract Versions</h2>
      
      <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFileA(e.target.files[0])} />
      <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFileB(e.target.files[0])} />

      <button
        className="mt-4 bg-blue-500 text-white px-4 py-2 rounded"
        onClick={handleUpload}
      >
        Compare Files
      </button>
    </div>
  );
}
