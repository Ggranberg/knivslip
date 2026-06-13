#!/usr/bin/env python3
"""Morgonbriefing for Knivkillarna — fullt paket.

Hamtar live-data fran Railway over HTTP + vader fran open-meteo, bygger en
komplett daglig briefing och skickar den som push-notis via ntfy. Stdlib only.

Kor manuellt for test:  python3 scripts/morning_brief.py
"""

import json
import os
from datetime import datetime, date, timedelta
from urllib.request import Request, urlopen

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo('Europe/Stockholm')
except Exception:
    TZ = None

BASE = os.environ.get('KNIV_BASE_URL', 'https://knivkillarna.up.railway.app')
TOPIC = os.environ.get('NTFY_BRIEF_TOPIC', 'knivkillarna-morgonbrief-h7k2qm')
LAT, LON = 59.3026, 18.1631  # Nacka
CAPACITY_PER_DAY = 70  # ~60-80 knivar/dag med 2x T-4

WD = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']
MO = ['januari', 'februari', 'mars', 'april', 'maj', 'juni', 'juli',
      'augusti', 'september', 'oktober', 'november', 'december']

WMO = {0: ('Klart', '☀️'), 1: ('Mest klart', '🌤️'), 2: ('Halvklart', '⛅'),
       3: ('Mulet', '☁️'), 45: ('Dimma', '🌫️'), 48: ('Dimma', '🌫️'),
       51: ('Duggregn', '🌦️'), 53: ('Duggregn', '🌦️'), 55: ('Duggregn', '🌦️'),
       61: ('Regn', '🌧️'), 63: ('Regn', '🌧️'), 65: ('Kraftigt regn', '🌧️'),
       71: ('Snö', '🌨️'), 73: ('Snö', '🌨️'), 75: ('Kraftig snö', '🌨️'),
       80: ('Regnskurar', '🌦️'), 81: ('Regnskurar', '🌧️'), 82: ('Kraftiga skurar', '⛈️'),
       95: ('Åska', '⛈️'), 96: ('Åska', '⛈️'), 99: ('Åska', '⛈️')}


def fj(f):
    r = Request(f'{BASE}/data/{f}', headers={'Cache-Control': 'no-cache'})
    return json.loads(urlopen(r, timeout=15).read().decode('utf-8'))


def pdate(s):
    """Plocka ut date ur en ISO-sträng (hanterar Z, offset, microsekunder)."""
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def kc(orders):
    return sum((o.get('actual_knife_count') or o.get('estimated_knife_count') or 0) for o in orders)


def get_weather():
    try:
        url = (f'https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}'
               '&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode'
               '&timezone=Europe%2FStockholm&forecast_days=1')
        d = json.loads(urlopen(url, timeout=10).read().decode('utf-8'))['daily']
        txt, emoji = WMO.get(d['weathercode'][0], ('', '🌡️'))
        lo, hi = round(d['temperature_2m_min'][0]), round(d['temperature_2m_max'][0])
        nb = d['precipitation_sum'][0]
        line = f"{emoji} {txt} {lo}–{hi}°C"
        if nb and nb >= 0.2:
            line += f", {nb:.1f} mm nederbörd"
        return line
    except Exception:
        return None


def build_briefing():
    now = datetime.now(TZ) if TZ else datetime.now()
    today = now.date()
    today_str = today.isoformat()
    yest = today - timedelta(days=1)
    datum = f"{WD[now.weekday()]} {now.day} {MO[now.month - 1]}"

    sched = fj('schedule.json').get('schedule', [])
    books = fj('bookings.json').get('bookings', [])
    orders = fj('orders.json').get('orders', [])
    customers = fj('customers.json').get('customers', [])
    reviews = fj('reviews.json').get('reviews', [])
    invoices = fj('invoices.json').get('invoices', [])
    txns = fj('transactions.json').get('transactions', [])

    L = [f"God morgon! Här är läget {datum}."]
    w = get_weather()
    if w:
        L.append(w)
    L.append("")

    # ---- Dagens rutt ----
    todays = [s for s in sched if s.get('date') == today_str]
    rl, dels = [], []
    for s in sorted(todays, key=lambda x: x.get('assigned_to', '')):
        st = [x for x in s.get('stops', []) if not x.get('completed')]
        if not st:
            continue
        d = (s.get('assigned_to') or 'Ej tilldelad').capitalize()
        h = sum(1 for x in st if x.get('type') == 'pickup')
        v = sum(1 for x in st if x.get('type') == 'delivery')
        tid = ''
        if s.get('estimated_start') and s.get('estimated_end'):
            tid = f", {s['estimated_start']}–{s['estimated_end']}"
        elif s.get('estimated_total_time_min'):
            tid = f", ~{s['estimated_total_time_min']} min"
        rl.append(f"  {d}: {len(st)} stopp ({h} hämt, {v} lev){tid}")
        dels += [x for x in st if x.get('type') == 'delivery']
    if rl:
        L.append("📋 Dagens rutt:")
        L += rl
    else:
        L.append("📋 Dagens rutt: inga stopp planerade.")
    L.append("")

    # ---- Måste levereras idag ----
    if dels:
        L.append(f"🚨 Måste levereras idag: {len(dels)}")
        for x in dels[:6]:
            L.append(f"  • {x.get('customer_name', '?')} — {x.get('notes', '')}")
        L.append("")

    # ---- Knivar nära/över 2-dagars-deadline (hämtade, ej levererade) ----
    active_open = [o for o in orders if o.get('status') not in ('completed', 'cancelled', 'lead', 'booked')]
    cust = {c['id']: c for c in customers}
    risky = []
    for o in active_open:
        if (o.get('delivery') or {}).get('completed_at'):
            continue
        pd = pdate((o.get('pickup') or {}).get('completed_at') or (o.get('pickup') or {}).get('date'))
        if not pd:
            continue
        days = (today - pd).days
        if days >= 1:
            risky.append((days, o))
    if risky:
        risky.sort(key=lambda t: -t[0])
        L.append(f"⏰ Nära/över deadline: {len(risky)}")
        for days, o in risky[:6]:
            namn = cust.get(o.get('customer_id'), {}).get('name', o.get('id'))
            flagga = '🔴 ÖVER' if days >= 2 else '🟡 dag 2'
            L.append(f"  • {namn} ({kc([o])} kn) — {flagga} ({days} dgr)")
        L.append("")

    # ---- Nya bokningar sedan igår + obekräftade ----
    nya = [b for b in books if pdate(b.get('created_at')) and pdate(b.get('created_at')) >= yest]
    pend = [b for b in books if b.get('status') == 'pending']
    if nya:
        L.append(f"🆕 Nya bokningar sedan igår: {len(nya)}")
    if pend:
        L.append(f"📥 Obekräftade att godkänna: {len(pend)}")
    if nya or pend:
        L.append("")

    # ---- Nya omdömen ----
    nyrev = [r for r in reviews if pdate(r.get('created_at')) and pdate(r.get('created_at')) >= yest]
    appr = [r for r in reviews if r.get('approved') and r.get('rating')]
    if nyrev:
        L.append(f"⭐ Nya omdömen sedan igår: {len(nyrev)}")
        for r in nyrev[:3]:
            L.append(f"  • {'★' * int(r.get('rating', 0))} {r.get('name', '?')}")
    if appr:
        snitt = sum(r['rating'] for r in appr) / len(appr)
        L.append(f"   Snittbetyg: {snitt:.1f} ({len(appr)} omdömen)")
    if nyrev or appr:
        L.append("")

    # ---- Leads att följa upp ----
    leads = [c for c in customers if not c.get('is_deleted')
             and pdate(c.get('next_call_at')) and pdate(c.get('next_call_at')) <= today]
    if leads:
        L.append(f"📞 Leads att ringa idag: {len(leads)}")
        for c in leads[:5]:
            L.append(f"  • {c.get('name', '?')} ({c.get('phone', '')})")
        L.append("")

    # ---- Kapacitet ----
    in_shop = [o for o in orders if o.get('status') in ('picked_up', 'registered', 'sharpening')]
    ready = [o for o in orders if o.get('status') in ('quality_check', 'ready', 'out_for_delivery')]
    queue_knives = kc(in_shop)
    if in_shop:
        bel = round(queue_knives / CAPACITY_PER_DAY * 100)
        L.append(f"🔪 Att slipa: {queue_knives} knivar ({len(in_shop)} ordrar) — ~{bel}% av dagskapacitet")
    if ready:
        L.append(f"✅ Redo att leverera: {kc(ready)} knivar ({len(ready)} ordrar)")
    active = [o for o in orders if o.get('status') not in ('completed', 'cancelled', 'lead')]
    L.append(f"📦 Aktiva ordrar totalt: {len(active)}")
    L.append("")

    # ---- Ekonomi ----
    obetalda = [i for i in invoices if i.get('status') not in ('paid', 'cancelled', 'draft')]
    if obetalda:
        summa = sum(i.get('total_incl_vat', 0) for i in obetalda)
        forfallna = [i for i in obetalda if pdate(i.get('due_date')) and pdate(i.get('due_date')) < today]
        rad = f"💰 Obetalda fakturor: {len(obetalda)} ({summa:,.0f} kr)".replace(',', ' ')
        if forfallna:
            rad += f" — varav {len(forfallna)} förfallna 🔴"
        L.append(rad)
    # Intäkter denna månad (income-transaktioner)
    inc = [t for t in txns if t.get('type') in ('income', 'revenue', 'sale', 'intäkt')
           and pdate(t.get('date')) and pdate(t.get('date')).month == today.month
           and pdate(t.get('date')).year == today.year]
    if inc:
        manad_int = sum(t.get('amount_incl_vat', 0) for t in inc)
        moms = sum(t.get('vat', 0) for t in inc)
        L.append(f"📈 Intäkt denna månad: {manad_int:,.0f} kr — lägg undan {moms:,.0f} kr moms".replace(',', ' '))

    # Skatte-/momsdeadlines
    deadlines = []
    for m_end, label in [(2, 'momsdekl Q4'), (5, 'momsdekl Q1'), (8, 'momsdekl Q2'), (11, 'momsdekl Q3')]:
        dd = date(today.year, m_end, 12)
        if 0 <= (dd - today).days <= 14:
            deadlines.append((dd, label))
    ar = date(today.year, 7, 31)
    if 0 <= (ar - today).days <= 30:
        deadlines.append((ar, 'årsredovisning till Bolagsverket'))
    for dd, label in sorted(deadlines):
        L.append(f"⚠️ Deadline {dd.strftime('%d/%m')}: {label} ({(dd - today).days} dgr kvar)")

    return datum, "\n".join(L).strip()


def send(datum, body):
    req = Request(
        f'https://ntfy.sh/{TOPIC}',
        data=body.encode('utf-8'),
        headers={
            'Title': f'Morgonbrief: {datum}',
            'Tags': 'sunrise,knife',
            'Priority': '4',
            'Click': f'{BASE}/admin',
        },
    )
    urlopen(req, timeout=10)


if __name__ == '__main__':
    datum, body = build_briefing()
    send(datum, body)
    print(f'[BRIEF] Skickad till {TOPIC} ({datum})')
    print('-' * 40)
    print(body)
