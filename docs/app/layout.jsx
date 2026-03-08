import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'nextra-theme-docs/style.css'
import './globals.css'
 
export const metadata = {
  // Define your metadata here
  // For more information on metadata API, see: https://nextjs.org/docs/app/building-your-application/optimizing/metadata
}
 
const navbar = (
  <Navbar
    projectLink="https://github.com/codebridgehq/convoy"
    logo={
      <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <img src="/logo.svg" alt="Convoy" style={{ height: '24px', width: 'auto' }} />
        <b>Convoy</b>
      </span>
    }
  />
)
const footer = <Footer>MIT {new Date().getFullYear()} © Convoy</Footer>
 
export default async function RootLayout({ children }) {
  return (
    <html
      // Not required, but good for SEO
      lang="en"
      // Required to be set
      dir="ltr"
      // Suggested by `next-themes` package https://github.com/pacocoursey/next-themes#with-app
      suppressHydrationWarning
    >
      <Head
        color={{
          hue: { light: 343, dark: 343 },        // Pink primary color (#FF6B9D)
          saturation: { light: 100, dark: 100 }, // Full saturation
          lightness: { light: 45, dark: 71 }     // Adjusted for light/dark mode visibility
        }}
        backgroundColor={{
          light: "rgb(255,255,255)",              // White background for light mode
          dark: "rgb(45,27,78)"                   // Dark purple background (#2D1B4E)
        }}
      >
        <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="shortcut icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/site.webmanifest" />
      </Head>
      <body>
        <Layout
          navbar={navbar}
          pageMap={await getPageMap()}
          docsRepositoryBase="https://github.com/codebridgehq/convoy/tree/main/docs"
          footer={footer}
          // ... Your additional layout options
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}