#!/usr/bin/env python3
"""Knivslip server — hemsida + API + automatisk bokning."""

import json
import os
import math
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PORT = int(os.environ.get('PORT', 8080))
NTFY_TOPIC = os.environ.get('NTFY_TOPIC', 'knivslip-bok-a7x9m')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
APP_DIR = os.path.join(BASE_DIR, 'app')
ALLOWED_FILES = ['users.json', 'timelog.json', 'customers.json', 'orders.json',
                 'knives.json', 'invoices.json', 'transactions.json', 'schedule.json',
                 'pricing.json', 'areas.json', 'legal.json', 'bookings.json',
                 'reviews.json', 'salary_payments.json']

# Template for empty data files (created on first run if missing)
DATA_TEMPLATES = {
    'customers.json': {'customers': []},
    'orders.json': {'orders': []},
    'knives.json': {'knives': []},
    'invoices.json': {'invoices': []},
    'transactions.json': {'transactions': []},
    'schedule.json': {'schedule': []},
    'timelog.json': {'entries': []},
    'bookings.json': {'bookings': []},
    'reviews.json': {'reviews': []},
    'salary_payments.json': {'payments': []},
    'pricing.json': {'pricing': {'currency': 'SEK', 'vat_rate': 0.25, 'last_updated': '2026-04-06', 'price_tiers': [{'min_knives': 1, 'max_knives': 2, 'price_incl_vat': 170, 'price_excl_vat': 136, 'description': '1-2 knivar: 170 kr/st'}, {'min_knives': 3, 'max_knives': 5, 'price_incl_vat': 140, 'price_excl_vat': 112, 'description': '3-5 knivar: 140 kr/st'}, {'min_knives': 6, 'max_knives': 999, 'price_incl_vat': 120, 'price_excl_vat': 96, 'description': '6+ knivar: 120 kr/st'}], 'minimum_order': 0, 'pickup_fee': 0}},
    'areas.json': {'areas': [{'id': 'AREA-NACKA-C', 'name': 'Nacka centrum/Sickla', 'postnummer_prefix': ['131']}, {'id': 'AREA-NACKA-SALTSJOBADEN', 'name': 'Saltsjobaden/Fisksatra', 'postnummer_prefix': ['133']}, {'id': 'AREA-NACKA-BOO', 'name': 'Boo/Orminge', 'postnummer_prefix': ['132']}, {'id': 'AREA-VARMDO-C', 'name': 'Gustavsberg', 'postnummer_prefix': ['134']}], 'home_base': 'AREA-NACKA-C'},
    'users.json': {'users': [
        {'id': 'USR-001', 'name': 'Gustav Granberg', 'pin': '9680', 'role': 'admin', 'roles': ['admin'], 'active': True, 'pay_type': None, 'pay_rate': None, 'pays': [], 'created_at': '2026-04-06T00:00:00'},
        {'id': 'USR-002', 'name': 'Philip Zetterlund', 'pin': '6769', 'role': 'admin', 'roles': ['admin'], 'active': True, 'pay_type': None, 'pay_rate': None, 'pays': [], 'created_at': '2026-04-06T00:00:00'},
        {'id': 'USR-003', 'name': 'Adam Zetterlund', 'pin': '1111', 'role': 'slipare', 'roles': ['slipare'], 'active': True, 'pay_type': 'per_knife', 'pay_rate': 30, 'pays': [{'type': 'per_knife', 'rate': 30}], 'created_at': '2026-04-06T00:00:00'}
    ]},
}

def init_data():
    """Create data directory and missing files on first run."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for filename, template in DATA_TEMPLATES.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            print(f'[INIT] Skapade {filename}')

HOME_BASE = [59.3021436, 18.2572736]  # Klostervägen 6, 132 46 Saltsjö-Boo

# Address → coordinates (approximate). Synkad med ADDRESS_COORDS i app/admin.html.
# OBS: Inkludera INTE generiska kommunnamn som "nacka" eller "varmdo" här —
# de fångar tusen olika adresser och ger fel optimering. Använd specifika
# områden (Boo, Orminge etc.) eller exakta gator.
COORD_MAP = {
    # Områden (specifika delar av kommunen)
    'sickla': [59.3055, 18.1235],
    'saltsjobaden': [59.2770, 18.1510],
    'saltsjo-boo': [59.3310, 18.2440],
    'orminge': [59.3250, 18.2100],
    'gustavsberg': [59.3270, 18.3950],
    'alta': [59.2960, 18.1780],
    'bullando': [59.3059, 18.6535],
    # Specifika hemmabaser
    'klostervagen 6': HOME_BASE,
    'klostervagen 6, 132 46': HOME_BASE,
    # Specifika adresser
    'platslagarvagen 12': [59.3055, 18.1235],
    'magnevagen 7': [59.308, 18.135],
    'charlottelundsvagen 3': [59.312, 18.158],
    'flugsnapparsvagen 9': [59.309, 18.148],
    'appelblomsvagen 7': [59.306, 18.142],
    'vitmossevagen 36': [59.313, 18.152],
    'telegramvagen 6a': [59.31, 18.13],
    'kalkarsvadvagen 1': [59.305, 18.155],
    'barkows vag 14': [59.314, 18.16],
    'gamla vagen 18': [59.308, 18.165],
    'jakthornsvagen 24': [59.311, 18.145],
    'pramvagen 5': [59.306, 18.15],
    'skottvallsvagen': [59.307, 18.138],
    'algplatan 4': [59.3095, 18.156],
    'larkvagen 11': [59.3125, 18.149],
    'igelbodaplatan': [59.283, 18.155],
    'karl gerhardsvag': [59.281, 18.152],
    'ormingeringen': [59.325, 18.21],
    'grisslinge': [59.32, 18.2],
    'boplatsringen 33h': [59.323, 18.205],
    'blabarssslingan 21': [59.324, 18.215],
    'ligustervagen 65': [59.294, 18.182],
    'solvagen 20a': [59.296, 18.178],
    'oxelbacken 3': [59.295, 18.175],
    'lobeliavagen 3': [59.3045, 18.141],
    'floxvagen 4': [59.304, 18.145],
    'mistelvagen 2': [59.3065, 18.153],
    'lonnvagen 4': [59.3075, 18.146],
    'lonnlovsvagen 4': [59.3271948, 18.2908347],
    'bromsstrackan 10': [59.3059431, 18.6535262],
    'bromsstrackan': [59.3059431, 18.6535262],
    'ronnbergsvagen 5': [59.3115, 18.154],
    'evalundsvagen 216': [59.3035, 18.162],
    'stensovagen 41b': [59.315, 18.168],
    'stensovagen 14': [59.314, 18.166],
    'oskarlundsbacken 22': [59.309, 18.159],
}

def migrate_users(data):
    """Migrera gamla user-records till nya schema (roles[], pays[])."""
    changed = False
    for u in data.get('users', []):
        if 'roles' not in u:
            u['roles'] = [u['role']] if u.get('role') else []
            changed = True
        if 'pays' not in u:
            if u.get('pay_type'):
                u['pays'] = [{'type': u['pay_type'], 'rate': u.get('pay_rate')}]
            else:
                u['pays'] = []
            changed = True
    return changed

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if filename == 'users.json' and migrate_users(data):
            save_json(filename, data)
            print('[MIGRATE] users.json: lade till roles[]/pays[]')
        return data
    return {}

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def coords_for_address(addr):
    clean = addr.lower().replace('å','a').replace('ä','a').replace('ö','o').replace('é','e')
    # Matcha längsta nycklar först så "lonnlovsvagen 4" träffar före "nacka"
    for key, val in sorted(COORD_MAP.items(), key=lambda kv: -len(kv[0])):
        if key in clean:
            return val
    # Fallback: hash-based scatter runt hemmabasen (inte Sickla)
    h = sum(ord(c) for c in addr)
    return [HOME_BASE[0] + (h % 50 - 25) * 0.0003, HOME_BASE[1] + (h % 70 - 35) * 0.0004]

def distance(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

def nearest_neighbor_sort(stops, home):
    if len(stops) <= 1:
        return stops
    remaining = list(stops)
    result = []
    current = home
    while remaining:
        nearest_idx = min(range(len(remaining)), key=lambda i: distance(current, coords_for_address(remaining[i].get('address',''))))
        stop = remaining.pop(nearest_idx)
        result.append(stop)
        current = coords_for_address(stop.get('address',''))
    return result

def detect_area(address, areas_data):
    clean = address.lower().replace('å','a').replace('ä','a').replace('ö','o')
    for area in areas_data.get('areas', []):
        for prefix in area.get('postnummer_prefix', []):
            if prefix in clean:
                return area['id']
        if area['name'].lower().replace('å','a').replace('ä','a').replace('ö','o').replace('/', ' ') in clean:
            return area['id']
    return None

def generate_id(prefix, existing_ids):
    today_str = datetime.now().strftime('%Y%m%d')
    today_ids = [i for i in existing_ids if f'{prefix}-{today_str}' in i]
    num = len(today_ids) + 1
    return f'{prefix}-{today_str}-{num:03d}'

def optimize_schedule():
    """Re-optimize the full schedule based on current orders."""
    orders_data = load_json('orders.json')
    customers_data = load_json('customers.json')
    areas_data = load_json('areas.json')

    orders = orders_data.get('orders', [])
    customers = customers_data.get('customers', [])

    # Find deliveries (ready to go out)
    deliveries = [o for o in orders if o['status'] in ('quality_check', 'ready', 'out_for_delivery')]
    # Find pickups (booked for today or tomorrow)
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    pickups = [o for o in orders if o['status'] == 'booked' and o.get('pickup',{}).get('date') in (today, tomorrow)]
    # Ordrar med manuellt satt leveransdatum idag/imorgon (oavsett status, ej completed/cancelled)
    scheduled_deliveries = [o for o in orders
                           if o.get('delivery',{}).get('date') in (today, tomorrow)
                           and o['status'] not in ('completed', 'cancelled', 'quality_check', 'ready', 'out_for_delivery')
                           and o not in deliveries]

    if not deliveries and not pickups and not scheduled_deliveries:
        return

    def get_customer(cid):
        return next((c for c in customers if c['id'] == cid), None)

    # Build stops
    all_stops = []
    for o in deliveries:
        c = get_customer(o['customer_id'])
        if not c: continue
        pickup_date = o.get('pickup',{}).get('completed_at') or o.get('pickup',{}).get('date') or o['created_at']
        all_stops.append({
            'order_id': o['id'], 'customer_id': o['customer_id'],
            'type': 'delivery', 'customer_name': c['name'],
            'address': f"{c['address']}, {c.get('postnummer') or ''} {c.get('stad') or 'Nacka'}".strip(', ').replace('  ', ' '),
            'area_id': c.get('area_id') or detect_area(c.get('address',''), areas_data),
            'time_window': '', 'estimated_time': '', 'sequence': 0,
            'completed': False, 'notes': f"LEVERANS {o.get('estimated_knife_count','?')} knivar",
            '_priority': 0,  # Lower = more urgent
            '_pickup_date': pickup_date,
            '_knives': o.get('estimated_knife_count', 0)
        })

    for o in pickups:
        c = get_customer(o['customer_id'])
        if not c: continue
        all_stops.append({
            'order_id': o['id'], 'customer_id': o['customer_id'],
            'type': 'pickup', 'customer_name': c['name'],
            'address': f"{c['address']}, {c.get('postnummer') or ''} {c.get('stad') or 'Nacka'}".strip(', ').replace('  ', ' '),
            'area_id': c.get('area_id') or detect_area(c.get('address',''), areas_data),
            'time_window': o.get('pickup',{}).get('time_window',''),
            'estimated_time': '', 'sequence': 0,
            'completed': False, 'notes': f"HAMTNING {o.get('estimated_knife_count','?')} knivar",
            '_priority': 1,
            '_pickup_date': '',
            '_knives': o.get('estimated_knife_count', 0)
        })

    # Schemalagda leveranser (manuellt datum satt)
    for o in scheduled_deliveries:
        c = get_customer(o['customer_id'])
        if not c: continue
        all_stops.append({
            'order_id': o['id'], 'customer_id': o['customer_id'],
            'type': 'delivery', 'customer_name': c['name'],
            'address': f"{c['address']}, {c.get('postnummer') or ''} {c.get('stad') or 'Nacka'}".strip(', ').replace('  ', ' '),
            'area_id': c.get('area_id') or detect_area(c.get('address',''), areas_data),
            'time_window': o.get('delivery',{}).get('time_window',''),
            'estimated_time': '', 'sequence': 0,
            'completed': False, 'notes': f"LEVERANS {o.get('actual_knife_count') or o.get('estimated_knife_count','?')} knivar (planerad)",
            '_priority': 0,
            '_pickup_date': o.get('pickup',{}).get('completed_at') or o.get('created_at',''),
            '_knives': o.get('actual_knife_count') or o.get('estimated_knife_count', 0)
        })

    if not all_stops:
        return

    # Sort: deliveries first (by pickup date = urgency), then pickups
    all_stops.sort(key=lambda s: (s['_priority'], s.get('_pickup_date','')))

    # Hämta befintligt schema — bevara manuellt tilldelade stopp
    existing_schedule = load_json('schedule.json').get('schedule', [])

    # Hämta aktiva förare från users.json
    users_data = load_json('users.json')
    drivers = [u['name'].split(' ')[0].lower() for u in users_data.get('users', [])
               if u.get('active') and u.get('role') in ('admin', 'forare')]
    if not drivers:
        drivers = ['gustav', 'philip']

    # Filtrera bort stopp som redan finns i schemat (undvik dubbletter)
    existing_order_ids = set()
    for s in existing_schedule:
        for stop in s.get('stops', []):
            existing_order_ids.add(stop.get('order_id'))

    new_stops = [s for s in all_stops if s.get('order_id') not in existing_order_ids]

    if not new_stops:
        return

    # Group by area
    area_groups = {}
    for s in new_stops:
        area = s.get('area_id') or 'unknown'
        if area not in area_groups:
            area_groups[area] = []
        area_groups[area].append(s)

    # Fördela nya stopp bland tillgängliga förare (balanserat)
    driver_stops = {d: [] for d in drivers}
    # Räkna befintliga stopp per förare
    for s in existing_schedule:
        d = s.get('assigned_to', '')
        if d in driver_stops:
            driver_stops[d] = list(driver_stops.get(d, []))  # kopiera

    sorted_areas = sorted(area_groups.items(), key=lambda x: -len(x[1]))
    for area_id, stops in sorted_areas:
        # Tilldela till förare med minst stopp
        min_driver = min(drivers, key=lambda d: len(driver_stops.get(d, [])))
        driver_stops.setdefault(min_driver, []).extend(stops)

    # Bygg nytt schema — bevara befintliga + lägg till nya
    target_date = tomorrow if pickups else today
    schedules = list(existing_schedule)  # börja med befintliga

    for driver, stops in driver_stops.items():
        if not stops:
            continue
        # Clean internal fields and optimize order
        clean_stops = []
        for s in stops:
            cs = {k: v for k, v in s.items() if not k.startswith('_')}
            clean_stops.append(cs)

        optimized = nearest_neighbor_sort(clean_stops, HOME_BASE)
        for i, s in enumerate(optimized):
            s['sequence'] = i + 1

        total_time = len(optimized) * 20 + 15  # 20 min per stop + 15 min buffer

        # Kolla om föraren redan har en rutt för detta datum
        existing_route = next((s for s in schedules if s['date'] == target_date and s['assigned_to'] == driver), None)
        if existing_route:
            # Lägg till nya stopp i befintlig rutt
            existing_route['stops'].extend(optimized)
            for i, s in enumerate(existing_route['stops']):
                s['sequence'] = i + 1
            existing_route['estimated_total_time_min'] = len(existing_route['stops']) * 20 + 15
        else:
            schedules.append({
                'date': target_date,
                'assigned_to': driver,
                'stops': optimized,
                'estimated_total_time_min': total_time,
                'estimated_start': '16:00',
                'estimated_end': f"{16 + total_time // 60}:{total_time % 60:02d}",
                'notes': f"Auto-optimerad rutt: {len(optimized)} stopp"
            })

    save_json('schedule.json', {'schedule': schedules})
    print(f'[AUTO] Schema optimerat: {sum(len(s["stops"]) for s in schedules)} stopp, {len(schedules)} forare')


def handle_booking(data):
    """Skapar kund + order direkt vid bokning (inget pending-steg)."""
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip() or None
    address = data.get('address', '').strip()
    postnummer = data.get('postnummer', '').strip() or None
    stad = data.get('stad', '').strip() or 'Nacka'
    knives_str = data.get('knives', '3-5')
    preferred_date = data.get('preferred_date', '').strip()
    time_window = data.get('time_window', '').strip()
    message = data.get('message', '').strip()

    if not name or not phone or not address:
        return {'ok': False, 'error': 'Namn, telefon och adress krävs'}

    now_str = datetime.now().isoformat()
    source = data.get('source', 'hemsida')

    # Skapa kund direkt
    customers_data = load_json('customers.json')
    orders_data = load_json('orders.json')
    areas_data = load_json('areas.json')
    customers = customers_data.get('customers', [])
    orders = orders_data.get('orders', [])

    knife_map = {'1-2': 2, '3-5': 4, '6+': 7}
    knife_count = knife_map.get(knives_str, 4)

    # Matcha på telefon OCH namn
    existing = next((c for c in customers if phone and c.get('phone') == phone
                     and c.get('name', '').lower().strip() == name.lower().strip()
                     and not c.get('is_deleted')), None)

    if existing:
        customer_id = existing['id']
        print(f'[BOKNING] Befintlig kund: {name} ({customer_id})')
    else:
        customer_id = generate_id('CUS', [c['id'] for c in customers])
        area_id = detect_area(address, areas_data)
        new_customer = {
            'id': customer_id, 'name': name, 'phone': phone, 'email': email,
            'address': address, 'postnummer': postnummer, 'stad': stad,
            'area_id': area_id, 'source': source,
            'gdpr_consent': {'given': True, 'timestamp': now_str, 'method': source, 'notes': 'Samtycke via bokningsformulär'},
            'notes': message, 'created_at': now_str, 'updated_at': now_str, 'is_deleted': False
        }
        customers.append(new_customer)
        save_json('customers.json', {'customers': customers})
        print(f'[BOKNING] Ny kund: {name} ({customer_id})')

    # Skapa order direkt med status booked
    pickup_date = preferred_date or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    order_id = generate_id('ORD', [o['id'] for o in orders])
    new_order = {
        'id': order_id, 'customer_id': customer_id, 'status': 'booked',
        'status_history': [
            {'status': 'booked', 'timestamp': now_str, 'by': source}
        ],
        'source': source, 'estimated_knife_count': knife_count, 'actual_knife_count': None,
        'pickup': {'date': pickup_date, 'time_window': time_window or None, 'assigned_to': None, 'completed_at': None},
        'delivery': {'date': None, 'time_window': None, 'assigned_to': None, 'completed_at': None},
        'quality_check': {'passed': None, 'checked_by': None, 'timestamp': None, 'notes': None},
        'has_incident': False, 'incident_notes': None, 'invoice_id': None,
        'notes': message, 'created_at': now_str, 'updated_at': now_str
    }
    orders.append(new_order)
    save_json('orders.json', {'orders': orders})

    optimize_schedule()
    print(f'[BOKNING] Order: {order_id} för {name}, {knife_count} knivar')

    # Skicka notis
    send_notification({'id': order_id, 'name': name, 'phone': phone, 'address': address, 'knives': knives_str})

    return {'ok': True, 'booking_id': order_id, 'customer_id': customer_id, 'order_id': order_id}


def handle_review(data):
    """Tar emot ny recension fran hemsidan. Sparas med approved=false tills godkand."""
    name = (data.get('name') or '').strip()
    rating = data.get('rating')
    text = (data.get('text') or '').strip()
    city = (data.get('city') or '').strip()

    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return {'ok': False, 'error': 'Betyg saknas'}

    if not name or rating < 1 or rating > 5 or not text:
        return {'ok': False, 'error': 'Namn, betyg (1-5) och text kravs'}

    if len(text) > 1000:
        return {'ok': False, 'error': 'Texten ar for lang (max 1000 tecken)'}
    if len(name) > 60:
        name = name[:60]
    if len(city) > 60:
        city = city[:60]

    reviews_data = load_json('reviews.json')
    reviews = reviews_data.get('reviews', [])
    now_str = datetime.now().isoformat()
    review_id = generate_id('REV', [r['id'] for r in reviews])

    new_review = {
        'id': review_id,
        'name': name,
        'rating': rating,
        'text': text,
        'city': city or None,
        'approved': False,
        'created_at': now_str
    }
    reviews.append(new_review)
    save_json('reviews.json', {'reviews': reviews})
    print(f'[RECENSION] Ny recension fran {name} ({rating} stjarnor) — vantar godkannande')

    # ntfy-notis
    try:
        title = f'Ny recension: {name} ({rating}/5)'
        body = f'{text[:200]}{"..." if len(text) > 200 else ""}\n\nGodkann i admin.'
        req = Request(
            f'https://ntfy.sh/{NTFY_TOPIC}',
            data=body.encode('utf-8'),
            headers={
                'Title': title,
                'Tags': 'star,memo',
                'Priority': '3',
                'Click': 'https://knivkillarna.up.railway.app/admin',
            }
        )
        urlopen(req, timeout=5)
    except Exception as e:
        print(f'[NTFY] Recensionsnotis misslyckades: {e}')

    return {'ok': True, 'review_id': review_id}


def get_public_reviews():
    """Returnerar bara godkanda recensioner, nyaste forst."""
    reviews_data = load_json('reviews.json')
    reviews = [r for r in reviews_data.get('reviews', []) if r.get('approved')]
    reviews.sort(key=lambda r: r.get('created_at', ''), reverse=True)
    # Returnera bara publika falt
    public = [{
        'name': r['name'],
        'rating': r['rating'],
        'text': r['text'],
        'city': r.get('city'),
        'created_at': r.get('created_at', '')[:10]
    } for r in reviews]
    avg = round(sum(r['rating'] for r in reviews) / len(reviews), 1) if reviews else None
    return {'reviews': public, 'count': len(reviews), 'average': avg}


def send_notification(booking):
    """Push-notis via ntfy.sh när ny bokning kommer in."""
    try:
        title = f"Ny bokning: {booking['name']}"
        body = f"{booking.get('knives', '?')} knivar\n{booking['address']}\nTel: {booking['phone']}"
        req = Request(
            f'https://ntfy.sh/{NTFY_TOPIC}',
            data=body.encode('utf-8'),
            headers={
                'Title': title,
                'Tags': 'knife,incoming_envelope',
                'Priority': '4',
                'Click': 'https://knivkillarna.up.railway.app/admin',
            }
        )
        urlopen(req, timeout=5)
        print(f'[NTFY] Notis skickad for {booking["id"]}')
    except Exception as e:
        print(f'[NTFY] Kunde inte skicka notis: {e}')


def approve_booking(booking_id):
    """Approve a pending booking — creates customer + order."""
    bookings_data = load_json('bookings.json')
    bookings = bookings_data.get('bookings', [])
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    if not booking:
        return {'ok': False, 'error': 'Bokning hittades inte'}

    name = booking['name']
    phone = booking['phone']
    email = booking.get('email')
    address = booking['address']
    postnummer = booking.get('postnummer')
    stad = booking.get('stad', 'Nacka')
    knives_str = booking.get('knives', '3-5')
    preferred_date = booking.get('preferred_date')
    time_window = booking.get('time_window')
    message = booking.get('message', '')

    knife_map = {'1-2': 2, '3-5': 4, '6+': 7}
    knife_count = knife_map.get(knives_str, 4)

    customers_data = load_json('customers.json')
    orders_data = load_json('orders.json')
    areas_data = load_json('areas.json')
    customers = customers_data.get('customers', [])
    orders = orders_data.get('orders', [])

    # Matcha på telefon OCH namn — nytt namn = ny kund
    existing = next((c for c in customers if phone and c.get('phone') == phone
                     and c.get('name', '').lower().strip() == name.lower().strip()
                     and not c.get('is_deleted')), None)
    now_str = datetime.now().isoformat()

    if existing:
        customer_id = existing['id']
    else:
        customer_id = generate_id('CUS', [c['id'] for c in customers])
        area_id = detect_area(address, areas_data)
        new_customer = {
            'id': customer_id, 'name': name, 'phone': phone, 'email': email,
            'address': address, 'postnummer': postnummer, 'stad': stad,
            'area_id': area_id, 'source': booking.get('source', 'hemsida'),
            'gdpr_consent': {'given': True, 'timestamp': now_str, 'method': booking.get('source', 'hemsida'), 'notes': 'Samtycke via bokningsformular'},
            'notes': message, 'created_at': now_str, 'updated_at': now_str, 'is_deleted': False
        }
        customers.append(new_customer)
        save_json('customers.json', {'customers': customers})
        print(f'[GODKAND] Ny kund: {name} ({customer_id})')

    pickup_date = preferred_date or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    order_id = generate_id('ORD', [o['id'] for o in orders])
    new_order = {
        'id': order_id, 'customer_id': customer_id, 'status': 'booked',
        'status_history': [
            {'status': 'lead', 'timestamp': now_str, 'by': booking.get('source', 'hemsida')},
            {'status': 'booked', 'timestamp': now_str, 'by': booking.get('source', 'hemsida')}
        ],
        'source': booking.get('source', 'hemsida'), 'estimated_knife_count': knife_count, 'actual_knife_count': None,
        'pickup': {'date': pickup_date, 'time_window': time_window or None, 'assigned_to': None, 'completed_at': None},
        'delivery': {'date': None, 'time_window': None, 'assigned_to': None, 'completed_at': None},
        'quality_check': {'passed': None, 'checked_by': None, 'timestamp': None, 'notes': None},
        'has_incident': False, 'incident_notes': None, 'invoice_id': None,
        'notes': message, 'created_at': now_str, 'updated_at': now_str
    }
    orders.append(new_order)
    save_json('orders.json', {'orders': orders})

    # Remove from pending bookings
    booking['status'] = 'approved'
    save_json('bookings.json', {'bookings': bookings})

    optimize_schedule()
    print(f'[GODKAND] Order: {order_id} for {name}, {knife_count} knivar')

    return {'ok': True, 'customer_id': customer_id, 'order_id': order_id}


def create_order_for_customer(data):
    """Create a new order for an existing customer (from admin panel)."""
    customer_id = data.get('customer_id', '').strip()
    knives_str = data.get('knives', '3-5')
    preferred_date = data.get('preferred_date', '').strip()
    time_window = data.get('time_window', '').strip()
    notes = data.get('notes', '').strip()

    if not customer_id:
        return {'ok': False, 'error': 'customer_id saknas'}

    customers_data = load_json('customers.json')
    customers = customers_data.get('customers', [])
    customer = next((c for c in customers if c['id'] == customer_id and not c.get('is_deleted')), None)
    if not customer:
        return {'ok': False, 'error': 'Kund hittades inte'}

    knife_map = {'1-2': 2, '3-5': 4, '6+': 7}
    knife_count = knife_map.get(knives_str, 4)
    actual_knife_count = data.get('actual_knife_count')
    if actual_knife_count is not None:
        try:
            actual_knife_count = int(actual_knife_count)
        except (ValueError, TypeError):
            actual_knife_count = None
    price_per_knife = data.get('price_per_knife')
    if price_per_knife is not None:
        try:
            price_per_knife = int(price_per_knife)
        except (ValueError, TypeError):
            price_per_knife = None

    orders_data = load_json('orders.json')
    orders = orders_data.get('orders', [])
    now_str = datetime.now().isoformat()

    pickup_date = preferred_date or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    order_id = generate_id('ORD', [o['id'] for o in orders])

    # Calculate custom total if both actual count and price given
    custom_total = None
    if actual_knife_count and price_per_knife:
        custom_total = actual_knife_count * price_per_knife

    new_order = {
        'id': order_id, 'customer_id': customer_id, 'status': 'booked',
        'status_history': [
            {'status': 'booked', 'timestamp': now_str, 'by': 'admin'}
        ],
        'source': 'admin', 'estimated_knife_count': knife_count,
        'actual_knife_count': actual_knife_count or (actual_knife_count if actual_knife_count == 0 else None),
        'price_per_knife': price_per_knife, 'custom_total_price': custom_total,
        'pickup': {'date': pickup_date, 'time_window': time_window or None, 'assigned_to': None, 'completed_at': None},
        'delivery': {'date': None, 'time_window': None, 'assigned_to': None, 'completed_at': None},
        'quality_check': {'passed': None, 'checked_by': None, 'timestamp': None, 'notes': None},
        'has_incident': False, 'incident_notes': None, 'invoice_id': None,
        'notes': notes, 'created_at': now_str, 'updated_at': now_str
    }
    orders.append(new_order)
    save_json('orders.json', {'orders': orders})

    optimize_schedule()
    print(f'[NY ORDER] {order_id} for {customer["name"]} ({customer_id}), {knife_count} knivar')

    return {'ok': True, 'order_id': order_id}


class KnivslipHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        # Public reviews API
        if path == '/api/reviews':
            result = get_public_reviews()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return
        # Serve admin app
        if path == '/admin' or path == '/admin/':
            path = '/admin/admin.html'
        if path.startswith('/admin/'):
            filepath = os.path.join(APP_DIR, path[7:])  # strip '/admin/'
            if os.path.exists(filepath):
                self.send_response(200)
                if filepath.endswith('.html'):
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                elif filepath.endswith('.css'):
                    self.send_header('Content-Type', 'text/css')
                elif filepath.endswith('.js'):
                    self.send_header('Content-Type', 'application/javascript')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                return
            self.send_error(404)
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except:
            data = {}

        if path == '/api/booking':
            # New booking from website
            result = handle_booking(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif path == '/api/review':
            result = handle_review(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        elif path.startswith('/api/save/'):
            filename = path.split('/api/save/')[-1]
            if filename not in ALLOWED_FILES:
                self.send_error(403, 'Fil ej tillaten')
                return
            try:
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode())
            except Exception as e:
                self.send_error(500, str(e))

        elif path == '/api/approve':
            booking_id = data.get('booking_id')
            if not booking_id:
                self.send_error(400, 'booking_id saknas')
                return
            result = approve_booking(booking_id)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif path == '/api/create-order':
            result = create_order_for_customer(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        elif path == '/api/optimize':
            optimize_schedule()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())

        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    init_data()
    server = HTTPServer(('0.0.0.0', PORT), KnivslipHandler)
    print(f'')
    print(f'  KNIVSLIP SERVER')
    print(f'  ═══════════════')
    print(f'  Admin:   http://localhost:{PORT}/admin')
    print(f'  Hemsida: http://localhost:{PORT}/docs/index.html')
    print(f'  API:     http://localhost:{PORT}/api/booking')
    print(f'  Port:    {PORT}')
    print(f'')
    print(f'  Bokningar fran hemsidan skapar kund + order automatiskt.')
    print(f'  Tryck Ctrl+C for att stoppa.')
    print(f'')
    server.serve_forever()
