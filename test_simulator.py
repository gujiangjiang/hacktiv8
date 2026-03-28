import os
import urllib.request
from urllib.error import HTTPError

from modules.server import start_local_server
from modules.utils import resource_path
from modules.payload import build_db_from_sql

def run_simulation():
    print("==================================================")
    print("Starting iOS Activation Simulation Test")
    print("==================================================")
    
    # 1. Start the local server
    print("\n[1] Starting local backend server...")
    try:
        backend_url = start_local_server()
        print(f" -> Server successfully started at: {backend_url}")
    except Exception as e:
        print(f" -> Failed to start server: {e}")
        return

    # 2. Test URL injection into payload database
    print("\n[2] Testing URL injection and payload generation...")
    sql_path = resource_path(os.path.join('assets', 'payload.sql'))
    if os.path.exists(sql_path):
        try:
            # Simulate generating the db for an iOS 10.3+ device
            test_path = '/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist'
            payload_db = build_db_from_sql(sql_path, backend_url, test_path)
            
            print(" -> Payload DB generation: SUCCESS")
            print(f" -> DB size: {len(payload_db)} bytes")
            print(f" -> Injected URL: {backend_url}")
            print(f" -> Target Path: {test_path}")
        except Exception as e:
            print(f" -> Payload DB generation: FAILED ({e})")
    else:
        print(f" -> ERROR: SQL file not found at {sql_path}")

    # 3. Simulate device requests for patched.plist
    print("\n[3] Simulating device requests to local server...")
    
    # Test cases containing: (model, build, expected_http_status)
    test_devices = [
        # Valid device existing in your assets
        ("iPhone5,4", "14G61", 200), 
        ("iPod5,1", "13G36", 200),
        ("iPad3,1", "12H321", 200),
        # Invalid device (Should be rejected with 403 Forbidden)
        ("iPhone99,9", "99Z99", 403),
        # Malicious directory traversal attempt
        ("../..", "14G61", 403)
    ]

    for model, build, expected_status in test_devices:
        print(f"\n--- Simulating Request: Model [{model}], Build [{build}] ---")
        
        # Construct the User-Agent string to match regex in server.py
        user_agent = f"CFNetwork/978.0.7 Darwin/18.7.0 (model/{model} build/{build})"
        
        # Create the HTTP request with the mocked User-Agent
        req = urllib.request.Request(backend_url, headers={'User-Agent': user_agent})
        
        try:
            response = urllib.request.urlopen(req)
            status = response.getcode()
            content_length = len(response.read())
            
            print(f" -> HTTP Status: {status} (Expected: {expected_status})")
            if status == 200:
                print(f" -> Result: SUCCESS. Received {content_length} bytes of plist data.")
            
        except HTTPError as e:
            status = e.code
            print(f" -> HTTP Status: {status} (Expected: {expected_status})")
            if status == expected_status:
                print(" -> Result: SUCCESS (Properly handled invalid/missing device).")
            else:
                print(" -> Result: UNEXPECTED STATUS CODE.")
        except Exception as e:
            print(f" -> Request error: {e}")

    print("\n==================================================")
    print("Simulation Test Complete.")
    print("==================================================")

if __name__ == '__main__':
    # Run the simulation when the script is executed directly
    run_simulation()