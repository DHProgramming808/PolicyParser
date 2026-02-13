export async function GET() {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5127";

  const upstream = await fetch(`${API_BASE}/api/v1/health`, {
    cache: "no-store",
  });

  const text = await upstream.text();

  return new Response(text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
