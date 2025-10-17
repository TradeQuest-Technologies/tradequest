/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Temporarily remove standalone for initial deployment
  // output: 'standalone',
  experimental: {
    serverComponentsExternalPackages: [],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Disabled rewrites - using catch-all API route instead
  // async rewrites() {
  //   const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: `${apiUrl}/api/:path*`,
  //     },
  //     {
  //       source: '/uploads/:path*',
  //       destination: `${apiUrl}/uploads/:path*`,
  //     },
  //   ]
  // },
}

module.exports = nextConfig
