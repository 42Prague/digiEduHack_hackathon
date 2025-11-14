/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/v1/:path*",
        destination: "http://reg-form:3100/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
