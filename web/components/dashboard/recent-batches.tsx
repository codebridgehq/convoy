import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { StatusBadge } from "@/components/dashboard/status-badge"
import { recentBatches } from "@/lib/mock-data"

export function RecentBatches() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium text-foreground">
          Recent Batches
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-muted-foreground">Batch ID</TableHead>
              <TableHead className="text-muted-foreground">Status</TableHead>
              <TableHead className="text-muted-foreground">Requests</TableHead>
              <TableHead className="text-muted-foreground">Created</TableHead>
              <TableHead className="text-right text-muted-foreground">Cost</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recentBatches.map((batch) => (
              <TableRow key={batch.id} className="border-border">
                <TableCell className="font-mono text-sm text-foreground">
                  {batch.id}
                </TableCell>
                <TableCell>
                  <StatusBadge status={batch.status} />
                </TableCell>
                <TableCell className="text-foreground">
                  {batch.requestsCount}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {batch.createdAt}
                </TableCell>
                <TableCell className="text-right font-mono text-foreground">
                  {batch.cost > 0 ? `$${batch.cost.toFixed(2)}` : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
