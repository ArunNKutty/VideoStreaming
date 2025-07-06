#!/usr/bin/env python3
"""
Test script for HLS Server authentication endpoints
"""
import requests
import json
import sys

def test_auth_endpoints(base_url="http://localhost:8080"):
    """Test authentication endpoints"""
    
    print("🔐 Testing HLS Server Authentication")
    print(f"Server: {base_url}")
    print("=" * 50)
    
    # Test 1: Create client credentials
    print("\n1️⃣ Creating client credentials...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/credentials",
            params={
                "name": "Test SDK Client",
                "description": "Client for testing Go SDK"
            }
        )
        
        if response.status_code == 200:
            creds = response.json()
            print("✅ Client credentials created successfully!")
            print(f"   Client ID: {creds['client_id']}")
            print(f"   Client Secret: {creds['client_secret']}")
            
            client_id = creds['client_id']
            client_secret = creds['client_secret']
        else:
            print(f"❌ Failed to create credentials: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating credentials: {e}")
        return False
    
    # Test 2: Get access token
    print("\n2️⃣ Getting access token...")
    try:
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/token",
            json=token_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token_resp = response.json()
            print("✅ Access token obtained successfully!")
            print(f"   Token Type: {token_resp['token_type']}")
            print(f"   Expires In: {token_resp['expires_in']} seconds")
            print(f"   Access Token: {token_resp['access_token'][:20]}...")
            
            access_token = token_resp['access_token']
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return False
    
    # Test 3: Verify token
    print("\n3️⃣ Verifying token...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            verify_resp = response.json()
            print("✅ Token verified successfully!")
            print(f"   Valid: {verify_resp['valid']}")
            print(f"   Client ID: {verify_resp['client_id']}")
        else:
            print(f"❌ Failed to verify token: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False
    
    # Test 4: Test authenticated endpoint (health check)
    print("\n4️⃣ Testing authenticated health check...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/health",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            health_resp = response.json()
            print("✅ Authenticated health check successful!")
            print(f"   Status: {health_resp['status']}")
            print(f"   Version: {health_resp['version']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in health check: {e}")
        return False
    
    # Test 5: Test invalid token
    print("\n5️⃣ Testing invalid token...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/auth/verify",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
        else:
            print(f"⚠️  Unexpected response for invalid token: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invalid token: {e}")
        return False
    
    print("\n🎉 All authentication tests passed!")
    print("\n📋 SDK Configuration:")
    print(f"   HLS_SERVER_URL={base_url}")
    print(f"   HLS_CLIENT_ID={client_id}")
    print(f"   HLS_CLIENT_SECRET={client_secret}")
    
    return True

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    success = test_auth_endpoints(base_url)
    sys.exit(0 if success else 1)
