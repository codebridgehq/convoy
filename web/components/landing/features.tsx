import { DollarSign, Zap, Package, RefreshCw } from "lucide-react"

const features = [
  {
    icon: DollarSign,
    title: "Cost Savings",
    description:
      "Take advantage of batch pricing without infrastructure complexity. Reduce your AI spend by 50% or more.",
  },
  {
    icon: Zap,
    title: "Zero Batching Logic",
    description:
      "No queues to manage, no timing windows to configure — just send requests and we handle the rest.",
  },
  {
    icon: Package,
    title: "No Minimum Volume",
    description:
      "Start with one request or send thousands. Convoy scales seamlessly with your workload.",
  },
  {
    icon: RefreshCw,
    title: "Built-in Reliability",
    description:
      "Automatic retry logic and error handling. Your cargo always arrives at its destination.",
  },
]

export function Features() {
  return (
    <section id="features" className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-3xl font-semibold tracking-tight text-primary md:text-4xl">
            Why Choose Convoy
          </h2>
          <p className="mt-4 text-muted-foreground">
            Infrastructure that gets out of your way so you can focus on building.
          </p>
        </div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/40"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <feature.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-foreground">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
