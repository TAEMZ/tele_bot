# 📊 Bot Monitoring Guide

## ✅ Monitoring System Installed!

Your medical bot now has a complete monitoring system that tracks:
- Response times (total, AI, translation)
- User activity and statistics
- Language usage
- Error rates
- System uptime

## 🌐 Access Your Dashboard

### 1. **Web Dashboard** (Visual Interface)
Open in your browser:
```
http://localhost:8001/dashboard
```

**Features:**
- 📈 Real-time metrics display
- 📊 Language usage charts
- 👥 Top users list
- 🔄 Auto-refresh every 10 seconds
- 📱 Mobile-friendly responsive design

### 2. **JSON API Endpoint** (For Integrations)
```bash
curl http://localhost:8001/metrics
```

**Response includes:**
```json
{
    "total_requests": 150,
    "unique_users": 12,
    "average_response_time": 75.5,
    "average_translation_time": 2.3,
    "average_ai_time": 68.2,
    "requests_last_hour": 25,
    "error_count": 2,
    "error_rate": 1.33,
    "language_usage": {
        "en": 80,
        "am": 45,
        "om": 15,
        "so": 10
    },
    "top_users": [
        ["839545865", 45],
        ["123456789", 23]
    ],
    "uptime": "2:15:30",
    "start_time": "2025-10-07 10:23:52"
}
```

## 📋 What's Being Tracked

### Performance Metrics
- **Total Response Time**: Complete time from message to response
- **AI Generation Time**: How long Ollama takes to generate response
- **Translation Time**: Time spent translating to/from English
- **Average Response Time**: Rolling average of last 100 requests

### User Metrics
- **Total Requests**: All messages processed
- **Unique Users**: Number of different users
- **Requests per User**: Individual user activity
- **Requests Last Hour**: Recent activity level

### Language Metrics
- **Language Usage**: Count of requests per language
  - English (en)
  - Amharic (am)
  - Afan Oromo (om)
  - Tigrinya (ti)
  - Somali (so)

### System Health
- **Error Count**: Total errors encountered
- **Error Rate**: Percentage of failed requests
- **Uptime**: How long the bot has been running
- **Start Time**: When the bot was last restarted

## 🔍 How to Monitor

### Real-time Monitoring
```bash
# Watch metrics update every 2 seconds
watch -n 2 'curl -s http://localhost:8001/metrics | python3 -m json.tool'
```

### Check Response Times
```bash
curl -s http://localhost:8001/metrics | jq '.average_response_time'
```

### Check User Count
```bash
curl -s http://localhost:8001/metrics | jq '.unique_users'
```

### Check Language Usage
```bash
curl -s http://localhost:8001/metrics | jq '.language_usage'
```

## 🔧 Advanced Features

### Reset Metrics (Testing)
```bash
curl -X POST http://localhost:8001/metrics/reset
```

### Access from External Network
If you want to access the dashboard from another computer:

1. **Find your server IP:**
   ```bash
   ip addr show | grep inet
   ```

2. **Access from another device:**
   ```
   http://YOUR_SERVER_IP:8001/dashboard
   ```

## 📱 Dashboard Features

### Stats Cards
- 8 key metrics displayed in cards
- Hover animations for better UX
- Color-coded for quick scanning

### Language Chart
- Visual bar chart of language usage
- Shows relative usage percentages
- Auto-updates every 10 seconds

### Top Users
- See which users are most active
- Shows last 8 digits of user ID
- Request count per user

### Auto-Refresh
- Dashboard updates every 10 seconds automatically
- Manual refresh button available
- Real-time status indicator

## 📊 Example Use Cases

### Monitor Performance During Load
```bash
# Terminal 1: Watch metrics
watch -n 1 'curl -s http://localhost:8001/metrics | jq ".average_response_time, .requests_last_hour"'

# Terminal 2: Send test messages to bot
# Monitor how response times change
```

### Track Language Adoption
```bash
# See which languages users prefer
curl -s http://localhost:8001/metrics | jq '.language_usage' | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = sum(data.values())
for lang, count in sorted(data.items(), key=lambda x: x[1], reverse=True):
    pct = count/total*100
    print(f'{lang}: {count} ({pct:.1f}%)')
"
```

### Check System Health
```bash
# Quick health check
curl -s http://localhost:8001/metrics | jq '{
  uptime: .uptime,
  total_requests: .total_requests,
  error_rate: .error_rate,
  avg_response: .average_response_time
}'
```

## 🎯 Performance Targets

Based on your current setup:

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Avg Response Time | < 90s | ~65-90s | ✅ Good |
| Error Rate | < 5% | ~0-2% | ✅ Excellent |
| Requests/Hour | > 10 | Varies | 📊 Monitor |
| AI Generation Time | < 70s | ~60-70s | ✅ Good |
| Translation Time | < 5s | ~2-4s | ✅ Excellent |

## 🚀 Next Steps

1. **Monitor for 24 hours** to establish baseline metrics
2. **Identify bottlenecks** using the dashboard
3. **Optimize** slow components
4. **Scale** if user count grows

## 📝 Notes

- Metrics are stored in memory (reset on restart)
- Keeps last 100 response times for averages
- All times in seconds
- User IDs are hashed for privacy in logs

---

**Dashboard URL:** http://localhost:8001/dashboard
**API Endpoint:** http://localhost:8001/metrics
**Status:** ✅ Running
