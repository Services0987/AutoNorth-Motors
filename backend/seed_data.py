"""Demo inventory data for AutoNorth Motors."""
from typing import List, Dict, Any


def _v(**kw) -> Dict[str, Any]:
    base = {
        "status": "available",
        "condition": "used",
        "transmission": "Automatic",
        "fuel_type": "Gas",
        "drivetrain": "AWD",
        "doors": 4,
        "seats": 5,
        "exterior_color": "Black",
        "interior_color": "Black",
        "features": [],
        "show_on_home": False,
        "featured": False,
    }
    base.update(kw)
    return base


def build_seed_vehicles() -> List[Dict[str, Any]]:
    img = lambda q: [
        f"https://images.unsplash.com/{q}?auto=format&fit=crop&w=1600&q=80",
    ]
    f150 = ["photo-1605559424843-9e4c228bf1c2", "photo-1502877338535-766e1452684a"]
    suv = ["photo-1568844293986-8d0400bd4745", "photo-1503376780353-7e6692767b70"]
    sedan = ["photo-1492144534655-ae79c964c9d7", "photo-1583121274602-3e2820c69888"]
    coupe = ["photo-1494976388531-d1058494cdd8", "photo-1542362567-b07e54358753"]
    ev = ["photo-1560958089-b8a1929cea89", "photo-1593941707882-a5bba14938c7"]

    seed = [
        _v(
            title="2023 Ford F-150 Lariat SuperCrew 4x4",
            make="Ford", model="F-150 Lariat", year=2023, price=64900, mileage=28450,
            body_type="Truck", fuel_type="Gas", drivetrain="4WD", doors=4, seats=5,
            vin="1FTFW1E84PFA12345", stock_number="AN24001",
            description="Premium Lariat trim with twin-panel moonroof, B&O sound, 360 camera, "
                        "tow package, and heated/cooled leather. Single owner, dealer-maintained.",
            features=["Moonroof", "B&O Premium Audio", "Heated/Cooled Leather", "Tow Package",
                      "360° Camera", "Adaptive Cruise", "Pro Power Onboard"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in f150],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2024 Ford Explorer ST Performance",
            make="Ford", model="Explorer ST", year=2024, price=72500, mileage=8200,
            body_type="SUV", fuel_type="Gas", drivetrain="AWD", seats=7,
            vin="1FM5K8GC1RGA22221", stock_number="AN24002",
            description="3.0L EcoBoost twin-turbo V6 producing 400 hp. ST Sport trim, captain's chairs, "
                        "panoramic roof, B&O 14-speaker sound system. Like new condition.",
            features=["400 HP Twin-Turbo", "Panoramic Roof", "Captain's Chairs", "B&O 14-Speaker",
                      "Heated/Cooled Front Seats", "Adaptive Cruise", "BLIS+"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2024 Ford Mustang GT Premium",
            make="Ford", model="Mustang GT", year=2024, price=68900, mileage=4100,
            body_type="Coupe", fuel_type="Gas", drivetrain="RWD", seats=4, doors=2,
            vin="1FA6P8CF6R5101010", stock_number="AN24003", exterior_color="Race Red",
            description="5.0L Coyote V8, 6-speed manual, Performance Package with MagneRide. "
                        "Recaro seats, B&O audio, active exhaust. A pure driver's car.",
            features=["5.0L V8 480HP", "6-Speed Manual", "Recaro Seats", "MagneRide",
                      "Active Exhaust", "Brembo Brakes", "Track Apps"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in coupe],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2023 Ford Mustang Mach-E GT",
            make="Ford", model="Mustang Mach-E GT", year=2023, price=58900, mileage=15800,
            body_type="SUV", fuel_type="Electric", drivetrain="AWD", seats=5,
            vin="3FMTK4SE8NMA90001", stock_number="AN24004",
            description="480 hp dual-motor EV with 480 km range. Glass roof, premium audio, "
                        "BlueCruise hands-free highway driving. Includes home charger.",
            features=["480 HP Dual Motor", "480 km Range", "Glass Roof", "BlueCruise 1.2",
                      "B&O 10-Speaker", "Heated Steering", "Wireless CarPlay"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in ev],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2022 Ford F-150 XLT SuperCrew",
            make="Ford", model="F-150 XLT", year=2022, price=49900, mileage=58200,
            body_type="Truck", fuel_type="Gas", drivetrain="4WD", doors=4,
            vin="1FTFW1E50NFA88888", stock_number="AN24005", exterior_color="Velocity Blue",
            description="3.5L EcoBoost V6, FX4 off-road package, trailer tow, spray-in liner. "
                        "Carfax verified single owner, all maintenance up to date.",
            features=["3.5L EcoBoost", "FX4 Off-Road", "Trailer Tow", "Spray-in Liner",
                      "Heated Seats", "SYNC 4", "Pro Trailer Backup"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in f150],
        ),
        _v(
            title="2023 Ford Bronco Sport Badlands",
            make="Ford", model="Bronco Sport", year=2023, price=41900, mileage=22100,
            body_type="SUV", fuel_type="Gas", drivetrain="4WD", seats=5,
            vin="3FMCR9D90PRA12345", stock_number="AN24006",
            description="Trail-ready Badlands trim with 7-mode GOAT system, locking rear diff, "
                        "and aggressive tires. Perfect Alberta adventure rig.",
            features=["GOAT Modes", "Locking Diff", "All-Terrain Tires", "Skid Plates",
                      "Heated Cloth", "SYNC 3", "FordPass Connect"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
            show_on_home=True,
        ),
        _v(
            title="2024 Ford Edge Titanium",
            make="Ford", model="Edge Titanium", year=2024, price=44500, mileage=12800,
            body_type="SUV", fuel_type="Gas", drivetrain="AWD", seats=5,
            vin="2FMPK4K94RBA55555", stock_number="AN24007",
            description="Titanium luxury trim with panoramic vista roof, 12-speaker B&O, "
                        "heated/cooled leather, and Co-Pilot360 Assist+ safety suite.",
            features=["Vista Panoramic Roof", "B&O 12-Speaker", "Heated/Cooled Leather",
                      "Co-Pilot360 Assist+", "Adaptive Cruise", "Lane Centering"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
        ),
        _v(
            title="2022 Ford Escape SE Hybrid",
            make="Ford", model="Escape SE Hybrid", year=2022, price=32900, mileage=41200,
            body_type="SUV", fuel_type="Hybrid", drivetrain="AWD", seats=5,
            vin="1FMCU0H66NUC11111", stock_number="AN24008",
            description="2.5L hybrid with 5.4L/100km combined. SYNC 3 with wireless CarPlay, "
                        "heated seats, and Co-Pilot360. Affordable, fuel-sipping family SUV.",
            features=["5.4L/100km", "Wireless CarPlay", "Heated Seats", "Co-Pilot360",
                      "Power Liftgate", "Backup Camera"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
        ),
        _v(
            title="2023 Ford Transit Connect Cargo",
            make="Ford", model="Transit Connect", year=2023, price=38900, mileage=24600,
            body_type="Van", fuel_type="Gas", drivetrain="FWD", seats=2, doors=4,
            vin="NM0LS7E26P1A22222", stock_number="AN24009", exterior_color="Oxford White",
            description="Work-ready cargo van with shelving package and partition. "
                        "Fleet-maintained, Carfax verified. Tools of the trade ready.",
            features=["Cargo Shelving", "Bulkhead Partition", "Backup Camera", "Cruise Control",
                      "Power Locks", "12V Outlets"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
        ),
        _v(
            title="2024 Ford F-250 Super Duty Lariat",
            make="Ford", model="F-250 Super Duty", year=2024, price=89900, mileage=11200,
            body_type="Truck", fuel_type="Diesel", drivetrain="4WD", seats=5,
            vin="1FT8W2BT9REA33333", stock_number="AN24010", exterior_color="Antimatter Blue",
            description="6.7L Power Stroke V8 turbo-diesel. Ultimate towing capability with "
                        "max-tow package, 5th wheel prep, and B&O audio. Heavy-duty luxury.",
            features=["6.7L Power Stroke", "Max Tow Package", "5th Wheel Prep", "B&O Premium",
                      "Heated/Cooled Leather", "360 Camera", "Trailer Tire Monitor"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in f150],
            featured=True,
        ),
        _v(
            title="2023 Ford Ranger Lariat FX4",
            make="Ford", model="Ranger Lariat", year=2023, price=46500, mileage=19800,
            body_type="Truck", fuel_type="Gas", drivetrain="4WD", seats=5,
            vin="1FTER4FH1PLA44444", stock_number="AN24011",
            description="Mid-size truck with 2.3L EcoBoost, FX4 off-road, leather, navigation, "
                        "and Trail Control. Perfect blend of capability and city-friendly size.",
            features=["FX4 Off-Road", "Trail Control", "Leather", "Navigation",
                      "Heated Seats", "Spray-in Liner", "Tow Package"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in f150],
        ),
        _v(
            title="2024 Ford Expedition Platinum Max",
            make="Ford", model="Expedition Platinum Max", year=2024, price=92500, mileage=6800,
            body_type="SUV", fuel_type="Gas", drivetrain="4WD", seats=8,
            vin="1FMJK1MT5REA55555", stock_number="AN24012", exterior_color="Star White",
            description="Top-tier Platinum Max trim with 8-passenger seating, panoramic roof, "
                        "22-speaker B&O Unleashed, massaging seats. The flagship family SUV.",
            features=["8-Passenger", "Panoramic Roof", "B&O 22-Speaker Unleashed",
                      "Massaging Seats", "ActiveGlide 1.2", "Power Running Boards", "Captain's Chairs"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2022 Ford Mustang Mach 1",
            make="Ford", model="Mustang Mach 1", year=2022, price=62900, mileage=18500,
            body_type="Coupe", fuel_type="Gas", drivetrain="RWD", seats=4, doors=2,
            vin="1FA6P8R03N5666666", stock_number="AN24013", exterior_color="Fighter Jet Gray",
            description="Track-inspired Mach 1 with 480 hp Coyote V8, Tremec 6-speed manual, "
                        "Handling Package with MagneRide. A modern muscle car icon.",
            features=["480 HP V8", "Tremec 6-Speed", "Handling Package", "MagneRide",
                      "Recaro Buckets", "Brembo Brakes", "Active Exhaust"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in coupe],
        ),
        _v(
            title="2023 Ford F-150 Lightning Lariat ER",
            make="Ford", model="F-150 Lightning", year=2023, price=78900, mileage=12400,
            body_type="Truck", fuel_type="Electric", drivetrain="4WD", seats=5,
            vin="1FT6W1EV5NWG77777", stock_number="AN24014",
            description="Electric F-150 with extended-range battery (515 km), 580 hp dual motor, "
                        "Pro Power Onboard 9.6kW, BlueCruise. The future of pickup trucks.",
            features=["515 km Range", "580 HP Dual Motor", "Pro Power 9.6kW", "BlueCruise",
                      "Mega Power Frunk", "Onboard Generator", "Tow 10,000 lb"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in ev],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2024 Ford Maverick Lariat Hybrid",
            make="Ford", model="Maverick Lariat", year=2024, price=39500, mileage=8900,
            body_type="Truck", fuel_type="Hybrid", drivetrain="FWD", seats=5,
            vin="3FTTW8E97RRA88888", stock_number="AN24015", exterior_color="Cactus Gray",
            description="Hybrid compact pickup with 5.4L/100km combined fuel economy. "
                        "Lariat Luxury package, FlexBed, and 1500 lb payload.",
            features=["5.4L/100km Hybrid", "Lariat Luxury", "FlexBed", "1500 lb Payload",
                      "Heated Leather", "B&O 8-Speaker", "Co-Pilot360"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in f150],
        ),
        _v(
            title="2021 Ford Edge ST",
            make="Ford", model="Edge ST", year=2021, price=37500, mileage=58900,
            body_type="SUV", fuel_type="Gas", drivetrain="AWD", seats=5,
            vin="2FMPK4AP9MBA99999", stock_number="AN24016",
            description="Performance-tuned Edge ST with 335 hp twin-turbo V6, sport-tuned "
                        "suspension, and Ford Performance brakes. Sporty family hauler.",
            features=["335 HP Twin-Turbo", "Sport Suspension", "Performance Brakes",
                      "Heated/Cooled Leather", "Panoramic Roof", "B&O 12-Speaker"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
        ),
        _v(
            title="2024 Ford Bronco Wildtrak 4-Door",
            make="Ford", model="Bronco Wildtrak", year=2024, price=72900, mileage=4500,
            body_type="SUV", fuel_type="Gas", drivetrain="4WD", seats=5,
            vin="1FMEE5DP8RLA00001", stock_number="AN24017", exterior_color="Eruption Green",
            description="2.7L EcoBoost V6, Sasquatch package with 35\" tires, electronic locking "
                        "diffs, and removable doors/roof. Ultimate Alberta off-roader.",
            features=["Sasquatch Package", "35\" Mud Tires", "Electronic Lockers", "Removable Doors",
                      "Removable Roof", "GOAT 7-Modes", "Trail Cameras"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
            featured=True, show_on_home=True,
        ),
        _v(
            title="2022 Ford Escape Titanium PHEV",
            make="Ford", model="Escape Titanium PHEV", year=2022, price=39900, mileage=28500,
            body_type="SUV", fuel_type="Hybrid", drivetrain="FWD", seats=5,
            vin="1FMCU0J90NUB11112", stock_number="AN24018",
            description="Plug-in hybrid with 60 km electric-only range plus gas backup. "
                        "Titanium luxury with B&O audio and panoramic roof.",
            features=["60 km EV Range", "Plug-in Hybrid", "B&O Premium", "Panoramic Roof",
                      "Heated Leather", "Active Park Assist", "Co-Pilot360"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in ev],
        ),
        _v(
            title="2023 Ford Transit 250 Medium Roof",
            make="Ford", model="Transit 250", year=2023, price=54900, mileage=22100,
            body_type="Van", fuel_type="Gas", drivetrain="RWD", seats=2,
            vin="1FTBR2X80PKA22223", stock_number="AN24019",
            description="Medium-roof cargo van with 148\" wheelbase. 3.5L EcoBoost, "
                        "interior shelving, partition, and ladder rack. Business-ready.",
            features=["3.5L EcoBoost", "Medium Roof", "148\" Wheelbase", "Interior Shelving",
                      "Bulkhead Partition", "Ladder Rack", "Backup Camera"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in suv],
        ),
        _v(
            title="2024 Ford Mustang Dark Horse Premium",
            make="Ford", model="Mustang Dark Horse", year=2024, price=84900, mileage=2100,
            body_type="Coupe", fuel_type="Gas", drivetrain="RWD", seats=4, doors=2,
            vin="1FA6P8R09R5333334", stock_number="AN24020", exterior_color="Blue Ember",
            description="500 hp track-bred Dark Horse with Tremec 6-speed, MagneRide, Brembos, "
                        "and Recaros. The most extreme road-going Mustang ever built.",
            features=["500 HP Coyote", "Tremec 6-Speed", "MagneRide", "Brembo Brakes",
                      "Recaro Buckets", "Track Cooling", "Performance Pack"],
            images=[f"https://images.unsplash.com/{i}?auto=format&fit=crop&w=1600&q=80" for i in coupe],
            featured=True, show_on_home=True,
        ),
    ]
    return seed
