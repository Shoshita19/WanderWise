from flask import Flask, render_template, request, jsonify
from database import connect_database, setup_database

app = Flask(__name__)


def destination_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "state": row["state"],
        "category": row["category"],
        "daily_cost": row["daily_cost"],
        "description": row["description"],
        "best_season": row["best_season"],
        "rating": row["rating"],
        "interests": row["interests"].split(","),
        "photo_url": row["photo_url"],
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/destinations")
def get_destinations():
    search = request.args.get("search", "").strip()
    interest = request.args.get("interest", "All").strip()
    max_budget = request.args.get("max_budget", "").strip()

    connection = connect_database()
    query = "SELECT * FROM destinations WHERE 1=1"
    parameters = []

    if search:
        query += " AND (name LIKE ? OR state LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        parameters.extend([term, term, term])

    if interest and interest != "All":
        query += " AND (interests LIKE ? OR category = ?)"
        parameters.extend([f"%{interest}%", interest])

    if max_budget:
        try:
            budget_value = max(0, int(max_budget))
            query += " AND daily_cost <= ?"
            parameters.append(budget_value)
        except ValueError:
            pass

    query += " ORDER BY rating DESC, daily_cost ASC"
    rows = connection.execute(query, parameters).fetchall()
    connection.close()
    return jsonify([destination_to_dict(row) for row in rows])


@app.route("/api/plan", methods=["POST"])
def create_plan():
    data = request.get_json(silent=True) or {}

    try:
        budget = int(data.get("budget", 0))
        days = int(data.get("days", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Please enter a valid budget and number of days."}), 400

    interest = str(data.get("interest", "Nature")).strip()
    if budget < 1000:
        return jsonify({"error": "Please enter a budget of at least ₹1,000."}), 400
    if days < 1 or days > 30:
        return jsonify({"error": "Choose a trip duration between 1 and 30 days."}), 400

    connection = connect_database()
    rows = connection.execute("""
        SELECT * FROM destinations
        WHERE interests LIKE ? OR category = ?
        ORDER BY rating DESC, daily_cost ASC
    """, (f"%{interest}%", interest)).fetchall()

    # If the selected interest has no exact match, show popular alternatives.
    if not rows:
        rows = connection.execute("""
            SELECT * FROM destinations ORDER BY rating DESC, daily_cost ASC
        """).fetchall()

    suggestions = []
    for row in rows:
        stay = connection.execute("""
            SELECT stay_name, stay_type, price_per_night
            FROM accommodations
            WHERE destination_id = ?
            ORDER BY price_per_night ASC LIMIT 1
        """, (row["id"],)).fetchone()

        transport = connection.execute("""
            SELECT transport_type, estimated_cost
            FROM transport_options
            WHERE destination_id = ?
            ORDER BY estimated_cost ASC LIMIT 1
        """, (row["id"],)).fetchone()

        activities = connection.execute("""
            SELECT activity_name, estimated_cost, duration_hours
            FROM activities WHERE destination_id = ?
            ORDER BY estimated_cost ASC
        """, (row["id"],)).fetchall()

        daily_expenses = row["daily_cost"] * days
        stay_cost = (stay["price_per_night"] * max(0, days - 1)) if stay else 0
        transport_cost = transport["estimated_cost"] if transport else 0
        activity_cost = sum(item["estimated_cost"] for item in activities[:min(days, len(activities))])
        miscellaneous = 150 * days
        total = daily_expenses + stay_cost + transport_cost + activity_cost + miscellaneous

        itinerary = []
        for day in range(days):
            activity = activities[day % len(activities)] if activities else None
            itinerary.append({
                "day": day + 1,
                "activity": activity["activity_name"] if activity else "Explore the destination at your own pace",
                "cost": activity["estimated_cost"] if activity else 0,
            })

        destination = destination_to_dict(row)
        destination.update({
            "daily_expenses": daily_expenses,
            "stay_name": stay["stay_name"] if stay else "Choose accommodation locally",
            "stay_cost": stay_cost,
            "transport_type": transport["transport_type"] if transport else "Check local transport",
            "transport_cost": transport_cost,
            "activity_cost": activity_cost,
            "miscellaneous": miscellaneous,
            "estimated_total": total,
            "remaining_budget": budget - total,
            "within_budget": total <= budget,
            "itinerary": itinerary,
        })
        suggestions.append(destination)

    # Prioritise destinations within budget, then lower estimated cost, then rating.
    suggestions.sort(key=lambda place: (not place["within_budget"], place["estimated_total"], -place["rating"]))
    suggestions = suggestions[:8]

    saved_plan_id = None
    if suggestions:
        chosen = suggestions[0]
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO travel_plans
            (budget, days, interest, destination_id, estimated_total)
            VALUES (?, ?, ?, ?, ?)
        """, (budget, days, interest, chosen["id"], chosen["estimated_total"]))
        saved_plan_id = cursor.lastrowid

        for item in chosen["itinerary"]:
            cursor.execute("""
                INSERT INTO itinerary_items (plan_id, day_number, activity_name, estimated_cost)
                VALUES (?, ?, ?, ?)
            """, (saved_plan_id, item["day"], item["activity"], item["cost"]))

        connection.commit()

    connection.close()
    return jsonify({
        "budget": budget,
        "days": days,
        "interest": interest,
        "saved_plan_id": saved_plan_id,
        "suggestions": suggestions,
    })


@app.route("/api/favorites", methods=["GET"])
def get_favorites():
    connection = connect_database()
    rows = connection.execute("""
        SELECT d.* FROM favorites f
        JOIN destinations d ON d.id = f.destination_id
        ORDER BY f.created_at DESC
    """).fetchall()
    connection.close()
    return jsonify([destination_to_dict(row) for row in rows])


@app.route("/api/favorites/<int:destination_id>", methods=["POST", "DELETE"])
def change_favorite(destination_id):
    connection = connect_database()
    exists = connection.execute(
        "SELECT id FROM destinations WHERE id = ?", (destination_id,)
    ).fetchone()

    if not exists:
        connection.close()
        return jsonify({"error": "Destination not found."}), 404

    if request.method == "POST":
        connection.execute(
            "INSERT OR IGNORE INTO favorites (destination_id) VALUES (?)",
            (destination_id,)
        )
        message = "Place saved to your favourites."
    else:
        connection.execute(
            "DELETE FROM favorites WHERE destination_id = ?", (destination_id,)
        )
        message = "Place removed from your favourites."

    connection.commit()
    connection.close()
    return jsonify({"message": message})


@app.route("/api/saved-plans")
def get_saved_plans():
    connection = connect_database()
    rows = connection.execute("""
        SELECT p.id, p.budget, p.days, p.interest, p.estimated_total,
               p.created_at, d.name AS destination_name, d.state AS state,
               d.photo_url AS photo_url
        FROM travel_plans p
        JOIN destinations d ON d.id = p.destination_id
        ORDER BY p.created_at DESC, p.id DESC
    """).fetchall()

    plans = []
    for row in rows:
        plans.append({
            "id": row["id"],
            "budget": row["budget"],
            "days": row["days"],
            "interest": row["interest"],
            "estimated_total": row["estimated_total"],
            "created_at": row["created_at"],
            "destination_name": row["destination_name"],
            "state": row["state"],
            "photo_url": row["photo_url"],
        })
    connection.close()
    return jsonify(plans)


@app.route("/api/saved-plans/<int:plan_id>", methods=["DELETE"])
def delete_saved_plan(plan_id):
    connection = connect_database()
    connection.execute("DELETE FROM itinerary_items WHERE plan_id = ?", (plan_id,))
    connection.execute("DELETE FROM travel_plans WHERE id = ?", (plan_id,))
    connection.commit()
    connection.close()
    return jsonify({"message": "Saved trip deleted."})


if __name__ == "__main__":
    setup_database()
    app.run(debug=True)
