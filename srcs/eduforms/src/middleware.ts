import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  // Only protect /admin routes
  if (request.nextUrl.pathname.startsWith("/admin")) {
    // Check for session cookie (lightweight check compatible with Edge Runtime)
    // Better Auth uses 'better-auth.session_token' cookie by default
    const sessionToken = request.cookies.get("better-auth.session_token");

    // If no session token exists, redirect to login
    // Full admin verification happens at the page level (Node.js runtime)
    if (!sessionToken) {
      const loginUrl = new URL("/", request.url);
      return NextResponse.redirect(loginUrl);
    }

    // Session exists, allow request to proceed to page-level verification
    return NextResponse.next();
  }

  return NextResponse.next();
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};

