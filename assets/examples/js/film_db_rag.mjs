// Node 18+ is required (Node 20 is preinstalled on dev-host via NVM)
const SCHEMA = process.env.SCHEMA_NAME || 'filmdata1'
const PROXY_HOST = (process.env.PROXY_HOST || '').trim()

function baseUrl() {
  if (PROXY_HOST) {
    if (PROXY_HOST.startsWith('http://') || PROXY_HOST.startsWith('https://')) return PROXY_HOST
    return `https://${PROXY_HOST}`
  }
  return 'http://postgrest:3000'
}

async function getJson(url) {
  const res = await fetch(url, { headers: { 'Accept-Profile': SCHEMA } })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return await res.json()
}

async function main() {
  const base = baseUrl()
  console.log(`Using schema=${SCHEMA}`)
  console.log(`Proxy base=${base}`)
  const url = `${base}/film?select=film_id,title,description&order=title.asc&limit=5`
  const rows = await getJson(url)
  console.log(JSON.stringify(rows, null, 2).slice(0, 2000))
  console.log('\nOK')
}

main().catch((e) => { console.error('ERROR:', e); process.exit(2) })

