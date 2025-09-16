#!/usr/bin/env python3
"""
CryptoBot Payment System Integration
Based on GitHub CasinoBot implementation with enhancements
"""

import asyncio
import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)

class CryptoBotPaymentProcessor:
    """Enhanced CryptoBot payment processor with deposit/withdrawal functionality"""
    
    def __init__(self, api_token: str, testnet: bool = False):
        self.api_token = api_token
        self.testnet = testnet
        self.base_url = "https://testnet-pay.crypt.bot/api" if testnet else "https://pay.crypt.bot/api"
        self.session = None
        self.supported_assets = ['USDT', 'TON', 'BTC', 'ETH', 'TRX', 'BNB']
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to CryptoBot"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Crypto-Pay-API-Token': self.api_token,
            'Content-Type': 'application/json'
        }
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.request(method, url, headers=headers, json=data) as response:
                result = await response.json()
                
                if not result.get('ok'):
                    logger.error(f"CryptoBot API error: {result}")
                    raise Exception(f"API Error: {result.get('error', 'Unknown error')}")
                    
                return result.get('result', {})
                
        except Exception as e:
            logger.error(f"CryptoBot request failed: {e}")
            raise
            
    async def get_me(self) -> Dict:
        """Get current app info"""
        return await self._make_request('GET', 'getMe')
        
    async def get_balance(self) -> List[Dict]:
        """Get account balance for all assets"""
        return await self._make_request('GET', 'getBalance')
        
    async def get_exchange_rates(self) -> List[Dict]:
        """Get current exchange rates"""
        return await self._make_request('GET', 'getExchangeRates')
        
    async def create_invoice(self, asset: str, amount: float, description: str = None, 
                           expires_in: int = 3600, user_id: int = None) -> Dict:
        """Create payment invoice for deposit"""
        data = {
            'asset': asset.upper(),
            'amount': str(amount),
            'expires_in': expires_in
        }
        
        if description:
            data['description'] = description
            
        if user_id:
            data['payload'] = json.dumps({'user_id': user_id, 'type': 'deposit'})
            
        return await self._make_request('POST', 'createInvoice', data)
        
    async def get_invoices(self, asset: str = None, status: str = None, 
                          offset: int = 0, count: int = 100) -> Dict:
        """Get list of invoices"""
        params = {
            'offset': offset,
            'count': count
        }
        
        if asset:
            params['asset'] = asset.upper()
        if status:
            params['status'] = status
            
        # Convert params to query string
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"getInvoices?{query_params}"
        
        return await self._make_request('GET', endpoint)
        
    async def transfer(self, user_id: int, asset: str, amount: float, 
                      spend_id: str = None, comment: str = None) -> Dict:
        """Transfer funds to user (withdrawal)"""
        data = {
            'user_id': user_id,
            'asset': asset.upper(),
            'amount': str(amount)
        }
        
        if spend_id:
            data['spend_id'] = spend_id
        if comment:
            data['comment'] = comment
            
        return await self._make_request('POST', 'transfer', data)
        
    async def create_check(self, asset: str, amount: float, pin_to_user_id: int = None,
                          pin_to_username: str = None) -> Dict:
        """Create a check for smaller withdrawals"""
        data = {
            'asset': asset.upper(),
            'amount': str(amount)
        }
        
        if pin_to_user_id:
            data['pin_to_user_id'] = pin_to_user_id
        if pin_to_username:
            data['pin_to_username'] = pin_to_username
            
        return await self._make_request('POST', 'createCheck', data)
        
    async def delete_check(self, check_id: int) -> bool:
        """Delete/cancel a check"""
        data = {'check_id': check_id}
        result = await self._make_request('POST', 'deleteCheck', data)
        return result.get('ok', False)
        
    async def get_checks(self, asset: str = None, status: str = None,
                        offset: int = 0, count: int = 100) -> Dict:
        """Get list of checks"""
        params = {
            'offset': offset,
            'count': count
        }
        
        if asset:
            params['asset'] = asset.upper()
        if status:
            params['status'] = status
            
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"getChecks?{query_params}"
        
        return await self._make_request('GET', endpoint)

class CasinoPaymentManager:
    """Enhanced casino payment manager with deposit/withdrawal processing"""
    
    def __init__(self, crypto_processor: CryptoBotPaymentProcessor, database_manager):
        self.crypto = crypto_processor
        self.db = database_manager
        self.min_deposit = 1.0  # USDT
        self.min_withdrawal = 5.0  # USDT
        self.max_withdrawal = 1000.0  # USDT
        self.withdrawal_fee = 0.1  # 10% fee
        self.small_transfer_threshold = 1.0  # Use check for transfers < 1 USDT
        
    async def process_deposit(self, user_id: int, amount: float, asset: str = 'USDT') -> Dict:
        """Process user deposit"""
        try:
            # Validate minimum deposit
            if amount < self.min_deposit:
                return {
                    'success': False,
                    'error': f'Minimum deposit is {self.min_deposit} {asset}'
                }
                
            # Create invoice
            invoice = await self.crypto.create_invoice(
                asset=asset,
                amount=amount,
                description=f'Casino Deposit - User {user_id}',
                user_id=user_id,
                expires_in=3600  # 1 hour
            )
            
            # Store pending deposit in database
            await self._store_pending_deposit(user_id, amount, asset, invoice['invoice_id'])
            
            return {
                'success': True,
                'invoice': invoice,
                'payment_url': invoice['pay_url'],
                'amount': amount,
                'asset': asset
            }
            
        except Exception as e:
            logger.error(f"Deposit processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def process_withdrawal(self, user_id: int, amount: float, asset: str = 'USDT') -> Dict:
        """Process user withdrawal"""
        try:
            # Validate withdrawal limits
            if amount < self.min_withdrawal:
                return {
                    'success': False,
                    'error': f'Minimum withdrawal is {self.min_withdrawal} {asset}'
                }
                
            if amount > self.max_withdrawal:
                return {
                    'success': False,
                    'error': f'Maximum withdrawal is {self.max_withdrawal} {asset}'
                }
                
            # Check user balance
            user_balance = await self._get_user_balance(user_id, asset)
            if user_balance < amount:
                return {
                    'success': False,
                    'error': 'Insufficient balance'
                }
                
            # Calculate fee
            fee_amount = amount * self.withdrawal_fee
            net_amount = amount - fee_amount
            
            # Generate unique spend_id
            spend_id = f"withdrawal_{user_id}_{int(time.time())}"
            
            try:
                # Process withdrawal
                if net_amount < self.small_transfer_threshold:
                    # Use check for small amounts
                    result = await self.crypto.create_check(
                        asset=asset,
                        amount=net_amount,
                        pin_to_user_id=user_id
                    )
                    
                    # Update user balance
                    await self._update_user_balance(user_id, -amount, asset)
                    
                    # Log transaction
                    await self._log_transaction(user_id, 'withdrawal_check', amount, asset, {
                        'check_id': result['check_id'],
                        'check_url': result['url'],
                        'fee': fee_amount,
                        'net_amount': net_amount
                    })
                    
                    return {
                        'success': True,
                        'type': 'check',
                        'check_url': result['url'],
                        'amount': amount,
                        'fee': fee_amount,
                        'net_amount': net_amount,
                        'asset': asset
                    }
                else:
                    # Use direct transfer
                    result = await self.crypto.transfer(
                        user_id=user_id,
                        asset=asset,
                        amount=net_amount,
                        spend_id=spend_id,
                        comment=f'Casino withdrawal - {net_amount} {asset}'
                    )
                    
                    # Update user balance
                    await self._update_user_balance(user_id, -amount, asset)
                    
                    # Log transaction
                    await self._log_transaction(user_id, 'withdrawal_transfer', amount, asset, {
                        'transfer_id': result['transfer_id'],
                        'fee': fee_amount,
                        'net_amount': net_amount
                    })
                    
                    return {
                        'success': True,
                        'type': 'transfer',
                        'transfer_id': result['transfer_id'],
                        'amount': amount,
                        'fee': fee_amount,
                        'net_amount': net_amount,
                        'asset': asset
                    }
                    
            except Exception as transfer_error:
                logger.error(f"Transfer/check creation failed: {transfer_error}")
                return {
                    'success': False,
                    'error': f'Transfer failed: {str(transfer_error)}'
                }
                
        except Exception as e:
            logger.error(f"Withdrawal processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    async def check_pending_deposits(self) -> List[Dict]:
        """Check for completed deposits and update user balances"""
        try:
            # Get recent invoices
            invoices = await self.crypto.get_invoices(status='paid')
            completed_deposits = []
            
            for invoice in invoices.get('items', []):
                # Check if we have this invoice in pending deposits
                pending = await self._get_pending_deposit(invoice['invoice_id'])
                if pending and not pending.get('processed'):
                    # Process the deposit
                    await self._complete_deposit(pending)
                    completed_deposits.append(pending)
                    
            return completed_deposits
            
        except Exception as e:
            logger.error(f"Error checking pending deposits: {e}")
            return []
            
    async def get_user_transaction_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's transaction history"""
        try:
            with self.db.get_connection() as conn:
                transactions = conn.execute('''
                    SELECT * FROM payment_transactions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_id, limit)).fetchall()
                
                return [dict(tx) for tx in transactions]
                
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
            
    async def _store_pending_deposit(self, user_id: int, amount: float, asset: str, invoice_id: str):
        """Store pending deposit in database"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO pending_deposits 
                    (user_id, amount, asset, invoice_id, created_at, processed)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, amount, asset, invoice_id, datetime.now().isoformat(), False))
                
        except Exception as e:
            logger.error(f"Error storing pending deposit: {e}")
            
    async def _get_pending_deposit(self, invoice_id: str) -> Optional[Dict]:
        """Get pending deposit by invoice ID"""
        try:
            with self.db.get_connection() as conn:
                result = conn.execute('''
                    SELECT * FROM pending_deposits WHERE invoice_id = ?
                ''', (invoice_id,)).fetchone()
                
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Error getting pending deposit: {e}")
            return None
            
    async def _complete_deposit(self, pending_deposit: Dict):
        """Complete a pending deposit"""
        try:
            user_id = pending_deposit['user_id']
            amount = pending_deposit['amount']
            asset = pending_deposit['asset']
            
            # Update user balance
            await self._update_user_balance(user_id, amount, asset)
            
            # Mark as processed
            with self.db.get_connection() as conn:
                conn.execute('''
                    UPDATE pending_deposits 
                    SET processed = ?, processed_at = ?
                    WHERE invoice_id = ?
                ''', (True, datetime.now().isoformat(), pending_deposit['invoice_id']))
                
            # Log transaction
            await self._log_transaction(user_id, 'deposit', amount, asset, {
                'invoice_id': pending_deposit['invoice_id']
            })
            
        except Exception as e:
            logger.error(f"Error completing deposit: {e}")
            
    async def _get_user_balance(self, user_id: int, asset: str) -> float:
        """Get user balance for specific asset"""
        try:
            with self.db.get_connection() as conn:
                result = conn.execute('''
                    SELECT balance FROM user_crypto_balances 
                    WHERE user_id = ? AND asset = ?
                ''', (user_id, asset)).fetchone()
                
                return result['balance'] if result else 0.0
                
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return 0.0
            
    async def _update_user_balance(self, user_id: int, amount: float, asset: str):
        """Update user balance"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_crypto_balances 
                    (user_id, asset, balance, updated_at)
                    VALUES (?, ?, 
                        COALESCE((SELECT balance FROM user_crypto_balances WHERE user_id = ? AND asset = ?), 0) + ?,
                        ?)
                ''', (user_id, asset, user_id, asset, amount, datetime.now().isoformat()))
                
        except Exception as e:
            logger.error(f"Error updating user balance: {e}")
            
    async def _log_transaction(self, user_id: int, tx_type: str, amount: float, asset: str, details: Dict):
        """Log transaction to database"""
        try:
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT INTO payment_transactions 
                    (user_id, type, amount, asset, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, tx_type, amount, asset, json.dumps(details), datetime.now().isoformat()))
                
        except Exception as e:
            logger.error(f"Error logging transaction: {e}")
            
    def get_user_payment_stats(self, user_id: int) -> Dict:
        """Get user payment statistics"""
        try:
            with self.db.get_connection() as conn:
                # Get total deposits
                total_deposits = conn.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM payment_transactions 
                    WHERE user_id = ? AND type = 'deposit'
                ''', (user_id,)).fetchone()[0]
                
                # Get total withdrawals
                total_withdrawals = conn.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM payment_transactions 
                    WHERE user_id = ? AND type LIKE 'withdrawal%'
                ''', (user_id,)).fetchone()[0]
                
                # Get daily deposits
                today = datetime.now().strftime('%Y-%m-%d')
                daily_deposited = conn.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM payment_transactions 
                    WHERE user_id = ? AND type = 'deposit' AND DATE(created_at) = ?
                ''', (user_id, today)).fetchone()[0]
                
                # Get daily withdrawals
                daily_withdrawn = conn.execute('''
                    SELECT COALESCE(SUM(amount), 0) FROM payment_transactions 
                    WHERE user_id = ? AND type LIKE 'withdrawal%' AND DATE(created_at) = ?
                ''', (user_id, today)).fetchone()[0]
                
                # Calculate remaining limits
                daily_deposit_limit = 10000000  # 10M FC daily limit
                daily_withdrawal_limit = 5000000  # 5M FC daily limit
                
                return {
                    'total_deposits': int(total_deposits),
                    'total_withdrawals': int(total_withdrawals),
                    'net_profit': int(total_deposits - total_withdrawals),
                    'total_bonuses': 0,  # Would need bonus tracking
                    'daily_deposited': int(daily_deposited),
                    'daily_withdrawn': int(daily_withdrawn),
                    'daily_bets': 0,  # Would need bet tracking
                    'remaining_deposit': max(0, daily_deposit_limit - int(daily_deposited)),
                    'remaining_withdrawal': max(0, daily_withdrawal_limit - int(daily_withdrawn))
                }
                
        except Exception as e:
            logger.error(f"Error getting user payment stats: {e}")
            return {
                'total_deposits': 0,
                'total_withdrawals': 0,
                'net_profit': 0,
                'total_bonuses': 0,
                'daily_deposited': 0,
                'daily_withdrawn': 0,
                'daily_bets': 0,
                'remaining_deposit': 10000000,
                'remaining_withdrawal': 5000000
            }
            
    def create_deposit_invoice(self, user_id: int, amount: int, crypto: str) -> Dict:
        """Create deposit invoice for user"""
        try:
            # Convert FC to crypto amount
            crypto_rates = {
                'USDT': 0.001,  # 1000 FC = 1 USDT
                'TON': 0.0002,  # 5000 FC = 1 TON
                'BTC': 0.000000015,  # 66667 FC = 1 BTC
                'ETH': 0.0000003,  # 3333 FC = 1 ETH
                'TRX': 0.01,  # 100 FC = 1 TRX
                'BNB': 0.0000015  # 667 FC = 1 BNB
            }
            
            rate = crypto_rates.get(crypto, 0.001)
            crypto_amount = amount * rate
            
            # Check minimum amounts
            min_amounts = {
                'USDT': 1.0,
                'TON': 1.0,
                'BTC': 0.001,
                'ETH': 0.001,
                'TRX': 100.0,
                'BNB': 0.01
            }
            
            min_amount = min_amounts.get(crypto, 1.0)
            if crypto_amount < min_amount:
                return {
                    'success': False,
                    'error': f'Minimum {crypto} deposit is {min_amount}'
                }
            
            # Create a simple invoice URL (in real implementation, would call CryptoBot API)
            invoice_id = f"deposit_{user_id}_{int(time.time())}"
            invoice_url = f"https://t.me/CryptoBot?start=deposit_{invoice_id}"
            
            # Store pending deposit
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO pending_deposits 
                    (user_id, amount, asset, invoice_id, created_at, processed)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, crypto_amount, crypto, invoice_id, datetime.now().isoformat(), False))
            
            return {
                'success': True,
                'amount': crypto_amount,
                'currency': crypto,
                'invoice_url': invoice_url,
                'invoice_id': invoice_id,
                'network': crypto,
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating deposit invoice: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Utility functions for integration
async def create_payment_tables(db_manager):
    """Create required payment tables"""
    try:
        with db_manager.get_connection() as conn:
            # Pending deposits table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pending_deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    asset TEXT NOT NULL,
                    invoice_id TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    processed_at TEXT
                )
            ''')
            
            # User crypto balances table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_crypto_balances (
                    user_id INTEGER NOT NULL,
                    asset TEXT NOT NULL,
                    balance REAL DEFAULT 0.0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, asset)
                )
            ''')
            
            # Payment transactions log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS payment_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    asset TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Add indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_pending_deposits_user ON pending_deposits(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON payment_transactions(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_balances_user ON user_crypto_balances(user_id)')
            
    except Exception as e:
        logger.error(f"Error creating payment tables: {e}")
        raise