import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'GET');
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'POST');
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'PUT');
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'DELETE');
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'PATCH');
}

async function handleRequest(request: NextRequest, params: { path: string[] }, method: string) {
  try {
    const path = params.path.join('/');
    const url = new URL(request.url);
    const searchParams = url.searchParams.toString();
    
    // Get the backend URL from environment variable, fallback to localhost for dev
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Construct the full backend URL
    // Note: path already includes 'v1/...', so we add /api prefix
    const fullBackendUrl = `${backendUrl}/api/${path}${searchParams ? `?${searchParams}` : ''}`;
    
    // Debug logging
    console.log('=== CATCH-ALL API PROXY DEBUG ===');
    console.log('Method:', method);
    console.log('Path:', path);
    console.log('Full URL:', url.pathname);
    console.log('Backend URL:', fullBackendUrl);
    console.log(`Proxying ${method} ${url.pathname} to ${fullBackendUrl}`);
    
    // Forward headers (excluding host and other problematic headers)
    const headers: Record<string, string> = {};
    request.headers.forEach((value, key) => {
      if (!['host', 'content-length'].includes(key.toLowerCase())) {
        headers[key] = value;
      }
    });
    
    // Forward the request to the backend
    const response = await fetch(fullBackendUrl, {
      method,
      headers,
      body: ['POST', 'PUT', 'PATCH'].includes(method) ? await request.text() : undefined,
    });
    
    console.log(`Backend responded with status ${response.status}`);
    
    // Check content type
    const contentType = response.headers.get('content-type') || '';
    
    // Handle Server-Sent Events (SSE) - stream through without buffering
    if (contentType.includes('text/event-stream')) {
      console.log('SSE detected - streaming response through');
      return new NextResponse(response.body, {
        status: response.status,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'X-Accel-Buffering': 'no'
        }
      });
    }
    
    // Handle images - return binary data directly
    if (contentType.startsWith('image/')) {
      const imageBuffer = await response.arrayBuffer();
      return new NextResponse(imageBuffer, {
        status: response.status,
        headers: {
          'Content-Type': contentType,
          'Cache-Control': response.headers.get('cache-control') || 'public, max-age=3600',
        }
      });
    }
    
    // For other responses, parse as JSON/text
    const responseText = await response.text();
    
    // Try to parse as JSON, fallback to text
    let responseData;
    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = responseText;
    }
    
    return NextResponse.json(responseData, { 
      status: response.status,
      headers: {
        'Content-Type': contentType || 'application/json',
      }
    });
    
  } catch (error: any) {
    console.error(`Error proxying ${method} request:`, error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message },
      { status: 500 }
    );
  }
}
