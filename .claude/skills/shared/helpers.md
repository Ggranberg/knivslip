---
name: Delade Hjälpinstruktioner
description: Gemensamma procedurer för alla Knivslip-agenter — JSON-hantering, ID-generering, GDPR, validering
---

# Delade Hjälpinstruktioner

Dessa instruktioner gäller för ALLA agenter i Knivslip-systemet.

## Datahantering

### Läsa JSON-fil
1. Använd Read-verktyget för att läsa filen
2. Parsa JSON-innehållet
3. Om filen är tom eller saknas, returnera tom array/objekt

### Skriva JSON-fil
1. Läs ALLTID filen först (för att få senaste versionen)
2. Gör ändringen i minnet
3. Skriv tillbaka hela filen med snyggt formaterad JSON (2 space indent)
4. Verifiera att filen skrevs korrekt

### Datakatalog
Alla JSON-filer finns i: `/Users/goonstav/AI Knivslip/data/`

## ID-generering

Format: `{PREFIX}-{YYYYMMDD}-{NNN}`

| Prefix | Typ |
|--------|-----|
| CUS | Kund (customer) |
| ORD | Order |
| KNF | Kniv (knife) |
| INV | Faktura (invoice) |
| TXN | Transaktion |

**Procedur:**
1. Läs relevant JSON-fil
2. Filtrera befintliga ID:n som börjar med `{PREFIX}-{dagens datum}`
3. Hitta högsta numret (NNN-delen)
4. Nästa ID = det numret + 1, nollpaddat till 3 siffror
5. Om inga finns för idag: börja på 001

Exempel: Om `CUS-20260406-003` finns → nästa blir `CUS-20260406-004`

## Validering

### Telefonnummer
- Svenskt format: `07X-XXX XX XX` eller `07XXXXXXXX`
- Acceptera med eller utan bindestreck/mellanslag
- Spara normaliserat: `07X-XXX XX XX`

### E-post
- Standardformat: text@domän.tld
- Valfritt fält — kan vara null

### Postnummer
- 5 siffror, format: `XXX XX` (med mellanslag)
- Spara med mellanslag: `712 34`

### Kundkälla (source)
Giltiga värden: `facebook`, `dorr`, `referral`, `hemsida`, `annat`

### Knivtyp (type)
Giltiga värden: `kockkniv`, `brodkniv`, `filetkniv`, `skalkniv`, `santoku`, `sax`, `jaktkniv`, `ovrig`

### Orderstatus
Giltig statusordning:
```
lead → booked → picked_up → registered → sharpening → quality_check → ready → out_for_delivery → delivered → completed
```
`cancelled` kan sättas från vilken status som helst.

## GDPR-procedurer

### Kontrollera samtycke
Innan en order skapas, verifiera att kunden har `gdpr_consent.given === true`.
Om inte: be användaren inhämta samtycke först.

### Radera kunddata (Right to Erasure)
1. Hitta kunden i `customers.json`
2. Sätt `is_deleted: true`
3. Ersätt persondata:
   - `name` → "Raderad kund"
   - `phone` → null
   - `email` → null
   - `address` → null
   - `notes` → null
4. BEHÅLL: `id`, `postnummer`, `area_id`, `source`, `created_at` (för anonymiserad statistik)
5. I `invoices.json`: ersätt `customer_name` → "Raderad kund", `customer_address` → null (BARA om fakturan är äldre än 7 år, annars behåll pga Bokföringslagen)
6. I `orders.json` och `knives.json`: behåll alla poster (länkade via ID, persondata finns bara i customers.json)
7. Logga raderingen: skriv ut bekräftelse med datum och vilka fält som anonymiserades

### Registerutdrag (Right to Access)
1. Hitta kunden i `customers.json`
2. Hitta alla ordrar i `orders.json` med matchande `customer_id`
3. Hitta alla knivar i `knives.json` med matchande `customer_id`
4. Hitta alla fakturor i `invoices.json` med matchande `customer_id`
5. Presentera allt i läsbart format

## Backup
Innan destruktiva operationer (radering, massuppdatering):
1. Kopiera berörd JSON-fil till `data/backups/{filnamn}-{YYYYMMDD-HHMMSS}.json`
2. Meddela användaren att backup skapades

## Formatering av output
- Använd svenska för all output
- Datumformat i visning: `YYYY-MM-DD`
- Belopp: `XXX kr` eller `X XXX kr` (med mellanslag som tusentalsavgränsare)
- Tabeller för listor med fler än 3 poster
