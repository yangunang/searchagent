#!/usr/bin/env python3
"""
Test script for Stock Search Agent
Run this locally before K8s deployment
"""
import requests
import json
import time


def test_local_deployment(base_url="http://localhost:8080"):
    """Test agent endpoints locally"""
    
    print("🧪 Testing Stock Search Agent")
    print(f"📍 Base URL: {base_url}\n")
    
    # Test 1: Health check
    print("1️⃣ Health Check")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Service is healthy")
        else:
            print(f"   ⚠️  Health check returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    time.sleep(1)
    
    # Test 2: NVIDIA stock query
    print("\n2️⃣ Query NVIDIA Stock")
    payload = {
        "input": [{
            "role": "user",
            "content": [{"type": "text", "text": "What is NVIDIA current stock price?"}]
        }],
        "session_id": "test123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   ⚠️  Request returned {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    time.sleep(1)
    
    # Test 3: Streaming query
    print("\n3️⃣ Streaming Query")
    payload = {
        "input": [{
            "role": "user",
            "content": [{"type": "text", "text": "Tell me about NVDA stock"}]
        }],
        "session_id": "test456"
    }
    
    try:
        response = requests.post(
            f"{base_url}/stream_chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=10
        )
        if response.status_code == 200:
            print("   📊 Streaming response:")
            for line in response.iter_lines():
                if line:
                    print(f"      {line.decode('utf-8')}")
        else:
            print(f"   ⚠️  Stream returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Stream failed: {e}")
    
    # Test 4: Direct tool test
    print("\n4️⃣ Direct Tool Test")
    from stock_agent_app import search_stock_price
    
    for symbol in ["NVDA", "AAPL", "MSFT", "UNKNOWN"]:
        result = search_stock_price(symbol)
        if result["status"] == "success":
            data = result["data"]
            print(f"   ✅ {symbol}: ${data['price']} ({data['change']})")
        else:
            print(f"   ⚠️  {symbol}: {result['message']}")
    
    print("\n🎉 Testing complete!")


def test_kubernetes_deployment(service_url):
    """Test K8s deployed service"""
    
    print(f"🧪 Testing Kubernetes Deployment")
    print(f"📍 Service URL: {service_url}\n")
    
    test_local_deployment(service_url)
    
    # Additional K8s specific tests
    print("\n5️⃣ Load Test (Multiple Requests)")
    import concurrent.futures
    
    def make_request(i):
        try:
            response = requests.post(
                f"{service_url}/chat",
                json={
                    "input": [{
                        "role": "user",
                        "content": [{"type": "text", "text": f"NVDA stock request {i}"}]
                    }],
                    "session_id": f"load-test-{i}"
                },
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(make_request, range(20)))
    
    success_rate = sum(results) / len(results) * 100
    print(f"   📊 Success rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test K8s deployment
        service_url = sys.argv[1]
        test_kubernetes_deployment(service_url)
    else:
        # Test local deployment
        print("💡 Usage:")
        print("   Local test:  python test_deployment.py")
        print("   K8s test:    python test_deployment.py http://your-service-url:8080")
        print()
        test_local_deployment()
