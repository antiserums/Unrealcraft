import type { NextConfig } from "next";

// The browser only ever talks to this app. /api/* is proxied to the FastAPI service so cookies stay same-origin.
const API_URL = process.env.API_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Proof uploads go through the /api proxy, which holds the request body in memory and cuts it off at 10 MB by
  // default. The chest takes up to 2 video clips of 50 MB plus images (api/app/routers/submit.py).
  experimental: { proxyClientMaxBodySize: "120mb" },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};

export default nextConfig;
