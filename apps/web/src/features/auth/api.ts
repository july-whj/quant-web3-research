import { apiRequest } from '../../lib/api'
import type { AuthChallenge, CurrentUser } from '../../types'

export function getCurrentUser() {
  return apiRequest<CurrentUser>('/auth/me')
}

export function createAuthChallenge(address: `0x${string}`, chainId: number) {
  return apiRequest<AuthChallenge>('/auth/nonce', {
    method: 'POST',
    body: JSON.stringify({ address, chain_id: chainId }),
  })
}

export function verifyWalletSignature(
  address: `0x${string}`,
  message: string,
  signature: `0x${string}`,
) {
  return apiRequest<CurrentUser>('/auth/verify', {
    method: 'POST',
    body: JSON.stringify({ address, message, signature }),
  })
}

export function logout() {
  return apiRequest<void>('/auth/logout', { method: 'POST' })
}
