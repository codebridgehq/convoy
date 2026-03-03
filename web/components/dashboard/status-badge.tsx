import { cn } from "@/lib/utils"

type StatusType = "completed" | "delivered" | "processing" | "in-transit" | "pending" | "queued" | "failed"

const statusConfig: Record<StatusType, { label: string; className: string }> = {
  completed: {
    label: "Completed",
    className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  },
  delivered: {
    label: "Delivered",
    className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  },
  processing: {
    label: "Processing",
    className: "bg-primary/15 text-primary border-primary/20",
  },
  "in-transit": {
    label: "In Transit",
    className: "bg-primary/15 text-primary border-primary/20",
  },
  pending: {
    label: "Pending",
    className: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  },
  queued: {
    label: "Queued",
    className: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  },
  failed: {
    label: "Failed",
    className: "bg-destructive/15 text-red-400 border-destructive/20",
  },
}

export function StatusBadge({ status }: { status: StatusType }) {
  const config = statusConfig[status]
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        config.className
      )}
    >
      {config.label}
    </span>
  )
}
