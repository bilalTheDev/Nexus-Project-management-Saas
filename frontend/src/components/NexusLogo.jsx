export function NexusLogo({ className = '', showWordmark = true }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width="28"
        height="28"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <rect width="32" height="32" rx="8" fill="#202A35" />
        <path
          d="M8 22V10h3.2l5.1 8.2V10H19v12h-3.2L10.7 13.8V22H8z"
          fill="#E5F1EC"
        />
        <circle cx="23.5" cy="11.5" r="2.5" fill="#347D78" />
      </svg>
      {showWordmark ? (
        <span className="font-display text-xl tracking-tight text-ink">
          Nexus
        </span>
      ) : null}
    </span>
  )
}
