#!/usr/bin/env python3
"""
Solana Payment Webhook Server
Helius webhook'larını dinleyip otomatik ödeme işleme yapar
"""

import asyncio
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
import threading

# Import existing components
from helius_webhook import HeliusPaymentMonitor, get_payment_monitor
from enhanced_payment_processor import process_webhook_payment

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global payment monitor
payment_monitor = None

@app.route('/helius-webhook', methods=['POST'])
async def helius_webhook_handler():
    """Helius webhook endpoint - Otomatik ödeme işleme"""
    try:
        # Webhook verisini al
        webhook_data = request.get_json()

        if not webhook_data:
            return jsonify({"error": "No data received"}), 400

        logger.info(f"Received webhook data: {len(webhook_data)} transactions")

        # Payment monitor'u al
        global payment_monitor
        if not payment_monitor:
            payment_monitor = await get_payment_monitor()

        # Webhook verisini parse et
        from helius_webhook import HeliusWebhookManager
        webhook_manager = HeliusWebhookManager()
        transactions = webhook_manager.parse_webhook_data(webhook_data)

        # Her transaction'ı işle
        processed_count = 0
        for transaction_data in transactions:
            try:
                # Otomatik ödeme işleme
                result = await payment_monitor.process_webhook_payment(transaction_data)

                if result:
                    processed_count += 1
                    logger.info(f"✅ Processed payment: User {result['user_id']} received {result['fc_amount']} FC")

                    # Telegram bildirim gönder
                    await send_payment_notification(result)

            except Exception as e:
                logger.error(f"Error processing transaction {transaction_data.signature}: {e}")

        return jsonify({
            "success": True,
            "message": f"Processed {processed_count}/{len(transactions)} transactions"
        }), 200

    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        return jsonify({"error": str(e)}), 500

async def send_payment_notification(result):
    """Kullanıcıya ödeme bildirimi gönder"""
    try:
        import telegram
        from config import BOT_TOKEN

        bot = telegram.Bot(token=BOT_TOKEN)

        message = f"""✅ **ÖDEMENİZ ONAYLANDI!** ✅

🎉 **Tebrikler!** Solana ödemeniz otomatik olarak işlendi.

💰 **İşlem Detayları:**
• SOL Miktarı: {result['sol_amount']:.6f} SOL
• Eklenen FC: **{result['fc_amount']:,} FC**
• Yeni Bakiye: **{result['new_balance']:,} FC**

🔗 **Transaction:**
`{result['transaction_signature']}`

🚀 **Artık oynamaya hazırsınız!**"""

        await bot.send_message(
            chat_id=result['user_id'],
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error sending notification: {e}")

@app.route('/webhook-status', methods=['GET'])
def webhook_status():
    """Webhook durumu kontrolü"""
    return jsonify({
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoint": "/helius-webhook"
    })

def run_webhook_server(host='0.0.0.0', port=8080):
    """Webhook server'ını başlat"""
    logger.info(f"Starting webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=False)

def start_webhook_server_thread(host='0.0.0.0', port=8080):
    """Webhook server'ını thread'de başlat"""
    server_thread = threading.Thread(
        target=run_webhook_server,
        args=(host, port),
        daemon=True
    )
    server_thread.start()
    logger.info("Webhook server started in background thread")
    return server_thread

if __name__ == "__main__":
    # Test için direct çalıştırma
    run_webhook_server()