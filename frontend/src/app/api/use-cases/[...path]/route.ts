import { NextRequest } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5127";

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;

  const targetPath = path.join("/");
  const url = `${API_BASE}/api/v1/use-cases/${targetPath}`;

  const body = await req.text();

  const upstream = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": req.headers.get("content-type") ?? "application/json",
    },
    body,
  });

  const text = await upstream.text();

  return new Response(text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
