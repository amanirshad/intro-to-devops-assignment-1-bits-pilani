import pytest
from app import app, calculate_calories, calculate_bmi, bmi_category, members


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_members():
    """Reset in-memory member list before each test."""
    members.clear()


# ── Unit tests for helper functions ────────────────────────────────────

class TestCalculateCalories:
    def test_fat_loss(self):
        assert calculate_calories(80, "fat_loss") == 1760

    def test_muscle_gain(self):
        assert calculate_calories(70, "muscle_gain") == 2450

    def test_beginner(self):
        assert calculate_calories(60, "beginner") == 1560

    def test_invalid_program(self):
        with pytest.raises(ValueError, match="Unknown program"):
            calculate_calories(70, "nonexistent")

    def test_zero_weight(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_calories(0, "fat_loss")

    def test_negative_weight(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_calories(-10, "fat_loss")


class TestCalculateBMI:
    def test_normal_bmi(self):
        bmi = calculate_bmi(70, 175)
        assert bmi == 22.86

    def test_high_bmi(self):
        bmi = calculate_bmi(100, 170)
        assert bmi == 34.6

    def test_zero_height(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_bmi(70, 0)

    def test_negative_height(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_bmi(70, -170)

    def test_zero_weight(self):
        with pytest.raises(ValueError, match="positive"):
            calculate_bmi(0, 170)


class TestBMICategory:
    def test_underweight(self):
        assert bmi_category(17.0) == "Underweight"

    def test_normal(self):
        assert bmi_category(22.0) == "Normal weight"

    def test_overweight(self):
        assert bmi_category(27.5) == "Overweight"

    def test_obese(self):
        assert bmi_category(32.0) == "Obese"

    def test_boundary_18_5(self):
        assert bmi_category(18.5) == "Normal weight"

    def test_boundary_25(self):
        assert bmi_category(25.0) == "Overweight"

    def test_boundary_30(self):
        assert bmi_category(30.0) == "Obese"


# ── Integration tests for routes ───────────────────────────────────────

class TestHomeRoute:
    def test_home_status(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_contains_title(self, client):
        resp = client.get("/")
        assert b"ACEest" in resp.data


class TestHealthRoute:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "healthy"


class TestProgramsRoute:
    def test_list_programs(self, client):
        resp = client.get("/programs")
        data = resp.get_json()
        assert "fat_loss" in data
        assert "muscle_gain" in data
        assert "beginner" in data

    def test_get_program_detail(self, client):
        resp = client.get("/programs/fat_loss")
        data = resp.get_json()
        assert data["name"] == "Fat Loss (FL)"
        assert data["calorie_factor"] == 22

    def test_get_program_not_found(self, client):
        resp = client.get("/programs/nonexistent")
        assert resp.status_code == 404


class TestCaloriesRoute:
    def test_valid_request(self, client):
        resp = client.post("/calculate/calories", json={"weight": 80, "program": "fat_loss"})
        assert resp.status_code == 200
        assert resp.get_json()["calories"] == 1760

    def test_missing_fields(self, client):
        resp = client.post("/calculate/calories", json={"weight": 80})
        assert resp.status_code == 400

    def test_invalid_program(self, client):
        resp = client.post("/calculate/calories", json={"weight": 80, "program": "xyz"})
        assert resp.status_code == 400


class TestBMIRoute:
    def test_valid_bmi(self, client):
        resp = client.post("/calculate/bmi", json={"weight": 70, "height": 175})
        data = resp.get_json()
        assert data["bmi"] == 22.86
        assert data["category"] == "Normal weight"

    def test_missing_fields(self, client):
        resp = client.post("/calculate/bmi", json={"weight": 70})
        assert resp.status_code == 400

    def test_invalid_height(self, client):
        resp = client.post("/calculate/bmi", json={"weight": 70, "height": 0})
        assert resp.status_code == 400


class TestMembersRoute:
    def test_empty_list(self, client):
        resp = client.get("/members")
        assert resp.get_json() == []

    def test_add_member(self, client):
        resp = client.post("/members", json={"name": "Ravi", "program": "fat_loss"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Ravi"
        assert data["program"] == "fat_loss"

    def test_add_member_default_program(self, client):
        resp = client.post("/members", json={"name": "Priya"})
        assert resp.status_code == 201
        assert resp.get_json()["program"] == "beginner"

    def test_add_member_missing_name(self, client):
        resp = client.post("/members", json={"program": "fat_loss"})
        assert resp.status_code == 400

    def test_add_member_invalid_program(self, client):
        resp = client.post("/members", json={"name": "Test", "program": "xyz"})
        assert resp.status_code == 400

    def test_list_after_add(self, client):
        client.post("/members", json={"name": "Arjun", "program": "muscle_gain"})
        resp = client.get("/members")
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Arjun"
