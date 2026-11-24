import type { NextConfig } from "next";

// Le navigateur appelle /api/v1/* sur le même domaine ; Next.js relaie vers le backend.
// Aucun secret n'est exposé au navigateur.
const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${backendUrl}/api/v1/:path*` }];
  },
};

export default nextConfig;
