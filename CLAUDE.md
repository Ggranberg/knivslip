# Knivslip AB — Projektkontext

## Företaget
**Knivslip AB** — Mobil knivslipningstjänst i Sverige.
Vi hämtar knivar från kunden och lämnar tillbaka dem **inom 2 dagar**. Konkurrenter (t.ex. Knivbrev) skickar via post och tar 10+ dagar.

- **Grundare:** Gustav Granberg (18) & Philip Zetterlund (20)
- **Utrustning:** TORMEK slipar (från Lindesberg)
- **Philip är från Lindesberg** — hemmaplan
- **Bolagsform:** Svenskt aktiebolag (under registrering)
- **Org.nr:** _FYLL I NÄR REGISTRERAT_
- **Momsreg.nr:** _FYLL I_
- **F-skatt:** Ja (ansökt)
- **Bankgiro:** _FYLL I_
- **Swish Företag:** _FYLL I_

## Kundanskaffning
- Facebook (inlägg + DM)
- Dörrknackning
- Mun-till-mun / referrals
- Hemsida (framtida)

## Agentsystem — 5 agenter

Alla agenter är Claude Code skills i `.claude/skills/`. Kör dem med `/hq`, `/pipeline`, `/ekonomi`, `/rutt`, `/analys`.

| Agent | Skill | Ansvar |
|-------|-------|--------|
| **HQ** | `/hq` | Orkestrerare — samlar data, delegerar, ger överblick |
| **Pipeline** | `/pipeline` | Hela kundresan: lead → leverans |
| **Ekonomi** | `/ekonomi` | Fakturor, bokföring, moms |
| **Rutt** | `/rutt` | Daglig ruttplanering, schema |
| **Analys** | `/analys` | KPI:er, retention, marknadsföring |

## Datakonventioner

- **Alla data:** JSON-filer i `data/`
- **Encoding:** UTF-8
- **Datum:** ISO 8601 (`YYYY-MM-DD`)
- **ID-format:** `{PREFIX}-{YYYYMMDD}-{NNN}` (t.ex. `CUS-20260406-001`)
- **Prefix:** CUS (kund), ORD (order), KNF (kniv), INV (faktura), TXN (transaktion)
- **Valuta:** SEK
- **Moms:** 25%
- **Språk:** All output på svenska

## Lagefterlevnad — OBLIGATORISKT

Alla agenter MÅSTE följa dessa lagar. Se `data/legal.json` för fullständiga detaljer.

### GDPR (alla agenter som hanterar kunddata)
- Samtycke krävs innan kunddata sparas (spåras med timestamp)
- Kund kan begära radering — anonymisera persondata, behåll ekonomiska poster (Bokföringslagen 7 år)
- Kund kan begära registerutdrag — exportera all data
- Samla bara nödvändig data — ingen överflödig profilering
- Noteringar ska INTE innehålla känsliga kategorier (hälsa, religion, etc.)

### Bokföringslagen (ekonomi-agenten)
- Bokför alla affärshändelser löpande — aldrig spara till årsskiftet
- Spara ALL bokföring i 7 år — radera ALDRIG fakturor eller transaktioner
- Årsredovisning till Bolagsverket senast 31 juli

### Momslagen (ekonomi-agenten)
- 25% moms på tjänster
- Momsdeklaration kvartalsvis (deadline: 12:e i 2:a månaden efter kvartal)
- Sätt undan 25% av intäkter som momsreserv

### Konsumenttjänstlagen (pipeline-agenten)
- Tjänsten ska utföras fackmässigt
- Vi ansvarar för knivar i vår besittning — ersätt vid skada/förlust
- Kunden har rätt att reklamera dåligt resultat

### Marknadsföringslagen (analys-agenten + hemsida)
- Ingen vilseledande reklam — 2-dagars löftet MÅSTE hållas
- Priser mot konsumenter ska ALLTID visas inklusive moms
- Erbjudanden måste vara tydliga med villkor

### F-skatt
- "Innehar F-skattsedel" på ALLA fakturor

### Produktsäkerhet (pipeline-agenten)
- Varje kniv MÅSTE kvalitetskontrolleras efter slipning
- Kniven måste vara säker (inga lösa delar, korrekt skärpa)

## Prissättning (inkl moms)
- 1-2 knivar: **170 kr/st**
- 3-5 knivar: **140 kr/st**
- 6+ knivar: **120 kr/st**
Samma pris oavsett knivtyp. Se `data/pricing.json` för exakta siffror exkl moms.

## Serviceområde
Nacka och Värmdö kommun (Stockholmsområdet).
**Hemmabase:** Klostervägen 6, Nacka.
Se `data/areas.json`.

## AUTO-OPTIMERING AV RUTTER (PERMANENT REGEL)

VARJE GANG en ny kund skapas, order laggs till, eller orderstatus andras:
1. Optimera schemat i `data/schedule.json` automatiskt
2. Prioritera leveranser efter 2-dagars deadline (mest bradskande forst)
3. Kombinera leverans + hamtning i samma omrade
4. Dela stopp mellan Gustav och Philip baserat pa geografi
5. Anvand nearest-neighbor for optimal ordning per forare
6. Visa den optimerade planen for anvandaren

Detta ar OBLIGATORISKT — hoppa aldrig over optimering.

## Viktigt
- Läs alltid JSON-filen innan du skriver till den
- Generera ID baserat på dagens datum + nästa lediga nummer
- Validera telefonnummer (07X-XXX XX XX) och postnummer (5 siffror)
- Skapa backup innan destruktiva operationer
