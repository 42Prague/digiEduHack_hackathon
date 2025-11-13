import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Add the rewrites function here
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://10.10.3.239:3000/v1/:path*",
      },
    ];
  },
};

export default nextConfig;

// Local destination when running directly on the client
//"http://localhost:3600/v1/:path*" - when running on the host
// destination: "http://lazy-forms-reg-form-1:3100/v1/:path*" - when running as container
//"temp aws IP address: 10.10.3.239
// AWS: "http://10.10.3.239:3000/v1/:path*" - when running in AWS cloud
