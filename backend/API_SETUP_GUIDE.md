# Google API Key Setup Guide

## 🚨 Current Issues Found

Based on the test results, your Google API key needs proper configuration:

### 1. **Billing Required** 
- Google Maps APIs require billing to be enabled
- Error: "You must enable Billing on the Google Cloud Project"

### 2. **APIs Not Enabled**
- REQUEST_DENIED suggests the required APIs aren't enabled for your project

### 3. **OpenWeatherMap Separate Key**
- OpenWeatherMap requires its own API key (not Google's)

## ✅ Setup Steps

### Step 1: Enable Billing (Required for Google Maps)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project or create a new one
3. Go to Billing → Link a billing account
4. **Note**: Google provides $300 free credits for new accounts

### Step 2: Enable Required APIs
In Google Cloud Console → APIs & Services → Library, enable:
- **Geocoding API** (for address to coordinates)
- **Places API** (for location search)
- **Maps JavaScript API** (for frontend maps)

### Step 3: Get OpenWeatherMap API Key
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Get your free API key (1000 calls/day)

### Step 4: Update Your .env File
```bash
# Google APIs (requires billing)


# OpenWeatherMap (free tier available)
OPENWEATHER_API_KEY=your_openweather_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Bureau of Meteorology (free, no key required)
BOM_API_BASE_URL=http://www.bom.gov.au/fwo
```

## 🆓 Free Alternatives (No Billing Required)

### Option 1: Use Bureau of Meteorology (Australia)
- **Cost**: Free
- **Coverage**: Australia only
- **No API key required**

### Option 2: OpenStreetMap Nominatim (for geocoding)
- **Cost**: Free
- **Rate limit**: 1 request/second
- **Usage policy**: Must provide user agent

### Option 3: Free Weather APIs
- **OpenWeatherMap**: 1000 calls/day free
- **WeatherAPI**: 1 million calls/month free
- **MeteoBlue**: Limited free tier

## 🛠️ Next Steps

**Immediate (Free Options)**:
1. Sign up for OpenWeatherMap free account
2. Use BOM for Australian weather data
3. Use OpenStreetMap Nominatim for geocoding

**Long-term (Production)**:
1. Enable Google Cloud billing for advanced features
2. Consider paid weather API for global coverage
3. Implement caching to reduce API calls

## 💰 Cost Estimates

**Google Maps APIs** (with billing):
- Geocoding: $5 per 1000 requests
- Places: $32 per 1000 requests
- $200/month free credit

**Recommended for Development**:
- Start with free APIs
- Enable Google billing when ready for production
