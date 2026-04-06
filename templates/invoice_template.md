# Fakturamall — Knivslip AB

Ekonomi-agenten anvander denna mall for att formatera fakturor.

## Format

```
╔══════════════════════════════════════════════════════╗
║                      FAKTURA                          ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  Knivslip AB                                          ║
║  {foretag_adress}                                     ║
║  Org.nr: {org_nr}                                     ║
║  Momsreg.nr: {vat_nr}                                ║
║  Innehar F-skattsedel                                 ║
║                                                       ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  Fakturanr:     {invoice_number}                      ║
║  Fakturadatum:  {invoice_date}                        ║
║  Forfallodatum: {due_date}                            ║
║  OCR:           {ocr}                                 ║
║                                                       ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  KUND                                                 ║
║  {customer_name}                                      ║
║  {customer_address}                                   ║
║                                                       ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  Beskrivning             | Antal | A-pris  |  Summa   ║
║  ────────────────────────|───────|─────────|───────── ║
║  {for varje rad:}                                     ║
║  {description}           | {qty} | {price} | {total}  ║
║                                                       ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  Netto (exkl moms):                    {total_excl} kr║
║  Moms 25%:                             {total_vat} kr ║
║  ─────────────────────────────────────────────────── ║
║  ATT BETALA:                           {total_incl} kr║
║                                                       ║
╠══════════════════════════════════════════════════════╣
║                                                       ║
║  BETALNING                                            ║
║  Bankgiro: {bankgiro}                                 ║
║  Swish:    {swish}                                    ║
║  OCR:      {ocr}                                      ║
║                                                       ║
║  Betalningsvillkor: 30 dagar netto                    ║
║  Vid forsenad betalning debiteras drojsmalsranta      ║
║  enligt rantelagen (referensranta + 8 procentenheter) ║
║                                                       ║
╚══════════════════════════════════════════════════════╝
```

## Paminnelsefaktura — tillagg

Lagg till under betalningsinfo:
```
║  BETALNINGSPAMINNELSE                                 ║
║  Avser faktura nr: {original_invoice_number}          ║
║  Ursprungligt belopp: {original_amount} kr            ║
║  Paminnelseavgift: 60 kr                              ║
║  Drojsmalsranta: {ranta} kr                           ║
║  TOTALT ATT BETALA: {total} kr                        ║
```

## Kreditfaktura — tillagg

Andringen:
- Titel: "KREDITFAKTURA" istallet for "FAKTURA"
- Referens: "Krediterar faktura nr: {original_invoice_number}"
- Belopp i NEGATIVT
