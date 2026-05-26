/**
 * middleware.ts — No auth check here.
 * Auth is handled client-side in ChatShell via Zustand (persisted to localStorage).
 * Middleware runs on the edge and can't read localStorage, so we keep it simple.
 */
import { NextResponse } from "next/server";
export function middleware() { return NextResponse.next(); }
export const config = { matcher: [] };
