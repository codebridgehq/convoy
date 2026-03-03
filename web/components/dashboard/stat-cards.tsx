import { Package, DollarSign, Layers, CheckCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { overviewStats } from "@/lib/mock-data"

const stats = [
  {
    title: "Total Requests",
    value: overviewStats.totalRequests.toLocaleString(),
    description: "This month",
    icon: Package,
  },
  {
    title: "Total Cost",
    value: `$${overviewStats.totalCost.toFixed(2)}`,
    description: "This month",
    icon: DollarSign,
  },
  {
    title: "Avg Batch Size",
    value: overviewStats.avgBatchSize.toString(),
    description: "Requests per batch",
    icon: Layers,
  },
  {
    title: "Success Rate",
    value: `${overviewStats.successRate}%`,
    description: "All time",
    icon: CheckCircle,
  },
]

export function StatCards() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold text-primary">
              {stat.value}
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {stat.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
