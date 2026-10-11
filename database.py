import sqlite3

# A separate database file keeps the older project database safe.
DATABASE_NAME = "smart_travel_v2.db"


def connect_database():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def setup_database():
    connection = connect_database()
    cursor = connection.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            state TEXT NOT NULL,
            category TEXT NOT NULL,
            daily_cost INTEGER NOT NULL,
            description TEXT NOT NULL,
            best_season TEXT NOT NULL,
            rating REAL NOT NULL,
            interests TEXT NOT NULL,
            photo_url TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_id INTEGER NOT NULL,
            activity_name TEXT NOT NULL,
            estimated_cost INTEGER NOT NULL,
            duration_hours REAL NOT NULL,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        );

        CREATE TABLE IF NOT EXISTS accommodations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_id INTEGER NOT NULL,
            stay_name TEXT NOT NULL,
            stay_type TEXT NOT NULL,
            price_per_night INTEGER NOT NULL,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        );

        CREATE TABLE IF NOT EXISTS transport_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_id INTEGER NOT NULL,
            transport_type TEXT NOT NULL,
            estimated_cost INTEGER NOT NULL,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        );

        CREATE TABLE IF NOT EXISTS travel_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget INTEGER NOT NULL,
            days INTEGER NOT NULL,
            interest TEXT NOT NULL,
            destination_id INTEGER NOT NULL,
            estimated_total INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
        );

        CREATE TABLE IF NOT EXISTS itinerary_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            activity_name TEXT NOT NULL,
            estimated_cost INTEGER NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES travel_plans(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_id INTEGER NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (destination_id) REFERENCES destinations(id) ON DELETE CASCADE
        );
    """)

    # Seed sample destinations only when the table is empty.
    count = cursor.execute("SELECT COUNT(*) FROM destinations").fetchone()[0]
    if count == 0:
        destinations = [
            ("Mysuru", "Karnataka", "Historical", 1100, "A relaxed city known for its palace, markets and local food.", "October to March", 4.7, "History,Family,Food,Shopping", "https://images.unsplash.com/photo-1600100397608-f010d2a1d1d5?auto=format&fit=crop&w=1000&q=80"),
            ("Coorg", "Karnataka", "Nature", 1500, "Green coffee estates, misty hills, waterfalls and peaceful homestays.", "October to March", 4.8, "Nature,Adventure,Family", "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1000&q=80"),
            ("Gokarna", "Karnataka", "Beach", 1200, "A laid-back coastal town with beaches, sunset walks and simple cafes.", "October to March", 4.5, "Beach,Nature,Food,Adventure", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1000&q=80"),
            ("Hampi", "Karnataka", "Historical", 1000, "Explore ancient ruins, rocky landscapes and fascinating heritage sites.", "November to February", 4.8, "History,Adventure,Photography", "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1000&q=80"),
            ("Ooty", "Tamil Nadu", "Nature", 1600, "A cool hill station with gardens, viewpoints and a scenic toy train.", "October to June", 4.5, "Nature,Family,Adventure,Food", "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=80"),
            ("Goa", "Goa", "Beach", 1800, "Enjoy sandy beaches, colourful streets, local markets and coastal food.", "November to February", 4.6, "Beach,Food,Shopping,Adventure,Nightlife", "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=1000&q=80"),
            ("Rishikesh", "Uttarakhand", "Adventure", 1400, "A riverside destination for rafting, yoga, walks and mountain views.", "September to April", 4.6, "Adventure,Nature,Food,Family", "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1000&q=80"),
            ("Jaipur", "Rajasthan", "Historical", 1500, "Discover forts, palaces, colourful bazaars and Rajasthani cuisine.", "October to March", 4.7, "History,Food,Shopping,Family", "https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=1000&q=80"),
            ("Kochi", "Kerala", "Food", 1600, "A coastal city with heritage lanes, waterfront views and tasty local food.", "October to March", 4.5, "History,Food,Shopping,Nature", "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1000&q=80"),
            ("Pondicherry", "Puducherry", "Beach", 1500, "Relax by the sea, walk through colourful French-style streets and visit cafes.", "October to March", 4.5, "Beach,Food,History,Shopping,Family", "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?auto=format&fit=crop&w=1000&q=80"),
            ("Munnar", "Kerala", "Nature", 1700, "Tea gardens, cool weather and beautiful green mountain scenery.", "September to March", 4.7, "Nature,Family,Photography", "https://images.unsplash.com/photo-1494783367193-149034c05e8f?auto=format&fit=crop&w=1000&q=80"),
            ("Manali", "Himachal Pradesh", "Adventure", 2200, "A mountain escape with valleys, snow-season views and outdoor activities.", "March to June, December to February", 4.6, "Adventure,Nature,Family,Photography", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1000&q=80"),
            ("Delhi", "Delhi", "Historical", 1700, "Explore famous monuments, museums, street markets and food streets.", "October to March", 4.4, "History,Food,Shopping,Family", "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1000&q=80"),
            ("Udaipur", "Rajasthan", "Historical", 1800, "A lakeside city with palaces, old streets and beautiful sunset views.", "September to March", 4.7, "History,Nature,Food,Photography", "https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?auto=format&fit=crop&w=1000&q=80"),
            ("Lucknow", "Uttar Pradesh", "Food", 1200, "A welcoming city known for its architecture, markets and famous cuisine.", "October to March", 4.5, "Food,History,Shopping,Family", "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?auto=format&fit=crop&w=1000&q=80"),
            ("Varkala", "Kerala", "Beach", 1400, "Cliffside sea views, beach walks, cafes and relaxed coastal days.", "October to March", 4.6, "Beach,Nature,Food,Adventure", "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1000&q=80"),
            ("Kaziranga", "Assam", "Nature", 2000, "A wildlife destination known for grasslands, birds and guided safaris.", "November to April", 4.6, "Wildlife,Nature,Photography,Family", "https://images.unsplash.com/photo-1511497584788-876760111969?auto=format&fit=crop&w=1000&q=80"),
            ("Amritsar", "Punjab", "Historical", 1300, "Visit important heritage sites and enjoy the city's rich food culture.", "October to March", 4.6, "History,Food,Family,Shopping", "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?auto=format&fit=crop&w=1000&q=80"),
            ("Shillong", "Meghalaya", "Nature", 1700, "Rolling green hills, waterfalls, music and scenic drives.", "October to April", 4.5, "Nature,Adventure,Food,Photography", "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1000&q=80"),
            ("Agra", "Uttar Pradesh", "Historical", 1400, "See iconic Mughal architecture, local craft shops and gardens.", "October to March", 4.5, "History,Food,Shopping,Family", "https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1000&q=80"),
            ("Pune", "Maharashtra", "Food", 1300, "A lively city with historic forts nearby, cafes and street food.", "October to February", 4.3, "Food,History,Shopping,Nature", "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1000&q=80"),
            ("Andaman Islands", "Andaman and Nicobar Islands", "Beach", 2800, "Clear water, coral views and island beaches for a special getaway.", "November to April", 4.8, "Beach,Nature,Adventure,Wildlife", "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?auto=format&fit=crop&w=1000&q=80"),
        ]

        cursor.executemany("""
            INSERT INTO destinations
            (name, state, category, daily_cost, description, best_season, rating, interests, photo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, destinations)

        activity_templates = {
            "Historical": [("Visit heritage landmarks", 100, 2), ("Explore local markets", 150, 2), ("Try a local food walk", 250, 2)],
            "Nature": [("Visit a scenic viewpoint", 100, 2), ("Take a nature walk", 150, 2), ("Explore a garden or waterfall", 200, 3)],
            "Beach": [("Enjoy a beach walk", 0, 2), ("Watch the sunset", 0, 1), ("Try a local cafe", 250, 2)],
            "Adventure": [("Explore the outdoors", 150, 2), ("Visit a viewpoint", 100, 2), ("Try a guided activity", 500, 3)],
            "Food": [("Try local breakfast", 150, 1), ("Explore a food street", 250, 2), ("Visit a local market", 100, 2)],
        }

        destination_rows = cursor.execute("SELECT id, category, daily_cost FROM destinations").fetchall()
        for destination in destination_rows:
            category = destination["category"]
            base_cost = destination["daily_cost"]
            activities = activity_templates.get(category, activity_templates["Nature"])
            for activity_name, cost, duration in activities:
                cursor.execute("""
                    INSERT INTO activities
                    (destination_id, activity_name, estimated_cost, duration_hours)
                    VALUES (?, ?, ?, ?)
                """, (destination["id"], activity_name, cost, duration))

            # These are sample prices, not live accommodation quotes.
            cursor.executemany("""
                INSERT INTO accommodations
                (destination_id, stay_name, stay_type, price_per_night)
                VALUES (?, ?, ?, ?)
            """, [
                (destination["id"], "Simple guesthouse", "Budget", max(250, int(base_cost * 0.25))),
                (destination["id"], "Local homestay", "Homestay", max(400, int(base_cost * 0.40))),
                (destination["id"], "Comfort hotel", "Standard", max(800, int(base_cost * 0.75))),
            ])

            # Transport figures are illustrative local/trip allowances. Actual fares depend on origin.
            cursor.executemany("""
                INSERT INTO transport_options
                (destination_id, transport_type, estimated_cost)
                VALUES (?, ?, ?)
            """, [
                (destination["id"], "Public transport allowance", max(100, int(base_cost * 0.20))),
                (destination["id"], "Shared cab allowance", max(250, int(base_cost * 0.40))),
            ])

    connection.commit()
    connection.close()


if __name__ == "__main__":
    setup_database()
    print("WanderWise database is ready.")