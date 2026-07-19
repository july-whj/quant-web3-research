import { useQuery } from '@tanstack/react-query'

import { ApiError } from '../../lib/api'
import { getCurrentUser } from './api'

export const sessionQueryKey = ['auth', 'session'] as const

export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: getCurrentUser,
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status === 401) && failureCount < 1,
  })
}
