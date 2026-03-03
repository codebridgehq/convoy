// Mock data for the Convoy dashboard

export const overviewStats = {
  totalRequests: 12847,
  totalCost: 342.56,
  avgBatchSize: 87,
  successRate: 99.2,
}

export const requestsOverTime = [
  { date: "Jan 1", requests: 420 },
  { date: "Jan 5", requests: 580 },
  { date: "Jan 10", requests: 720 },
  { date: "Jan 15", requests: 640 },
  { date: "Jan 20", requests: 890 },
  { date: "Jan 25", requests: 1100 },
  { date: "Feb 1", requests: 980 },
  { date: "Feb 5", requests: 1250 },
  { date: "Feb 10", requests: 1430 },
]

export type BatchStatus = "completed" | "processing" | "pending" | "failed"

export interface Batch {
  id: string
  status: BatchStatus
  requestsCount: number
  createdAt: string
  cost: number
}

export const recentBatches: Batch[] = [
  { id: "BATCH-001", status: "completed", requestsCount: 100, createdAt: "2026-02-10 14:32", cost: 4.21 },
  { id: "BATCH-002", status: "completed", requestsCount: 100, createdAt: "2026-02-10 14:18", cost: 3.87 },
  { id: "BATCH-003", status: "processing", requestsCount: 67, createdAt: "2026-02-10 14:05", cost: 2.54 },
  { id: "BATCH-004", status: "completed", requestsCount: 100, createdAt: "2026-02-10 13:48", cost: 4.12 },
  { id: "BATCH-005", status: "pending", requestsCount: 23, createdAt: "2026-02-10 13:30", cost: 0.0 },
  { id: "BATCH-006", status: "completed", requestsCount: 100, createdAt: "2026-02-10 12:55", cost: 3.96 },
  { id: "BATCH-007", status: "failed", requestsCount: 45, createdAt: "2026-02-10 12:12", cost: 0.0 },
]

export type CargoStatus = "delivered" | "in-transit" | "queued" | "failed"

export interface CargoRequest {
  id: string
  status: CargoStatus
  model: string
  created: string
  deliveryTime: string
}

export const cargoRequests: CargoRequest[] = [
  { id: "CRG-8847", status: "delivered", model: "claude-3-sonnet", created: "2026-02-10 14:32", deliveryTime: "2.3s" },
  { id: "CRG-8846", status: "delivered", model: "claude-3-haiku", created: "2026-02-10 14:31", deliveryTime: "1.1s" },
  { id: "CRG-8845", status: "in-transit", model: "claude-3-sonnet", created: "2026-02-10 14:30", deliveryTime: "—" },
  { id: "CRG-8844", status: "delivered", model: "gpt-4o", created: "2026-02-10 14:28", deliveryTime: "3.7s" },
  { id: "CRG-8843", status: "queued", model: "claude-3-opus", created: "2026-02-10 14:27", deliveryTime: "—" },
  { id: "CRG-8842", status: "delivered", model: "claude-3-haiku", created: "2026-02-10 14:25", deliveryTime: "0.8s" },
  { id: "CRG-8841", status: "failed", model: "gpt-4o", created: "2026-02-10 14:22", deliveryTime: "—" },
  { id: "CRG-8840", status: "delivered", model: "claude-3-sonnet", created: "2026-02-10 14:20", deliveryTime: "2.1s" },
  { id: "CRG-8839", status: "in-transit", model: "claude-3-haiku", created: "2026-02-10 14:18", deliveryTime: "—" },
  { id: "CRG-8838", status: "delivered", model: "claude-3-sonnet", created: "2026-02-10 14:15", deliveryTime: "2.5s" },
]

export interface Project {
  id: string
  name: string
  requestCount: number
  totalSpend: number
  lastActive: string
}

export const projects: Project[] = [
  { id: "proj-1", name: "Email Summarizer", requestCount: 4520, totalSpend: 124.30, lastActive: "2 hours ago" },
  { id: "proj-2", name: "Support Bot v3", requestCount: 3210, totalSpend: 89.45, lastActive: "5 minutes ago" },
  { id: "proj-3", name: "Content Pipeline", requestCount: 2890, totalSpend: 76.20, lastActive: "1 day ago" },
  { id: "proj-4", name: "Data Classifier", requestCount: 1540, totalSpend: 42.80, lastActive: "3 hours ago" },
  { id: "proj-5", name: "Translation Service", requestCount: 687, totalSpend: 19.81, lastActive: "12 hours ago" },
]

export interface ApiKey {
  id: string
  name: string
  prefix: string
  created: string
  lastUsed: string
}

export const apiKeys: ApiKey[] = [
  { id: "key-1", name: "Production Key", prefix: "ck_prod_abc12...", created: "2026-01-15", lastUsed: "2 minutes ago" },
  { id: "key-2", name: "Staging Key", prefix: "ck_stag_def34...", created: "2026-01-20", lastUsed: "3 hours ago" },
  { id: "key-3", name: "Development Key", prefix: "ck_dev_ghi56...", created: "2026-02-01", lastUsed: "1 day ago" },
]

export const expenseBreakdown = [
  { date: "Jan 1", cost: 18.40 },
  { date: "Jan 8", cost: 24.60 },
  { date: "Jan 15", cost: 31.20 },
  { date: "Jan 22", cost: 28.90 },
  { date: "Jan 29", cost: 42.10 },
  { date: "Feb 1", cost: 38.70 },
  { date: "Feb 5", cost: 45.30 },
  { date: "Feb 10", cost: 52.80 },
]

export const expenseByModel = [
  { model: "claude-3-sonnet", cost: 156.30, requests: 5420 },
  { model: "claude-3-haiku", cost: 42.10, requests: 4210 },
  { model: "gpt-4o", cost: 98.40, requests: 2180 },
  { model: "claude-3-opus", cost: 45.76, requests: 1037 },
]
