/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  // Enable standalone output for optimized Docker production builds
  // This creates a minimal server with only required dependencies
  output: 'standalone',
}

export default nextConfig
