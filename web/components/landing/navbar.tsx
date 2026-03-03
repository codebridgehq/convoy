"use client"

import Link from "next/link"
import { useState } from "react"
import { Menu, X, Star } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="fixed top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-semibold text-primary">
          convoy
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <Link
            href="/docs"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Docs
          </Link>
          <Link
            href="/pricing"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Pricing
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Sign In
          </Link>
          <Button asChild size="sm" className="rounded-full px-5">
            <Link href="/dashboard">Try Convoy</Link>
          </Button>
          <Button asChild variant="outline" size="sm" className="rounded-full px-5 bg-transparent">
            <Link
              href="https://github.com/frain-dev/convoy"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5"
            >
              <Star className="h-3.5 w-3.5" />
              GitHub
            </Link>
          </Button>
        </div>

        <button
          type="button"
          className="text-foreground md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {mobileOpen && (
        <div className="border-t border-border/50 bg-background px-6 pb-6 pt-4 md:hidden">
          <div className="flex flex-col gap-4">
            <Link
              href="/docs"
              className="text-sm text-muted-foreground"
              onClick={() => setMobileOpen(false)}
            >
              Docs
            </Link>
            <Link
              href="/pricing"
              className="text-sm text-muted-foreground"
              onClick={() => setMobileOpen(false)}
            >
              Pricing
            </Link>
            <Link
              href="/dashboard"
              className="text-sm text-muted-foreground"
              onClick={() => setMobileOpen(false)}
            >
              Sign In
            </Link>
            <Button asChild size="sm" className="w-full rounded-full">
              <Link href="/dashboard">Try Convoy</Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="w-full rounded-full bg-transparent">
              <Link
                href="https://github.com/frain-dev/convoy"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1.5"
                onClick={() => setMobileOpen(false)}
              >
                <Star className="h-3.5 w-3.5" />
                GitHub
              </Link>
            </Button>
          </div>
        </div>
      )}
    </header>
  )
}
