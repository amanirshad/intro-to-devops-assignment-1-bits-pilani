from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# ── Fitness Programs Data ──────────────────────────────────────────────
PROGRAMS = {
    "fat_loss": {
        "name": "Fat Loss (FL)",
        "workout": (
            "Mon: Back Squat 5x5 + Core\n"
            "Tue: EMOM 20min Assault Bike\n"
            "Wed: Bench Press + 21-15-9\n"
            "Thu: Deadlift + Box Jumps\n"
            "Fri: Zone 2 Cardio 30min"
        ),
        "diet": (
            "Breakfast: Egg Whites + Oats\n"
            "Lunch: Grilled Chicken + Brown Rice\n"
            "Dinner: Fish Curry + Millet Roti\n"
            "Target: ~2000 kcal"
        ),
        "calorie_factor": 22,
    },
    "muscle_gain": {
        "name": "Muscle Gain (MG)",
        "workout": (
            "Mon: Squat 5x5\n"
            "Tue: Bench 5x5\n"
            "Wed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\n"
            "Fri: Incline Press 4x10\n"
            "Sat: Barbell Rows 4x10"
        ),
        "diet": (
            "Breakfast: Eggs + Peanut Butter Oats\n"
            "Lunch: Chicken Biryani\n"
            "Dinner: Mutton Curry + Rice\n"
            "Target: ~3200 kcal"
        ),
        "calorie_factor": 35,
    },
    "beginner": {
        "name": "Beginner (BG)",
        "workout": (
            "Full Body Circuit:\n"
            "- Air Squats\n"
            "- Ring Rows\n"
            "- Push-ups\n"
            "Focus: Technique & Consistency"
        ),
        "diet": (
            "Balanced Meals: Idli / Dosa / Rice + Dal\n"
            "Protein Target: 120g/day"
        ),
        "calorie_factor": 26,
    },
}

# In-memory member store
members = []


# ── Helper functions ───────────────────────────────────────────────────
def calculate_calories(weight: float, program_key: str) -> int:
    """Return daily calorie target based on weight and program factor."""
    program = PROGRAMS.get(program_key)
    if program is None:
        raise ValueError(f"Unknown program: {program_key}")
    if weight <= 0:
        raise ValueError("Weight must be positive")
    return int(weight * program["calorie_factor"])


def calculate_bmi(weight: float, height_cm: float) -> float:
    """Return BMI given weight (kg) and height (cm)."""
    if height_cm <= 0:
        raise ValueError("Height must be positive")
    if weight <= 0:
        raise ValueError("Weight must be positive")
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)


def bmi_category(bmi: float) -> str:
    """Return the BMI category string."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    return "Obese"


# ── HTML template ──────────────────────────────────────────────────────
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ACEest Fitness & Gym</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #eee; margin: 0; }
        .header { background: #d4af37; color: #000; text-align: center; padding: 20px; }
        .container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
        .card { background: #2a2a2a; border-radius: 8px; padding: 20px; margin: 15px 0; }
        .card h3 { color: #d4af37; }
        a { color: #d4af37; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ACEest Functional Fitness & Gym</h1>
        <p>Your path to peak performance</p>
    </div>
    <div class="container">
        <div class="card">
            <h3>API Endpoints</h3>
            <ul>
                <li><a href="/programs">/programs</a> – List all fitness programs</li>
                <li><a href="/programs/fat_loss">/programs/&lt;key&gt;</a> – Program details</li>
                <li>/calculate/calories (POST) – Daily calorie estimate</li>
                <li>/calculate/bmi (POST) – BMI calculator</li>
                <li><a href="/members">/members</a> – Member list</li>
            </ul>
        </div>
        <div class="card">
            <h3>Available Programs</h3>
            <ul>
            {% for key, prog in programs.items() %}
                <li><a href="/programs/{{ key }}">{{ prog.name }}</a></li>
            {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""


# ── Routes ─────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE, programs=PROGRAMS)


@app.route("/programs")
def list_programs():
    result = {}
    for key, prog in PROGRAMS.items():
        result[key] = {"name": prog["name"], "calorie_factor": prog["calorie_factor"]}
    return jsonify(result)


@app.route("/programs/<program_key>")
def get_program(program_key):
    program = PROGRAMS.get(program_key)
    if program is None:
        return jsonify({"error": "Program not found"}), 404
    return jsonify(program)


@app.route("/calculate/calories", methods=["POST"])
def calories_endpoint():
    data = request.get_json(silent=True) or {}
    weight = data.get("weight")
    program_key = data.get("program")
    if weight is None or program_key is None:
        return jsonify({"error": "weight and program are required"}), 400
    try:
        weight = float(weight)
        cal = calculate_calories(weight, program_key)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"calories": cal, "program": program_key, "weight": weight})


@app.route("/calculate/bmi", methods=["POST"])
def bmi_endpoint():
    data = request.get_json(silent=True) or {}
    weight = data.get("weight")
    height = data.get("height")
    if weight is None or height is None:
        return jsonify({"error": "weight and height are required"}), 400
    try:
        weight = float(weight)
        height = float(height)
        bmi = calculate_bmi(weight, height)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"bmi": bmi, "category": bmi_category(bmi)})


@app.route("/members", methods=["GET"])
def list_members():
    return jsonify(members)


@app.route("/members", methods=["POST"])
def add_member():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    program = data.get("program", "beginner")
    if program not in PROGRAMS:
        return jsonify({"error": f"Invalid program: {program}"}), 400
    member = {"name": name, "program": program}
    members.append(member)
    return jsonify(member), 201


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
