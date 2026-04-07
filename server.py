#!/usr/bin/env python3
"""Knivslip server — hemsida + API + automatisk bokning."""

import json
import os
import math
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.environ.get('PORT', 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
APP_DIR = os.path.join(BASE_DIR, 'app')
ALLOWED_FILES = ['users.json', 'timelog.json', 'customers.json', 'orders.json',
                 'knives.json', 'invoices.json', 'transactions.json', 'schedule.json',
                 'pricing.json', 'areas.json', 'legal.json']

# Template for empty data files (created on first run if missing)
DATA_TEMPLATES = {
    'customers.json': {'customers': []},
    'orders.json': {'orders': []},
    'knives.json': {'knives': []},
    'invoices.json': {'invoices': []},
    'transactions.json': {'transactions': []},
    'schedule.json': {'schedule': []},
    'timelog.json': {'entries': []},
    'pricing.json': {'pricing': {'currency': 'SEK', 'vat_rate': 0.25, 'last_updated': '2026-04-06', 'price_tiers': [{'min_knives': 1, 'max_knives': 2, 'price_incl_vat': 170, 'price_excl_vat': 136, 'description': '1-2 knivar: 170 kr/st'}, {'min_knives': 3, 'max_knives': 5, 'price_incl_vat': 140, 'price_excl_vat': 112, 'description': '3-5 knivar: 140 kr/st'}, {'min_knives': 6, 'max_knives': 999, 'price_incl_vat': 120, 'price_excl_vat': 96, 'description': '6+ knivar: 120 kr/st'}], 'minimum_order': 0, 'pickup_fee': 0}},
    'areas.json': {'areas': [{'id': 'AREA-NACKA-C', 'name': 'Nacka centrum/Sickla', 'postnummer_prefix': ['131']}, {'id': 'AREA-NACKA-SALTSJOBADEN', 'name': 'Saltsjobaden/Fisksatra', 'postnummer_prefix': ['133']}, {'id': 'AREA-NACKA-BOO', 'name': 'Boo/Orminge', 'postnummer_prefix': ['132']}, {'id': 'AREA-VARMDO-C', 'name': 'Gustavsberg', 'postnummer_prefix': ['134']}], 'home_base': 'AREA-NACKA-C'},
    'users.json': {'users': [
        {'id': 'USR-001', 'name': 'Gustav Granberg', 'pin': '9680', 'role': 'admin', 'active': True, 'pay_type': None, 'pay_rate': None, 'created_at': '2026-04-06T00:00:00'},
        {'id': 'USR-002', 'name': 'Philip Zetterlund', 'pin': '6769', 'role': 'admin', 'active': True, 'pay_type': None, 'pay_rate': None, 'created_at': '2026-04-06T00:00:00'},
        {'id': 'USR-003', 'name': 'Adam Zetterlund', 'pin': '1111', 'role': 'slipare', 'active': True, 'pay_type': 'per_knife', 'pay_rate': 30, 'created_at': '2026-04-06T00:00:00'}
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

HOME_BASE = [59.3107, 18.1268]  # Klostervagen 6, Nacka

# Address → coordinates (approximate)
COORD_MAP = {
    'klostervagen': [59.3107, 18.1268],
    'sickla': [59.3055, 18.1235],
    'varmdovagen': [59.3100, 18.1420],
    'saltsjobadsvagen': [59.2850, 18.1600],
    'ormingeringen': [59.3250, 18.2100],
    'fisksatravagen': [59.2900, 18.1500],
    'gustavsberg': [59.3270, 18.3950],
    'nacka': [59.3107, 18.1268],
    'saltsjobaden': [59.2850, 18.1600],
    'boo': [59.3250, 18.2100],
    'orminge': [59.3250, 18.2100],
}

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def coords_for_address(addr):
    clean = addr.lower().replace('å','a').replace('ä','a').replace('ö','o').replace('é','e')
    for key, val in COORD_MAP.items():
        if key in clean:
            return val
    # Fallback: hash-based offset from Nacka center
    h = sum(ord(c) for c in addr)
    return [59.31 + (h % 50) * 0.0003, 18.14 + (h % 70) * 0.0004]

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

    if not deliveries and not pickups:
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
            'address': f"{c['address']}, {c.get('postnummer','')} {c.get('stad','Nacka')}".strip(', '),
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
            'address': f"{c['address']}, {c.get('postnummer','')} {c.get('stad','Nacka')}".strip(', '),
            'area_id': c.get('area_id') or detect_area(c.get('address',''), areas_data),
            'time_window': o.get('pickup',{}).get('time_window',''),
            'estimated_time': '', 'sequence': 0,
            'completed': False, 'notes': f"HAMTNING {o.get('estimated_knife_count','?')} knivar",
            '_priority': 1,
            '_pickup_date': '',
            '_knives': o.get('estimated_knife_count', 0)
        })

    if not all_stops:
        return

    # Sort: deliveries first (by pickup date = urgency), then pickups
    all_stops.sort(key=lambda s: (s['_priority'], s.get('_pickup_date','')))

    # Split between 2 drivers by area clustering
    gustav_stops = []
    philip_stops = []

    # Group by area
    area_groups = {}
    for s in all_stops:
        area = s.get('area_id') or 'unknown'
        if area not in area_groups:
            area_groups[area] = []
        area_groups[area].append(s)

    # Assign areas to drivers alternately, balancing stop count
    sorted_areas = sorted(area_groups.items(), key=lambda x: -len(x[1]))
    for area_id, stops in sorted_areas:
        if len(gustav_stops) <= len(philip_stops):
            gustav_stops.extend(stops)
        else:
            philip_stops.extend(stops)

    # If one driver has no stops, don't create empty schedule
    schedules = []
    target_date = tomorrow if pickups else today

    for driver, stops in [('gustav', gustav_stops), ('philip', philip_stops)]:
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
    """Process a new booking from the website form."""
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
        return {'ok': False, 'error': 'Namn, telefon och adress kravs'}

    # Estimate knife count from tier
    knife_map = {'1-2': 2, '3-5': 4, '6+': 7}
    knife_count = knife_map.get(knives_str, 4)

    # Load data
    customers_data = load_json('customers.json')
    orders_data = load_json('orders.json')
    areas_data = load_json('areas.json')

    customers = customers_data.get('customers', [])
    orders = orders_data.get('orders', [])

    # Check if customer already exists (by phone)
    existing = next((c for c in customers if c.get('phone') == phone), None)

    now_str = datetime.now().isoformat()

    if existing:
        customer_id = existing['id']
    else:
        # Create new customer
        customer_id = generate_id('CUS', [c['id'] for c in customers])
        area_id = detect_area(address, areas_data)
        new_customer = {
            'id': customer_id, 'name': name, 'phone': phone, 'email': email,
            'address': address, 'postnummer': postnummer, 'stad': stad,
            'area_id': area_id, 'source': 'hemsida',
            'gdpr_consent': {'given': True, 'timestamp': now_str, 'method': 'hemsida', 'notes': 'Samtycke via bokningsformular'},
            'notes': message, 'created_at': now_str, 'updated_at': now_str, 'is_deleted': False
        }
        customers.append(new_customer)
        save_json('customers.json', {'customers': customers})
        print(f'[AUTO] Ny kund: {name} ({customer_id})')

    # Create order
    pickup_date = preferred_date or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    order_id = generate_id('ORD', [o['id'] for o in orders])
    new_order = {
        'id': order_id, 'customer_id': customer_id, 'status': 'booked',
        'status_history': [
            {'status': 'lead', 'timestamp': now_str, 'by': 'hemsida'},
            {'status': 'booked', 'timestamp': now_str, 'by': 'hemsida'}
        ],
        'source': 'hemsida', 'estimated_knife_count': knife_count, 'actual_knife_count': None,
        'pickup': {'date': pickup_date, 'time_window': time_window or None, 'assigned_to': None, 'completed_at': None},
        'delivery': {'date': None, 'time_window': None, 'assigned_to': None, 'completed_at': None},
        'quality_check': {'passed': None, 'checked_by': None, 'timestamp': None, 'notes': None},
        'has_incident': False, 'incident_notes': None, 'invoice_id': None,
        'notes': message, 'created_at': now_str, 'updated_at': now_str
    }
    orders.append(new_order)
    save_json('orders.json', {'orders': orders})
    print(f'[AUTO] Ny order: {order_id} for {name}, {knife_count} knivar, hamtning {pickup_date}')

    # Auto-optimize schedule
    optimize_schedule()

    return {'ok': True, 'customer_id': customer_id, 'order_id': order_id}


class KnivslipHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
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
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

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
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode())
            except Exception as e:
                self.send_error(500, str(e))

        elif path == '/api/optimize':
            optimize_schedule()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())

        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
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
