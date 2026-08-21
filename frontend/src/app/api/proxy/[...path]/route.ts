import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function handleProxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/');
  const url = new URL(req.url);
  const searchParams = url.searchParams.toString();
  const targetUrl = `${API_URL}/${path}${searchParams ? `?${searchParams}` : ''}`;
  
  const cookieStore = await cookies();
  const token = cookieStore.get('token')?.value;
  
  const headers = new Headers(req.headers);
  headers.delete('host');
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  let body = undefined;
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    body = await req.arrayBuffer();
  }

  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body,
      redirect: 'manual',
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete('content-encoding');
    
    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    return new NextResponse(JSON.stringify({ error: 'Gateway Timeout / Backend indisponível' }), { status: 502 });
  }
}

export const GET = handleProxy;
export const POST = handleProxy;
export const PUT = handleProxy;
export const DELETE = handleProxy;
export const PATCH = handleProxy;
