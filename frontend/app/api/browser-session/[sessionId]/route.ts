import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await params;
  try {

    // Forward the request to the backend
    const backendUrl = `http://localhost:8000/api/browser-session/${sessionId}`;
    const response = await fetch(backendUrl);
    
    if (response.ok) {
      const data = await response.json();
      return NextResponse.json(data);
    }
    
    // If backend returns 404, return a default response instead of propagating the error
    if (response.status === 404) {
      return NextResponse.json({
        session_id: sessionId,
        status: "active", 
        browsers: {},
        task: "Web agent task in progress"
      });
    }
    
    // For other errors, return the backend error
    const errorData = await response.text();
    return NextResponse.json(
      { error: errorData }, 
      { status: response.status }
    );
    
  } catch (error) {
    console.error('Error fetching browser session:', error);
    
    // Return a fallback response instead of an error
    return NextResponse.json({
      session_id: sessionId,
      status: "active",
      browsers: {},
      task: "Web agent task in progress"
    });
  }
}