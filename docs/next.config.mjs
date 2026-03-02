import nextra from 'nextra'

// Set up Nextra with its configuration
const withNextra = nextra({
  // Nextra-specific options
})

// Export the final Next.js config with Nextra included
export default withNextra({
  // Enable static export for S3/CloudFront hosting
  output: 'export',
  
  // Use trailing slashes for better S3 compatibility
  trailingSlash: true,
  
  // Required for static export - disable image optimization
  images: {
    unoptimized: true
  }
})
