import { createConfig, http } from 'wagmi'
import { bsc, bscTestnet } from 'wagmi/chains'
import { injected } from 'wagmi/connectors'

const connectors = [injected()]

export const wagmiConfig = createConfig({
  chains: [bsc, bscTestnet],
  connectors,
  transports: {
    [bsc.id]: http(),
    [bscTestnet.id]: http(),
  },
})

declare module 'wagmi' {
  interface Register {
    config: typeof wagmiConfig
  }
}
