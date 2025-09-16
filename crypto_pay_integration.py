#!/usr/bin/env python3
"""
🚀 Crypto Pay API Integration Setup
Main integration file to setup enhanced payment system
"""

import asyncio
import logging
from config import CRYPTO_BOT_TOKEN, CRYPTO_TESTNET
from enhanced_crypto_pay_api import CryptoPayAPI, EnhancedPaymentManager
from payment_handlers import set_enhanced_payment_manager

logger = logging.getLogger(__name__)

async def initialize_crypto_pay_system(database_manager):
    """Initialize the enhanced Crypto Pay system"""
    try:
        if not CRYPTO_BOT_TOKEN:
            logger.warning("CRYPTO_BOT_TOKEN not found in config, enhanced payment system disabled")
            return None
            
        # Initialize Crypto Pay API
        crypto_api = CryptoPayAPI(CRYPTO_BOT_TOKEN, testnet=CRYPTO_TESTNET)
        
        # Test API connection
        async with crypto_api:
            try:
                app_info = await crypto_api.get_me()
                logger.info(f"Crypto Pay API connected successfully: {app_info.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to connect to Crypto Pay API: {e}")
                return None
        
        # Initialize Enhanced Payment Manager
        enhanced_pm = EnhancedPaymentManager(crypto_api, database_manager)
        
        # Initialize database tables
        await enhanced_pm.initialize_tables()
        
        # Set global payment manager
        set_enhanced_payment_manager(enhanced_pm)
        
        logger.info("Enhanced Crypto Pay system initialized successfully")
        return enhanced_pm
        
    except Exception as e:
        logger.error(f"Failed to initialize Crypto Pay system: {e}")
        return None

async def test_crypto_pay_features(enhanced_pm):
    """Test various Crypto Pay API features"""
    try:
        if not enhanced_pm:
            logger.info("Enhanced payment manager not available, skipping tests")
            return
            
        logger.info("Testing Crypto Pay API features...")
        
        async with enhanced_pm.crypto_api:
            # Test 1: Get app info
            app_info = await enhanced_pm.crypto_api.get_me()
            logger.info(f"✅ App Info: {app_info.get('name', 'N/A')}")
            
            # Test 2: Get supported currencies
            currencies = await enhanced_pm.crypto_api.get_currencies()
            logger.info(f"✅ Supported currencies: {len(currencies)} found")
            
            # Test 3: Get exchange rates
            try:
                rates = await enhanced_pm.crypto_api.get_exchange_rates()
                logger.info(f"✅ Exchange rates: {len(rates)} pairs available")
            except Exception as e:
                logger.warning(f"⚠️ Exchange rates not available: {e}")
            
            # Test 4: Get balance
            try:
                balances = await enhanced_pm.crypto_api.get_balance()
                logger.info(f"✅ Account balances: {len(balances)} assets")
            except Exception as e:
                logger.warning(f"⚠️ Balance check failed: {e}")
                
        logger.info("Crypto Pay API test completed")
        
    except Exception as e:
        logger.error(f"Error testing Crypto Pay features: {e}")

# Webhook handler for integration with main bot
async def setup_crypto_webhooks(app, enhanced_pm):
    """Setup webhook endpoints for Crypto Pay"""
    try:
        if not enhanced_pm:
            logger.warning("Enhanced payment manager not available, webhooks not set up")
            return
            
        from aiohttp import web
        
        async def handle_webhook(request):
            """Handle incoming Crypto Pay webhooks"""
            try:
                webhook_data = await request.json()
                logger.info(f"Received Crypto Pay webhook: {webhook_data.get('update_type')}")
                
                # Process webhook
                result = await enhanced_pm.process_webhook(webhook_data)
                
                if result['success']:
                    return web.Response(status=200, text='OK')
                else:
                    logger.error(f"Webhook processing failed: {result.get('error')}")
                    return web.Response(status=400, text='Processing failed')
                    
            except Exception as e:
                logger.error(f"Webhook handler error: {e}")
                return web.Response(status=500, text='Internal error')
        
        # Add webhook route
        app.router.add_post('/crypto-pay-webhook', handle_webhook)
        logger.info("Crypto Pay webhook endpoint set up at /crypto-pay-webhook")
        
    except Exception as e:
        logger.error(f"Error setting up webhooks: {e}")

def get_crypto_pay_menu_callbacks():
    """Get callback mappings for crypto pay menus"""
    return {
        # Enhanced menu callbacks
        'enhanced_crypto_rates': 'show_enhanced_crypto_rates',
        'enhanced_payment_stats': 'show_enhanced_payment_stats',
        'crypto_stats': 'show_enhanced_payment_stats',
        
        # Deposit callbacks with enhanced features
        'deposit_usdt_enhanced': 'handle_enhanced_deposit_usdt',
        'deposit_ton_enhanced': 'handle_enhanced_deposit_ton',
        'deposit_btc_enhanced': 'handle_enhanced_deposit_btc',
        'deposit_eth_enhanced': 'handle_enhanced_deposit_eth',
        
        # Withdrawal callbacks with enhanced features
        'withdraw_usdt_enhanced': 'handle_enhanced_withdraw_usdt',
        'withdraw_ton_enhanced': 'handle_enhanced_withdraw_ton',
        'withdraw_btc_enhanced': 'handle_enhanced_withdraw_btc',
        'withdraw_eth_enhanced': 'handle_enhanced_withdraw_eth',
        
        # Fiat currency support
        'deposit_fiat_usd': 'handle_fiat_deposit_usd',
        'deposit_fiat_eur': 'handle_fiat_deposit_eur',
        'deposit_fiat_rub': 'handle_fiat_deposit_rub',
        
        # Check management
        'manage_checks': 'show_check_management',
        'create_check': 'handle_create_check',
        'cancel_check': 'handle_cancel_check',
        
        # Advanced features
        'payment_analytics': 'show_payment_analytics',
        'transaction_history': 'show_transaction_history',
        'set_payment_preferences': 'show_payment_preferences'
    }

# Helper functions for integration
async def create_enhanced_deposit_invoice(user_id: int, amount: int, asset: str = 'USDT'):
    """Create enhanced deposit invoice with bonus calculation"""
    try:
        from payment_handlers import get_enhanced_payment_manager
        
        enhanced_pm = get_enhanced_payment_manager()
        if not enhanced_pm:
            return {'success': False, 'error': 'Enhanced payment system not available'}
            
        return await enhanced_pm.create_deposit_invoice(user_id, amount, asset)
        
    except Exception as e:
        logger.error(f"Error creating enhanced deposit invoice: {e}")
        return {'success': False, 'error': str(e)}

async def process_enhanced_withdrawal(user_id: int, amount: int, asset: str = 'USDT'):
    """Process enhanced withdrawal with checks or transfers"""
    try:
        from payment_handlers import get_enhanced_payment_manager
        
        enhanced_pm = get_enhanced_payment_manager()
        if not enhanced_pm:
            return {'success': False, 'error': 'Enhanced payment system not available'}
            
        return await enhanced_pm.process_withdrawal(user_id, amount, asset)
        
    except Exception as e:
        logger.error(f"Error processing enhanced withdrawal: {e}")
        return {'success': False, 'error': str(e)}

async def get_real_time_rates():
    """Get real-time cryptocurrency rates"""
    try:
        from payment_handlers import get_enhanced_payment_manager
        
        enhanced_pm = get_enhanced_payment_manager()
        if not enhanced_pm:
            return None
            
        async with enhanced_pm.crypto_api:
            rates = await enhanced_pm.crypto_api.get_exchange_rates()
            currencies = await enhanced_pm.crypto_api.get_currencies()
            
            return {
                'rates': rates,
                'currencies': currencies,
                'timestamp': asyncio.get_event_loop().time()
            }
            
    except Exception as e:
        logger.error(f"Error getting real-time rates: {e}")
        return None

async def get_user_crypto_stats(user_id: int):
    """Get comprehensive user crypto statistics"""
    try:
        from payment_handlers import get_enhanced_payment_manager
        
        enhanced_pm = get_enhanced_payment_manager()
        if not enhanced_pm:
            return None
            
        return await enhanced_pm.get_user_stats(user_id)
        
    except Exception as e:
        logger.error(f"Error getting user crypto stats: {e}")
        return None

# Configuration validation
def validate_crypto_pay_config():
    """Validate Crypto Pay configuration"""
    issues = []
    
    if not CRYPTO_BOT_TOKEN:
        issues.append("CRYPTO_BOT_TOKEN not set in environment variables")
    
    if CRYPTO_BOT_TOKEN and len(CRYPTO_BOT_TOKEN) < 32:
        issues.append("CRYPTO_BOT_TOKEN appears to be invalid (too short)")
    
    if CRYPTO_TESTNET is None:
        issues.append("CRYPTO_TESTNET not set, defaulting to True")
    
    if issues:
        for issue in issues:
            logger.warning(f"Config issue: {issue}")
        return False
    
    logger.info("Crypto Pay configuration validated successfully")
    return True

# Export main functions
__all__ = [
    'initialize_crypto_pay_system',
    'test_crypto_pay_features',
    'setup_crypto_webhooks',
    'get_crypto_pay_menu_callbacks',
    'create_enhanced_deposit_invoice',
    'process_enhanced_withdrawal',
    'get_real_time_rates',
    'get_user_crypto_stats',
    'validate_crypto_pay_config'
]