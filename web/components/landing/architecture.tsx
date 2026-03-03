import { Globe, Brain, Workflow, Cloud, Truck } from "lucide-react"

const sections = [
  {
    number: "01",
    icon: Globe,
    title: "REST API Gateway",
    description:
      "A simple, well-documented API. Load cargo with a single POST request and receive a tracking ID instantly.",
  },
  {
    number: "02",
    icon: Brain,
    title: "Intelligent Queue System",
    description:
      "Requests are automatically grouped and optimized. No configuration needed — Convoy finds the best batch window.",
  },
  {
    number: "03",
    icon: Workflow,
    title: "Temporal Workflows",
    description:
      "Durable, fault-tolerant execution powered by Temporal. Every request is tracked, retried, and guaranteed to complete.",
  },
  {
    number: "04",
    icon: Cloud,
    title: "AWS Bedrock Integration",
    description:
      "Native integration with AWS Bedrock batch APIs. Access the latest models with optimized pricing.",
  },
  {
    number: "05",
    icon: Truck,
    title: "Callback Delivery System",
    description:
      "Results are delivered to your webhook as they complete. Real-time updates, zero polling required.",
  },
]

export function Architecture() {
  return (
    <section id="architecture" className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-3xl font-semibold tracking-tight text-primary md:text-4xl">
            Under the Hood
          </h2>
          <p className="mt-4 text-muted-foreground">
            Built on battle-tested infrastructure for reliability at any scale.
          </p>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sections.map((section) => (
            <div
              key={section.number}
              className="group rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/40"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs text-primary/60">
                  {section.number}
                </span>
                <section.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-foreground">
                {section.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {section.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
