import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "export",
  basePath: "/davi-finance",
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
