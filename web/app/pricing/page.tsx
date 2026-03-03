import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { Navbar } from "@/components/landing/navbar"
import { Button } from "@/components/ui/button"

const models = [
  { provider: "OpenAI", model: "GPT-4o", input: "$2.50", output: "$10.00", convoyFee: "$0.125" },
  { provider: "OpenAI", model: "GPT-4o mini", input: "$0.15", output: "$0.60", convoyFee: "$0.0075" },
  { provider: "OpenAI", model: "GPT-4.1", input: "$2.00", output: "$8.00", convoyFee: "$0.100" },
  { provider: "OpenAI", model: "GPT-4.1 mini", input: "$0.40", output: "$1.60", convoyFee: "$0.020" },
  { provider: "OpenAI", model: "GPT-4.1 nano", input: "$0.10", output: "$0.40", convoyFee: "$0.005" },
  { provider: "OpenAI", model: "o3", input: "$2.00", output: "$8.00", convoyFee: "$0.100" },
  { provider: "OpenAI", model: "o3 mini", input: "$1.10", output: "$4.40", convoyFee: "$0.055" },
  { provider: "OpenAI", model: "o4 mini", input: "$1.10", output: "$4.40", convoyFee: "$0.055" },
  { provider: "Anthropic", model: "Claude Sonnet 4", input: "$3.00", output: "$15.00", convoyFee: "$0.180" },
  { provider: "Anthropic", model: "Claude Haiku 3.5", input: "$0.80", output: "$4.00", convoyFee: "$0.048" },
  { provider: "Anthropic", model: "Claude Opus 4", input: "$15.00", output: "$75.00", convoyFee: "$0.900" },
  { provider: "Google", model: "Gemini 2.5 Pro", input: "$1.25", output: "$10.00", convoyFee: "$0.113" },
  { provider: "Google", model: "Gemini 2.5 Flash", input: "$0.15", output: "$0.60", convoyFee: "$0.0075" },
  { provider: "Google", model: "Gemini 2.0 Flash", input: "$0.10", output: "$0.40", convoyFee: "$0.005" },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 pb-24 pt-32">
        {/* Hero */}
        <div className="text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5">
            <span className="text-xs font-medium text-muted-foreground">Simple, transparent pricing</span>
          </div>
          <h1 className="text-balance text-5xl font-bold tracking-tight text-foreground md:text-7xl">
            Just <span className="text-primary">1%</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-muted-foreground">
            We charge 1% on top of the model provider{"'"}s batch processing price.
            No subscriptions, no platform fees, no hidden costs. You only pay for what you use.
          </p>
        </div>

        {/* How it works */}
        <div className="mx-auto mt-16 grid max-w-3xl gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-border bg-card p-6 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
              1
            </div>
            <h3 className="text-sm font-semibold text-foreground">Provider charges you</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Standard batch API pricing from OpenAI, Anthropic, Google, etc.
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-6 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
              2
            </div>
            <h3 className="text-sm font-semibold text-foreground">Convoy adds 1%</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              A flat 1% fee on the batch processing cost. That{"'"}s it.
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-6 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
              3
            </div>
            <h3 className="text-sm font-semibold text-foreground">You save up to 50%</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Batch processing is already up to 50% cheaper than real-time API calls.
            </p>
          </div>
        </div>

        {/* Model pricing table */}
        <div className="mt-20">
          <h2 className="text-center text-2xl font-semibold tracking-tight text-foreground">
            Batch processing prices per model
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-center text-sm text-muted-foreground">
            Prices shown per 1M tokens. Convoy fee is calculated as 1% of the combined input + output cost.
          </p>

          <div className="mt-8 overflow-hidden rounded-xl border border-border">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border bg-card">
                    <th className="px-6 py-3.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Provider</th>
                    <th className="px-6 py-3.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Model</th>
                    <th className="px-6 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Input / 1M</th>
                    <th className="px-6 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Output / 1M</th>
                    <th className="px-6 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-primary">Convoy Fee / 1M</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m, i) => (
                    <tr
                      key={`${m.provider}-${m.model}`}
                      className={`border-b border-border last:border-0 ${i % 2 === 0 ? "bg-background" : "bg-card/50"}`}
                    >
                      <td className="px-6 py-3 text-muted-foreground">{m.provider}</td>
                      <td className="px-6 py-3 font-medium text-foreground">{m.model}</td>
                      <td className="px-6 py-3 text-right font-mono text-muted-foreground">{m.input}</td>
                      <td className="px-6 py-3 text-right font-mono text-muted-foreground">{m.output}</td>
                      <td className="px-6 py-3 text-right font-mono font-semibold text-primary">{m.convoyFee}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            Prices reflect batch API rates from each provider. Convoy fee = 1% of (input + output cost).
          </p>
        </div>

        {/* CTA */}
        <div className="mt-20 text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            Ready to start saving?
          </h2>
          <p className="mt-2 text-muted-foreground">
            Get started in minutes. No credit card required.
          </p>
          <Button asChild size="lg" className="mt-6 rounded-full px-8">
            <Link href="/dashboard" className="flex items-center gap-2">
              Try Convoy
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </main>
    </div>
  )
}
