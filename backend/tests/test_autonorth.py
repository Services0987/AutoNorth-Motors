"""AutoNorth Motors Backend API Tests"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "admin@autonorth.ca"
ADMIN_PASSWORD = "AdminPass2024"

@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s

@pytest.fixture(scope="module")
def auth_session(session):
    resp = session.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    # Try Bearer token fallback
    token = resp.cookies.get("access_token") or resp.json().get("token")
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    return session

# --- Auth Tests ---
class TestAuth:
    def test_login_success(self, session):
        resp = session.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == ADMIN_EMAIL
        print("PASS: Admin login success")

    def test_login_invalid(self, session):
        resp = session.post(f"{BASE_URL}/api/auth/login", json={"email": "bad@email.com", "password": "wrongpass"})
        assert resp.status_code == 401
        print("PASS: Invalid login returns 401")

    def test_me_authenticated(self, auth_session):
        resp = auth_session.get(f"{BASE_URL}/api/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == ADMIN_EMAIL
        print("PASS: /me returns current user")

# --- Vehicle Tests ---
class TestVehicles:
    def test_list_vehicles_public(self, session):
        resp = session.get(f"{BASE_URL}/api/vehicles")
        assert resp.status_code == 200
        data = resp.json()
        assert "vehicles" in data
        assert data["total"] >= 8
        print(f"PASS: Vehicles list returned {data['total']} vehicles")

    def test_list_vehicles_filter_condition(self, session):
        resp = session.get(f"{BASE_URL}/api/vehicles?condition=new")
        assert resp.status_code == 200
        data = resp.json()
        for v in data["vehicles"]:
            assert v["condition"] == "new"
        print(f"PASS: Filter by condition=new works, got {data['total']}")

    def test_list_vehicles_filter_body_type(self, session):
        resp = session.get(f"{BASE_URL}/api/vehicles?body_type=Truck")
        assert resp.status_code == 200
        data = resp.json()
        for v in data["vehicles"]:
            assert v["body_type"] == "Truck"
        print(f"PASS: Filter by body_type=Truck works")

    def test_get_vehicle_by_id(self, session):
        list_resp = session.get(f"{BASE_URL}/api/vehicles")
        vid = list_resp.json()["vehicles"][0]["id"]
        resp = session.get(f"{BASE_URL}/api/vehicles/{vid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == vid
        print(f"PASS: Get vehicle by id works")

    def test_get_vehicle_invalid_id(self, session):
        resp = session.get(f"{BASE_URL}/api/vehicles/invalid_id_here")
        assert resp.status_code == 400
        print("PASS: Invalid vehicle id returns 400")

    def test_create_vehicle(self, auth_session):
        payload = {
            "title": "TEST_2024 Test Car", "make": "TEST_Make", "model": "TestModel",
            "year": 2024, "price": 30000, "mileage": 0, "condition": "new",
            "body_type": "Sedan", "fuel_type": "Gas", "transmission": "Automatic"
        }
        resp = auth_session.post(f"{BASE_URL}/api/vehicles", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == payload["title"]
        TestVehicles.created_id = data["id"]
        print(f"PASS: Vehicle created with id {data['id']}")

    def test_update_vehicle(self, auth_session):
        vid = TestVehicles.created_id
        resp = auth_session.put(f"{BASE_URL}/api/vehicles/{vid}", json={"price": 28000})
        assert resp.status_code == 200
        assert resp.json()["price"] == 28000
        print("PASS: Vehicle updated")

    def test_delete_vehicle(self, auth_session):
        vid = TestVehicles.created_id
        resp = auth_session.delete(f"{BASE_URL}/api/vehicles/{vid}")
        assert resp.status_code == 200
        # Verify deletion
        get_resp = auth_session.get(f"{BASE_URL}/api/vehicles/{vid}")
        assert get_resp.status_code == 404
        print("PASS: Vehicle deleted and verified")

# --- Lead Tests ---
class TestLeads:
    def test_create_lead(self, session):
        payload = {
            "lead_type": "contact",
            "name": "TEST_John Doe",
            "email": "test_john@example.com",
            "phone": "780-555-0001",
            "message": "Interested in a vehicle"
        }
        resp = session.post(f"{BASE_URL}/api/leads", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == payload["name"]
        assert data["status"] == "new"
        TestLeads.created_id = data["id"]
        print(f"PASS: Lead created id={data['id']}")

    def test_list_leads_requires_auth(self, session):
        # Anonymous should fail
        anon = requests.Session()
        resp = anon.get(f"{BASE_URL}/api/leads")
        assert resp.status_code == 401
        print("PASS: Leads list requires auth")

    def test_list_leads_authenticated(self, auth_session):
        resp = auth_session.get(f"{BASE_URL}/api/leads")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        print(f"PASS: Leads list returned {len(resp.json())} leads")

    def test_update_lead_status(self, auth_session):
        lid = TestLeads.created_id
        resp = auth_session.put(f"{BASE_URL}/api/leads/{lid}", json={"status": "contacted"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "contacted"
        print("PASS: Lead status updated")

    def test_delete_lead(self, auth_session):
        lid = TestLeads.created_id
        resp = auth_session.delete(f"{BASE_URL}/api/leads/{lid}")
        assert resp.status_code == 200
        print("PASS: Lead deleted")

# --- Stats Test ---
class TestStats:
    def test_stats_requires_auth(self, session):
        anon = requests.Session()
        resp = anon.get(f"{BASE_URL}/api/stats")
        assert resp.status_code == 401
        print("PASS: Stats requires auth")

    def test_stats_authenticated(self, auth_session):
        resp = auth_session.get(f"{BASE_URL}/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_vehicles" in data
        assert "total_leads" in data
        assert "available" in data
        assert "sold" in data
        print(f"PASS: Stats returned total_vehicles={data['total_vehicles']}")
