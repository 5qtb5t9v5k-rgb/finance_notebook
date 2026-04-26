# mcp-inventory auth patch

Lisää bearer-token autentikaation, CORS-allowlistin ja per-IP rate limitin
HTTP-transporttiin sekä `health`- että `todoist`-servereille.

## Asennus

1. Kopioi `middleware.ts` molempiin servereihin:

   ```sh
   cp middleware.ts <mcp-inventory>/servers/health/src/middleware.ts
   cp middleware.ts <mcp-inventory>/servers/todoist/src/middleware.ts
   ```

2. Päivitä molempien serverien `src/index.ts`. HTTP-handlerin alkuun, ennen
   tool-reititystä:

   ```ts
   import { applyCors, checkBearer, rateLimit } from "./middleware.js";

   // ... sisällä http-pyynnön käsittelijässä:
   applyCors(req, res);
   if (req.method === "OPTIONS") {
     res.statusCode = 204;
     res.end();
     return;
   }
   if (!rateLimit(req, res)) return;
   if (!checkBearer(req, res)) return;
   // ... olemassaoleva MCP transport / tool routing jatkuu tästä
   ```

   Poista samalla nykyinen `Access-Control-Allow-Origin: *` -setteri ja
   `"WARNING: No MCP_API_KEY set"` -varoitusblokki — middleware hoitaa
   molemmat (fail-closed: ilman avainta serveri palauttaa 503:n).

3. Aseta vahva avain Fly secretiksi (eri avain per serveri):

   ```sh
   fly secrets set MCP_API_KEY="$(openssl rand -base64 32)" -a health-mcp-server
   fly secrets set MCP_API_KEY="$(openssl rand -base64 32)" -a todoist-mcp-server
   ```

   Älä laita avainta `fly.toml`:n `[env]`-blockkiin — se commitoituu julkiseen
   repoon.

4. Päivitä Claude-clientit lisäämään `Authorization: Bearer <key>` jokaiseen
   HTTP-pyyntöön:
   - **Claude Desktop / `~/.claude/settings.json`**: jos käytät HTTP-modea,
     lisää headers-osio MCP-serverin konffiin.
   - **claude.ai custom connectors**: lisää avain connector-asetuksiin.
   - **Local stdio** (Claude Desktop ilman Fly:tä): ei toimenpiteitä,
     middleware ajetaan vain HTTP-polulla.

## Mitä tämä korjaa

- **Auth**: nykyinen koodi lukee `MCP_API_KEY`:n mutta ei vertaa sitä
  pyyntöön. Middleware vaatii `Authorization: Bearer <key>`:n ja vertaa
  `timingSafeEqual`:lla. Ilman avainta serveri palauttaa 503 (fail closed)
  sen sijaan että palvelisi avoimesti.
- **CORS**: `*` -wildcardin tilalle allowlist (`claude.ai` ja sen
  alidomainit + `localhost`). `Vary: Origin` jotta CDN ei cachetä väärää
  origin-vastausta.
- **Rate limit**: 60 req/min per IP (token bucket). Estää että vuotaneella
  URL:llä joku puskee Oura-API:n quotan loppuun. Muistissa, joten Fly
  scale-to-zero nollaa tilan — riittää alkuun.

## Mitä tämä EI korjaa

- Lokitusta — käy läpi `console.log`:t ja varmista ettei
  `Authorization`-headeria tai `req.body`:ä logata.
- Tokenin rotaatiota — kun rotatat, päivitä Fly secret + clientit
  samaan aikaan; downtimea tulee parin sekunnin verran kun machine
  käynnistyy uudella envillä.
- DDoS-luokan hyökkäyksiä — Fly:n edessä Cloudflarea / Tailscale
  Funnelia jos haluat oikeasti rajata pääsyn omiin laitteisiin.

## Testaus

```sh
# Ilman tokenia → 401
curl -i https://health-mcp-server.fly.dev/mcp -X POST -d '{}'

# Väärä token → 401
curl -i https://health-mcp-server.fly.dev/mcp -X POST \
  -H "Authorization: Bearer wrong" -d '{}'

# Oikea token → 200 (tai mitä MCP transport vastaakaan)
curl -i https://health-mcp-server.fly.dev/mcp -X POST \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "Content-Type: application/json" -d '{}'

# Spämmi → 429 jossain vaiheessa
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    https://health-mcp-server.fly.dev/mcp -X POST \
    -H "Authorization: Bearer $MCP_API_KEY" -d '{}'
done | sort | uniq -c
```
