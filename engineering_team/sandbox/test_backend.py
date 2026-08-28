"""
Test module for the trading simulation backend.
Uses Python standard library unittest.
"""

import unittest
from datetime import datetime, timezone
from backend import (
    TradingAccount,
    get_share_price,
    TEST_SHARE_PRICES,
    TransactionType,
    Transaction,
    HoldingReport,
    PortfolioReport,
    AccountError,
    InvalidAmountError,
    InsufficientFundsError,
    InsufficientHoldingsError,
    UnknownSymbolError,
    AccountAlreadyCreatedError,
    AccountNotCreatedError,
)


class TestTradingAccount(unittest.TestCase):
    """Test cases for TradingAccount class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.account = TradingAccount()

    def _create_account_with_deposit(self, initial_deposit: float = 1000.0) -> None:
        """Helper to create account with initial deposit."""
        self.account.create_account(initial_deposit)

    # Account Creation Tests
    def test_create_account_sets_initial_cash_and_net_deposits(self) -> None:
        """Test account creation sets cash and net deposits correctly."""
        txn = self.account.create_account(1000.0)

        self.assertTrue(self.account.is_created())
        self.assertEqual(self.account.get_cash_balance(), 1000.0)
        self.assertEqual(self.account.get_net_deposits(), 1000.0)
        self.assertEqual(len(self.account.get_transactions()), 1)
        self.assertEqual(txn.transaction_type, TransactionType.CREATE_ACCOUNT)
        self.assertEqual(txn.amount, 1000.0)
        self.assertEqual(txn.cash_balance_after, 1000.0)

    def test_create_account_twice_raises(self) -> None:
        """Test creating account twice raises AccountAlreadyCreatedError."""
        self.account.create_account(1000.0)

        with self.assertRaises(AccountAlreadyCreatedError):
            self.account.create_account(500.0)

    def test_create_account_with_non_positive_initial_deposit_raises(self) -> None:
        """Test creating account with non-positive deposit raises InvalidAmountError."""
        with self.assertRaises(InvalidAmountError):
            self.account.create_account(0)

        with self.assertRaises(InvalidAmountError):
            self.account.create_account(-100.0)

    # Deposit Tests
    def test_deposit_increases_cash_and_net_deposits(self) -> None:
        """Test deposit increases cash and net deposits."""
        self._create_account_with_deposit(1000.0)
        initial_cash = self.account.get_cash_balance()
        initial_net_deposits = self.account.get_net_deposits()
        initial_txn_count = len(self.account.get_transactions())

        txn = self.account.deposit(500.0)

        self.assertEqual(self.account.get_cash_balance(), initial_cash + 500.0)
        self.assertEqual(self.account.get_net_deposits(), initial_net_deposits + 500.0)
        self.assertEqual(len(self.account.get_transactions()), initial_txn_count + 1)
        self.assertEqual(txn.transaction_type, TransactionType.DEPOSIT)
        self.assertEqual(txn.amount, 500.0)

    def test_deposit_before_account_creation_raises(self) -> None:
        """Test deposit before account creation raises AccountNotCreatedError."""
        with self.assertRaises(AccountNotCreatedError):
            self.account.deposit(100.0)

    def test_deposit_non_positive_amount_raises(self) -> None:
        """Test deposit with non-positive amount raises InvalidAmountError."""
        self._create_account_with_deposit(1000.0)

        with self.assertRaises(InvalidAmountError):
            self.account.deposit(0)

        with self.assertRaises(InvalidAmountError):
            self.account.deposit(-50.0)

    # Withdraw Tests
    def test_withdraw_decreases_cash_and_net_deposits(self) -> None:
        """Test withdraw decreases cash and net deposits."""
        self._create_account_with_deposit(1000.0)
        initial_cash = self.account.get_cash_balance()
        initial_net_deposits = self.account.get_net_deposits()
        initial_txn_count = len(self.account.get_transactions())

        txn = self.account.withdraw(300.0)

        self.assertEqual(self.account.get_cash_balance(), initial_cash - 300.0)
        self.assertEqual(self.account.get_net_deposits(), initial_net_deposits - 300.0)
        self.assertEqual(len(self.account.get_transactions()), initial_txn_count + 1)
        self.assertEqual(txn.transaction_type, TransactionType.WITHDRAW)
        self.assertEqual(txn.amount, 300.0)

    def test_withdraw_more_than_cash_raises(self) -> None:
        """Test withdrawing more than cash raises InsufficientFundsError."""
        self._create_account_with_deposit(1000.0)
        initial_cash = self.account.get_cash_balance()
        initial_txn_count = len(self.account.get_transactions())

        with self.assertRaises(InsufficientFundsError):
            self.account.withdraw(1500.0)

        # State should be unchanged
        self.assertEqual(self.account.get_cash_balance(), initial_cash)
        self.assertEqual(len(self.account.get_transactions()), initial_txn_count)

    def test_withdraw_non_positive_amount_raises(self) -> None:
        """Test withdraw with non-positive amount raises InvalidAmountError."""
        self._create_account_with_deposit(1000.0)

        with self.assertRaises(InvalidAmountError):
            self.account.withdraw(0)

        with self.assertRaises(InvalidAmountError):
            self.account.withdraw(-50.0)

    # Buy Tests
    def test_buy_decreases_cash_and_adds_holdings(self) -> None:
        """Test buy decreases cash and adds holdings."""
        self._create_account_with_deposit(1000.0)
        initial_cash = self.account.get_cash_balance()
        initial_txn_count = len(self.account.get_transactions())

        txn = self.account.buy("AAPL", 2)

        self.assertEqual(self.account.get_cash_balance(), initial_cash - 300.0)  # 2 * 150
        self.assertEqual(self.account.get_holdings().get("AAPL"), 2)
        self.assertEqual(len(self.account.get_transactions()), initial_txn_count + 1)
        self.assertEqual(txn.transaction_type, TransactionType.BUY)
        self.assertEqual(txn.symbol, "AAPL")
        self.assertEqual(txn.quantity, 2)
        self.assertEqual(txn.share_price, 150.0)
        self.assertEqual(txn.amount, 300.0)

    def test_buy_multiple_times_accumulates_holdings(self) -> None:
        """Test buying multiple times accumulates holdings."""
        self._create_account_with_deposit(1000.0)

        self.account.buy("AAPL", 2)
        self.account.buy("AAPL", 3)

        self.assertEqual(self.account.get_holdings().get("AAPL"), 5)

    def test_buy_more_than_cash_allows_raises(self) -> None:
        """Test buying more than cash allows raises InsufficientFundsError."""
        self._create_account_with_deposit(1000.0)
        initial_cash = self.account.get_cash_balance()
        initial_holdings = dict(self.account.get_holdings())
        initial_txn_count = len(self.account.get_transactions())

        with self.assertRaises(InsufficientFundsError):
            self.account.buy("GOOGL", 1)  # 2800 > 1000

        # State should be unchanged
        self.assertEqual(self.account.get_cash_balance(), initial_cash)
        self.assertEqual(self.account.get_holdings(), initial_holdings)
        self.assertEqual(len(self.account.get_transactions()), initial_txn_count)

    def test_buy_requires_positive_integer_quantity(self) -> None:
        """Test buy requires positive integer quantity."""
        self._create_account_with_deposit(1000.0)

        with self.assertRaises(InvalidAmountError):
            self.account.buy("AAPL", 0)

        with self.assertRaises(InvalidAmountError):
            self.account.buy("AAPL", -1)

        with self.assertRaises(InvalidAmountError):
            self.account.buy("AAPL", 1.5)  # type: ignore

    # Sell Tests
    def test_sell_increases_cash_and_reduces_holdings(self) -> None:
        """Test sell increases cash and reduces holdings."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 3)  # Cost: 450, cash: 550
        cash_after_buy = self.account.get_cash_balance()
        initial_txn_count = len(self.account.get_transactions())

        txn = self.account.sell("AAPL", 1)  # Proceeds: 150

        self.assertEqual(self.account.get_cash_balance(), cash_after_buy + 150.0)
        self.assertEqual(self.account.get_holdings().get("AAPL"), 2)
        self.assertEqual(len(self.account.get_transactions()), initial_txn_count + 1)
        self.assertEqual(txn.transaction_type, TransactionType.SELL)
        self.assertEqual(txn.symbol, "AAPL")
        self.assertEqual(txn.quantity, 1)
        self.assertEqual(txn.share_price, 150.0)
        self.assertEqual(txn.amount, 150.0)

    def test_selling_all_shares_removes_holding(self) -> None:
        """Test selling all shares removes holding from dictionary."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)

        self.account.sell("AAPL", 2)

        self.assertNotIn("AAPL", self.account.get_holdings())

    def test_sell_more_than_owned_raises(self) -> None:
        """Test selling more than owned raises InsufficientHoldingsError."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)
        cash_before = self.account.get_cash_balance()
        holdings_before = dict(self.account.get_holdings())
        txn_count_before = len(self.account.get_transactions())

        with self.assertRaises(InsufficientHoldingsError):
            self.account.sell("AAPL", 5)

        # State should be unchanged
        self.assertEqual(self.account.get_cash_balance(), cash_before)
        self.assertEqual(self.account.get_holdings(), holdings_before)
        self.assertEqual(len(self.account.get_transactions()), txn_count_before)

    def test_sell_requires_positive_integer_quantity(self) -> None:
        """Test sell requires positive integer quantity."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 5)

        with self.assertRaises(InvalidAmountError):
            self.account.sell("AAPL", 0)

        with self.assertRaises(InvalidAmountError):
            self.account.sell("AAPL", -1)

        with self.assertRaises(InvalidAmountError):
            self.account.sell("AAPL", 1.5)  # type: ignore

    # Unknown Symbol Tests
    def test_unknown_symbol_raises(self) -> None:
        """Test unknown symbol raises UnknownSymbolError."""
        self._create_account_with_deposit(1000.0)

        with self.assertRaises(UnknownSymbolError):
            self.account.buy("MSFT", 1)

        with self.assertRaises(UnknownSymbolError):
            self.account.sell("MSFT", 1)

    # Symbol Normalization Tests
    def test_symbol_is_normalized(self) -> None:
        """Test symbol is normalized (uppercase, stripped)."""
        self._create_account_with_deposit(1000.0)

        self.account.buy(" aapl ", 1)

        self.assertIn("AAPL", self.account.get_holdings())
        self.assertNotIn("aapl", self.account.get_holdings())
        self.assertNotIn(" aapl ", self.account.get_holdings())

    # Holdings Report Tests
    def test_holdings_report_calculates_market_values(self) -> None:
        """Test holdings report calculates market values correctly."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)

        report = self.account.get_holdings_report()

        self.assertEqual(len(report), 1)
        holding = report[0]
        self.assertEqual(holding.symbol, "AAPL")
        self.assertEqual(holding.quantity, 2)
        self.assertEqual(holding.current_price, 150.0)
        self.assertEqual(holding.market_value, 300.0)

    def test_holdings_report_sorted_alphabetically(self) -> None:
        """Test holdings report is sorted alphabetically by symbol."""
        self._create_account_with_deposit(10000.0)
        self.account.buy("TSLA", 1)
        self.account.buy("AAPL", 1)
        self.account.buy("GOOGL", 1)

        report = self.account.get_holdings_report()

        symbols = [h.symbol for h in report]
        self.assertEqual(symbols, ["AAPL", "GOOGL", "TSLA"])

    # Portfolio Value Tests
    def test_portfolio_value_includes_cash_and_holdings(self) -> None:
        """Test portfolio value includes cash and holdings."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)  # Cost: 300, cash: 700, holdings: 300

        portfolio_value = self.account.calculate_portfolio_value()

        self.assertEqual(portfolio_value, 1000.0)  # 700 + 300

    def test_calculate_holdings_value(self) -> None:
        """Test calculate_holdings_value sums correctly."""
        self._create_account_with_deposit(10000.0)
        self.account.buy("AAPL", 2)   # 300
        self.account.buy("TSLA", 1)   # 250
        self.account.buy("GOOGL", 1)  # 2800

        holdings_value = self.account.calculate_holdings_value()

        self.assertEqual(holdings_value, 3350.0)  # 300 + 250 + 2800

    # Profit/Loss Tests
    def test_profit_loss_is_portfolio_value_minus_net_deposits(self) -> None:
        """Test profit/loss calculation."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)  # No price change, P/L = 0

        pnl = self.account.calculate_profit_loss()

        self.assertEqual(pnl, 0.0)

    def test_profit_loss_with_custom_price_provider(self) -> None:
        """Test profit/loss changes with price changes using custom provider."""
        # Create account with custom price provider that we can modify
        prices = {"AAPL": 150.0, "TSLA": 250.0, "GOOGL": 2800.0}

        def mutable_provider(symbol: str) -> float:
            norm = symbol.strip().upper()
            if norm not in prices:
                raise UnknownSymbolError(f"Unknown symbol: {symbol}")
            return prices[norm]

        account = TradingAccount(price_provider=mutable_provider)
        account.create_account(1000.0)
        account.buy("AAPL", 2)  # Cost: 300

        # Initial P/L should be 0
        self.assertEqual(account.calculate_profit_loss(), 0.0)

        # Change price
        prices["AAPL"] = 200.0  # Now holdings worth 400, cash 700, portfolio 1100, net_dep 1000, P/L = 100
        pnl = account.calculate_profit_loss()
        self.assertEqual(pnl, 100.0)

        # Change price down
        prices["AAPL"] = 100.0  # Holdings worth 200, cash 700, portfolio 900, net_dep 1000, P/L = -100
        pnl = account.calculate_profit_loss()
        self.assertEqual(pnl, -100.0)

    # Transaction Tests
    def test_transactions_are_listed_in_order(self) -> None:
        """Test transactions are listed in order with sequential IDs."""
        self._create_account_with_deposit(1000.0)
        self.account.deposit(500.0)
        self.account.buy("AAPL", 1)
        self.account.sell("AAPL", 1)
        self.account.withdraw(100.0)

        transactions = self.account.get_transactions()

        self.assertEqual(len(transactions), 5)
        for i, txn in enumerate(transactions):
            self.assertEqual(txn.transaction_id, i + 1)

        types = [txn.transaction_type for txn in transactions]
        self.assertEqual(types, [
            TransactionType.CREATE_ACCOUNT,
            TransactionType.DEPOSIT,
            TransactionType.BUY,
            TransactionType.SELL,
            TransactionType.WITHDRAW,
        ])

    # Defensive Copy Tests
    def test_get_holdings_returns_copy(self) -> None:
        """Test get_holdings returns a defensive copy."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)

        holdings = self.account.get_holdings()
        holdings["AAPL"] = 999
        holdings["FAKE"] = 100

        # Internal state should be unchanged
        self.assertEqual(self.account.get_holdings().get("AAPL"), 2)
        self.assertNotIn("FAKE", self.account.get_holdings())

    def test_get_transactions_returns_copy(self) -> None:
        """Test get_transactions returns a defensive copy."""
        self._create_account_with_deposit(1000.0)

        transactions = self.account.get_transactions()
        transactions.append("fake")  # type: ignore

        # Internal state should be unchanged
        self.assertEqual(len(self.account.get_transactions()), 1)

    # Portfolio Report Test
    def test_get_portfolio_report_returns_complete_snapshot(self) -> None:
        """Test get_portfolio_report returns complete portfolio snapshot."""
        self._create_account_with_deposit(1000.0)
        self.account.buy("AAPL", 2)

        report = self.account.get_portfolio_report()

        self.assertIsInstance(report, PortfolioReport)
        self.assertEqual(report.cash_balance, 700.0)
        self.assertEqual(report.holdings_value, 300.0)
        self.assertEqual(report.total_portfolio_value, 1000.0)
        self.assertEqual(report.net_deposits, 1000.0)
        self.assertEqual(report.profit_loss, 0.0)
        self.assertEqual(len(report.holdings), 1)
        self.assertEqual(report.holdings[0].symbol, "AAPL")

    # get_share_price Tests
    def test_get_share_price_returns_fixed_prices(self) -> None:
        """Test get_share_price returns correct fixed prices."""
        self.assertEqual(get_share_price("AAPL"), 150.0)
        self.assertEqual(get_share_price("TSLA"), 250.0)
        self.assertEqual(get_share_price("GOOGL"), 2800.0)

    def test_get_share_price_normalizes_symbol(self) -> None:
        """Test get_share_price normalizes symbol."""
        self.assertEqual(get_share_price(" aapl "), 150.0)
        self.assertEqual(get_share_price("tsla"), 250.0)

    def test_get_share_price_unknown_raises(self) -> None:
        """Test get_share_price raises for unknown symbol."""
        with self.assertRaises(UnknownSymbolError):
            get_share_price("MSFT")


class TestDataClasses(unittest.TestCase):
    """Test data class definitions."""

    def test_transaction_creation(self) -> None:
        """Test Transaction dataclass creation."""
        txn = Transaction(
            transaction_id=1,
            timestamp=datetime.now(timezone.utc),
            transaction_type=TransactionType.BUY,
            amount=300.0,
            symbol="AAPL",
            quantity=2,
            share_price=150.0,
            cash_balance_after=700.0,
            description="Test buy",
        )

        self.assertEqual(txn.transaction_id, 1)
        self.assertEqual(txn.transaction_type, TransactionType.BUY)
        self.assertEqual(txn.amount, 300.0)

    def test_holding_report_creation(self) -> None:
        """Test HoldingReport dataclass creation."""
        holding = HoldingReport(
            symbol="AAPL",
            quantity=2,
            current_price=150.0,
            market_value=300.0,
        )

        self.assertEqual(holding.symbol, "AAPL")
        self.assertEqual(holding.quantity, 2)
        self.assertEqual(holding.current_price, 150.0)
        self.assertEqual(holding.market_value, 300.0)

    def test_portfolio_report_creation(self) -> None:
        """Test PortfolioReport dataclass creation."""
        holding = HoldingReport("AAPL", 2, 150.0, 300.0)
        report = PortfolioReport(
            cash_balance=700.0,
            holdings_value=300.0,
            total_portfolio_value=1000.0,
            net_deposits=1000.0,
            profit_loss=0.0,
            holdings=[holding],
        )

        self.assertEqual(report.cash_balance, 700.0)
        self.assertEqual(report.holdings_value, 300.0)
        self.assertEqual(report.total_portfolio_value, 1000.0)
        self.assertEqual(report.net_deposits, 1000.0)
        self.assertEqual(report.profit_loss, 0.0)
        self.assertEqual(len(report.holdings), 1)


class TestExceptions(unittest.TestCase):
    """Test exception hierarchy."""

    def test_exception_hierarchy(self) -> None:
        """Test all custom exceptions inherit from AccountError."""
        self.assertTrue(issubclass(InvalidAmountError, AccountError))
        self.assertTrue(issubclass(InsufficientFundsError, AccountError))
        self.assertTrue(issubclass(InsufficientHoldingsError, AccountError))
        self.assertTrue(issubclass(UnknownSymbolError, AccountError))
        self.assertTrue(issubclass(AccountAlreadyCreatedError, AccountError))
        self.assertTrue(issubclass(AccountNotCreatedError, AccountError))

    def test_can_catch_all_as_account_error(self) -> None:
        """Test all specific exceptions can be caught as AccountError."""
        errors = [
            InvalidAmountError("test"),
            InsufficientFundsError("test"),
            InsufficientHoldingsError("test"),
            UnknownSymbolError("test"),
            AccountAlreadyCreatedError("test"),
            AccountNotCreatedError("test"),
        ]

        for error in errors:
            with self.assertRaises(AccountError):
                raise error


if __name__ == "__main__":
    unittest.main()