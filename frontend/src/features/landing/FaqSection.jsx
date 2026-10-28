import { useId, useState } from 'react'
import { m, AnimatePresence, useReducedMotion } from 'motion/react'

const FAQS = [
  {
    q: 'How is Nexus different from Jira?',
    a: 'Nexus eliminates custom field bloat, slow page transitions, and excessive configuration overhead. It is built strictly for engineering teams who want high-speed keyboard shortcuts, standardized 5-stage workflows, and sub-100ms responsiveness without sacrificing compliance.',
  },
  {
    q: 'Can we migrate existing issue data into Nexus?',
    a: 'Yes. Import CSV or Jira Cloud exports, map statuses to the five-stage workflow, and preserve assignees, priorities, and comments. Large workspaces can run a dry-run validation before cutover.',
  },
  {
    q: 'Does Nexus support SSO, SCIM, and enterprise RBAC?',
    a: 'SSO via SAML and OIDC is available on Enterprise, with SCIM provisioning for automatic membership sync. Role matrices go down to field-level mutations with signed tokens.',
  },
  {
    q: 'Where is customer data hosted and how is it isolated?',
    a: 'Each organization gets a dedicated PostgreSQL schema. Connection pools enforce tenant boundaries, and audit events stream to your webhook for compliance retention.',
  },
  {
    q: 'Is there a free trial available?',
    a: 'Start free with a seeded demo workspace — no credit card required. Upgrade when you need SSO, custom retention, or dedicated support.',
  },
]

function FaqItem({ item, open, onToggle, panelId, buttonId }) {
  const reduceMotion = useReducedMotion()

  return (
    <div className="border-b border-[var(--border)]">
      <h3>
        <button
          type="button"
          id={buttonId}
          aria-expanded={open}
          aria-controls={panelId}
          onClick={onToggle}
          className="flex w-full items-center justify-between gap-4 px-6 py-6 text-left focus-ring"
        >
          <span className="font-display text-lg text-[var(--text)] sm:text-xl">
            {item.q}
          </span>
          <span
            className="flex size-6 shrink-0 items-center justify-center text-[var(--accent)]"
            aria-hidden
          >
            {open ? '−' : '+'}
          </span>
        </button>
      </h3>
      <AnimatePresence initial={false}>
        {open ? (
          <m.div
            id={panelId}
            role="region"
            aria-labelledby={buttonId}
            initial={reduceMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <p className="px-6 pb-6 text-[15px] leading-[22px] text-[var(--text-muted)]">
              {item.a}
            </p>
          </m.div>
        ) : null}
      </AnimatePresence>
    </div>
  )
}

export function FaqSection() {
  const baseId = useId()
  const [openIndex, setOpenIndex] = useState(0)

  return (
    <section
      className="px-10 py-28"
      aria-labelledby="faq-heading"
    >
      <div className="mx-auto flex max-w-[800px] flex-col gap-10">
        <header className="flex flex-col items-center gap-3 text-center">
          <span className="inline-flex rounded-full bg-[var(--accent-soft)] px-3 py-1 font-mono text-[13px] uppercase tracking-[0.05em] text-[var(--accent)]">
            FAQ
          </span>
          <h2
            id="faq-heading"
            className="font-display text-[clamp(1.75rem,4vw,3rem)] leading-[1.125] tracking-[-0.025em] text-[var(--text)]"
          >
            Questions, answered plainly.
          </h2>
        </header>

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] shadow-[var(--inset-shine)]">
          {FAQS.map((item, i) => (
            <FaqItem
              key={item.q}
              item={item}
              open={openIndex === i}
              onToggle={() => setOpenIndex((prev) => (prev === i ? -1 : i))}
              buttonId={`${baseId}-btn-${i}`}
              panelId={`${baseId}-panel-${i}`}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
