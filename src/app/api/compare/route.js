// src/app/api/compare/route.js
import { NextResponse } from 'next/server';

const BACKEND = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request) {
  try {
    // Expect multipart/form-data from client
    const formData = await request.formData();

    // Create a new FormData to forward to the backend
    const forwardForm = new FormData();

    // Forward all fields (including files)
    for (const [key, value] of formData.entries()) {
      // value can be string or File
      forwardForm.append(key, value);
    }

    // Forward the multipart to the backend compare endpoint
    const backendRes = await fetch(`${BACKEND.replace(/\/$/, '')}/compare`, {
      method: 'POST',
      body: forwardForm,
      // NOTE: Do NOT set Content-Type header; the fetch implementation will set the correct multipart boundary.
    });

    // If backend returned JSON or other content, stream it back to client preserving content-type
    const contentType = backendRes.headers.get('content-type') || 'application/json';
    const body = backendRes.body;

    return new NextResponse(body, {
      status: backendRes.status,
      headers: { 'content-type': contentType },
    });
  } catch (err) {
    console.error('Error in /api/compare proxy:', err);
    return new NextResponse(JSON.stringify({ error: 'Internal proxy error' }), { status: 500, headers: { 'content-type': 'application/json' } });
  }
}
