#!/usr/bin/env python3
"""
Database setup for webhook automatic payments
Otomatik ödeme sistemi için gerekli tabloları oluşturur
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def setup_webhook_tables(db_path: str = "casino_bot.db"):
    """Webhook sistemi için gerekli tabloları oluştur"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Pending transactions table - webhook sistemi için
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                expected_amount REAL NOT NULL,
                wallet_address TEXT NOT NULL,
                fc_amount INTEGER,
                status TEXT DEFAULT 'pending',
                transaction_signature TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        # Webhook events log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                transaction_signature TEXT,
                from_address TEXT,
                to_address TEXT,
                amount_sol REAL,
                amount_lamports INTEGER,
                user_id INTEGER,
                processed BOOLEAN DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Automatic deposits log (başarılı otomatik işlemler)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automatic_deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_signature TEXT NOT NULL,
                sol_amount REAL NOT NULL,
                fc_amount INTEGER NOT NULL,
                old_balance INTEGER NOT NULL,
                new_balance INTEGER NOT NULL,
                processing_method TEXT DEFAULT 'webhook',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        conn.commit()
        logger.info("✅ Webhook database tables created successfully")

        # Test database functionality
        cursor.execute("SELECT COUNT(*) FROM pending_transactions")
        cursor.execute("SELECT COUNT(*) FROM webhook_events")
        cursor.execute("SELECT COUNT(*) FROM automatic_deposits")

        logger.info("✅ Database tables verified")

    except Exception as e:
        logger.error(f"Error setting up webhook tables: {e}")
        raise
    finally:
        conn.close()

def add_pending_transaction(user_id: int, expected_amount: float, wallet_address: str, db_path: str = "casino_bot.db"):
    """Bekleyen işlem ekle"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pending_transactions (user_id, expected_amount, wallet_address)
            VALUES (?, ?, ?)
        """, (user_id, expected_amount, wallet_address))

        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Added pending transaction: ID {transaction_id}, User {user_id}, Amount {expected_amount} SOL")
        return transaction_id

    except Exception as e:
        logger.error(f"Error adding pending transaction: {e}")
        return None

def get_pending_transaction_by_criteria(wallet_address: str, amount: float, tolerance: float = 0.001, db_path: str = "casino_bot.db"):
    """Kriterlere göre bekleyen işlem bul"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Miktar toleransı ile arama
        cursor.execute("""
            SELECT id, user_id, expected_amount, wallet_address, created_at, status
            FROM pending_transactions
            WHERE wallet_address = ?
            AND status = 'pending'
            AND ABS(expected_amount - ?) <= ?
            ORDER BY created_at ASC
            LIMIT 1
        """, (wallet_address, amount, tolerance))

        result = cursor.fetchone()
        conn.close()

        return result

    except Exception as e:
        logger.error(f"Error finding pending transaction: {e}")
        return None

def confirm_transaction(transaction_id: int, transaction_signature: str, fc_amount: int, db_path: str = "casino_bot.db"):
    """İşlemi onayla"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pending_transactions
            SET status = 'confirmed',
                transaction_signature = ?,
                fc_amount = ?,
                confirmed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending'
        """, (transaction_signature, fc_amount, transaction_id))

        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"✅ Transaction {transaction_id} confirmed with signature {transaction_signature}")
            return True
        else:
            logger.warning(f"❌ Transaction {transaction_id} not found or already processed")
            return False

    except Exception as e:
        logger.error(f"Error confirming transaction: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Setup database tables
    print("🔧 Setting up webhook database tables...")
    setup_webhook_tables()
    print("✅ Database setup completed!")

    # Test functionality
    print("\n🧪 Testing database functionality...")

    # Test adding pending transaction
    test_transaction_id = add_pending_transaction(
        user_id=12345,
        expected_amount=0.1,
        wallet_address="DsJd8pDi44f82dRjG3zBnxrv2t32ZyfKUjz5cqFkdrY9"
    )

    if test_transaction_id:
        print(f"✅ Test transaction created: ID {test_transaction_id}")

        # Test finding transaction
        result = get_pending_transaction_by_criteria(
            wallet_address="DsJd8pDi44f82dRjG3zBnxrv2t32ZyfKUjz5cqFkdrY9",
            amount=0.1,
            tolerance=0.001
        )

        if result:
            print(f"✅ Test transaction found: {result}")

            # Test confirming transaction
            success = confirm_transaction(
                transaction_id=result[0],
                transaction_signature="test_signature_123",
                fc_amount=10
            )

            if success:
                print("✅ Test transaction confirmed successfully!")
            else:
                print("❌ Failed to confirm test transaction")
        else:
            print("❌ Test transaction not found")
    else:
        print("❌ Failed to create test transaction")

    print("\n🎯 Database setup and test completed!")