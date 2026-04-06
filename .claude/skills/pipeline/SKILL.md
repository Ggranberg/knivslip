---
name: pipeline
description: Hanterar hela kundresan — lead, bokning, hamtning, knivregistrering, slipning, kvalitetskontroll, leverans, uppfoljning
user_invocable: true
---

# Orderpipeline — Knivslip AB

Du hanterar hela kundresan fran forsta kontakt till levererad order. Du ar den mest anvanda agenten.

Folj instruktionerna i `.claude/skills/shared/helpers.md` for ID-generering, validering och GDPR.

## Statusflodet

```
lead → booked → picked_up → registered → sharpening → quality_check → ready → out_for_delivery → delivered → completed
```
`cancelled` kan sattas fran vilken status som helst.

## AUTO-OPTIMERING AV RUTTER (OBLIGATORISKT)

Varje gang en av dessa handelser intraffar MASTE du optimera schemat:
- Ny kund skapas med order
- Ny order skapas
- Orderstatus andras (sarskilt: picked_up, quality_check, ready)
- Order avbokas

### Optimeringsprocedur (kor ALLTID efter andring):

1. Las `data/orders.json` — identifiera:
   - LEVERANSER: ordrar med status `quality_check`, `ready`, `out_for_delivery` (knivar klara)
   - HAMTNINGAR: ordrar med status `booked` och pickup.date = idag eller imorgon
2. Las `data/customers.json` — hamta adresser och omraden
3. Las `data/areas.json` — hamta restider mellan omraden

4. PRIORITERA leveranser:
   - Berakna deadline per order: pickup.completed_at + 2 dagar
   - Sortera: mest bradskande forst (narmast deadline)
   - Ordrar som redan passerat deadline = ROD FLAGGA

5. KLUSTRA per omrade:
   - Gruppera alla stopp (leverans + hamtning) per area_id
   - Om leverans OCH hamtning i samma omrade: KOMBINERA pa samma tur

6. TILLDELA till forare (2 st: Gustav och Philip):
   - Dela omraden: en forare tar norr/ost, andra tar soder/vast
   - Balansera antal stopp (max 2 stopp skillnad)
   - Om bara 1-2 stopp totalt: en forare racker

7. OPTIMERA ruttordning per forare:
   - Leveranser FORST (kunder vantar)
   - Nearest-neighbor: borja fran hemmabase (Klostervagen 6), ga till narmaste stopp, sedan narmaste oanbesokta, osv.
   - Avsluta med hamtningar i samma omrade som sista leverans

8. SPARA i `data/schedule.json`
9. VISA optimerad plan for anvandaren

### Tiduppskattning:
- Hamtning: 15 min per stopp
- Leverans: 10 min per stopp
- Restid mellan omraden: fran areas.json distances_minutes
- Inom omrade: 5 min mellan stopp
- Buffert: 15 min per rutt

## Kommandon

### 1. Ny kund

Trigger: "ny kund", "lagg till kund", "registrera kund"

Samla foljande information:
- **Namn** (obligatoriskt)
- **Telefon** (obligatoriskt, validera svenskt format)
- **E-post** (valfritt)
- **Adress** (obligatoriskt)
- **Postnummer** (obligatoriskt, 5 siffror)
- **Stad** (obligatoriskt)
- **Kalla** (facebook/dorr/referral/hemsida/annat)
- Notera: prisinfo behover INTE samlas in — pris bestams automatiskt av antal knivar (se pricing.json)
- **GDPR-samtycke** (obligatoriskt — fraga: "Har kunden gett samtycke till att vi sparar deras uppgifter?")
- **Anteckningar** (valfritt)

Procedur:
1. Las `data/customers.json`
2. Kontrollera att kunden inte redan finns (sok pa telefonnummer)
3. Om kunden redan finns: visa befintlig kund och fraga om ny order istallet
4. Generera ID (CUS-YYYYMMDD-NNN)
5. Bestam `area_id` fran postnummer genom att matcha mot `data/areas.json`
6. Skapa kundobjekt:
```json
{
  "id": "CUS-YYYYMMDD-NNN",
  "name": "...",
  "phone": "07X-XXX XX XX",
  "email": null,
  "address": "...",
  "postnummer": "XXX XX",
  "stad": "...",
  "area_id": "AREA-XXX",
  "source": "facebook",
  "gdpr_consent": {
    "given": true,
    "timestamp": "YYYY-MM-DDTHH:MM:SS",
    "method": "verbal",
    "notes": ""
  },
  "notes": "",
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "updated_at": "YYYY-MM-DDTHH:MM:SS",
  "is_deleted": false
}
```
7. Lagg till i `customers.json`
8. Bekrafta: "Kund {namn} skapad med ID {id}. Vill du skapa en order direkt?"

### 2. Ny order

Trigger: "ny order", "boka", "ny bokning"

Samla:
- **Kund** (sok pa namn, telefon eller ID)
- **Uppskattat antal knivar**
- **Onskat hamtningsdatum** (forslag: narmaste vardag)
- **Tidfonster** (t.ex. "17:00-19:00")
- **Anteckningar**

Procedur:
1. Las `data/customers.json` — hitta kunden
2. Verifiera GDPR-samtycke
3. Las `data/orders.json`
4. Generera ID (ORD-YYYYMMDD-NNN)
5. Skapa orderobjekt:
```json
{
  "id": "ORD-YYYYMMDD-NNN",
  "customer_id": "CUS-...",
  "status": "lead",
  "status_history": [
    {"status": "lead", "timestamp": "...", "by": "gustav"}
  ],
  "source": "facebook",
  "estimated_knife_count": 5,
  "actual_knife_count": null,
  "pickup": {
    "date": "YYYY-MM-DD",
    "time_window": "17:00-19:00",
    "assigned_to": null,
    "completed_at": null
  },
  "delivery": {
    "date": null,
    "time_window": null,
    "assigned_to": null,
    "completed_at": null
  },
  "quality_check": {
    "passed": null,
    "checked_by": null,
    "timestamp": null,
    "notes": null
  },
  "has_incident": false,
  "incident_notes": null,
  "invoice_id": null,
  "notes": "",
  "created_at": "...",
  "updated_at": "..."
}
```
6. Lagg till i `orders.json`
7. Bekrafta: "Order {id} skapad for {kundnamn}. {antal} knivar, hamtning {datum} {tid}."

### 3. Boka hamtning

Trigger: "boka hamtning", "bekrafta bokning"

1. Hitta ordern (sok pa order-ID, kundnamn)
2. Satt status till `booked`
3. Satt `pickup.date`, `pickup.time_window`, `pickup.assigned_to` (gustav/philip)
4. Lagg till i status_history
5. Bekrafta

### 4. Registrera hamtning

Trigger: "hamtad", "knivar hamtade"

1. Hitta ordern
2. Satt status till `picked_up`
3. Satt `pickup.completed_at`
4. Fraga: "Hur manga knivar hamtades?" — uppdatera `actual_knife_count`
5. Bekrafta: "Vill du registrera knivarna nu?" → om ja, kor "Registrera knivar"

### 5. Registrera knivar

Trigger: "registrera knivar", "logga knivar"

For varje kniv i ordern:
1. Fraga: typ, marke (valfritt), storlek cm (valfritt), skick fore (1-5), speciella noteringar
2. Las `data/knives.json`
3. Generera ID (KNF-YYYYMMDD-NNN)
4. Skapa knivobjekt:
```json
{
  "id": "KNF-YYYYMMDD-NNN",
  "order_id": "ORD-...",
  "customer_id": "CUS-...",
  "type": "kockkniv",
  "brand": "Global",
  "size_cm": 20,
  "condition_before": 2,
  "condition_after": null,
  "status": "registered",
  "special_notes": "Liten hack i eggen",
  "created_at": "...",
  "updated_at": "..."
}
```
5. Lagg till i `knives.json`
6. Nar alla knivar registrerade: satt orderstatus till `registered`
7. Sammanfatta: tabell med alla registrerade knivar

### 6. Uppdatera status

Trigger: "uppdatera status", "flytta", "status [order-id]"

1. Hitta ordern
2. Visa nuvarande status och nasta steg
3. Bekrafta statusandring
4. Uppdatera status, lagg till i status_history
5. Om ny status ar `sharpening`: uppdatera alla knivar i ordern till `sharpening`
6. Om ny status ar `quality_check`: kor kvalitetskontroll
7. Om ny status ar `delivered`: satt `delivery.completed_at`, fraga om faktura ska skapas

### 7. Kvalitetskontroll

Trigger: "kvalitetskontroll", "QC", "kontrollera"

For varje kniv i ordern:
1. Fraga: "Skick efter slipning (1-5)?"
2. Uppdatera `condition_after` i knives.json
3. Satt knivstatus till `completed`

Sedan for ordern:
4. Checklista:
   - [ ] Alla knivar slipade?
   - [ ] Ingen skada?
   - [ ] Rena och torra?
   - [ ] Forpackade for leverans?
5. Om allt OK: satt `quality_check.passed = true`, status → `ready`
6. Om problem: notera i `quality_check.notes`, behall status `quality_check`

### 8. Visa pipeline

Trigger: "visa pipeline", "alla ordrar", "aktivt"

1. Las `data/orders.json`
2. Filtrera bort `completed` och `cancelled` (visa dem om man ber om det)
3. For varje aktiv order: las kundnamn fran `data/customers.json`
4. Visa som tabell:

```
AKTIVA ORDRAR
═══════════════
Status          | Order       | Kund              | Knivar | Dagar
────────────────|─────────────|───────────────────|────────|──────
Bokad          | ORD-...-001 | Anna Svensson     | 5      | 1
Under slipning | ORD-...-002 | Erik Johansson    | 3      | 0
Redo           | ORD-...-003 | Maria Lindqvist   | 8      | 0
```

### 9. Sok kund

Trigger: "sok kund", "hitta kund", "kund [namn/telefon]"

1. Las `data/customers.json`
2. Sok pa: namn (case-insensitive partial match), telefon, ID
3. Visa matchande kunder med senaste order

### 10. Kundhistorik

Trigger: "historik [kund]", "kundhistorik"

1. Hitta kunden
2. Las alla ordrar for kunden
3. Las alla knivar for kunden
4. Las alla fakturor for kunden
5. Visa tidslinje

### 11. Forlorad kniv

Trigger: "forlorad kniv", "tappat kniv", "kniv saknas"

1. Hitta kniven (via order eller kniv-ID)
2. Satt knivstatus till `lost`
3. Satt `has_incident = true` pa ordern
4. Fraga om kompensation/anteckning
5. Varna: "Du bor kontakta kunden och erbjuda kompensation"

### 12. Paminnelselista

Trigger: "paminnelser", "aterkommande", "tid for slipning"

1. Las `data/orders.json` — hitta alla `completed` ordrar
2. Filtrera: leveransdatum > 3 manader sedan (konfigurerbart)
3. Las kundinfo
4. Visa lista sorterad pa omrade (for effektiv kontakt):

```
DAGS FOR PAMINELSE (senaste slipning > 3 manader)
══════════════════════════════════════════════════
Kund              | Senast | Omrade     | Telefon
Anna Svensson     | jan-06 | Lindesberg | 073-...
Erik Johansson    | dec-05 | Lindesberg | 070-...
Maria Lindqvist   | jan-06 | Orebro     | 076-...
```

## Datafiler

- **Laser och skriver:** `data/customers.json`, `data/orders.json`, `data/knives.json`
- **Laser:** `data/areas.json`, `data/pricing.json`

## Kundlivscykel

Varje kund har en livscykelfas. Bestam den automatiskt:

| Fas | Kriterium |
|-----|-----------|
| **Ny** | 0-1 ordrar |
| **Aterkommande** | 2-3 ordrar |
| **Lojal** | 4+ ordrar |
| **Risk** | Senaste order > 4 manader sedan |
| **Tappad** | Senaste order > 12 manader sedan |

Visa fasen nar kundinfo visas. For "Risk"-kunder: foresla paminnelse-SMS.

## Uppfoljning efter leverans

Nar en order satts till `delivered` eller `completed`:
1. Pamin om att skicka SMS samma dag: "Tack! Hur kanns knivarna?"
2. Berakna `next_service_due` = leveransdatum + 4 manader
3. Notera detta i kundens anteckningar

## Referral-sparning

Nar en ny kund skapas med source `referral`:
- Fraga: "Vem tipsade kunden?"
- Om tipskunden finns i systemet: notera referral-kopplingen
- Vid nasta kontakt med tipskunden: tacka for tipset

## Kompensationsguide vid problem

| Problem | Kompensation |
|---------|-------------|
| Dalig slipning | Gratis omgor + gratis nasta slipning |
| Sen leverans (>2 dagar) | 50% rabatt pa ordern |
| Forlorad kniv | Ersattningsvarde upp till 2000 kr, eller gratis slipning i 1 ar |
| Skadad kniv | Gratis reparation om mojligt, annars som forlorad |

Logga ALLTID incidenter med `has_incident: true` och detaljerade `incident_notes`.

## Regler

- Skapa ALDRIG en order utan GDPR-samtycke
- Validera ALLTID telefonnummer och postnummer
- Kolla ALLTID att kunden inte redan finns innan ny skapas
- Logga ALLTID statusandringar i status_history
- Vid statusandring: uppdatera bade order och knivar
- Svara pa leads inom 12 timmar — langre = risk att tappa kunden
- Samla ALLTID telefonnummer — utan det kan vi inte folja upp
- Fraga ALLTID om referral-kalla vid source=referral
