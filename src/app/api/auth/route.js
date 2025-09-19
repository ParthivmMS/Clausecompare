// src/app/api/auth/route.js
import { NextResponse } from 'next/server';

const BACKEND = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request) {
  try {
    // Expect JSON body from client (e.g., { email, password, action: "login" } or plain /auth/login)
    const json = await request.json();

    // Determine backend path. If the frontend sends { path: '/auth/login', ... } you can forward to that.
    // Otherwise, default to /auth/login when json.action === 'login', or /auth/signup when 'signup'.
    let backendPath = '/auth/login';
    if (json.path) {
      backendPath = json.path;
    } else if (json.action === 'signup') {
      backendPath = '/auth/signup';
    } else if (json.action === 'login') {
      backendPath = '/auth/login';
    }

    // Forward body as JSON
    const backendRes = await fetch(`${BACKEND.replace(/\/$/, '')}${backendPath}`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
      },
      body: JSON.stringify(json),
      credentials: 'include',
    });

    const contentType = backendRes.headers.get('content-type') || 'application/json';

    // If backend returns JSON, stream it back
    const body = backendRes.body;

    // If backend sets cookies (Set-Cookie), NextResponse will not automatically forward them.
    // If you need to set cookies from backend onto client, you'll have to parse Set-Cookie header and set them via NextResponse.
    // For now we simply proxy the body + status + content-type.
    return new NextResponse(body, {
      status: backendRes.status,
      headers: { 'content-type': contentType },
    });
  } catch (err) {
    console.error('Error in /api/auth proxy:', err);
    return new NextResponse(JSON.stringify({ error: 'Internal auth proxy error' }), { status: 500, headers: { 'content-type': 'application/json' } });
  }
}
