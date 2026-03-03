import { Send, Layers, Box, Bell } from "lucide-react"

const steps = [
  {
    icon: Send,
    label: "Your App",
    sublabel: "POST /cargo/load",
  },
  {
    icon: Layers,
    label: "Queue Staging",
    sublabel: "Intelligent grouping",
  },
  {
    icon: Box,
    label: "Batch (100)",
    sublabel: "Optimized delivery",
  },
  {
    icon: Bell,
    label: "Callback",
    sublabel: "Results delivered",
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-3xl font-semibold tracking-tight text-primary md:text-4xl">
            The Journey: Request to Response
          </h2>
          <p className="mt-4 text-muted-foreground">
            From loading dock to delivery — your cargo is in good hands.
          </p>
        </div>

        <div className="mt-16 flex flex-col items-center gap-8 md:flex-row md:justify-center md:gap-0">
          {steps.map((step, i) => (
            <div key={step.label} className="flex items-center">
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-primary bg-card">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <div className="text-center">
                  <p className="font-medium text-foreground">{step.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {step.sublabel}
                  </p>
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className="mx-6 hidden h-0.5 w-16 bg-primary/30 md:block lg:w-24" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
