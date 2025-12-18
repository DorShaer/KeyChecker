#!/usr/bin/env python3
"""
Google API Key Service Checker

This script checks which paid Google services are accessible with a given API key.
It tests various Google Cloud APIs to identify potential cost exposure.
"""

import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode


# List of Google APIs to test (service_name, test_endpoint, method, description)
GOOGLE_APIS = [
    # Maps & Places APIs (can be expensive)
    {
        "name": "Maps Geocoding API",
        "url": "https://maps.googleapis.com/maps/api/geocode/json",
        "params": {"address": "1600 Amphitheatre Parkway"},
        "paid": True,
        "cost_info": "$5 per 1000 requests"
    },
    {
        "name": "Maps Directions API",
        "url": "https://maps.googleapis.com/maps/api/directions/json",
        "params": {"origin": "New York", "destination": "Los Angeles"},
        "paid": True,
        "cost_info": "$5-10 per 1000 requests"
    },
    {
        "name": "Maps Distance Matrix API",
        "url": "https://maps.googleapis.com/maps/api/distancematrix/json",
        "params": {"origins": "New York", "destinations": "Los Angeles"},
        "paid": True,
        "cost_info": "$5-10 per 1000 elements"
    },
    {
        "name": "Maps Places API (Nearby Search)",
        "url": "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
        "params": {"location": "37.7749,-122.4194", "radius": "1000"},
        "paid": True,
        "cost_info": "$32 per 1000 requests"
    },
    {
        "name": "Maps Places API (Text Search)",
        "url": "https://maps.googleapis.com/maps/api/place/textsearch/json",
        "params": {"query": "restaurant"},
        "paid": True,
        "cost_info": "$32 per 1000 requests"
    },
    {
        "name": "Maps Places API (Details)",
        "url": "https://maps.googleapis.com/maps/api/place/details/json",
        "params": {"place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"},
        "paid": True,
        "cost_info": "$17 per 1000 requests"
    },
    {
        "name": "Maps Places API (Autocomplete)",
        "url": "https://maps.googleapis.com/maps/api/place/autocomplete/json",
        "params": {"input": "Paris"},
        "paid": True,
        "cost_info": "$2.83 per 1000 requests"
    },
    {
        "name": "Maps Elevation API",
        "url": "https://maps.googleapis.com/maps/api/elevation/json",
        "params": {"locations": "39.7391536,-104.9847034"},
        "paid": True,
        "cost_info": "$5 per 1000 requests"
    },
    {
        "name": "Maps Roads API (Snap to Roads)",
        "url": "https://roads.googleapis.com/v1/snapToRoads",
        "params": {"path": "60.170880,24.942795|60.170879,24.942796"},
        "paid": True,
        "cost_info": "$10 per 1000 requests"
    },
    {
        "name": "Maps Timezone API",
        "url": "https://maps.googleapis.com/maps/api/timezone/json",
        "params": {"location": "39.6034810,-119.6822510", "timestamp": "1331161200"},
        "paid": True,
        "cost_info": "$5 per 1000 requests"
    },
    {
        "name": "Maps Static API",
        "url": "https://maps.googleapis.com/maps/api/staticmap",
        "params": {"center": "Brooklyn+Bridge,New+York,NY", "zoom": "13", "size": "600x300"},
        "paid": True,
        "cost_info": "$2 per 1000 requests"
    },
    {
        "name": "Maps Street View Static API",
        "url": "https://maps.googleapis.com/maps/api/streetview/metadata",
        "params": {"location": "46.414382,10.013988"},
        "paid": True,
        "cost_info": "$7 per 1000 requests"
    },
    # AI/ML APIs
    {
        "name": "Cloud Vision API",
        "url": "https://vision.googleapis.com/v1/images:annotate",
        "params": {},
        "method": "POST",
        "body": {"requests": [{"features": [{"type": "LABEL_DETECTION"}]}]},
        "paid": True,
        "cost_info": "$1.50 per 1000 images"
    },
    {
        "name": "Cloud Natural Language API",
        "url": "https://language.googleapis.com/v1/documents:analyzeSentiment",
        "params": {},
        "method": "POST",
        "body": {"document": {"type": "PLAIN_TEXT", "content": "Hello world"}},
        "paid": True,
        "cost_info": "$1-2 per 1000 records"
    },
    {
        "name": "Cloud Translation API",
        "url": "https://translation.googleapis.com/language/translate/v2",
        "params": {"q": "Hello", "target": "es"},
        "paid": True,
        "cost_info": "$20 per 1M characters"
    },
    {
        "name": "Cloud Speech-to-Text API",
        "url": "https://speech.googleapis.com/v1/speech:recognize",
        "params": {},
        "method": "POST",
        "body": {"config": {"languageCode": "en-US"}},
        "paid": True,
        "cost_info": "$0.006 per 15 seconds"
    },
    {
        "name": "Cloud Text-to-Speech API",
        "url": "https://texttospeech.googleapis.com/v1/voices",
        "params": {},
        "paid": True,
        "cost_info": "$4-16 per 1M characters"
    },
    {
        "name": "Generative Language API (Gemini)",
        "url": "https://generativelanguage.googleapis.com/v1/models",
        "params": {},
        "paid": True,
        "cost_info": "Varies by model"
    },
    # YouTube APIs
    {
        "name": "YouTube Data API v3",
        "url": "https://www.googleapis.com/youtube/v3/search",
        "params": {"part": "snippet", "q": "test", "maxResults": "1"},
        "paid": False,
        "cost_info": "Free with quota limits"
    },
    # Other APIs
    {
        "name": "Custom Search API",
        "url": "https://www.googleapis.com/customsearch/v1",
        "params": {"q": "test", "cx": "000000000000000000000:aaaaaaaaaaa"},
        "paid": True,
        "cost_info": "$5 per 1000 queries (after free tier)"
    },
    {
        "name": "PageSpeed Insights API",
        "url": "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
        "params": {"url": "https://www.google.com"},
        "paid": False,
        "cost_info": "Free"
    },
    {
        "name": "Safe Browsing API",
        "url": "https://safebrowsing.googleapis.com/v4/threatLists",
        "params": {},
        "paid": False,
        "cost_info": "Free"
    },
    {
        "name": "Civic Information API",
        "url": "https://www.googleapis.com/civicinfo/v2/elections",
        "params": {},
        "paid": False,
        "cost_info": "Free"
    },
    {
        "name": "Fact Check Tools API",
        "url": "https://factchecktools.googleapis.com/v1alpha1/claims:search",
        "params": {"query": "test"},
        "paid": False,
        "cost_info": "Free"
    },
]


def test_api(api_info: dict, api_key: str, verbose: bool = False) -> dict:
    """Test a single API endpoint with the given API key."""
    url = api_info["url"]
    params = api_info.get("params", {}).copy()
    params["key"] = api_key
    method = api_info.get("method", "GET")

    result = {
        "name": api_info["name"],
        "accessible": False,
        "paid": api_info["paid"],
        "cost_info": api_info["cost_info"],
        "status": None,
        "error": None,
        "request": None,
        "response": None
    }

    try:
        if method == "GET":
            # Mask the API key in logged URL
            display_params = params.copy()
            display_params["key"] = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            full_url = f"{url}?{urlencode(params)}"
            display_url = f"{url}?{urlencode(display_params)}"
            req = Request(full_url)
            request_body = None
        else:
            display_url = f"{url}?key={api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else f"{url}?key=***"
            full_url = f"{url}?key={api_key}"
            request_body = api_info.get("body", {})
            body = json.dumps(request_body).encode('utf-8')
            req = Request(full_url, data=body, method=method)
            req.add_header('Content-Type', 'application/json')

        if verbose:
            result["request"] = {
                "method": method,
                "url": display_url,
                "body": request_body
            }

        with urlopen(req, timeout=10) as response:
            result["status"] = response.status
            response_data = response.read().decode('utf-8')

            if verbose:
                result["response"] = {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "body": None
                }

            # Check for API-specific error responses that come with 200 status
            try:
                json_response = json.loads(response_data)
                if verbose:
                    # Truncate response body if too large
                    if len(response_data) > 1000:
                        result["response"]["body"] = json.loads(response_data[:1000] + '..."truncated"...')
                    else:
                        result["response"]["body"] = json_response

                # Check for various error patterns in Google API responses
                error_msg = (json_response.get("error_message") or
                            json_response.get("errorMessage") or
                            json_response.get("error", {}).get("message") or "")
                status = json_response.get("status", "")

                # Phrases that indicate the key cannot access the API
                denial_phrases = [
                    "not authorized",
                    "not enabled",
                    "enable billing",
                    "api key not valid",
                    "invalid api key",
                    "permission denied",
                    "access denied",
                    "has not been used in project",
                    "api is not enabled",
                ]

                is_denied = any(phrase in error_msg.lower() for phrase in denial_phrases)

                if "error" in json_response and json_response["error"].get("code") in (401, 403):
                    # HTTP-style error in JSON body - clearly denied
                    result["accessible"] = False
                    result["error"] = error_msg or "Access denied"
                elif status == "REQUEST_DENIED" and is_denied:
                    # REQUEST_DENIED with clear denial message
                    result["accessible"] = False
                    result["error"] = error_msg or "Request denied"
                elif status in ("OVER_QUERY_LIMIT", "RESOURCE_EXHAUSTED"):
                    # Hit rate limits - but key HAS access
                    result["accessible"] = True
                    result["error"] = f"Rate limited (but key has access): {error_msg}"
                elif status == "REQUEST_DENIED" and not is_denied:
                    # REQUEST_DENIED but unclear why - could be temporary, mark accessible with warning
                    result["accessible"] = True
                    result["error"] = f"Possibly accessible (unclear denial): {error_msg}"
                elif is_denied:
                    # Clear denial phrase in error message
                    result["accessible"] = False
                    result["error"] = error_msg
                else:
                    result["accessible"] = True
            except json.JSONDecodeError:
                # Non-JSON response (like images) - if we got here, it's accessible
                result["accessible"] = True
                if verbose:
                    result["response"]["body"] = f"<binary or non-JSON data, {len(response_data)} bytes>"

    except HTTPError as e:
        result["status"] = e.code
        try:
            error_body = e.read().decode('utf-8')
            error_json = json.loads(error_body)

            if verbose:
                result["request"] = {
                    "method": method,
                    "url": display_url,
                    "body": request_body if method != "GET" else None
                }
                result["response"] = {
                    "status_code": e.code,
                    "headers": dict(e.headers) if hasattr(e, 'headers') else {},
                    "body": error_json
                }

            if "error" in error_json:
                error_msg = error_json["error"].get("message", str(e))
                # Check if it's a "not enabled" vs "invalid key" error
                if "has not been used" in error_msg or "is not enabled" in error_msg:
                    result["error"] = "API not enabled for this project"
                elif "API key not valid" in error_msg or "invalid" in error_msg.lower():
                    result["error"] = "Invalid API key"
                elif "denied" in error_msg.lower():
                    result["error"] = "Access denied"
                else:
                    result["error"] = error_msg
            else:
                result["error"] = str(e)
        except:
            result["error"] = str(e)

    except URLError as e:
        result["error"] = f"Connection error: {e.reason}"
        if verbose:
            result["request"] = {
                "method": method,
                "url": display_url,
                "body": request_body if method != "GET" else None
            }
    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Check which Google services are accessible with an API key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_google_api_key.py YOUR_API_KEY
  python check_google_api_key.py YOUR_API_KEY --paid-only
  python check_google_api_key.py YOUR_API_KEY --json
        """
    )
    parser.add_argument("api_key", help="Google API key to test")
    parser.add_argument("--paid-only", action="store_true",
                        help="Only test paid services")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all results, not just accessible services")

    args = parser.parse_args()

    apis_to_test = GOOGLE_APIS
    if args.paid_only:
        apis_to_test = [api for api in GOOGLE_APIS if api["paid"]]

    results = []
    accessible_paid = []
    accessible_free = []

    if not args.json:
        print(f"\nTesting Google API key against {len(apis_to_test)} services...\n")
        print("-" * 70)

    for api in apis_to_test:
        result = test_api(api, args.api_key, verbose=args.verbose)
        results.append(result)

        if result["accessible"]:
            if result["paid"]:
                accessible_paid.append(result)
            else:
                accessible_free.append(result)

        if not args.json:
            status_icon = "\033[92m[ACCESSIBLE]\033[0m" if result["accessible"] else "\033[91m[BLOCKED]\033[0m"
            paid_tag = "\033[93m[PAID]\033[0m" if result["paid"] else "[FREE]"

            if result["accessible"] or args.verbose:
                print(f"{status_icon} {paid_tag} {result['name']}")
                if result["accessible"] and result["paid"]:
                    print(f"           Cost: {result['cost_info']}")
                if args.verbose and result["error"]:
                    print(f"           Error: {result['error']}")

                # Show request/response details in verbose mode
                if args.verbose and result["request"]:
                    print(f"\n           \033[96m--- REQUEST ---\033[0m")
                    print(f"           Method: {result['request']['method']}")
                    print(f"           URL: {result['request']['url']}")
                    if result['request']['body']:
                        print(f"           Body: {json.dumps(result['request']['body'], indent=12)}")

                if args.verbose and result["response"]:
                    print(f"\n           \033[96m--- RESPONSE ---\033[0m")
                    print(f"           Status: {result['response']['status_code']}")
                    if result['response'].get('headers'):
                        print(f"           Headers:")
                        for k, v in list(result['response']['headers'].items())[:5]:
                            print(f"             {k}: {v[:50]}..." if len(str(v)) > 50 else f"             {k}: {v}")
                    if result['response'].get('body'):
                        body_str = json.dumps(result['response']['body'], indent=2)
                        # Truncate long responses
                        if len(body_str) > 500:
                            body_lines = body_str[:500].split('\n')
                            print(f"           Body (truncated):")
                            for line in body_lines:
                                print(f"             {line}")
                            print(f"             ... (truncated)")
                        else:
                            print(f"           Body:")
                            for line in body_str.split('\n'):
                                print(f"             {line}")
                    print()

    if args.json:
        output = {
            "total_tested": len(results),
            "accessible_paid_services": len(accessible_paid),
            "accessible_free_services": len(accessible_free),
            "results": results
        }
        print(json.dumps(output, indent=2))
    else:
        print("-" * 70)
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total APIs tested: {len(results)}")
        print(f"\033[92mAccessible paid services: {len(accessible_paid)}\033[0m")
        print(f"Accessible free services: {len(accessible_free)}")

        if accessible_paid:
            print(f"\n\033[93m{'!'*70}\033[0m")
            print("\033[93mWARNING: The following PAID services are accessible with this API key:\033[0m")
            print(f"\033[93m{'!'*70}\033[0m\n")
            for svc in accessible_paid:
                print(f"  - {svc['name']}")
                print(f"    Cost: {svc['cost_info']}")
            print("\n\033[93mRecommendation: Review API restrictions in Google Cloud Console\033[0m")
            print("https://console.cloud.google.com/apis/credentials")
        else:
            print(f"\n\033[92m{'='*70}\033[0m")
            print("\033[92mGOOD NEWS: No paid services are accessible with this API key!\033[0m")
            print(f"\033[92m{'='*70}\033[0m")


if __name__ == "__main__":
    main()
