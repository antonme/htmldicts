#!/usr/bin/env python
"""
Load testing script for the Dictionary Search API
"""
import time
import statistics
import concurrent.futures
import httpx
import random
import argparse

# Sample queries in different languages
SAMPLE_QUERIES = [
    "tree",
    "forest",
    "лес",
    "дерево",
    "хъæд",
    "test",
    "word",
    "книга",
    "язык",
    "земля"
]

def make_request(url, query, timeout=10):
    """Make a request to the API and measure response time"""
    start_time = time.time()
    try:
        response = httpx.get(url, params={"q": query}, timeout=timeout)
        response_time = time.time() - start_time
        status_code = response.status_code
        
        # Get response size
        content_length = len(response.content)
        
        return {
            "query": query,
            "status_code": status_code,
            "response_time": response_time,
            "response_size": content_length,
            "success": status_code == 200
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "query": query,
            "status_code": 0,
            "response_time": response_time,
            "response_size": 0,
            "success": False,
            "error": str(e)
        }

def run_load_test(base_url, num_requests=100, concurrency=10):
    """
    Run a load test against the API
    
    Args:
        base_url: Base URL of the API
        num_requests: Total number of requests to make
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary of test results
    """
    print(f"Running load test with {num_requests} requests, {concurrency} concurrent...")
    
    # Create request URLs
    search_url = f"{base_url}/search"
    
    # Prepare queries
    queries = []
    for _ in range(num_requests):
        queries.append(random.choice(SAMPLE_QUERIES))
    
    # Make concurrent requests
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, search_url, query) for query in queries]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                # Print progress
                if len(results) % 10 == 0 or len(results) == num_requests:
                    print(f"Completed {len(results)}/{num_requests} requests")
            except Exception as e:
                print(f"Request failed: {str(e)}")
                results.append({
                    "query": "unknown",
                    "status_code": 0,
                    "response_time": 0,
                    "response_size": 0,
                    "success": False,
                    "error": str(e)
                })
    
    # Calculate statistics
    successful_results = [r for r in results if r["success"]]
    failed_results = [r for r in results if not r["success"]]
    
    if successful_results:
        response_times = [r["response_time"] for r in successful_results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        response_sizes = [r["response_size"] for r in successful_results]
        avg_response_size = sum(response_sizes) / len(response_sizes)
    else:
        avg_response_time = max_response_time = min_response_time = median_response_time = p95_response_time = 0
        avg_response_size = 0
    
    # Print results
    print("\nLoad Test Results:")
    print(f"Total Requests: {num_requests}")
    print(f"Successful Requests: {len(successful_results)} ({len(successful_results)/num_requests*100:.2f}%)")
    print(f"Failed Requests: {len(failed_results)} ({len(failed_results)/num_requests*100:.2f}%)")
    print(f"Average Response Time: {avg_response_time*1000:.2f} ms")
    print(f"Minimum Response Time: {min_response_time*1000:.2f} ms")
    print(f"Maximum Response Time: {max_response_time*1000:.2f} ms")
    print(f"Median Response Time: {median_response_time*1000:.2f} ms")
    print(f"95th Percentile Response Time: {p95_response_time*1000:.2f} ms")
    print(f"Average Response Size: {avg_response_size/1024:.2f} KB")
    
    # Check if we met our 500ms requirement
    if p95_response_time * 1000 < 500:
        print("\n✅ Performance requirement met: 95% of requests completed in under 500ms")
    else:
        print("\n❌ Performance requirement not met: 95% of requests took longer than 500ms")
    
    return {
        "total_requests": num_requests,
        "successful_requests": len(successful_results),
        "failed_requests": len(failed_results),
        "avg_response_time_ms": avg_response_time * 1000,
        "min_response_time_ms": min_response_time * 1000,
        "max_response_time_ms": max_response_time * 1000,
        "median_response_time_ms": median_response_time * 1000,
        "p95_response_time_ms": p95_response_time * 1000,
        "avg_response_size_kb": avg_response_size / 1024
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test the Dictionary Search API")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests to make")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests")
    
    args = parser.parse_args()
    
    run_load_test(args.url, args.requests, args.concurrency) 