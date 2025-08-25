# 🚀 Server Startup Guide

You now have **multiple ways** to start your weather visualization server:

## 🎯 **Option 1: Using .env file (RECOMMENDED)**

### Method A: Python Script
```bash
python start_server.py
```

### Method B: Batch File (Windows)
```bash
start_server.bat
```

### Method C: Direct uvicorn (still works)
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## ⚙️ **Configuration Details**

### Your `.env` file now contains:
```properties
DATABASE_URL=postgresql://postgres:password@localhost:5433/weatherdb
API_HOST=0.0.0.0
API_PORT=8000
```

### Benefits of using .env:
- ✅ **No need to type long commands**
- ✅ **Consistent configuration** across different environments
- ✅ **Easy to modify** database settings
- ✅ **Secure** - can exclude .env from version control
- ✅ **Cross-platform** - works on Windows, Mac, Linux

## 🔧 **How It Works**

1. **python-dotenv** automatically loads variables from `.env`
2. **main.py** reads `DATABASE_URL` from environment
3. **start_server.py** reads `API_HOST` and `API_PORT` settings
4. **No manual environment variable setting required**

## 🎉 **What You Can Do Now**

Just run any of these simple commands:

```bash
# Easiest way
python start_server.py

# Or use the batch file
start_server.bat

# Or the traditional way (still works)
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🔒 **Security Note**

For production, you should:
1. Add `.env` to your `.gitignore` file
2. Use different credentials for production
3. Set `ENVIRONMENT=production` in your production `.env`

## ✅ **Current Status**

Your server is now running with .env configuration and you can access:
- **Frontend**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
