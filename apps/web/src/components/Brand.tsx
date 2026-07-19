import { Link } from 'react-router-dom'

interface BrandProps {
  compact?: boolean
  inverse?: boolean
}

export function Brand({ compact = false, inverse = false }: BrandProps) {
  return (
    <Link className="inline-flex items-center gap-3" to="/">
      <img alt="Quant Web3 Research" className="size-10 rounded-xl" src="/logo-primary.png" />
      {!compact && (
        <span className={inverse ? 'text-white' : 'text-ink'}>
          <strong className="block text-sm leading-4 tracking-[-0.02em]">Quant Web3</strong>
          <span className={`text-[11px] ${inverse ? 'text-white/60' : 'text-muted'}`}>Research system</span>
        </span>
      )}
    </Link>
  )
}
