---
name: Ekonomi
description: Fakturor, bokforing, momsredovisning, resultatrapport — svensk standard for aktiebolag
user_invocable: true
---

# Ekonomi — Knivslip AB

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
    "name": "Knivslip AB",
    "org_nr": "XXXXXX-XXXX",
    "vat_nr": "SE XXXXXXXXXXXX",
    "address": "FYLL I ADRESS",
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
║ Knivslip AB                                   ║
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
- Kategori: bransle, material, forpackning, telefon, forsakring, marknadsforing, kontorsmaterial, ovrigt
- Momsavdrag? (ja/nej — 25% for de flesta)
- Kvittoreferens (valfritt)

Procedur:
1. Las `data/transactions.json`
2. Generera ID (TXN-YYYYMMDD-NNN)
3. Berakna: belopp exkl moms = belopp inkl moms / 1.25 (om momsavdrag)
4. Skapa transaktionsobjekt med type "expense"
5. Lagg till i `transactions.json`

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

## Regler

- Fakturanummer ar SEKVENTIELLA och far ALDRIG ateranvandas
- Radera ALDRIG fakturor eller transaktioner (Bokforingslagen 7 ar)
- Moms ar ALLTID 25% pa tjanster
- OCR-nummer MASTE vara korrekt (Luhn-algoritm)
- Forfallodatum ar ALLTID 30 dagar fran fakturadatum om inte annat anges
- Alla belopp avrundas till hela kronor
