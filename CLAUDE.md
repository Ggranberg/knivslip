# Altravo AB (Knivkillarna) — Projektkontext

## Företaget
**Altravo AB** — Mobil knivslipningstjänst i Sverige som drivs under varumärket **Knivkillarna**.
Vi hämtar knivar från kunden och lämnar tillbaka dem **inom 2 dagar**. Konkurrenter (t.ex. Knivbrev) skickar via post och tar 10+ dagar.

- **Juridiskt namn:** Altravo AB
- **Varumärke / brand:** Knivkillarna (allt utåt mot kund — logo, hemsida, marknadsföring)
- **Org.nr:** 559548-0384
- **Bolagsadress:** c/o Philip Zetterlund, Sjöfärarvägen 18, 132 46 Saltsjö-Boo (registrerad bolagsadress)
- **Verksamhetsbas:** Klostervägen 6, Nacka (Gustavs adress)
- **Grundare:** Gustav Granberg (18, gymnasieelev) & Philip Zetterlund (20, VD i Altravo AB, säljjobb med flexibla tider)
- **Utrustning:** 2 st TORMEK T-4 (från Lindesberg)
- **Philip är från Lindesberg** — hemmaplan
- **Transport:** Föräldrarnas Peugeot 307 (tillfälligt — skåpbil planeras)
- **Vision:** Heltidsjobb → expandera från Nacka/Värmdö till fler områden/städer med egna lokaler
- **Gustav kan lämna skolan** om verksamheten kräver det
- **Bolagsform:** Svenskt aktiebolag (registrerat)
- **Momsreg.nr:** _FYLL I_
- **F-skatt:** Ja (ansökt)
- **Bankgiro:** _FYLL I_
- **Swish Företag:** _FYLL I_

## Namnregler — VIKTIGT

- **Juridiska texter** (fakturor, GDPR, integritetspolicy, avtal, footer): "**Altravo AB**" med org.nr 559548-0384
- **Marknadsföring/kund-fronten** (logo, hero, Facebook, hemsida, mejl): "**Knivkillarna**" som brand
- **Kombinerad form** (footer, första referensen): "Knivkillarna drivs av Altravo AB"

## Kapacitet & kostnader

- **Slipkapacitet per T-4:** ~5 min/kniv (erfaren), ~8 min/kniv (normal) → ca 30–40 knivar/dag/maskin
- **Maxkapacitet idag (2x T-4):** ~60–80 knivar/dag om båda slipar heltid
- **Nuvarande takt:** ~24 knivar/vecka (begränsat av tid, inte maskiner)
- **Bensinkostnad:** Peugeot 307 drar ~0,75 L/mil. Bensinpris ~19 kr/L (april 2026). Typisk dagsrutt Nacka/Värmdö ~4–6 mil = **55–85 kr/dag i bensin**
- **Övriga kostnader:** Slipstenar (byts sällan, låg kostnad), inga lokalkostnader

## Kundanskaffning
- Facebook (inlägg + DM) — huvudsaklig kommunikationskanal med kunder
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

## Tonalitet & stil

- **"Storebror-stil":** När du ger råd om affärsbeslut, nämn gärna "genvägen" eller det frestande alternativet — och förklara sedan varför man INTE ska göra det. Exempel: "Ni *kunde* låta kompisen jobba svart... men gör inte det, för Skatteverket älskar att göra exempel av småföretag." Detta gör att Gustav och Philip förstår *varför* regler finns, inte bara att de finns.
- Var rak, ärlig och lite rolig. Inte corporate-tråkig.
- Prata som en kompis som råkar kunna affärsjuridik, inte som en revisor.

## Viktigt
- Läs alltid JSON-filen innan du skriver till den
- Generera ID baserat på dagens datum + nästa lediga nummer
- Validera telefonnummer (07X-XXX XX XX) och postnummer (5 siffror)
- Skapa backup innan destruktiva operationer
