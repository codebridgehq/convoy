"use client"

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { requestsOverTime } from "@/lib/mock-data"

export function RequestsChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium text-foreground">
          Requests Over Time
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={requestsOverTime}>
              <defs>
                <linearGradient id="requestsFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(340 100% 71%)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="hsl(340 100% 71%)" stopOpacity={0} />
                </linearGradient>
              </defs>
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
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(261 51% 12%)",
                  border: "1px solid hsl(264 40% 28%)",
                  borderRadius: "8px",
                  color: "#fff",
                  fontSize: 13,
                }}
              />
              <Area
                type="monotone"
                dataKey="requests"
                stroke="hsl(340 100% 71%)"
                strokeWidth={2}
                fill="url(#requestsFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
