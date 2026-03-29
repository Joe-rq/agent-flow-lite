import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { parseDocsVerifyArgs, verifyDocs } from './docs-verify.mjs'

const root = process.cwd()
const errors = []
let docsVerifyOptions = {}
const expectedDocsVerifyScript =
  'git -c safe.directory=* status --porcelain=v1 -uall > .claude/.docs-verify-status && node scripts/docs-verify.mjs --status-file .claude/.docs-verify-status'
const expectedDocsImpactScript =
  'git -c safe.directory=* status --porcelain=v1 -uall > .claude/.docs-impact-status && node scripts/docs-verify.mjs --status-file .claude/.docs-impact-status --impact-only'
const expectedDocsImpactJsonScript =
  'git -c safe.directory=* status --porcelain=v1 -uall > .claude/.docs-impact-json-status && node scripts/docs-verify.mjs --status-file .claude/.docs-impact-json-status --impact-only --format json'
const expectedGovernanceScript =
  'git -c safe.directory=* status --porcelain=v1 -uall > .claude/.check-governance-status && node scripts/check-governance.mjs --status-file .claude/.check-governance-status'
const expectedReqCompleteScript =
  'git -c safe.directory=* status --porcelain=v1 -uall > .claude/.req-complete-status && node scripts/req-cli.mjs complete --status-file .claude/.req-complete-status'

try {
  docsVerifyOptions = parseDocsVerifyArgs(process.argv.slice(2))
} catch (error) {
  errors.push(error.message)
}

function read(relPath) {
  return readFileSync(path.join(root, relPath), 'utf8')
}

function requireFile(relPath) {
  if (!existsSync(path.join(root, relPath))) {
    errors.push(`Missing required file: ${relPath}`)
  }
}

function requireText(relPath, expectedSnippets) {
  const content = read(relPath)
  for (const snippet of expectedSnippets) {
    if (!content.includes(snippet)) {
      errors.push(`Expected "${snippet}" in ${relPath}`)
    }
  }
}

function getSection(markdown, heading) {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`${escaped}\\n([\\s\\S]*?)(?=\\n## |$)`)
  const match = markdown.match(regex)
  return match ? match[1] : ''
}

const requiredFiles = [
  'AGENTS.md',
  'CLAUDE.md',
  'README.md',
  'CONTRIBUTING.md',
  'package.json',
  '.claude/progress.txt',
  'scripts/docs-sync-rules.json',
  'scripts/docs-verify.mjs',
  'scripts/check-governance.mjs',
  'scripts/req-cli.mjs',
  'skills/README.md',
  'context/business/README.md',
  'context/business/product-overview.md',
  'context/tech/README.md',
  'context/tech/architecture.md',
  'context/tech/tech-stack.md',
  'context/tech/testing-strategy.md',
  'context/tech/env-contract.md',
  'context/tech/deployment-runbook.md',
  'context/experience/README.md',
  'requirements/INDEX.md',
  'requirements/REQ_TEMPLATE.md',
  'docs/plans/REQ-2026-001-design.md',
  'requirements/completed/REQ-2026-001-harness-lab-integration.md',
  'requirements/reports/REQ-2026-001-code-review.md',
  'requirements/reports/REQ-2026-001-qa.md'
]

for (const relPath of requiredFiles) {
  requireFile(relPath)
}

requireText('README.md', [
  'npm run docs:impact',
  'npm run docs:impact:json',
  'npm run docs:verify',
  'npm run check:governance',
  'npm run verify',
  'requirements/INDEX.md',
  '.claude/progress.txt'
])
requireText('AGENTS.md', ['requirements/INDEX.md', '.claude/progress.txt', 'context/*/README.md'])
requireText('CLAUDE.md', ['npm run check:governance', 'requirements/INDEX.md', '.claude/progress.txt'])
requireText('CONTRIBUTING.md', [
  'Files To Update Together',
  'scripts/docs-sync-rules.json',
  'npm run docs:impact',
  'npm run docs:verify',
  'npm run check:governance'
])
requireText('requirements/INDEX.md', ['## 当前搁置 REQ', 'REQ-2026-001-harness-lab-integration.md'])
requireText('requirements/REQ_TEMPLATE.md', ['### 约束（Scope Control，可选）', '## 阻塞 / 搁置说明（可选）'])

const packageJson = JSON.parse(read('package.json'))
if (packageJson.scripts?.['docs:impact'] !== expectedDocsImpactScript) errors.push('package.json must expose the git-status-backed docs:impact command')
if (packageJson.scripts?.['docs:impact:json'] !== expectedDocsImpactJsonScript) errors.push('package.json must expose the git-status-backed docs:impact:json command')
if (packageJson.scripts?.['docs:verify'] !== expectedDocsVerifyScript) errors.push('package.json must expose the git-status-backed docs:verify command')
if (packageJson.scripts?.['check:governance'] !== expectedGovernanceScript) errors.push('package.json must expose the git-status-backed check:governance command')
if (packageJson.scripts?.['req:complete'] !== expectedReqCompleteScript) errors.push('package.json must expose the git-status-backed req:complete command')

for (const scriptName of [
  'frontend:type-check', 'frontend:build', 'frontend:lint', 'frontend:test:critical',
  'backend:test', 'backend:test:critical', 'lint', 'build', 'test', 'verify',
  'req', 'req:create', 'req:start', 'req:block'
]) {
  if (!packageJson.scripts?.[scriptName]) errors.push(`package.json must expose "${scriptName}"`)
}

const indexText = read('requirements/INDEX.md')
const progressText = read('.claude/progress.txt')
const activeSection = getSection(indexText, '## 当前活跃 REQ').trim()
const activeItems = activeSection.split('\n').map((line) => line.trim()).filter((line) => line.startsWith('- ') && line !== '- 无')
const progressMatch = progressText.match(/^Current active REQ:\s*(.+)$/m)

if (!progressMatch) {
  errors.push('progress.txt must include "Current active REQ"')
} else {
  const progressActive = progressMatch[1].trim()
  if (activeItems.length === 0 && progressActive !== 'none') errors.push('requirements/INDEX.md says there is no active REQ, but progress.txt does not say "none"')
  if (activeItems.length > 0 && progressActive === 'none') errors.push('requirements/INDEX.md lists an active REQ, but progress.txt says "none"')
  if (activeItems.length > 0 && !activeItems.some((item) => item.includes(progressActive))) errors.push('Active REQ in progress.txt must appear in requirements/INDEX.md')
}

if (errors.length > 0) {
  console.error('Governance check failed:')
  for (const error of errors) console.error(`- ${error}`)
  process.exit(1)
}

const docsVerify = verifyDocs(root, docsVerifyOptions)
if (docsVerify.errors.length > 0) {
  console.error('Governance check failed because docs:verify failed:')
  for (const error of docsVerify.errors) console.error(`- ${error}`)
  process.exit(1)
}

console.log('Governance check passed.')
console.log('- Required governance files are present.')
console.log('- Entry docs, REQ index, and progress file are aligned.')
console.log('- docs:verify passed.')