import requests
import json

BASE_URL = 'http://localhost:5009'

def test_home_endpoint():
    """Test the home endpoint"""
    response = requests.get(f'{BASE_URL}/')
    print(f"Home endpoint: {response.status_code}")
    print("HTML content returned (UI page)")
    print()

def test_api_endpoint():
    """Test the API info endpoint"""
    response = requests.get(f'{BASE_URL}/api')
    print(f"API endpoint: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_get_users():
    """Test getting all users"""
    response = requests.get(f'{BASE_URL}/users')
    print(f"Get users: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_create_user():
    """Test creating a new user"""
    user_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }
    response = requests.post(
        f'{BASE_URL}/users',
        json=user_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f"Create user: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()
    return response.json().get('user', {}).get('id')

def test_get_user(user_id):
    """Test getting a specific user"""
    response = requests.get(f'{BASE_URL}/user/{user_id}')
    print(f"Get user {user_id}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_update_user(user_id):
    """Test updating a user"""
    update_data = {
        'name': 'Updated Test User',
        'email': 'updated@example.com'
    }
    response = requests.put(
        f'{BASE_URL}/user/{user_id}',
        json=update_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f"Update user {user_id}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_search_users():
    """Test searching users"""
    response = requests.get(f'{BASE_URL}/search?name=John')
    print(f"Search users: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_login():
    """Test user login"""
    login_data = {
        'email': 'john@example.com',
        'password': 'password123'
    }
    response = requests.post(
        f'{BASE_URL}/login',
        json=login_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f"Login: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_delete_user(user_id):
    """Test deleting a user"""
    response = requests.delete(f'{BASE_URL}/user/{user_id}')
    print(f"Delete user {user_id}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

if __name__ == '__main__':
    print("Testing refactored User Management API")
    print("=" * 50)
    
    try:
        test_home_endpoint()
        test_api_endpoint()
        test_get_users()
        test_search_users()
        test_login()
        
        # Test CRUD operations
        user_id = test_create_user()
        if user_id:
            test_get_user(user_id)
            test_update_user(user_id)
            test_delete_user(user_id)
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the server is running on http://localhost:5009")
    except Exception as e:
        print(f"Error during testing: {str(e)}") 