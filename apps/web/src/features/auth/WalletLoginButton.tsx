import { useQueryClient } from '@tanstack/react-query'
import { Check, LoaderCircle, LogOut, ShieldCheck, Wallet, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import {
  useConnect,
  useConnection,
  useConnectors,
  useDisconnect,
  useSignMessage,
} from 'wagmi'

import { shortenAddress } from '../../lib/format'
import { createAuthChallenge, logout, verifyWalletSignature } from './api'
import { sessionQueryKey, useSession } from './useSession'

interface WalletLoginButtonProps {
  compact?: boolean
}

function readableError(error: unknown) {
  if (!(error instanceof Error)) return '钱包登录失败，请稍后重试。'
  if (error.message.toLowerCase().includes('rejected')) return '你取消了钱包操作。'
  return error.message
}

export function WalletLoginButton({ compact = false }: WalletLoginButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [step, setStep] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
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
      setStep('正在生成一次性登录消息')
      const challenge = await createAuthChallenge(address, chainId)
      setStep('请在钱包中签名')
      const signature = await signMessage.mutateAsync({ message: challenge.message })
      setStep('正在验证签名')
      await verifyWalletSignature(address, challenge.message, signature)
      await queryClient.invalidateQueries({ queryKey: sessionQueryKey })
      setIsOpen(false)
    } catch (error) {
      setErrorMessage(readableError(error))
    } finally {
      setStep('')
    }
  }

  async function connectAndAuthenticate(connector: (typeof availableConnectors)[number]) {
    setErrorMessage('')
    try {
      setStep('正在连接钱包')
      const result = await connect.mutateAsync({ connector })
      await authenticate(result.accounts[0], result.chainId)
    } catch (error) {
      setErrorMessage(readableError(error))
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
        className={session.data ? 'button-outline' : 'button-primary'}
        onClick={handlePrimaryClick}
        disabled={isBusy}
        type="button"
      >
        {isBusy ? <LoaderCircle className="animate-spin" size={17} /> : session.data ? <LogOut size={17} /> : <Wallet size={17} />}
        {session.data
          ? compact ? '退出' : shortenAddress(session.data.address)
          : compact ? '登录' : '连接钱包登录'}
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
                <p className="eyebrow">Wallet access</p>
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.03em]" id="wallet-dialog-title">
                  用钱包证明“这是你”
                </h2>
              </div>
              <button
                aria-label="关闭"
                className="grid size-10 place-items-center rounded-xl border border-line text-muted hover:bg-[#f6f5fb]"
                onClick={() => setIsOpen(false)}
                type="button"
              >
                <X size={18} />
              </button>
            </div>

            <p className="mt-3 text-sm leading-6 text-muted">
              登录只需要签署一次性文本消息，不会发起链上交易，也不会要求授权资产。
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
                  <span className="text-xs text-muted">BSC / EVM</span>
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
              <span className="flex items-center gap-2"><Check size={14} className="text-success" />不读取私钥</span>
              <span className="flex items-center gap-2"><ShieldCheck size={14} className="text-success" />会话可随时退出</span>
            </div>
          </section>
        </div>
      )}
    </>
  )
}
