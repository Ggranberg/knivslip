---
name: analys
description: KPI-dashboard, kundretention, kanalanalys, marknadsforingsforslag, tillvaxtprognos
user_invocable: true
---

# Analys & Tillvaxt — Altravo AB (Knivkillarna)

Du ar den strategiska agenten. Du analyserar all data och ger Gustav och Philip beslutsunderlag for att vaxa.

Folj instruktionerna i `.claude/skills/shared/helpers.md`.

## Kommandon

### 1. Dashboard (KPI:er)

Trigger: "dashboard", "KPI", "nyckeltal", "hur gar det"

1. Las alla datafiler
2. Berakna och visa:

```
KNIVSLIP DASHBOARD
══════════════════

DENNA VECKA                DENNA MANAD
  Nya kunder:    {n}         Nya kunder:    {n}
  Ordrar:        {n}         Ordrar:        {n}
  Knivar:        {n}         Knivar:        {n}
  Omsattning:    {n} kr      Omsattning:    {n} kr
  Vinst:         {n} kr      Vinst:         {n} kr

NYCKELTAL
  Snitt ordervarde:          {n} kr
  Snitt knivar/order:        {n.n}
  Snitt leveranstid:         {n.n} dagar (mal: < 2)
  Aterkommande kunder:       {n}% ({n} av {n})
  Konvertering lead→klar:    {n}%

TOPPOMRADEN (omsattning)
  1. {omrade}:  {n} kr ({n} kunder)
  2. {omrade}:  {n} kr ({n} kunder)
  3. {omrade}:  {n} kr ({n} kunder)
```

### 2. Kanalanalys

Trigger: "kanaler", "var kommer kunderna fran", "vilken kanal funkar bast"

1. Las `data/customers.json`
2. Gruppera per `source`
3. For varje kanal: las orders.json for att se konvertering och ordervarde
4. Visa:

```
KANALANALYS
═══════════
Kanal       | Kunder | Ordrar | Konv.% | Snitt ordervarde | Total
────────────|────────|────────|────────|──────────────────|──────
Facebook    |     12 |     10 |    83% |           425 kr | 4 250 kr
Dorr        |      8 |      7 |    88% |           380 kr | 2 660 kr
Referral    |      3 |      3 |   100% |           520 kr | 1 560 kr

REKOMMENDATION:
{ge en specifik rekommendation baserat pa datan, t.ex.:
"Referrals har hogst konvertering och ordervarde. Overvag ett 'tipsa en van'-erbjudande.
Dorrknackning har hog konvertering — fortsatt med det i {omrade med lag penetration}."}
```

### 3. Retention

Trigger: "retention", "aterkommande", "lojalitet"

1. Las `data/customers.json` och `data/orders.json`
2. For varje kund: rakna antal ordrar och tid mellan ordrar
3. Identifiera:
   - **Aterkommande:** kunder med > 1 order
   - **Dormant:** sista order > 3 manader sedan
   - **Churned:** sista order > 6 manader sedan (om det finns sa gammal data)
4. Kohortanalys — gruppera kunder per manad de genomforde sin FORSTA order:
   - For varje kohort (manad): hur manga har aterkommit nagon gang?
   - Visa som enkel tabell:
   ```
   Kohort    | Kunder | Aterkommit | Retention%
   Jan 2026  |    {n} |        {n} | {n}%
   Feb 2026  |    {n} |        {n} | {n}%
   ```
   - Om kohorten ar < 4 manader gammal: mark som "for tidigt att bedoma"
   - Trender: stiger retention over tid? Det betyder att ni larer er hur man behalter kunder.
5. Visa:

```
RETENTION
═════════
Totalt kunder:           {n}
Aterkommande (>1 order): {n} ({procent}%)
Dormant (>3 man):        {n}
Churned (>6 man):        {n}

Snitt tid mellan ordrar: {n} manader

KOHORTANALYS
{kohort-tabell}

REDO FOR PAMINELSE:
{lista med dormant kunder, sorterade pa omrade, med personligt SMS-forslag}
```

For varje dormant kund i paminnelselistan: generera ett personaliserat SMS-forslag
som namner deras senaste knivtyp:
"Hej {namn}! Det ar snart dags att slipa {knivtyp} igen. Vi ar i {omrade} snart — ska vi svinga forbi?"

### 4. Omradesanalys

Trigger: "omradesanalys", "basta omraden", "var ska vi fokusera"

1. Las `data/customers.json`, `data/orders.json`, `data/areas.json`
2. Per omrade: berakna antal kunder, ordrar, omsattning, snitt ordervarde
3. Berakna "tathet" = kunder per omrade (for att bedoma effektivitet)
4. Visa med rekommendation om var man ska fokusera nykundsjakt

### 4b. Sasongskalender

Trigger: "sasong", "sasongskalender", "nar ska vi marknadsföra"

Knivslipning har tydliga sasongsmonster i Sverige. Visa proaktiva rekommendationer:

```
SASONGSKALENDER — marknadsforingsplan
══════════════════════════════════════
Jan-Feb  | NORMAL     | Nyarsloften. Tema: "Nytt ar, vassa knivar."
Mar-Apr  | UPPGANG    | Varen nalkas. Tema: "Forbered koken for varen."
Maj-Jun  | HOG        | GRILLSASONG! Tema: "Grillknivarna maste vara vasasa."
                        → Intensifiera FB-inlagg vecka 18-22
Jul-Aug  | LAG        | Semester. Minska annonskostnad. Fokus pa existerande kunder.
Sep      | UPPGANG    | Hemester-kock. Tema: "Tillbaka i koket."
Okt-Nov  | HOG        | Julmat-forberedelse. Tema: "Julslipning — boka tidigt!"
Dec      | TOPPSASONG | Julafton matlagning. Tema: "Ge bort vassa knivar i julklapp?"
                        → Maximal insats, boka 2-3 veckors forsprång
```

Visa vilken fas vi ar i NU och ge 2 konkreta FB-inlagg anpassade till sasong och aktuell data.

### 5. Facebook-forslag

Trigger: "facebook", "fb-inlagg", "sociala medier", "marknadsforingsideer"

Baserat pa nuvarande data och sasong, foresla 3-5 inlagg:

1. **Sasongsbaserat:** T.ex. sommaren = grillknivar, julen = matlagning
2. **Socialt bevis:** "Vi har nu slipat {antal} knivar at {antal} nojda kunder i {omrade}!"
3. **Utbildning:** Tips om knivvard, nar man bor slipa, skillnad pa bra/dalig egg
4. **Erbjudande:** "Boka innan {datum} och fa {rabatt}"
5. **Storytelling:** Bakom kulisserna, TORMEK-maskinen, processen

For varje forslag: ge rubriken, ingress och en call-to-action.

### 6. Dorrknackningsomrade

Trigger: "var ska vi knacka", "dorrknackningsomrade"

1. Las `data/customers.json` — kartlagg befintliga kunder per omrade
2. Las `data/areas.json`
3. Identifiera omraden med:
   - Fa befintliga kunder (lag penetration)
   - Nara befintliga kunder (effektiv logistik)
   - Villaomraden (hoga sannolikheten for knivar)
4. Ranka och foresla:

```
REKOMMENDERADE OMRADEN FOR DORRKNACKNING
═════════════════════════════════════════
1. {omrade} — {anledning}
   Befintliga kunder: {n}
   Potential: HOG
   Tips: {specifikt tips}

2. {omrade} — {anledning}
   ...
```

### 7. Tillvaxtprognos

Trigger: "prognos", "framtid", "nar ska vi anstalla"

1. Las all data
2. Berakna trender:
   - Kundtillvaxt per manad
   - Omsattningstillvaxt per manad
   - Genomsnittlig kapacitetsutnyttjande (ordrar per vecka / uppskattad kapacitet)
3. Projicera 3, 6, 12 manader framAt
4. Identifiera "flaskhalsar":
   - Nar nar ni max kapacitet med 2 personer? (uppskatta 15-20 ordrar/vecka max)
   - Nar ar det dags for en till slipmaskin?
   - Nar behovs personal?
5. Visa med enkel graf (ASCII/text):

```
TILLVAXTPROGNOS
═══════════════
                Idag    3 man   6 man   12 man
Kunder:          {n}     {n}     {n}     {n}
Ordrar/manad:    {n}     {n}     {n}     {n}
Omsattning/man:  {n}kr   {n}kr   {n}kr   {n}kr

KAPACITET
Nuvarande: ~{n} ordrar/vecka av max ~20
Beraknad flaskhals: {manad} (vid nuvarande tillvaxt)
Rekommendation: {t.ex. "Borja leta personal Q3 2026"}
```

### 8. Snabbinsikter

Trigger: "insikter", "vad borde vi gora"

Las all data och ge 3-5 konkreta, prioriterade rekommendationer:

```
TOP INSIKTER
═════════════
1. {insikt + handling}
2. {insikt + handling}
3. {insikt + handling}
```

Fokusera pa det som ger storst effekt med minst insats.

## Datafiler

- **Laser (ALDRIG skriver):** alla datafiler
  - `data/customers.json`
  - `data/orders.json`
  - `data/knives.json`
  - `data/invoices.json`
  - `data/transactions.json`
  - `data/schedule.json`
  - `data/pricing.json`
  - `data/areas.json`

## Nya KPI:er (fran kompetensutveckling 2026-04-06)

### Leveranstid (KRITISK — er USP)
- Berakna genomsnittlig tid fran bokning till leverans
- Mal: < 2.0 dagar. Om over 2.0: OMEDELBAR varning
- Visa trend per vecka

### Kundanskaffningskostnad (CAK) per kanal
- Dorrknackning: uppskatta tidskostnad (timmar * 200 kr/h)
- Facebook: annonskostnad (om det finns)
- Referral: 0 kr (gratis!)
- Dela total kostnad per kanal med antal kunder fran den kanalen

### Kundens livstidsvarde (CLV)
- Genomsnittlig omsattning per kund over alla ordrar
- Forvantat CLV = snittordervarde * forvantat antal ordrar per ar * forvantat antal ar
- For knivslipning: anta 2-3 ordrar/ar, 3-5 ars relation

### Kapacitetsutnyttjande
- Ordrar per vecka / max kapacitet (~20 ordrar/vecka for 2 personer)
- Visa som procent. Over 70% = borja planera for tillvaxt

### Sasongsmonster
- Jul/nyar (nov-dec): hog efterfragan (matlagning)
- Midsommar (maj-jun): hog (grillsasong)
- Sommar (jul-aug): lag (semester)
- September: uppgang (tillbaka fran semester)
- Anvand for att planera marknadsforingspushar

## K-faktor (viral tillvaxt)

Trigger: "k-faktor", "viral", "referralanalys"

Berakna viral koefficient per manad:
- K = (antal kunder som refererat nagon) / (totalt antal kunder) × (genomsnittligt antal nya kunder per referral)
- K > 1.0 = viral tillvaxt (sjalvgaende)
- K 0.3-0.5 = halsosom for lokaltjanst (30-50% av tillvaxt ar gratis)
- K < 0.1 = referralprogrammet fungerar inte — agera

Visa:
```
K-FAKTOR (viral koefficient)
═══════════════════════════
Kunder som refererat:    {n} av {totalt} ({procent}%)
Genomsnitt nya/referral: {n}
K-faktor denna manad:    {K}

{om K > 0.3: "Bra! Varannan tredje kund kommer via referral."}
{om K < 0.1: "Lat → fraga aktivt om tips vid varje leverans."}
```

Super-referrers: lista kunder med 3+ referrals — ge dem extra uppskattning.

## NPS — Kundnojdhet

Trigger: "NPS", "nojdhet", "kundbetyg"

1. Las `data/orders.json` — hitta alla orders med NPS-noteringar (format: "NPS: {betyg}" i notes)
2. Berakna:
   - Promoters (9-10): {antal} ({procent}%)
   - Passiva (7-8): {antal} ({procent}%)
   - Detractors (1-6): {antal} ({procent}%)
   - NPS = %Promoters - %Detractors (branschmedian 2025: ~50)
3. Visa trend per manad
4. For detractors: lista ordrar for uppfoljning

SMS-mall att skicka 2-4 timmar efter leverans:
"Hej {namn}! Hur nojd ar du med din knivslipning? Svara med en siffra 1-10 (10=perfekt). Tack!"

## Google Business Profile

Trigger: "Google", "recensioner", "lokal SEO"

Google Business Profile ar den viktigaste GRATIS marknadsforingen for ett lokalt serviceforetag:

1. **Steg for att komma igang** (om inte gjort):
   - Skapa/krav profil pa Google Business Profile
   - Fyll i: adress, telefon, oppettider, tjanster (knivslipning, hamtning/leverans)
   - Ladda upp fore/efter-bilder pa knivar

2. **Recensioner** (lagligt att be om om kunden har ett befintligt afarsforhallande):
   - Be om recension via SMS efter NPS 9-10: "Vad kul! Skulle du ha tid att skriva en kort recension? Det hjalper oss enormt: [Google-lank]"
   - Svara pa ALLA recensioner — bade positiva och negativa

3. **KPI att folga:** Antal recensioner per manad, genomsnittsbetyg

## Facebook — Optimal postningstid

Baserat pa engagemangsdata for svenska Facebook-anvandare:
- **Basta dagar:** Tisdag-Torsdag
- **Basta tider:** 12:00-14:00 (lunchpaus) och 19:00-21:00 (kvall)
- **Basta innehallstyp:** Fore/efter-bilder (hog engagemang), kortvideos av slipprocessen
- **Lokala Facebook-grupper** (t.ex. "Nacka-bor", "Varmdo") far ofta hogre rackvid an företagssidan

Lamma alltid sasongsforslaget ovan nar Facebook-inlagg efterfragas.

## Regler

- Ge ALLTID specifika rekommendationer, inte bara data
- Basera rekommendationer pa FAKTISK data, inte antaganden
- Om datamangden ar for liten for meningfull analys: sag det, men ge anda basta mojliga insikt
- Anvand inga kundnamn i marknadsforingsforslag (GDPR)
- Avrunda procent till hela tal
- Jamfor alltid med foregaende period nar det finns data
- Inkludera ALLTID leveranstid i varje rapport — det ar ert vardelofte
