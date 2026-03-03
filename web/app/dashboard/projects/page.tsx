import { Plus, Package, DollarSign, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { projects } from "@/lib/mock-data"

export default function ProjectsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Projects</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Organize your cargo by project.
          </p>
        </div>
        <Button className="rounded-lg">
          <Plus className="mr-2 h-4 w-4" />
          Create Project
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((project) => (
          <Card
            key={project.id}
            className="cursor-pointer transition-colors hover:border-primary/40"
          >
            <CardContent className="p-6">
              <h3 className="text-lg font-medium text-foreground">
                {project.name}
              </h3>
              <div className="mt-4 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Package className="h-3.5 w-3.5" />
                  <span>{project.requestCount.toLocaleString()} requests</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <DollarSign className="h-3.5 w-3.5" />
                  <span>${project.totalSpend.toFixed(2)} spent</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" />
                  <span>Active {project.lastActive}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
