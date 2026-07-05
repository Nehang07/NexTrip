"""
Mock inventory for the Flights, Hotels, and Buses/Trains booking modules.
Generated deterministically (fixed random seed) so the same data appears
every time the database is freshly seeded. Airline names are real (for
realism); hotel names are invented so nothing implies a real property
is bookable through this demo.
"""
import random

random.seed(42)

# ---------------------------------------------------------------------------
# Cities (used across flights + hotels)
# ---------------------------------------------------------------------------
CITIES = [
    dict(code="DEL", name="Delhi", country="India"),
    dict(code="BOM", name="Mumbai", country="India"),
    dict(code="BLR", name="Bangalore", country="India"),
    dict(code="MAA", name="Chennai", country="India"),
    dict(code="CCU", name="Kolkata", country="India"),
    dict(code="GOI", name="Goa", country="India"),
    dict(code="JAI", name="Jaipur", country="India"),
    dict(code="SYD", name="Sydney", country="Australia"),
    dict(code="LON", name="London", country="London"),
    dict(code="PAR", name="Paris", country="France"),
    dict(code="BKK", name="Bangkok", country="Thailand"),
]

DOMESTIC_AIRLINES = ["IndiGo", "Air India", "Vistara", "SpiceJet", "Akasa Air"]
INTERNATIONAL_AIRLINES = ["Emirates", "Qantas", "British Airways", "Air France", "Thai Airways", "Singapore Airlines"]

# Curated routes: (origin_code, destination_code, is_international, base_price_inr, duration_mins)
ROUTES = [
    ("DEL", "BOM", False, 4500, 130), ("BOM", "DEL", False, 4600, 130),
    ("DEL", "BLR", False, 5200, 165), ("BLR", "DEL", False, 5100, 165),
    ("DEL", "GOI", False, 5800, 150), ("GOI", "DEL", False, 5700, 150),
    ("BOM", "GOI", False, 3200, 70), ("GOI", "BOM", False, 3100, 70),
    ("DEL", "JAI", False, 2800, 60), ("JAI", "DEL", False, 2700, 60),
    ("BOM", "BLR", False, 3900, 95), ("BLR", "BOM", False, 3800, 95),
    ("DEL", "MAA", False, 5600, 170), ("MAA", "DEL", False, 5500, 170),
    ("BOM", "CCU", False, 5900, 145), ("CCU", "BOM", False, 5800, 145),
    ("DEL", "SYD", True, 62000, 780), ("SYD", "DEL", True, 63000, 800),
    ("DEL", "LON", True, 48000, 570), ("LON", "DEL", True, 47000, 560),
    ("BOM", "LON", True, 45000, 555), ("LON", "BOM", True, 46000, 565),
    ("DEL", "PAR", True, 51000, 590), ("PAR", "DEL", True, 50500, 600),
    ("BOM", "BKK", True, 26000, 275), ("BKK", "BOM", True, 25500, 270),
    ("DEL", "BKK", True, 24000, 260), ("BKK", "DEL", True, 23500, 265),
    ("LON", "PAR", True, 12000, 90), ("PAR", "LON", True, 11800, 90),
    ("SYD", "BKK", True, 34000, 545), ("BKK", "SYD", True, 34500, 555),
]


def _fmt_time(minutes_from_midnight):
    h = (minutes_from_midnight // 60) % 24
    m = minutes_from_midnight % 60
    return f"{h:02d}:{m:02d}"


def generate_flights():
    flights = []
    fid = 1
    for origin, dest, intl, base_price, duration in ROUTES:
        airlines = INTERNATIONAL_AIRLINES if intl else DOMESTIC_AIRLINES
        num_options = 3 if not intl else 2
        for i in range(num_options):
            airline = random.choice(airlines)
            depart_minutes = random.choice([360, 480, 600, 720, 840, 960, 1080, 1200, 1320])
            arrive_minutes = (depart_minutes + duration) % 1440
            price = base_price + random.randint(-400, 1200) + i * 350
            flights.append(dict(
                id=fid, airline=airline, flight_number=f"{airline[:2].upper()}{random.randint(100,999)}",
                origin=origin, destination=dest, depart_time=_fmt_time(depart_minutes),
                arrive_time=_fmt_time(arrive_minutes), duration_mins=duration,
                price=max(price, 1500), seats_available=random.randint(3, 42),
                cabin_class="Economy", is_international=intl,
            ))
            fid += 1
    return flights


HOTEL_NAME_PARTS_A = ["Grand", "Royal", "Golden", "Silver", "The Palm", "Emerald", "Azure", "Heritage", "Sunset", "Riverside", "Hilltop", "Crescent", "Lotus", "Meridian", "Coral"]
HOTEL_NAME_PARTS_B = ["Palace", "Residency", "Inn", "Suites", "Resort & Spa", "Boutique Hotel", "Grand Hotel", "Retreat", "Manor", "Court"]

HOTEL_IMAGES = [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&auto=format&fit=crop&q=75",
    "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&auto=format&fit=crop&q=75",
    "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600&auto=format&fit=crop&q=75",
    "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=600&auto=format&fit=crop&q=75",
    "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=600&auto=format&fit=crop&q=75",
    "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=600&auto=format&fit=crop&q=75",
]

AMENITY_SETS = [
    ["Free WiFi", "Breakfast Included", "Pool", "Parking"],
    ["Free WiFi", "Spa", "Gym", "Airport Shuttle"],
    ["Free WiFi", "Restaurant", "Bar", "Room Service"],
    ["Free WiFi", "Pool", "Gym", "Business Center"],
]


def generate_hotels():
    hotels = []
    hid = 1
    for city in CITIES:
        tiers = [
            (2, 2500, 4500),   # budget: 2-star
            (4, 5500, 9500),   # mid: 4-star
            (5, 11000, 22000), # luxury: 5-star
        ]
        for star, low, high in tiers:
            name = f"{random.choice(HOTEL_NAME_PARTS_A)} {random.choice(HOTEL_NAME_PARTS_B)}"
            hotels.append(dict(
                id=hid, name=name, city=city["name"], country=city["country"],
                star_rating=star, price_per_night=random.randint(low, high),
                rating=round(random.uniform(3.9, 4.9), 1), reviews_count=random.randint(80, 3200),
                amenities=random.choice(AMENITY_SETS), img=random.choice(HOTEL_IMAGES),
                address=f"Near City Center, {city['name']}",
            ))
            hid += 1
    return hotels


BUS_OPERATORS = ["NexTrip Express", "Highway King Travels", "Royal Cruiser", "Volvo Prime", "Sundar Travels", "Comfort Line"]
BUS_TYPES = ["AC Sleeper", "AC Seater (2+2)", "Non-AC Seater", "Volvo Multi-Axle AC"]

# Domestic India routes only — buses/trains don't cross oceans.
BUS_ROUTES = [
    ("Delhi", "Jaipur", 280, 5.5), ("Jaipur", "Delhi", 270, 5.5),
    ("Mumbai", "Goa", 590, 11), ("Goa", "Mumbai", 590, 11),
    ("Bangalore", "Chennai", 350, 6.5), ("Chennai", "Bangalore", 350, 6.5),
    ("Delhi", "Agra", 230, 4), ("Agra", "Delhi", 230, 4),
    ("Mumbai", "Pune", 150, 3.5), ("Pune", "Mumbai", 150, 3.5),
    ("Delhi", "Chandigarh", 250, 5), ("Chandigarh", "Delhi", 250, 5),
    ("Bangalore", "Goa", 560, 10), ("Goa", "Bangalore", 560, 10),
    ("Kolkata", "Delhi", 190, 4), ("Delhi", "Kolkata", 190, 4),  # train-length flight substitute skipped; kept short for demo
]


def generate_buses():
    buses = []
    bid = 1
    for origin, dest, price_base, duration_hrs in BUS_ROUTES:
        num_options = 3
        for i in range(num_options):
            operator = random.choice(BUS_OPERATORS)
            bus_type = random.choice(BUS_TYPES)
            depart_minutes = random.choice([1260, 1320, 1350, 1380, 420, 480])  # evening or early-morning departures
            duration_mins = int(duration_hrs * 60) + random.randint(-20, 40)
            arrive_minutes = (depart_minutes + duration_mins) % 1440
            price = price_base + random.randint(-100, 400) + (i * 150 if "AC" in bus_type else 0)
            buses.append(dict(
                id=bid, operator=operator, bus_type=bus_type, origin=origin, destination=dest,
                depart_time=_fmt_time(depart_minutes), arrive_time=_fmt_time(arrive_minutes),
                duration_mins=duration_mins, price=max(price, 300),
                seats_available=random.randint(4, 38),
            ))
            bid += 1
    return buses
