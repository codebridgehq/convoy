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
    projectLink="https://github.com/Sonic-Web-Dev/convoy"
    logo={<b>🚂 Convoy</b>}
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
        {/* Your additional tags should be passed as `children` of `<Head>` element */}
      </Head>
      <body>
        <Layout
          navbar={navbar}
          pageMap={await getPageMap()}
          docsRepositoryBase="https://github.com/Sonic-Web-Dev/convoy/tree/master/docs"
          footer={footer}
          // ... Your additional layout options
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}