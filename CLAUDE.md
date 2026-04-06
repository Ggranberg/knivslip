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

## GDPR-policy

- Samtycke krävs innan kunddata sparas (spåras med timestamp)
- Kund kan begära radering — anonymisera persondata, behåll ekonomiska poster (Bokföringslagen 7 år)
- Kund kan begära registerutdrag — exportera all data
- Samla bara nödvändig data — ingen överflödig profilering
- Noteringar ska INTE innehålla känsliga kategorier (hälsa, religion, etc.)

## Prissättning (inkl moms)
- 1-2 knivar: **170 kr/st**
- 3-5 knivar: **140 kr/st**
- 6+ knivar: **120 kr/st**
Samma pris oavsett knivtyp. Se `data/pricing.json` för exakta siffror exkl moms.

## Serviceområde
Nacka och Värmdö kommun (Stockholmsområdet).
**Hemmabase:** Klostervägen 6, Nacka.
Se `data/areas.json`.

## Viktigt
- Läs alltid JSON-filen innan du skriver till den
- Generera ID baserat på dagens datum + nästa lediga nummer
- Validera telefonnummer (07X-XXX XX XX) och postnummer (5 siffror)
- Skapa backup innan destruktiva operationer
