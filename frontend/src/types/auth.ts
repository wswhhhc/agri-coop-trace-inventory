export type UserRole =
  | 'SYSTEM_ADMIN'
  | 'COOPERATIVE_ADMIN'
  | 'WAREHOUSE_STAFF'
  | string

export type UserStatus = 'ACTIVE' | 'LOCKED' | 'INACTIVE'

export interface AuthUser {
  id: string
  username: string
  displayName: string
  role: UserRole
  cooperativeId: string | null
  status: UserStatus | string
}

export interface CurrentUser extends AuthUser {
  warehouseIds: string[] | null
  permissions: string[]
}

export interface AuthTokenData {
  accessToken: string
  tokenType: string
  expiresIn: number
  user: AuthUser
  permissions: string[]
}

export interface LoginRequest {
  username: string
  password: string
}
