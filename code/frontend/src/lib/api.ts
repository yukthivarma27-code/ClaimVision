const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchJSON(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json()
}

export interface Claim {
  user_id: string
  image_paths: string
  user_claim: string
  claim_object: string
  image_list?: string[]
}

export interface UserHistory {
  user_id: string
  past_claim_count: number
  accept_claim: number
  manual_review_claim: number
  rejected_claim: number
  last_90_days_claim_count: number
  history_flags: string
  history_summary: string
}

export interface DashboardStats {
  total_claims: number
  unique_users: number
  objects: Record<string, number>
  users_with_risk: number
  high_risk_users: number
}

export interface Prediction {
  user_id: string
  image_paths: string
  user_claim: string
  claim_object: string
  evidence_standard_met: string
  evidence_standard_met_reason: string
  risk_flags: string
  issue_type: string
  object_part: string
  claim_status: string
  claim_status_justification: string
  supporting_image_ids: string
  valid_image: string
  severity: string
}

export async function getDashboard(): Promise<DashboardStats> {
  return fetchJSON('/api/dashboard')
}

export async function getClaims(): Promise<Claim[]> {
  return fetchJSON('/api/claims')
}

export async function getUsers(): Promise<UserHistory[]> {
  return fetchJSON('/api/users')
}

export async function getUser(userId: string): Promise<UserHistory> {
  return fetchJSON(`/api/users/${userId}`)
}

export async function getPredictions(): Promise<Prediction[]> {
  return fetchJSON('/api/output')
}
