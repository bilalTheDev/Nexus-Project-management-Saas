import nexusMark from '@/assets/nexus-mark.png'

export function NexusLogo({
  className = '',
  markClassName = 'size-7',
  wordmarkClassName = 'text-xl tracking-tight text-ink',
  showWordmark = true,
}) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <img
        src={nexusMark}
        alt=""
        width={28}
        height={28}
        className={`shrink-0 rounded-lg ${markClassName}`}
        decoding="async"
      />
      {showWordmark ? (
        <span className={`font-display ${wordmarkClassName}`}>Nexus</span>
      ) : null}
    </span>
  )
}
