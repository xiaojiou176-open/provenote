import type { NextConfig } from "next";
import createBundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = createBundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig: NextConfig = {
  // Enable standalone output for optimized Docker deployment
  output: "standalone",
  distDir: process.env.NEXT_DIST_DIR || ".runtime-cache/build/next",
  reactStrictMode: true,
  turbopack: {},
  devIndicators: false,

  // Experimental features
  // Type assertion needed because Next.js experimental typing can lag behind runtime flags.
  experimental: {
    // Increase proxy body size limit for file uploads (default is 10MB)
    // This allows larger files to be uploaded through the /api/* rewrite proxy to FastAPI
    proxyClientMaxBodySize: "100mb",
    serverActions: {
      bodySizeLimit: "10mb",
    },
  } as NextConfig['experimental'],
  webpack: (config, { isServer }) => {
    // Fixes npm packages that depend on Node-only modules in browser bundles.
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },

  // API Rewrites: Proxy /api/* requests to FastAPI backend
  // This simplifies reverse proxy configuration - users only need to proxy to port 8502
  // Next.js handles internal routing to the API backend on port 5055
  async rewrites() {
    // INTERNAL_API_URL: Where Next.js server-side should proxy API requests
    // Default: http://localhost:5055 (single-container deployment)
    // Override for multi-container: INTERNAL_API_URL=http://api-service:5055
    const internalApiUrl = process.env.INTERNAL_API_URL || "http://localhost:5055";

    console.log(`[Next.js Rewrites] Proxying /api/* to ${internalApiUrl}/api/*`);

    return [
      {
        source: "/api/:path*",
        destination: `${internalApiUrl}/api/:path*`,
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
