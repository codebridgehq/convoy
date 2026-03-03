import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"

export function CtaFooter() {
  return (
    <section className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight text-primary md:text-5xl">
          All Aboard?
        </h2>
        <p className="mx-auto mt-6 max-w-xl text-pretty text-lg leading-relaxed text-muted-foreground">
          Ready to simplify your batch processing and start saving on AI costs?
          Get started in minutes.
        </p>
        <div className="mt-10">
          <Button asChild size="lg" className="rounded-full px-10 text-base">
            <Link href="/dashboard">
              Try Convoy
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      <footer className="mx-auto mt-24 max-w-7xl border-t border-border pt-8">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <span className="text-lg font-semibold text-primary">convoy</span>
          <p className="text-sm text-muted-foreground">
            {'\u00A9'} 2026 Convoy. All rights reserved.
          </p>
        </div>
      </footer>
    </section>
  )
}
