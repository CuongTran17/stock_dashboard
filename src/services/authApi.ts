/**
 * Auth API Service
 * ================
 * Manages JWT authentication, user state, and API calls for auth/payment/portfolio.
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

const TOKEN_KEY = 'stockai_token'
const USER_KEY = 'stockai_user'

export interface UserInfo {
  id: number
  email: string
  phone: string | null
  first_name?: string | null
  last_name?: string | null
  fullname: string
  avatar_data: string | null
  role: 'user' | 'premium' | 'admin'
  created_at?: string
}

export interface AuthResponse {
  message: string
  token: string
  user: UserInfo
}

export interface PaymentInfo {
  bank_name: string
  account_number: string
  account_name: string
  amount: number
  transfer_content: string
  qr_url: string
}

export interface SubscriptionStatus {
  is_premium: boolean
  role: string
  active_subscription: {
    plan: string
    expires_at: string | null
  } | null
}

export interface PortfolioItem {
  id: number
  symbol: string
  quantity: number
  avg_price: number | null
  tp_price: number | null
  sl_price: number | null
  note: string | null
  created_at?: string
  updated_at?: string
}

export interface SalesStats {
  total_revenue: number
  total_subscriptions: number
  active_premium_count: number
  total_users: number
  pending_count: number
  monthly_revenue: { month: string; revenue: number; count: number }[]
}

export interface AdminUserPortfolio {
  user: { id: number; email: string; fullname: string; role: string }
  holdings: {
    symbol: string
    quantity: number
    avg_price: number | null
    tp_price: number | null
    sl_price: number | null
    note: string | null
  }[]
  total_symbols: number
}

// ── Token Management ────────────────────────────────────────────────

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getSavedUser(): UserInfo | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveUser(user: UserInfo): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export function isAdmin(): boolean {
  const user = getSavedUser()
  return user?.role === 'admin'
}

export function isPremium(): boolean {
  const user = getSavedUser()
  return user?.role === 'premium' || user?.role === 'admin'
}

export function logout(): void {
  removeToken()
}

// ── API Fetch Helper ────────────────────────────────────────────────

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BACKEND_URL}${path}`, { ...init, headers })

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }))
    const msg = body.detail || body.error || body.message || `Error ${response.status}`
    throw new Error(msg)
  }

  return response.json() as Promise<T>
}

// ── Auth Endpoints ──────────────────────────────────────────────────

export async function register(
  email: string,
  password: string,
  fullname: string,
  phone?: string,
): Promise<AuthResponse> {
  const data = await authFetch<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, fullname, phone: phone || null }),
  })
  setToken(data.token)
  saveUser(data.user)
  return data
}

export async function login(emailOrPhone: string, password: string): Promise<AuthResponse> {
  const data = await authFetch<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email_or_phone: emailOrPhone, password }),
  })
  setToken(data.token)
  saveUser(data.user)
  return data
}

export async function getMe(): Promise<UserInfo> {
  const user = await authFetch<UserInfo>('/api/auth/me')
  saveUser(user)
  return user
}

export async function updateProfile(
  payload: {
    firstName?: string
    lastName?: string
    fullname?: string
    phone?: string
    avatarData?: string | null
  },
): Promise<AuthResponse> {
  const data = await authFetch<AuthResponse>('/api/auth/profile', {
    method: 'PUT',
    body: JSON.stringify({
      first_name: payload.firstName,
      last_name: payload.lastName,
      fullname: payload.fullname,
      phone: payload.phone,
      avatar_data: payload.avatarData,
    }),
  })
  setToken(data.token)
  saveUser(data.user)
  return data
}

export async function updatePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
  return authFetch('/api/auth/password', {
    method: 'PUT',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
}

// ── Payment Endpoints ───────────────────────────────────────────────

export async function getPremiumPaymentInfo(): Promise<PaymentInfo> {
  return authFetch<PaymentInfo>('/api/payment/premium-info')
}

export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  return authFetch<SubscriptionStatus>('/api/payment/subscription-status')
}

// ── Portfolio Endpoints ─────────────────────────────────────────────

export async function getMyPortfolio(): Promise<{ count: number; items: PortfolioItem[] }> {
  return authFetch('/api/portfolio/')
}

export async function addToPortfolio(
  symbol: string,
  quantity: number = 0,
  avgPrice?: number,
  tpPrice?: number,
  slPrice?: number,
  note?: string,
): Promise<{ message: string; item: PortfolioItem }> {
  return authFetch('/api/portfolio/', {
    method: 'POST',
    body: JSON.stringify({ symbol, quantity, avg_price: avgPrice, tp_price: tpPrice, sl_price: slPrice, note }),
  })
}

export async function updatePortfolioItem(
  symbol: string,
  data: { quantity?: number; avg_price?: number; tp_price?: number; sl_price?: number; note?: string },
): Promise<{ message: string; item: PortfolioItem }> {
  return authFetch(`/api/portfolio/${symbol.toUpperCase()}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function removeFromPortfolio(symbol: string): Promise<{ message: string }> {
  return authFetch(`/api/portfolio/${symbol.toUpperCase()}`, { method: 'DELETE' })
}

// ── Admin Endpoints ─────────────────────────────────────────────────

export async function getAdminSalesStats(): Promise<SalesStats> {
  return authFetch<SalesStats>('/api/admin/sales-stats')
}

export async function getAdminUsers(
  page: number = 1,
  perPage: number = 20,
  role?: string,
): Promise<{ total: number; page: number; per_page: number; users: UserInfo[] }> {
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  if (role) params.set('role', role)
  return authFetch(`/api/admin/users?${params}`)
}

export async function getAdminUserPortfolios(
  page: number = 1,
  perPage: number = 50,
): Promise<{ total: number; portfolios: AdminUserPortfolio[] }> {
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  return authFetch(`/api/admin/user-portfolios?${params}`)
}

export async function updateUserRole(userId: number, role: string): Promise<{ message: string }> {
  return authFetch(`/api/admin/users/${userId}/role?role=${role}`, { method: 'PUT' })
}

export async function lockUser(userId: number, reason: string): Promise<{ message: string }> {
  return authFetch(`/api/admin/users/${userId}/lock?reason=${encodeURIComponent(reason)}`, { method: 'PUT' })
}

export async function unlockUser(userId: number): Promise<{ message: string }> {
  return authFetch(`/api/admin/users/${userId}/unlock`, { method: 'PUT' })
}
