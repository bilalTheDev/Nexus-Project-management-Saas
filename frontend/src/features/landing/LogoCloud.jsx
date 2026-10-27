const logos = [
  'Northstar',
  'Underline',
  'Everbright',
  'Fieldnote',
  'Copperline',
  'Harbor & Co.',
]

export function LogoCloud() {
  return (
    <section
      className="border-b border-border bg-paper py-12"
      aria-label="Trusted by teams"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="text-center font-mono text-[11px] uppercase tracking-[0.2em] text-ink-muted">
          Trusted by focused product teams
        </p>
        <ul className="mt-8 grid grid-cols-2 items-center gap-x-8 gap-y-6 sm:grid-cols-3 md:grid-cols-6">
          {logos.map((name) => (
            <li
              key={name}
              className="text-center font-display text-lg tracking-tight text-ink-muted/80 sm:text-xl"
            >
              {name}
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
