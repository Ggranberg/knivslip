---
name: ekonomi
description: Fakturor, bokforing, momsredovisning, resultatrapport — svensk standard for aktiebolag
user_invocable: true
---

# Ekonomi — Altravo AB (Knivkillarna)

Du hanterar all ekonomi: fakturor, bokforing, moms och rapporter. Allt ska folja svensk lag for aktiebolag.

Folj instruktionerna i `.claude/skills/shared/helpers.md` for ID-generering och validering.

## Kommandon

### 1. Skapa faktura

Trigger: "skapa faktura", "fakturera", "faktura for [order/kund]"

Procedur:
1. Las `data/orders.json` — hitta ordern (maste ha status `delivered` eller `completed`)
2. Las `data/customers.json` — hamta kundinfo
3. Las `data/knives.json` — hamta alla knivar for ordern
4. Las `data/pricing.json` — hamta priser per knivtyp
5. Las `data/invoices.json` — hamta `next_invoice_number`

6. Berakna rader:
   - Las `data/pricing.json` for prisstegen
   - Rakna totalt antal knivar i ordern
   - Bestam pris per kniv baserat pa antal:
     * 1-2 knivar: 170 kr inkl moms (136 kr exkl)
     * 3-5 knivar: 140 kr inkl moms (112 kr exkl)
     * 6+ knivar: 120 kr inkl moms (96 kr exkl)
   - ALLA knivar i ordern far samma styckpris (baserat pa totalt antal)
   - En rad pa fakturan: "Slipning {antal} knivar a {pris} kr"

7. Berakna OCR-nummer fran fakturanummer:
   - Ta fakturanumret (t.ex. 1001)
   - Berakna kontrollsiffra med Luhn-algoritmen:
     a. Borja fran hoger, varannan siffra multipliceras med 2
     b. Om resultat > 9, subtrahera 9
     c. Summera alla siffror
     d. Kontrollsiffra = (10 - (summa % 10)) % 10
   - OCR = fakturanummer + kontrollsiffra (t.ex. 1001 → 10016)

8. Skapa fakturaobjekt:
```json
{
  "id": "INV-YYYYMMDD-NNN",
  "invoice_number": 1001,
  "order_id": "ORD-...",
  "customer_id": "CUS-...",
  "customer_name": "Anna Svensson",
  "customer_address": "Storgatan 12, 712 34 Lindesberg",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD (+ 30 dagar)",
  "ocr": "10016",
  "lines": [
    {
      "description": "Slipning kockkniv",
      "quantity": 3,
      "unit_price_excl_vat": 80,
      "vat_rate": 0.25,
      "total_excl_vat": 240
    }
  ],
  "total_excl_vat": 420,
  "total_vat": 105,
  "total_incl_vat": 525,
  "status": "draft",
  "payment": {
    "paid": false,
    "paid_date": null,
    "method": null,
    "amount_paid": 0
  },
  "is_credit_note": false,
  "credit_for_invoice": null,
  "reminder_sent": false,
  "reminder_date": null,
  "seller": {
    "name": "Altravo AB",
    "brand": "Knivkillarna",
    "org_nr": "559548-0384",
    "vat_nr": "SE XXXXXXXXXXXX",
    "address": "c/o Philip Zetterlund, Sjofararvagen 18, 132 46 Saltsjo-Boo",
    "fskatt": true,
    "bankgiro": "XXX-XXXX",
    "swish": "123XXXXXXX"
  },
  "created_at": "..."
}
```

9. Lagg till i `invoices.json`, oka `next_invoice_number`
10. Uppdatera ordern: satt `invoice_id`
11. Skapa transaktion i `transactions.json` (typ: income)

12. Visa fakturan formaterad:

```
╔══════════════════════════════════════════════╗
║                  FAKTURA                      ║
╠══════════════════════════════════════════════╣
║ Altravo AB (driver varumarket Knivkillarna)                 ║
║ [adress]                                      ║
║ Org.nr: XXXXXX-XXXX                          ║
║ Innehar F-skattsedel                          ║
║ Momsreg.nr: SE XXXXXXXXXXXX                  ║
╠══════════════════════════════════════════════╣
║ Fakturanr:    1001                            ║
║ Fakturadatum: YYYY-MM-DD                      ║
║ Forfallodatum: YYYY-MM-DD                     ║
║ OCR:          10016                           ║
╠══════════════════════════════════════════════╣
║ Kund:                                         ║
║ Anna Svensson                                 ║
║ Storgatan 12, 712 34 Lindesberg              ║
╠══════════════════════════════════════════════╣
║ Beskrivning        | Antal | A-pris |  Summa  ║
║ ────────────────────|───────|────────|──────── ║
║ Slipning kockkniv  |     3 |  80 kr |  240 kr ║
║ Slipning sax       |     1 | 100 kr |  100 kr ║
╠══════════════════════════════════════════════╣
║ Netto (exkl moms):              340 kr        ║
║ Moms 25%:                        85 kr        ║
║ ATT BETALA:                     425 kr        ║
╠══════════════════════════════════════════════╣
║ Betalning: Swish [nummer] / Bankgiro [nummer] ║
║ Ange OCR: 10016                               ║
║ Betalningsvillkor: 30 dagar netto             ║
║ Drojsmalsranta enl. rantelagen                ║
╚══════════════════════════════════════════════╝
```

13. Fraga: "Vill du markera fakturan som skickad?"
    Om ja: satt status till `sent`

### 2. Registrera betalning

Trigger: "betald", "betalning", "kunden har betalat"

1. Hitta fakturan (sok pa fakturanummer, kund eller order)
2. Fraga: betalningsdatum, metod (swish/bankgiro/kontant)
3. Uppdatera faktura: `payment.paid = true`, `payment.paid_date`, `payment.method`, `payment.amount_paid`
4. Satt fakturastatus till `paid`
5. Uppdatera orderstatus till `completed` om inte redan
6. Bekrafta: "Faktura {nr} markerad som betald. {belopp} kr via {metod}."

### 3. Registrera kostnad

Trigger: "kostnad", "utgift", "kvitto"

Samla:
- Datum
- Beskrivning (t.ex. "Bensin OKQ8")
- Belopp inkl moms
- Kategori: bransle, material, forpackning, telefon, forsakring, marknadsforing, kontorsmaterial, milersattning, ovrigt
- Momsavdrag? (ja/nej — 25% for de flesta; milersattning har ingen moms)
- Kvittoreferens (valfritt)

Procedur:
1. Las `data/transactions.json`
2. Generera ID (TXN-YYYYMMDD-NNN)
3. Berakna: belopp exkl moms = belopp inkl moms / 1.25 (om momsavdrag)
4. Skapa transaktionsobjekt med type "expense"
5. Lagg till i `transactions.json`

**For milersattning (kategori: milersattning):**
- Skatteverkets sats: 25 kr/mil for privatbil i tjansten (2025)
- Berakna: antal mil × 25 kr = avdragsgill kostnad (ingen moms)
- Pamin: "Spara korjournal med datum, start, slut, antal mil och syfte — Skatteverket kraver detta vid kontroll"
- Exempel: "Rutt Nacka-Gustavsberg 3 mil = 75 kr milersattning"

### 3b. Registrera milersattning

Trigger: "milersattning", "korkostnad", "bil"

Snabbregistrering av milersattning fran dagsrutten:
1. Fraga: datum, fran, till, antal mil (tur och retur)
2. Berakna: antal mil × 25 kr
3. Registrera som expense med kategori "milersattning"
4. Papar: "Inga kvitton kravs for milersattning, men korjournalen maste finnas"

### 4. Momsredovisning

Trigger: "moms", "momsrapport", "momsredovisning"

Fraga: period (kvartal, t.ex. "Q1 2026" = jan-mar)

1. Las `data/transactions.json`
2. Filtrera pa period
3. Berakna:
   - Utgaende moms (forsaljning): summa av alla income-transaktioners moms
   - Ingaende moms (inkop): summa av alla expense-transaktioners moms
   - Moms att betala = utgaende - ingaende

Visa:
```
MOMSREDOVISNING Q1 2026
═══════════════════════
Utgaende moms (forsaljning):    {summa} kr
Ingaende moms (inkop):         -{summa} kr
────────────────────────────────────────
Moms att betala:                {summa} kr
```

### 5. Resultatrapport

Trigger: "resultat", "vinst", "rapport", "hur gar det ekonomiskt"

Fraga: period (vecka/manad/kvartal/ar)

1. Las `data/transactions.json`
2. Gruppera per kategori
3. Visa:

```
RESULTATRAPPORT {period}
════════════════════════
INTAKTER
  Forsaljning:          {summa} kr
  Ovrigt:               {summa} kr
  Totalt:               {summa} kr

KOSTNADER
  Bransle:              {summa} kr
  Material:             {summa} kr
  Forpackning:          {summa} kr
  Telefon:              {summa} kr
  Marknadsforing:       {summa} kr
  Ovrigt:               {summa} kr
  Totalt:               {summa} kr

RESULTAT:               {summa} kr
Vinstmarginal:          {procent}%
```

### 6. Obetalda fakturor

Trigger: "obetalda", "forfalma", "vem har inte betalat"

1. Las `data/invoices.json`
2. Filtrera: `payment.paid === false`
3. Berakna dagar sedan forfallodatum
4. Sortera med mest forfalma forst
5. Visa med kundnamn och kontaktinfo

### 7. Paminnelsefaktura

Trigger: "paminnelse faktura", "betalningspaminnelse"

1. Hitta forfalien faktura
2. Skapa paminnelse med:
   - Referens till originalfaktura
   - Paminnelseavgift (valfritt, max 60 kr for privatpersoner)
   - Drojsmalsranta (referensranta + 8%)
3. Satt `reminder_sent = true`, `reminder_date` pa originalfakturan

### 8. Kreditfaktura

Trigger: "kreditera", "kreditfaktura"

1. Hitta originalfakturan
2. Skapa ny faktura med `is_credit_note = true` och negativt belopp
3. Referera till originalfakturan i `credit_for_invoice`
4. Skapa en negativ transaktion

### 9. Export for revisor

Trigger: "export", "revisor", "bokforing export"

1. Las `data/transactions.json`
2. Fraga: period
3. Presentera alla transaktioner sorterade pa datum i tabellformat
4. Inkludera: datum, verifikationsnr, beskrivning, belopp exkl moms, moms, belopp inkl moms, kategori

## Datafiler

- **Laser och skriver:** `data/invoices.json`, `data/transactions.json`
- **Laser:** `data/orders.json`, `data/customers.json`, `data/knives.json`, `data/pricing.json`

## Momsreserv

Nar en faktura skapas eller betalning registreras:
- Momsreserv = utgaende moms - ingaende moms for innevarande kvartal
- Formel: om kunden betalar 500 kr inkl moms → 100 kr ar moms (20% av brutto = 25% av netto)
- Pamin: "Satt undan {momsbelopp} kr for moms. Totalt bor ni ha {total_reserv} kr reserverat for Q{kvartal}."
- Avsatt kvartalets momsreserv pa ett separat konto — roer den INTE fore deklarationen

## Kassaflodesprognos (Runway)

Trigger: "kassaflode", "pengar", "hur mycket har vi", "runway"

Visa:
```
KASSAFLODE
══════════
Intakter (betalda):      {summa} kr
Kostnader:              -{summa} kr
Momsreserv (satt undan): -{summa} kr
────────────────────────────────
Disponibelt:              {summa} kr

VANTER PA BETALNING:     {summa} kr ({antal} fakturor)

RUNWAY
Manadlig nettokostnad:   {summa} kr
Disponibelt kapital:     {summa} kr
Uppskattad runway:       {manad} manader
```

Berakna runway = disponibelt kapital / manadlig nettokostnad (kostnader minus intakter).
Om runway < 3 manader: ROD varning. Om < 6 manader: GUL varning.

## Deadlines och paminnelser

Pamin automatiskt nar relevant. Berakna alltid exakt antal dagar kvar fran today:

| Deadline | Datum | Dagar kvar | Status |
|----------|-------|------------|--------|
| Moms Q1 (jan-mar) | 12 maj (17 maj e-dekl.) | {berakna} | {ROD <7d, GUL <30d} |
| Moms Q2 (apr-jun) | 12 aug (17 aug e-dekl.) | {berakna} | {ROD <7d, GUL <30d} |
| Moms Q3 (jul-sep) | 12 nov (17 nov e-dekl.) | {berakna} | {ROD <7d, GUL <30d} |
| Moms Q4 (okt-dec) | 12 feb nasta ar | {berakna} | {ROD <7d, GUL <30d} |
| Arsredovisning | 31 juli | {berakna} | {ROD <30d} |
| Inkomstdeklaration 2 | 1 juli | {berakna} | {ROD <30d} |

Visa denna tabell automatiskt i kassaflodes-oversikten och nar momsrapport kors.

- **Arbetsgivardeklaration:** 12:e varje manad (om lon betalas)

Nar datum narmar sig: varna i output med exakt antal dagar.

## Svenska fakturakrav (lagstadgade)

En FULLSTANDIG faktura MASTE innehalla:
1. Fakturadatum
2. Unikt lopnummer (obruten serie)
3. Saljarens namn, adress, org.nr
4. Saljarens momsregistreringsnummer (SE + org.nr + 01)
5. Koparens namn och adress
6. Beskrivning av tjansten
7. Antal och pris per enhet exkl moms
8. Momssats (25%)
9. Momsbelopp
10. Totalbelopp inkl moms
11. Betalningsvillkor
12. Bankgiro/Swish
13. "Innehar F-skattsedel"

FORENKLAD faktura (tillaten under 4 000 kr inkl moms):
- Fakturadatum, saljarens namn och momsnr, beskrivning, momsbelopp, totalbelopp

## BAS-konton (for export/revisor)

Anvand dessa konton vid bokforing:
- 3010: Forsaljning tjanster 25% moms
- 4010: Inkop material
- 5600: Transportkostnader (bensin)
- 6200: Telefon/internet
- 6530: Forsakringar
- 2610: Utgaende moms 25%
- 2640: Ingaende moms
- 1930: Foretagskonto bank
- 1510: Kundfordringar

## Bidrag per order (contribution margin)

Nar resultatrapport kors, berakna aven bidrag per order:
- Intakt per order (exkl moms): snitt ordervarde exkl moms
- Rorliga kostnader per order: milersattning (uppskatta andel per order) + forpackningsmaterial
- Bidrag = intakt - rorliga kostnader
- Bidragsmarginal = bidrag / intakt × 100%
- Mal: >70% bidragsmarginal (tjansteforetag med lag materialandel bor ligga hogt)

## Arbetsgivaravgifter — viktig ungdomsrabatt

Om ni anstaller Gustav (18 ar) eller annan person under 26 ar:
- Standard arbetsgivaravgift: 31,42% pa lon
- For anstallda under 26 ar: bara 19,73% (ungdomsrabatt)
- Skillnad: ~12 procentenheter — sparar ca 1 200 kr pa en 10 000 kr-lon
- Galler fram till den manad den anstallde fyller 26 ar
- Paverkar INTE den anstalldes lon eller formaner

## NYA 3:12-reglerna fran 2026 (KRITISKT — andrat helt)

**Forenklingsregeln ar AVSKAFFAD fran 1 januari 2026.** Det gemensamma "grundbeloppet" gallar nu for alla famansforetag.

- **Grundbelopp 2026:** 322 400 kr (4 inkomstbasbelopp) per fataget
- Galler ALLA delagare gemensamt — inte langre per delagare
- Lonekravet for huvudregeln ar i princip BORTTAGET, ersatt av schablonavdrag
- Du kan fortfarande lagga till lonebaserat utrymme + ranta pa omkostnadsbelopp utover grundbeloppet
- Utdelning upp till granbeloppet beskattas med 20% (kapitalskatt)
- Utdelning over: beskattas som lon (upp till brytpunkt) → 32-57% skatt

**For Gustav och Philip (50/50 agare):**
- Grundbelopp DELAS — varje far cirka 161 200 kr/ar i utdelningsutrymme till lag skatt
- Forst nar bolaget gar med riktig vinst (nar overskottet >300 000 kr/ar) blir detta relevant
- Innan dess: ta INGEN lon eller utdelning — terminvera vinsten in i bolaget for att bygga upp omkostnadsbelopp
- **Kommando:** "3:12" — visa beraknat utrymme baserat pa nuvarande resultat

## Representation 2026 — viktig momsandring

**Fran 1 april 2026 sanks momsen pa mat fran 12% till 6%.** Detta paverkar momsavdrag for representation.

- **Enklare fortaring** (kaffe, lask, kex, frukt): max 60 kr/person — momsavdrag tilllatet
- **Maltider** (lunch, middag): EJ avdragsgill kostnad sedan 2017
- **Momsavdrag for mat:** max pa underlag 300 kr/person/tillfalle
  - Med 6% moms (fran 1 april 2026): max 18 kr/person i momsavdrag
  - Schablonavdrag om kostnaden overstiger 300 kr: 33 kr/person/tillfalle (sankt fran 36 kr)
- Alkohol: hogre moms — separat berakning kravs
- Spara ALLTID kvitto + anteckning om syfte och deltagare (Skatteverket kraver detta)

## Friskvardsbidrag 2026 (om ni anstaller)

Om bolaget anstaller nagon (Gustav, Philip eller annan):
- **Skattefritt belopp:** 5 000 kr/anstalld/ar
- Maste erbjudas ALLA anstallda pa lika villkor
- Aktiviteter utan motion (t.ex. massage): max 1 000 kr/tillfalle
- Galler INTE for delagare som tar utdelning utan lon — kraver lon
- Bra incitament tidigt: lag kostnad, hog upskattning, helt skattefritt

## Periodisering vid arsskifte (K2-regler)

Altravo AB (Knivkillarna) foljer formodligen K2 (forenklat) eftersom omsattning < 3 MSEK och balansomslutning < 1.5 MSEK.

Vid arsbokslut (31 dec):
1. **Kundfordringar:** Bokfor som intakt om fakturan ar utstalld 31 dec, aven om betalning kommer i januari
2. **Leverantorsskulder:** Bokfor som kostnad om fakturan ar mottagen 31 dec, aven om vi betalar i januari
3. **Momsperiodisering:** Sista kvartalets moms (Q4) deklareras i februari nasta ar — bokfor som skuld
4. **Slipstenar / utrustning:** Om kop > 25 000 kr → aktiveras som anlaggningstillgang (avskrivning), annars direkt kostnad
5. **Periodisera INTE smabopa under 5 000 kr** (forenkling i K2)

## Skatteverket-triggers — undvik kontroll

Sma AB med dessa monster fastnar oftare i kontroll:
- **Hog kontant-andel:** Skatteverket misstanker svartarbete. Kor SWISH eller bankoverforing — undvik kontant.
- **Bil i bolaget utan korjournal:** Skatteverket kraver komplett korjournal vid kontroll. Spara start/slut/syfte for VARJE resa.
- **Privata utgifter pa foretagskortet:** Aldrig handla privat med Knivslip-kort. Ar det otydligt? Notera "Eget uttag" och bokfor som lon.
- **Stora kontant-uttag:** Eget uttag for delagare i AB beskattas som lon — ar inte tillaten utan lonebesked.
- **Saknade kvitton:** Bokforingslagen kraver kvitto for ALLA transaktioner. Fota direkt med kameran.

## Regler

- Fakturanummer ar SEKVENTIELLA och far ALDRIG ateranvandas
- Radera ALDRIG fakturor eller transaktioner (Bokforingslagen 7 ar)
- Moms ar ALLTID 25% pa tjanster
- OCR-nummer MASTE vara korrekt (Luhn-algoritm)
- Forfallodatum ar ALLTID 30 dagar fran fakturadatum om inte annat anges
- Alla belopp avrundas till hela kronor
- Bokfor lopande — ALDRIG spara till arsskiftet
- Stam av moms MANATLIGEN (aven om ni deklarerar kvartalsvis) — fanger fel tidigt
- Fotografera kvitton SAMMA DAG (termokvitton bleknar)
- Separera privat och foretagsekonomi ALLTID
- Fakturera SAMMA DAG som leverans — vanta aldrig
