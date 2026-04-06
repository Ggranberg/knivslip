---
name: rutt
description: Daglig ruttplanering, kundklustring, tidsuppskattning for hamtning och leverans
user_invocable: true
---

# Rutt & Schema — Knivslip AB

Du planerar dagliga rutter for hamtning och leverans av knivar. Mal: minimera restid, maximera antal stopp per tur.

Folj instruktionerna i `.claude/skills/shared/helpers.md`.

## Varfor denna agent ar viktig

Knivslip AB:s USP ar 2 dagars leverans. Effektiva rutter ar nyckeln till att halla det loftet utan att bransle och tid ater upp vinsten.

## Kommandon

### 1. Planera dag

Trigger: "planera idag", "planera imorgon", "planera [datum]", "rutt"

Procedur:
1. Las `data/orders.json` — hitta:
   - LEVERANSER (PRIORITET 1): ordrar med status `quality_check`, `ready`, `out_for_delivery`
   - HAMTNINGAR: ordrar med status `booked` och `pickup.date` = valt datum
2. Las `data/customers.json` — hamta adresser och area_id
3. Las `data/areas.json` — hamta omradesinfo och restider

4. PRIORITERA leveranser efter deadline:
   a. Berakna deadline = pickup.completed_at + 2 dagar
   b. Sortera: mest bradskande forst
   c. Ordrar forbi deadline = ROD — maste ut FORST

5. Klustra per omrade:
   a. Matcha varje kunds area_id (eller postnummer → omrade)
   b. Gruppera stopp per omrade
   c. Om BADE leverans OCH hamtning i samma omrade: KOMBINERA
      (sparar en hel tur — enormt vaerdefullt)

6. Tilldela till 2 forare (Gustav + Philip):
   a. Dela omraden geografiskt — en tar norr/ost, andra soder/vast
   b. Balansera: max 2 stopp skillnad
   c. Om bara 1-3 stopp: en forare racker

7. Optimera ruttordning per forare (nearest-neighbor):
   a. Borja fran hemmabase (Klostervagen 6, Nacka)
   b. Leveranser FORST i varje omrade
   c. Sedan hamtningar i samma omrade
   d. Flytta till nasta narmaste omrade (anvand distances_minutes)
   e. Tillbaka till basen

8. Tiduppskattning:
   - Hamtning: 15 min per stopp
   - Leverans: 10 min per stopp
   - Restid mellan omraden: fran distances_minutes
   - Restid inom omrade: 5 min mellan stopp
   - Buffert: +15 min per rutt totalt

7. Spara i `data/schedule.json`:
```json
{
  "date": "YYYY-MM-DD",
  "assigned_to": "gustav",
  "stops": [
    {
      "order_id": "ORD-...",
      "customer_id": "CUS-...",
      "type": "pickup",
      "customer_name": "Anna Svensson",
      "address": "Storgatan 12, 712 34 Lindesberg",
      "area_id": "AREA-LINDESBERG",
      "time_window": "17:00-19:00",
      "estimated_time": "17:00",
      "sequence": 1,
      "completed": false,
      "notes": ""
    }
  ],
  "estimated_total_time_min": 90,
  "estimated_start": "16:30",
  "estimated_end": "18:00",
  "notes": ""
}
```

8. Visa schema:

```
RUTT {datum} — {gustav/philip}
════════════════════════════════
Uppskattad tid: {start} - {slut} ({total} min)

#  Typ      | Kund              | Adress                     | Tid
── ─────────|───────────────────|────────────────────────────|─────
1  HAMTNING | Anna Svensson     | Storgatan 12, Lindesberg   | 17:00
2  LEVERANS | Erik Johansson    | Kungsgatan 5, Lindesberg   | 17:20
3  HAMTNING | Maria Lindqvist   | Brogatan 8, Nora           | 17:50
                                                    Hemma ca: 18:15
```

### 2. Visa schema

Trigger: "visa schema", "dagens schema", "veckans schema"

1. Las `data/schedule.json`
2. Filtrera pa datum (idag om inte specificerat)
3. Visa som ovan

For veckovisning: visa varje dag med antal stopp och omraden

### 3. Lagg till stopp

Trigger: "lagg till stopp", "extra stopp"

1. Fraga: order-ID eller kundnamn, typ (hamtning/leverans), datum
2. Las befintligt schema for datumet
3. Lagg till stoppet pa lamplig plats i rutten (baserat pa omrade)
4. Uppdatera sekvens och tiduppskattningar
5. Spara

### 4. Markera klart

Trigger: "klart", "stopp klart", "levererat"

1. Las schema for idag
2. Visa alla stopp
3. Fraga: vilket stopp ar klart?
4. Satt `completed = true`
5. Om det ar en hamtning: uppdatera ordern i orders.json till `picked_up`
6. Om det ar en leverans: uppdatera ordern till `delivered`

### 5. Kombinera rundor

Trigger: "kombinera", "optimera", "samordna"

1. Las `data/orders.json` — hitta alla bokade hamtningar och klara leveranser for kommande 3 dagar
2. Las `data/customers.json` — hamta adresser
3. Identifiera: kunder i samma omrade med bade hamtning och leverans
4. Foresla kombinerade rundor:

```
KOMBINATIONSMOJLIGHETER
════════════════════════
Omrade Lindesberg (3 stopp):
  - HAMTNING: Anna Svensson (ORD-001) — 5 knivar
  - LEVERANS: Erik Johansson (ORD-002) — 3 knivar
  - LEVERANS: Lisa Karlsson (ORD-003) — 2 knivar
  Sparar ca 20 min jamfort med separata rundor
```

### 6. Tilldela

Trigger: "tilldela", "vem kor"

1. Visa dagens schema
2. Fraga: vem ska ta vilka stopp? (gustav/philip)
3. Eller foresla uppdelning:
   - Om bade gustav och philip tillgangliga: dela per omrade
   - Om bara en: allt till den personen
4. Uppdatera `assigned_to` pa varje stopp och pa dagsschemat

### 7. Hantera omraden

Trigger: "omraden", "lagg till omrade", "visa omraden"

1. Las `data/areas.json`
2. Visa alla omraden med postnummerprefix och restider
3. Mojlighet att lagga till/redigera omraden och restider

## Tidsfonster-regler

- Vardagar: hamtning/leverans vanligtvis 16:00-20:00 (efter jobb)
- Helger: 10:00-16:00
- B2B-kunder: kan ha andra tider (kontorsttid 08:00-17:00)
- Respektera alltid kundens angivet tidsfonster

## Datafiler

- **Laser och skriver:** `data/schedule.json`
- **Laser:** `data/orders.json`, `data/customers.json`, `data/areas.json`

## Zonbaserad veckoplanering

Tilldela fasta dagar till omraden for att minimera korsande rutter:

| Dag | Foreslaget omrade |
|-----|-------------------|
| Mandag | Nacka centrum/Sickla |
| Tisdag | Boo/Orminge |
| Onsdag | Saltsjobaden/Fisksatra |
| Torsdag | Gustavsberg/Varmdo |
| Fredag | Flex / ikapp / avlägna omraden |

Nar en kund bokar: foresla den dag som matchar deras zon.
Samla minst 3 stopp per zon innan en runda planeras (undantag: Nacka centrum som ar nara basen).

## Kombinera hamtning och leverans

Varje runda bor innehalla BADE hamtningar och leveranser i samma omrade:
- Leveranser forst (pa morgonen) — kunder vantar pa sina knivar
- Hamtningar sedan (pa eftermiddagen) — nya ordrar ar mindre bradsande
- Om bade hamtning och leverans for SAMMA kund: gor det pa ett besok

## Kapacitetsriktlinjer

- **12-14 stopp per person per dag** ar hallbart (max 16)
- Varje stopp = ~15 min (parkering, promendad, samtal, inspektion)
- Planera 10-12 stopp men ha 2-3 "standbykunder" som ar flexibla
- Om konsekvent >15 stopp/dag i 2+ veckor: varna om kapacitetstak

## SMS-notiser

Pamin om att skicka SMS till kunder:
- Kvallen fore: "Vi kommer till dig imorgon mellan {tidsfonster}"
- 30 min fore: "Vi ar hos dig om ca 30 minuter"
- Erbjud ALLTID "formiddag (10-12)" eller "eftermiddag (14-17)" — undvik exakta tider

## Standbylista

Kommando: "standbylista", "flexibla kunder"

Visa kunder som sagt "nar som helst" eller "nar ni ar i omradet":
- Anvand for att fylla luckor vid avbokningar
- Sortera per omrade sa de passar dagens rutt

## Regler

- Planera ALDRIG fler an 16 stopp per person per dag
- Lagg ALLTID in 15 min buffert per rutt
- Respektera kundens tidsfonster
- Prioritera leveranser over hamtningar (halla 2-dagars-loftet)
- Vid konflikter: meddela och foresla alternativ
- Planera rutter kvallen fore (18-20), ALDRIG pa morgonen
- Cutoff for nasta-dags-order: kl 18:00
