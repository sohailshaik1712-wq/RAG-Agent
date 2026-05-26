/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",

  // API rewrites run server-side, so we can use the Docker service name here.
  // The browser never sees this URL — it just calls /api/* on the same origin.
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source:      "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
