"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { expenseBreakdown, expenseByModel } from "@/lib/mock-data"

const PIE_COLORS = [
  "hsl(340 100% 71%)",
  "hsl(339 100% 65%)",
  "hsl(331 100% 86%)",
  "hsl(265 36% 74%)",
]

const totalSpend = expenseByModel.reduce((sum, item) => sum + item.cost, 0)

export default function ExpensesPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Expenses</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Track your spending and optimize costs.
        </p>
      </div>

      {/* Total Spend Card */}
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-10">
          <p className="text-sm font-medium text-muted-foreground">
            Total Spend This Period
          </p>
          <p className="mt-2 text-5xl font-semibold text-primary">
            ${totalSpend.toFixed(2)}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Across {expenseByModel.reduce((sum, m) => sum + m.requests, 0).toLocaleString()} requests
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cost Over Time */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium text-foreground">
              Cost Over Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={expenseBreakdown}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="hsl(264 40% 28%)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "hsl(265 36% 74%)", fontSize: 12 }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "hsl(265 36% 74%)", fontSize: 12 }}
                    tickFormatter={(v) => `$${v}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(261 51% 12%)",
                      border: "1px solid hsl(264 40% 28%)",
                      borderRadius: "8px",
                      color: "#fff",
                      fontSize: 13,
                    }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, "Cost"]}
                  />
                  <Bar
                    dataKey="cost"
                    fill="hsl(340 100% 71%)"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Breakdown by Model */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-medium text-foreground">
              Cost by Model
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={expenseByModel}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="cost"
                    nameKey="model"
                    strokeWidth={0}
                  >
                    {expenseByModel.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PIE_COLORS[index % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(261 51% 12%)",
                      border: "1px solid hsl(264 40% 28%)",
                      borderRadius: "8px",
                      color: "#fff",
                      fontSize: 13,
                    }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, "Cost"]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Cost Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium text-foreground">
            Cost Breakdown by Model
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-muted-foreground">Model</TableHead>
                <TableHead className="text-muted-foreground">Requests</TableHead>
                <TableHead className="text-right text-muted-foreground">Cost</TableHead>
                <TableHead className="text-right text-muted-foreground">Avg Cost / Req</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {expenseByModel.map((item) => (
                <TableRow key={item.model} className="border-border">
                  <TableCell className="font-mono text-sm text-foreground">
                    {item.model}
                  </TableCell>
                  <TableCell className="text-foreground">
                    {item.requests.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-foreground">
                    ${item.cost.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-muted-foreground">
                    ${(item.cost / item.requests).toFixed(4)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
