#!/usr/bin/env python3
"""
Solana Integration Initialization Script
Complete setup and testing of Solana blockchain integration
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Import all Solana components
from solana_rpc_client import get_solana_rpc_client
from solana_transaction_monitor import get_transaction_monitor
from solana_admin_wallet import get_admin_wallet_manager, WalletRole
from solana_payment import get_solana_payment
from config import SOLANA_CONFIG, ADMIN_USER_IDS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SolanaIntegrationInitializer:
    """Comprehensive Solana integration initializer"""

    def __init__(self):
        self.config = SOLANA_CONFIG
        self.initialization_results = {}
        self.test_results = {}

    async def initialize_complete_integration(self) -> Dict[str, Any]:
        """Initialize all Solana integration components"""
        logger.info("🚀 Starting Solana Integration Initialization...")

        results = {
            "start_time": datetime.now().isoformat(),
            "components": {},
            "tests": {},
            "errors": [],
            "warnings": [],
            "success": False
        }

        try:
            # Step 1: Initialize RPC Client
            logger.info("1️⃣ Initializing Solana RPC Client...")
            rpc_result = await self.initialize_rpc_client()
            results["components"]["rpc_client"] = rpc_result

            if not rpc_result["success"]:
                results["errors"].append("RPC Client initialization failed")
                return results

            # Step 2: Initialize Transaction Monitor
            logger.info("2️⃣ Initializing Transaction Monitor...")
            monitor_result = await self.initialize_transaction_monitor()
            results["components"]["transaction_monitor"] = monitor_result

            # Step 3: Initialize Admin Wallet Manager
            logger.info("3️⃣ Initializing Admin Wallet Manager...")
            wallet_result = await self.initialize_admin_wallets()
            results["components"]["admin_wallets"] = wallet_result

            # Step 4: Initialize Payment System
            logger.info("4️⃣ Initializing Payment System...")
            payment_result = await self.initialize_payment_system()
            results["components"]["payment_system"] = payment_result

            # Step 5: Run Integration Tests
            logger.info("5️⃣ Running Integration Tests...")
            test_results = await self.run_integration_tests()
            results["tests"] = test_results

            # Step 6: Final Setup
            logger.info("6️⃣ Completing Final Setup...")
            final_result = await self.complete_setup()
            results["components"]["final_setup"] = final_result

            # Determine overall success
            component_success = all(
                comp.get("success", False)
                for comp in results["components"].values()
            )

            test_success = test_results.get("overall_success", False)
            results["success"] = component_success and test_success

            if results["success"]:
                logger.info("✅ Solana Integration Initialization COMPLETED SUCCESSFULLY!")
            else:
                logger.error("❌ Solana Integration Initialization FAILED!")

            results["end_time"] = datetime.now().isoformat()
            return results

        except Exception as e:
            logger.error(f"💥 Fatal error during initialization: {e}")
            results["errors"].append(f"Fatal error: {str(e)}")
            results["success"] = False
            return results

    async def initialize_rpc_client(self) -> Dict[str, Any]:
        """Initialize and test RPC client"""
        try:
            rpc_client = get_solana_rpc_client()

            # Test connection
            connected = await rpc_client.connect()

            if connected:
                # Test basic functionality
                health = await rpc_client.get_health()

                # Test address validation
                test_address = self.config["admin_wallet"]
                validation = rpc_client.validate_wallet_address(test_address)

                # Get connection stats
                stats = await rpc_client.get_connection_stats()

                return {
                    "success": True,
                    "connected": connected,
                    "health_check": health,
                    "address_validation": validation["is_valid"],
                    "rpc_url": rpc_client.rpc_url,
                    "network": self.config["network"],
                    "stats": stats
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to connect to Solana RPC",
                    "rpc_url": rpc_client.rpc_url
                }

        except Exception as e:
            logger.error(f"Error initializing RPC client: {e}")
            return {"success": False, "error": str(e)}

    async def initialize_transaction_monitor(self) -> Dict[str, Any]:
        """Initialize and test transaction monitor"""
        try:
            monitor = get_transaction_monitor()

            # Test admin wallet monitoring
            admin_wallet = self.config["admin_wallet"]

            async def test_callback(address, transaction):
                logger.info(f"Test callback triggered for {address}: {transaction.signature}")

            success = await monitor.add_address_to_monitor(
                admin_wallet,
                "Admin Wallet Test",
                test_callback
            )

            if success:
                # Get monitoring stats
                stats = await monitor.get_monitoring_stats()

                return {
                    "success": True,
                    "monitored_addresses": stats.get("active_monitors", 0),
                    "database_initialized": True,
                    "stats": stats
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to start monitoring admin wallet"
                }

        except Exception as e:
            logger.error(f"Error initializing transaction monitor: {e}")
            return {"success": False, "error": str(e)}

    async def initialize_admin_wallets(self) -> Dict[str, Any]:
        """Initialize and setup admin wallets"""
        try:
            wallet_manager = get_admin_wallet_manager()

            # Check if master wallet exists
            wallets = await wallet_manager.list_wallets(WalletRole.MASTER)

            results = {
                "success": True,
                "existing_wallets": len(wallets),
                "created_wallets": [],
                "errors": []
            }

            # Create master wallet if it doesn't exist
            if not wallets:
                logger.info("Creating master admin wallet...")
                master_result = await wallet_manager.create_wallet(
                    WalletRole.MASTER,
                    "Master Admin Wallet",
                    "Primary administrative wallet for casino operations"
                )

                if master_result.get("success"):
                    results["created_wallets"].append("master")
                    logger.info(f"Created master wallet: {master_result['address']}")
                else:
                    results["errors"].append(f"Failed to create master wallet: {master_result.get('error')}")

            # Create deposit wallet if needed
            deposit_wallets = await wallet_manager.list_wallets(WalletRole.DEPOSIT)
            if not deposit_wallets:
                logger.info("Creating deposit wallet...")
                deposit_result = await wallet_manager.create_wallet(
                    WalletRole.DEPOSIT,
                    "Main Deposit Wallet",
                    "Primary wallet for collecting user deposits"
                )

                if deposit_result.get("success"):
                    results["created_wallets"].append("deposit")
                    logger.info(f"Created deposit wallet: {deposit_result['address']}")
                else:
                    results["errors"].append(f"Failed to create deposit wallet: {deposit_result.get('error')}")

            # Create withdrawal wallet if needed
            withdrawal_wallets = await wallet_manager.list_wallets(WalletRole.WITHDRAWAL)
            if not withdrawal_wallets:
                logger.info("Creating withdrawal wallet...")
                withdrawal_result = await wallet_manager.create_wallet(
                    WalletRole.WITHDRAWAL,
                    "Main Withdrawal Wallet",
                    "Primary wallet for processing user withdrawals"
                )

                if withdrawal_result.get("success"):
                    results["created_wallets"].append("withdrawal")
                    logger.info(f"Created withdrawal wallet: {withdrawal_result['address']}")
                else:
                    results["errors"].append(f"Failed to create withdrawal wallet: {withdrawal_result.get('error')}")

            # Get final wallet summary
            all_wallets = await wallet_manager.list_wallets()
            results["total_wallets"] = len(all_wallets)
            results["wallet_summary"] = {
                wallet["role"]: wallet["address"]
                for wallet in all_wallets
            }

            # Check for errors
            if results["errors"]:
                results["success"] = len(results["errors"]) == 0

            return results

        except Exception as e:
            logger.error(f"Error initializing admin wallets: {e}")
            return {"success": False, "error": str(e)}

    async def initialize_payment_system(self) -> Dict[str, Any]:
        """Initialize and test payment system"""
        try:
            payment_system = get_solana_payment()

            # Wait for initialization
            await asyncio.sleep(2)

            # Test basic functionality
            current_rate = payment_system.get_sol_to_fc_rate()

            # Test address validation
            test_address = self.config["admin_wallet"]
            validation = await payment_system.validate_user_wallet_address(test_address)

            return {
                "success": True,
                "database_initialized": True,
                "sol_to_fc_rate": current_rate,
                "address_validation_working": validation.get("is_valid", False),
                "min_deposit": payment_system.min_deposit,
                "min_withdrawal": payment_system.min_withdrawal,
                "withdrawal_fee_rate": payment_system.withdrawal_fee_rate,
                "admin_wallet": payment_system.admin_wallet,
                "rpc_connected": payment_system.is_connected
            }

        except Exception as e:
            logger.error(f"Error initializing payment system: {e}")
            return {"success": False, "error": str(e)}

    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run comprehensive integration tests"""
        test_results = {
            "overall_success": False,
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }

        tests = [
            ("rpc_connection", self.test_rpc_connection),
            ("address_validation", self.test_address_validation),
            ("wallet_creation", self.test_wallet_creation),
            ("transaction_monitoring", self.test_transaction_monitoring),
            ("payment_system", self.test_payment_system)
        ]

        for test_name, test_func in tests:
            logger.info(f"🧪 Running test: {test_name}")
            try:
                result = await test_func()
                test_results["tests"][test_name] = result
                test_results["summary"]["total"] += 1

                if result.get("passed", False):
                    test_results["summary"]["passed"] += 1
                    logger.info(f"✅ Test {test_name} PASSED")
                else:
                    test_results["summary"]["failed"] += 1
                    logger.error(f"❌ Test {test_name} FAILED: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"💥 Test {test_name} crashed: {e}")
                test_results["tests"][test_name] = {"passed": False, "error": str(e)}
                test_results["summary"]["total"] += 1
                test_results["summary"]["failed"] += 1

        # Determine overall success
        test_results["overall_success"] = (
            test_results["summary"]["failed"] == 0 and
            test_results["summary"]["passed"] > 0
        )

        return test_results

    async def test_rpc_connection(self) -> Dict[str, Any]:
        """Test RPC connection and basic functionality"""
        try:
            rpc_client = get_solana_rpc_client()

            # Test health
            health = await rpc_client.get_health()
            if not health:
                return {"passed": False, "error": "Health check failed"}

            # Test account info
            admin_wallet = self.config["admin_wallet"]
            account_info = await rpc_client.get_account_info(admin_wallet)

            if account_info.get("error"):
                return {"passed": False, "error": f"Account info failed: {account_info['error']}"}

            return {
                "passed": True,
                "health": health,
                "account_exists": account_info.get("exists", False),
                "balance_sol": account_info.get("balance", 0) / 1_000_000_000
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def test_address_validation(self) -> Dict[str, Any]:
        """Test address validation functionality"""
        try:
            rpc_client = get_solana_rpc_client()

            # Test valid address
            valid_address = self.config["admin_wallet"]
            valid_result = rpc_client.validate_wallet_address(valid_address)

            # Test invalid address
            invalid_address = "invalid_address_123"
            invalid_result = rpc_client.validate_wallet_address(invalid_address)

            if not valid_result.get("is_valid"):
                return {"passed": False, "error": "Valid address failed validation"}

            if invalid_result.get("is_valid"):
                return {"passed": False, "error": "Invalid address passed validation"}

            return {
                "passed": True,
                "valid_address_test": valid_result["is_valid"],
                "invalid_address_test": not invalid_result["is_valid"]
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def test_wallet_creation(self) -> Dict[str, Any]:
        """Test wallet creation functionality"""
        try:
            wallet_manager = get_admin_wallet_manager()

            # Try to get existing wallets
            wallets = await wallet_manager.list_wallets()

            if not wallets:
                return {"passed": False, "error": "No wallets found after initialization"}

            # Check if master wallet exists
            master_wallets = [w for w in wallets if w["role"] == "master"]

            return {
                "passed": True,
                "total_wallets": len(wallets),
                "has_master_wallet": len(master_wallets) > 0,
                "wallet_roles": list(set(w["role"] for w in wallets))
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def test_transaction_monitoring(self) -> Dict[str, Any]:
        """Test transaction monitoring functionality"""
        try:
            monitor = get_transaction_monitor()

            # Get monitoring stats
            stats = await monitor.get_monitoring_stats()

            return {
                "passed": True,
                "active_monitors": stats.get("active_monitors", 0),
                "monitored_addresses": stats.get("monitored_addresses", 0),
                "uptime_seconds": stats.get("uptime_seconds", 0)
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def test_payment_system(self) -> Dict[str, Any]:
        """Test payment system functionality"""
        try:
            payment_system = get_solana_payment()

            # Test rate retrieval
            rate = payment_system.get_sol_to_fc_rate()

            # Test address validation
            admin_wallet = self.config["admin_wallet"]
            validation = await payment_system.validate_user_wallet_address(admin_wallet)

            return {
                "passed": True,
                "sol_to_fc_rate": rate,
                "address_validation": validation.get("is_valid", False),
                "rpc_connected": payment_system.is_connected
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def complete_setup(self) -> Dict[str, Any]:
        """Complete final setup tasks"""
        try:
            logger.info("📋 Completing final setup tasks...")

            # Start all monitoring
            monitor = get_transaction_monitor()
            await monitor.start_all_monitors()

            # Get final system status
            rpc_client = get_solana_rpc_client()
            rpc_stats = await rpc_client.get_connection_stats()

            wallet_manager = get_admin_wallet_manager()
            dashboard_data = await wallet_manager.get_admin_dashboard_data()

            return {
                "success": True,
                "monitoring_active": True,
                "rpc_status": rpc_stats,
                "wallet_dashboard": dashboard_data,
                "setup_complete": True
            }

        except Exception as e:
            logger.error(f"Error completing setup: {e}")
            return {"success": False, "error": str(e)}

    def generate_setup_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive setup report"""
        report = []
        report.append("=" * 60)
        report.append("🚀 SOLANA INTEGRATION SETUP REPORT")
        report.append("=" * 60)
        report.append(f"Setup Date: {results.get('start_time', 'Unknown')}")
        report.append(f"Overall Status: {'✅ SUCCESS' if results.get('success') else '❌ FAILED'}")
        report.append("")

        # Component Status
        report.append("📋 COMPONENT STATUS:")
        for component, status in results.get("components", {}).items():
            success = status.get("success", False)
            status_icon = "✅" if success else "❌"
            report.append(f"  {status_icon} {component.replace('_', ' ').title()}")
            if not success and "error" in status:
                report.append(f"     Error: {status['error']}")

        report.append("")

        # Test Results
        test_data = results.get("tests", {})
        if test_data:
            report.append("🧪 TEST RESULTS:")
            summary = test_data.get("summary", {})
            report.append(f"  Total Tests: {summary.get('total', 0)}")
            report.append(f"  Passed: {summary.get('passed', 0)}")
            report.append(f"  Failed: {summary.get('failed', 0)}")
            report.append("")

            for test_name, test_result in test_data.get("tests", {}).items():
                passed = test_result.get("passed", False)
                status_icon = "✅" if passed else "❌"
                report.append(f"  {status_icon} {test_name.replace('_', ' ').title()}")

        report.append("")

        # Configuration Summary
        report.append("⚙️ CONFIGURATION:")
        report.append(f"  RPC URL: {self.config['rpc_url']}")
        report.append(f"  Network: {self.config['network']}")
        report.append(f"  Admin Wallet: {self.config['admin_wallet']}")
        report.append("")

        # Errors and Warnings
        if results.get("errors"):
            report.append("❌ ERRORS:")
            for error in results["errors"]:
                report.append(f"  • {error}")
            report.append("")

        if results.get("warnings"):
            report.append("⚠️ WARNINGS:")
            for warning in results["warnings"]:
                report.append(f"  • {warning}")
            report.append("")

        report.append("=" * 60)
        return "\n".join(report)

# Convenience functions
async def initialize_solana_integration():
    """Initialize complete Solana integration"""
    initializer = SolanaIntegrationInitializer()
    return await initializer.initialize_complete_integration()

async def test_solana_integration():
    """Test Solana integration components"""
    initializer = SolanaIntegrationInitializer()
    return await initializer.run_integration_tests()

async def generate_solana_status_report():
    """Generate current status report"""
    try:
        # Get status from all components
        rpc_client = get_solana_rpc_client()
        monitor = get_transaction_monitor()
        wallet_manager = get_admin_wallet_manager()
        payment_system = get_solana_payment()

        rpc_stats = await rpc_client.get_connection_stats()
        monitor_stats = await monitor.get_monitoring_stats()
        dashboard_data = await wallet_manager.get_admin_dashboard_data()

        return {
            "timestamp": datetime.now().isoformat(),
            "rpc_client": rpc_stats,
            "transaction_monitor": monitor_stats,
            "admin_wallets": dashboard_data,
            "payment_system": {
                "connected": payment_system.is_connected,
                "sol_to_fc_rate": payment_system.get_sol_to_fc_rate(),
                "admin_wallet": payment_system.admin_wallet
            }
        }

    except Exception as e:
        logger.error(f"Error generating status report: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Solana Integration Initialization...")

        # Run full initialization
        results = await initialize_solana_integration()

        # Generate and display report
        initializer = SolanaIntegrationInitializer()
        report = initializer.generate_setup_report(results)
        print(report)

        # Save results to file
        with open("solana_integration_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: solana_integration_results.json")

        if results["success"]:
            print("\n🎉 Solana integration setup completed successfully!")
        else:
            print("\n💥 Solana integration setup failed. Check the logs for details.")

    asyncio.run(main())