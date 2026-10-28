#!/usr/bin/env node
/**
 * Fail the build if production dist bundles look like they embedded secrets.
 * Heuristic only — not a substitute for proper secret scanning (gitleaks).
 */
import { readdir, readFile, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const distRoot = path.resolve(__dirname, '../dist')

const PATTERNS = [
  { name: 'AWS access key', re: /AKIA[0-9A-Z]{16}/g },
  { name: 'Django secret-like', re: /django-insecure-[A-Za-z0-9!@#$%^&*()_+=-]{8,}/g },
  { name: 'Private key block', re: /-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----/g },
  { name: 'Generic API key assignment', re: /(api[_-]?key|secret[_-]?key|JWT_SIGNING_KEY|DATABASE_URL)\s*[:=]\s*['"][^'"]{12,}/gi },
  { name: 'Neon/Postgres URL with password', re: /postgres(?:ql)?:\/\/[^:\s]+:[^@\s]+@/gi },
]

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const files = []
  for (const entry of entries) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await walk(full)))
    } else if (/\.(js|mjs|cjs|html|css|map|json)$/i.test(entry.name)) {
      files.push(full)
    }
  }
  return files
}

async function main() {
  try {
    await stat(distRoot)
  } catch {
    console.error(`dist/ not found at ${distRoot}. Run npm run build first.`)
    process.exit(1)
  }

  const files = await walk(distRoot)
  const hits = []

  for (const file of files) {
    const text = await readFile(file, 'utf8')
    for (const { name, re } of PATTERNS) {
      re.lastIndex = 0
      if (re.test(text)) {
        hits.push({ file: path.relative(distRoot, file), name })
      }
    }
  }

  if (hits.length) {
    console.error('Potential secret-like content in dist/:')
    for (const hit of hits) {
      console.error(`  - ${hit.name} in ${hit.file}`)
    }
    process.exit(1)
  }

  console.log(`Checked ${files.length} dist files — no secret-like patterns.`)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
