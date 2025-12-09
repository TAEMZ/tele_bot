from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.telegram_bot import bot
from app.metrics import get_metrics, reset_metrics
from app.model import safe_generate_response
import threading
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="Medical AI Telegram Bot")

class TestMessage(BaseModel):
    text: str
    language: str = "en"
    user_id: str = "stress_test"

@app.post("/test_chat")
async def test_chat_endpoint(msg: TestMessage):
    """Direct endpoint for stress testing the bot logic"""
    try:
        response = await safe_generate_response(msg.text, user_id=msg.user_id, target_language=msg.language)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in test_chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/health_check")
async def health_check_endpoint(msg: TestMessage):
    """Lightweight endpoint for stress testing without external API calls"""
    return {
        "status": "ok",
        "message": f"Received: {msg.text}",
        "language": msg.language,
        "timestamp": "2024-12-04"
    }

@app.get("/")
async def root():
    return {"message": "Medical AI Telegram Bot is running.", "metrics_url": "/metrics", "dashboard_url": "/dashboard"}

@app.get("/metrics")
async def metrics():
    """Get bot performance metrics"""
    return get_metrics()

@app.post("/metrics/reset")
async def reset_metrics_endpoint():
    """Reset metrics (admin only)"""
    reset_metrics()
    return {"message": "Metrics reset successfully"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Web dashboard for monitoring"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Medical Bot Monitoring Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
            .stat-label {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .stat-value {
                color: #333;
                font-size: 2.5em;
                font-weight: bold;
            }
            .stat-unit {
                color: #999;
                font-size: 0.6em;
            }
            .chart-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-bottom: 20px;
            }
            .chart-title {
                font-size: 1.3em;
                color: #333;
                margin-bottom: 15px;
            }
            .language-bar {
                background: #f0f0f0;
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
            }
            .language-bar-fill {
                background: linear-gradient(90deg, #667eea, #764ba2);
                height: 30px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                padding: 0 15px;
                color: white;
                font-weight: bold;
                transition: width 0.5s ease;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
            }
            .status-running {
                background: #10b981;
                color: white;
            }
            .refresh-btn {
                background: white;
                color: #667eea;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 1em;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                margin: 20px auto;
                display: block;
            }
            .refresh-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 7px 20px rgba(0,0,0,0.3);
            }
            .top-users {
                list-style: none;
            }
            .top-users li {
                background: #f9fafb;
                padding: 12px;
                margin: 8px 0;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .user-id {
                color: #667eea;
                font-weight: 600;
            }
            .request-count {
                background: #667eea;
                color: white;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 0.9em;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .loading {
                animation: pulse 1.5s infinite;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Medical Bot Dashboard</h1>

            <div style="text-align: center; margin-bottom: 20px;">
                <span class="status status-running">● RUNNING</span>
            </div>

            <div class="stats-grid" id="stats-grid">
                <!-- Stats will be loaded here -->
            </div>

            <div class="chart-card">
                <h2 class="chart-title">📊 Language Usage</h2>
                <div id="language-chart"></div>
            </div>

            <div class="chart-card">
                <h2 class="chart-title">👥 Top Users</h2>
                <ul class="top-users" id="top-users"></ul>
            </div>

            <button class="refresh-btn" onclick="loadMetrics()">🔄 Refresh Data</button>
        </div>

        <script>
            async function loadMetrics() {
                try {
                    const response = await fetch('/metrics');
                    const data = await response.json();

                    // Update stats grid
                    const statsGrid = document.getElementById('stats-grid');
                    statsGrid.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-label">Total Requests</div>
                            <div class="stat-value">${data.total_requests}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Unique Users</div>
                            <div class="stat-value">${data.unique_users}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg Response Time</div>
                            <div class="stat-value">${data.average_response_time} <span class="stat-unit">sec</span></div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg AI Time</div>
                            <div class="stat-value">${data.average_ai_time} <span class="stat-unit">sec</span></div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Avg Translation</div>
                            <div class="stat-value">${data.average_translation_time} <span class="stat-unit">sec</span></div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Requests (Last Hour)</div>
                            <div class="stat-value">${data.requests_last_hour}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Error Rate</div>
                            <div class="stat-value">${data.error_rate}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Uptime</div>
                            <div class="stat-value" style="font-size: 1.5em;">${data.uptime}</div>
                        </div>
                    `;

                    // Update language chart
                    const languageChart = document.getElementById('language-chart');
                    const maxRequests = Math.max(...Object.values(data.language_usage));
                    languageChart.innerHTML = Object.entries(data.language_usage).map(([lang, count]) => {
                        const percentage = maxRequests > 0 ? (count / maxRequests * 100) : 0;
                        const langNames = {
                            'en': 'English',
                            'am': 'Amharic (አማርኛ)',
                            'om': 'Afan Oromo',
                            'ti': 'Tigrinya (ትግርኛ)',
                            'so': 'Somali'
                        };
                        return `
                            <div class="language-bar">
                                <div class="language-bar-fill" style="width: ${percentage}%">
                                    ${langNames[lang] || lang}: ${count}
                                </div>
                            </div>
                        `;
                    }).join('');

                    // Update top users
                    const topUsers = document.getElementById('top-users');
                    if (data.top_users && data.top_users.length > 0) {
                        topUsers.innerHTML = data.top_users.map(([userId, count]) => `
                            <li>
                                <span class="user-id">User ${userId.slice(-8)}</span>
                                <span class="request-count">${count} requests</span>
                            </li>
                        `).join('');
                    } else {
                        topUsers.innerHTML = '<li>No users yet</li>';
                    }

                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }

            // Load metrics on page load
            loadMetrics();

            // Auto-refresh every 10 seconds
            setInterval(loadMetrics, 10000);
        </script>
    </body>
    </html>
    """

def start_bot():
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    logger.info("Telegram bot thread started")
     
