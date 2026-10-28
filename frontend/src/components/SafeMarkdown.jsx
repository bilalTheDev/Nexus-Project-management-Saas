import DOMPurify from 'dompurify'

/** Very small markdown → HTML then sanitize. No raw HTML passthrough. */
function toSafeHtml(source) {
  const text = String(source || '')
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  const withCode = escaped.replace(
    /`([^`]+)`/g,
    '<code class="rounded bg-surface-low px-1 font-mono text-[0.85em]">$1</code>',
  )
  const withBold = withCode.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  const withLinks = withBold.replace(
    /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
    '<a href="$2" rel="noopener noreferrer" target="_blank" class="text-brand underline">$1</a>',
  )
  const withBreaks = withLinks.replace(/\n/g, '<br />')
  return DOMPurify.sanitize(withBreaks, {
    ALLOWED_TAGS: ['br', 'strong', 'code', 'a'],
    ALLOWED_ATTR: ['href', 'rel', 'target', 'class'],
  })
}

export function SafeMarkdown({ source, className = '' }) {
  return (
    <div
      className={className}
      // Sanitized via DOMPurify; raw HTML from users is escaped first.
      dangerouslySetInnerHTML={{ __html: toSafeHtml(source) }}
    />
  )
}
