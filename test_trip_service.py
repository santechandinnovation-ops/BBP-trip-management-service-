import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8002"

def test_health():
    """Test health check endpoint."""
    print("\n=== Testing GET /health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ Health check passed")

def test_create_trip(token):
    """Test creating a new trip."""
    print("\n=== Testing POST /trips ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "startTime": datetime.utcnow().isoformat() + "Z"
    }

    response = requests.post(f"{BASE_URL}/trips", json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 201
    trip_id = response.json()["tripId"]
    print(f"✅ Trip created: {trip_id}")
    return trip_id

def test_add_coordinates(token, trip_id):
    """Test adding GPS coordinates to a trip."""
    print("\n=== Testing POST /trips/:id/coordinates ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Add multiple coordinates (simulating 5-second intervals)
    coordinates = [
        {"latitude": 45.4642, "longitude": 9.1900, "elevation": 120},
        {"latitude": 45.4652, "longitude": 9.1910, "elevation": 121},
        {"latitude": 45.4662, "longitude": 9.1920, "elevation": 122},
        {"latitude": 45.4672, "longitude": 9.1930, "elevation": 123},
        {"latitude": 45.4682, "longitude": 9.1940, "elevation": 124},
    ]

    base_time = datetime.utcnow()

    for i, coord in enumerate(coordinates):
        coord["timestamp"] = (base_time + timedelta(seconds=i*5)).isoformat() + "Z"

        response = requests.post(
            f"{BASE_URL}/trips/{trip_id}/coordinates",
            json=coord,
            headers=headers
        )

        print(f"Coordinate {i+1} Status: {response.status_code}")
        assert response.status_code == 201

    print("✅ All coordinates added")

def test_complete_trip(token, trip_id):
    """Test completing a trip."""
    print("\n=== Testing PUT /trips/:id/complete ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "endTime": (datetime.utcnow() + timedelta(seconds=30)).isoformat() + "Z"
    }

    response = requests.put(
        f"{BASE_URL}/trips/{trip_id}/complete",
        json=data,
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "COMPLETED"
    assert result["totalDistance"] > 0
    print("✅ Trip completed with statistics")

def test_get_trip_history(token):
    """Test getting trip history."""
    print("\n=== Testing GET /trips ===")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/trips", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    print("✅ Trip history retrieved")

def test_get_trip_detail(token, trip_id):
    """Test getting trip detail."""
    print("\n=== Testing GET /trips/:id ===")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/trips/{trip_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    result = response.json()
    assert len(result["coordinates"]) >= 5
    print("✅ Trip detail retrieved with coordinates")

def test_error_cases(token):
    """Test error scenarios."""
    print("\n=== Testing Error Cases ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Test invalid trip ID
    print("\n1. Invalid trip ID (404):")
    response = requests.get(
        f"{BASE_URL}/trips/00000000-0000-0000-0000-000000000000",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 404

    # Test invalid coordinates
    print("\n2. Invalid coordinates (400):")
    data = {
        "latitude": 100,  # Invalid: > 90
        "longitude": 9.19,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    trip_id = test_create_trip(token)
    response = requests.post(
        f"{BASE_URL}/trips/{trip_id}/coordinates",
        json=data,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 422  # Validation error

    print("✅ Error cases handled correctly")

if __name__ == "__main__":
    print("=" * 60)
    print("BBP Trip Management Service - Test Suite")
    print("=" * 60)

    # First, test health check
    test_health()

    # Note: You need a valid JWT token from User Management Service
    print("\n⚠️  To run authenticated tests, you need a valid JWT token")
    print("Get a token by:")
    print("1. Register/Login through User Management Service (port 8000)")
    print("2. Copy the token from the login response")
    print("3. Paste it when prompted\n")

    token = input("Enter your JWT token (or press Enter to skip authenticated tests): ").strip()

    if token:
        try:
            # Test create trip
            trip_id = test_create_trip(token)

            # Test add coordinates
            test_add_coordinates(token, trip_id)

            # Test complete trip
            test_complete_trip(token, trip_id)

            # Test get history
            test_get_trip_history(token)

            # Test get detail
            test_get_trip_detail(token, trip_id)

            # Test error cases
            test_error_cases(token)

            print("\n" + "=" * 60)
            print("✅ All tests passed successfully!")
            print("=" * 60)

        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("\n⚠️  Skipping authenticated tests")
        print("Only health check was performed")
