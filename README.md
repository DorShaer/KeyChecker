# Google API Key Checker

A Python script to check which Google services are accessible with a given API key.

## Usage

```bash
# Basic check
python3 check_google_api_key.py YOUR_API_KEY

# Only test paid services
python3 check_google_api_key.py YOUR_API_KEY --paid-only

# Show all results with request/response details
python3 check_google_api_key.py YOUR_API_KEY --verbose

# Output as JSON
python3 check_google_api_key.py YOUR_API_KEY --json
```

## Tested APIs

**Paid Services:**
- Maps APIs (Geocoding, Directions, Places, Distance Matrix, Elevation, Roads, Timezone, Static, Street View)
- Cloud Vision API
- Cloud Natural Language API
- Cloud Translation API
- Cloud Speech-to-Text API
- Cloud Text-to-Speech API
- Generative Language API (Gemini)
- Custom Search API

**Free Services:**
- YouTube Data API v3
- PageSpeed Insights API
- Safe Browsing API
- Civic Information API
- Fact Check Tools API

## Requirements

Python 3.6+ (no external dependencies - uses standard library only)
