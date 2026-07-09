/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // basePath is injected by GitHub Actions automatically, DO NOT hardcode it here.
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
