import { StatCards } from "@/components/dashboard/stat-cards"
import { RequestsChart } from "@/components/dashboard/requests-chart"
import { RecentBatches } from "@/components/dashboard/recent-batches"

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Overview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Monitor your batch processing activity and costs.
        </p>
      </div>
      <StatCards />
      <RequestsChart />
      <RecentBatches />
    </div>
  )
}
