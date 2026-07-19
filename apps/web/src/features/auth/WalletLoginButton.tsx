import { useQueryClient } from '@tanstack/react-query'
import type { TFunction } from 'i18next'
import { Check, LoaderCircle, LogOut, ShieldCheck, Wallet, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  useConnect,
  useConnection,
  useConnectors,
  useDisconnect,
  useSignMessage,
} from 'wagmi'

import { shortenAddress } from '../../lib/format'
import { ApiError } from '../../lib/api'
import { createAuthChallenge, logout, verifyWalletSignature } from './api'
import { sessionQueryKey, useSession } from './useSession'

interface WalletLoginButtonProps {
  compact?: boolean
}

function readableError(error: unknown, t: TFunction) {
  if (!(error instanceof Error)) return t('wallet.errorGeneric')
  if (error.message.toLowerCase().includes('rejected')) return t('wallet.errorRejected')
  if (error instanceof ApiError) return t('wallet.errorServer')
  return error.message
}

export function WalletLoginButton({ compact = false }: WalletLoginButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [step, setStep] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const { t } = useTranslation()
  const connection = useConnection()
  const connectors = useConnectors()
  const connect = useConnect()
  const disconnect = useDisconnect()
  const signMessage = useSignMessage()
  const session = useSession()
  const queryClient = useQueryClient()

  const isBusy = connect.isPending || signMessage.isPending || Boolean(step)
  const availableConnectors = useMemo(
    () => connectors.filter((connector, index, list) =>
      list.findIndex((candidate) => candidate.id === connector.id) === index,
    ),
    [connectors],
  )

  async function authenticate(address: `0x${string}`, chainId: number) {
    setErrorMessage('')
    try {
      setStep(t('wallet.stepChallenge'))
      const challenge = await createAuthChallenge(address, chainId)
      setStep(t('wallet.stepSign'))
      const signature = await signMessage.mutateAsync({ message: challenge.message })
      setStep(t('wallet.stepVerify'))
      await verifyWalletSignature(address, challenge.message, signature)
      await queryClient.invalidateQueries({ queryKey: sessionQueryKey })
      setIsOpen(false)
    } catch (error) {
      setErrorMessage(readableError(error, t))
    } finally {
      setStep('')
    }
  }

  async function connectAndAuthenticate(connector: (typeof availableConnectors)[number]) {
    setErrorMessage('')
    try {
      setStep(t('wallet.stepConnect'))
      const result = await connect.mutateAsync({ connector })
      await authenticate(result.accounts[0], result.chainId)
    } catch (error) {
      setErrorMessage(readableError(error, t))
      setStep('')
    }
  }

  async function handlePrimaryClick() {
    if (session.data) {
      await logout()
      queryClient.setQueryData(sessionQueryKey, null)
      disconnect.mutate()
      return
    }
    if (connection.status === 'connected') {
      await authenticate(connection.address, connection.chainId)
      return
    }
    setIsOpen(true)
  }

  return (
    <>
      <button
        className={`${session.data ? 'button-outline' : 'button-primary'} whitespace-nowrap`}
        onClick={handlePrimaryClick}
        disabled={isBusy}
        type="button"
      >
        {isBusy ? <LoaderCircle className="animate-spin" size={17} /> : session.data ? <LogOut size={17} /> : <Wallet size={17} />}
        {session.data
          ? compact ? t('wallet.logout') : shortenAddress(session.data.address)
          : compact ? t('wallet.login') : t('wallet.connect')}
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/35 p-5 backdrop-blur-[3px]">
          <section
            aria-labelledby="wallet-dialog-title"
            aria-modal="true"
            className="research-card w-full max-w-md p-6"
            role="dialog"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="eyebrow">{t('wallet.access')}</p>
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]" id="wallet-dialog-title">
                  {t('wallet.title')}
                </h2>
              </div>
              <button
                aria-label={t('common.close')}
                className="grid size-10 place-items-center rounded-xl border border-line text-muted hover:bg-[#f6f5fb]"
                onClick={() => setIsOpen(false)}
                type="button"
              >
                <X size={18} />
              </button>
            </div>

            <p className="mt-3 text-sm leading-6 text-muted">
              {t('wallet.description')}
            </p>

            <div className="mt-6 grid gap-3">
              {availableConnectors.map((connector) => (
                <button
                  className="flex min-h-14 items-center justify-between rounded-xl border border-line px-4 text-left font-semibold transition hover:border-brand hover:bg-[rgba(113,50,245,0.04)]"
                  disabled={isBusy}
                  key={connector.uid}
                  onClick={() => connectAndAuthenticate(connector)}
                  type="button"
                >
                  <span className="flex items-center gap-3">
                    <span className="grid size-9 place-items-center rounded-lg bg-[rgba(113,50,245,0.10)] text-brand">
                      <Wallet size={18} />
                    </span>
                    {connector.name}
                  </span>
                  <span className="text-xs text-muted">{t('wallet.network')}</span>
                </button>
              ))}
            </div>

            {step && (
              <div className="mt-4 flex items-center gap-2 rounded-xl bg-[rgba(113,50,245,0.08)] px-4 py-3 text-sm text-brand-deep">
                <LoaderCircle className="animate-spin" size={16} />
                {step}
              </div>
            )}
            {errorMessage && (
              <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {errorMessage}
              </p>
            )}

            <div className="mt-6 grid grid-cols-2 gap-3 border-t border-line pt-5 text-xs text-muted">
              <span className="flex items-center gap-2"><Check size={14} className="text-success" />{t('wallet.noPrivateKey')}</span>
              <span className="flex items-center gap-2"><ShieldCheck size={14} className="text-success" />{t('wallet.exitAnytime')}</span>
            </div>
          </section>
        </div>
      )}
    </>
  )
}
