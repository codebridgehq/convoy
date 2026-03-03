import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Hero() {
  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 pt-20">
      {/* Subtle glow */}
      <div className="pointer-events-none absolute top-1/3 left-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-[120px]" />

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
          Now in Public Beta
        </div>

        <h1 className="text-balance text-4xl font-semibold tracking-tight text-primary sm:text-5xl md:text-6xl lg:text-7xl">
          Batch Processing
          <br />
          Made Simple
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-muted-foreground md:text-xl">
          Reduce AI infrastructure costs by 50% or more. No queues to manage,
          no minimum volumes — just send requests and get results.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button asChild size="lg" className="rounded-full px-8 text-base">
            <Link href="/dashboard">
              Get Started
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            size="lg"
            className="rounded-full border-primary/30 px-8 text-base text-primary hover:bg-primary/10 hover:text-primary bg-transparent"
          >
            <Link href="#how-it-works">View Docs</Link>
          </Button>
        </div>

        {/* Code snippet preview */}
        <div className="mx-auto mt-16 max-w-xl overflow-hidden rounded-lg border border-border bg-card">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <span className="h-2.5 w-2.5 rounded-full bg-primary/40" />
            <span className="h-2.5 w-2.5 rounded-full bg-primary/20" />
            <span className="h-2.5 w-2.5 rounded-full bg-primary/10" />
            <span className="ml-3 text-xs text-muted-foreground">
              cargo_load.sh
            </span>
          </div>
          <pre className="overflow-x-auto p-5 text-left font-mono text-sm leading-relaxed">
            <code>
              <span className="text-muted-foreground">{'# Load your cargo'}</span>
              {'\n'}
              <span className="text-primary">curl</span>
              <span className="text-foreground">
                {' -X POST https://api.convoy.dev/cargo/load \\'}
              </span>
              {'\n'}
              <span className="text-foreground">
                {'  -H "Authorization: Bearer $API_KEY" \\'}
              </span>
              {'\n'}
              <span className="text-foreground">
                {'  -d \'{"model": "claude-3", "messages": [...]}\''}
              </span>
            </code>
          </pre>
        </div>
      </div>
    </section>
  )
}
