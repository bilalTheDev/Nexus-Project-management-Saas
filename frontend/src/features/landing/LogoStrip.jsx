const LOGOS = [
  'KINETIX',
  'AETHER',
  'MONOLITH',
  'VELOCE',
  'SYNTHETIX',
  'ORBITAL',
  'HYPERPLANE',
  'BASEFORM',
]

export function LogoStrip() {
  return (
    <section
      className="border-y border-[var(--border)] bg-[var(--surface-logo)] px-10 py-16"
      aria-label="Customers"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col gap-8 px-8">
        <p className="text-center font-mono text-xs uppercase tracking-[0.1em] text-[var(--text-muted)]">
          Built for teams that ship
        </p>
        <ul className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 opacity-60 sm:justify-between sm:gap-x-6">
          {LOGOS.map((name) => (
            <li
              key={name}
              className="font-mono text-[15px] font-semibold tracking-[0.05em] text-[var(--text)]"
            >
              {name}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
