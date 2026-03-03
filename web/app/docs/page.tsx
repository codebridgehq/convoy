import Link from "next/link"
import { ArrowLeft, BookOpen } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function DocsPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-muted">
        <BookOpen className="h-8 w-8 text-muted-foreground" />
      </div>
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          Documentation
        </h1>
        <p className="mt-2 text-muted-foreground">
          Convoy docs are coming soon. Stay tuned.
        </p>
      </div>
      <Button asChild variant="outline" size="sm" className="rounded-full px-5 bg-transparent">
        <Link href="/" className="flex items-center gap-2">
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Home
        </Link>
      </Button>
    </div>
  )
}
