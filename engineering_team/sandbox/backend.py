"""
Backend module for the trading simulation account manager.
Contains all core trading/account logic.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional


# Constants
TEST_SHARE_PRICES: dict[str, float] = {
    "AAPL": 150.00,
    "TSLA": 250.00,
    "GOOGL": 2800.00,
}


# Price provider function
def get_share_price(symbol: str) -> float:
    """Get the current price for a share symbol."""
    normalized = symbol.strip().upper()
    if normalized not in TEST_SHARE_PRICES:
        raise UnknownSymbolError(f"Unknown symbol: {symbol}")
    return TEST_SHARE_PRICES[normalized]


# Exceptions
class AccountError(Exception):
    """Base exception for account errors."""
    pass


class InvalidAmountError(AccountError):
    """Raised when an amount or quantity is invalid."""
    pass


class InsufficientFundsError(AccountError):
    """Raised when there are insufficient funds for an operation."""
    pass


class InsufficientHoldingsError(AccountError):
    """Raised when attempting to sell more shares than owned."""
    pass


class UnknownSymbolError(AccountError):
    """Raised when a symbol is not supported."""
    pass


class AccountAlreadyCreatedError(AccountError):
    """Raised when attempting to create an account that already exists."""
    pass


class AccountNotCreatedError(AccountError):
    """Raised when operating on an account that hasn't been created."""
    pass


# Enums
class TransactionType(Enum):
    CREATE_ACCOUNT = "CREATE_ACCOUNT"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    BUY = "BUY"
    SELL = "SELL"


# Data Classes
@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    timestamp: datetime
    transaction_type: TransactionType
    amount: float = 0.0
    symbol: Optional[str] = None
    quantity: int = 0
    share_price: Optional[float] = None
    cash_balance_after: float = 0.0
    description: str = ""


@dataclass(frozen=True)
class HoldingReport:
    symbol: str
    quantity: int
    current_price: float
    market_value: float


@dataclass(frozen=True)
class PortfolioReport:
    cash_balance: float
    holdings_value: float
    total_portfolio_value: float
    net_deposits: float
    profit_loss: float
    holdings: list[HoldingReport]


# Main Service Class
class TradingAccount:
    def __init__(
        self,
        price_provider: Callable[[str], float] = get_share_price,
    ) -> None:
        self._price_provider = price_provider
        self._is_created = False
        self._cash_balance = 0.0
        self._net_deposits = 0.0
        self._holdings: dict[str, int] = {}
        self._transactions: list[Transaction] = []
        self._next_transaction_id = 1

    # Private helper methods
    def _normalize_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise UnknownSymbolError("Empty symbol")
        return normalized

    def _validate_positive_amount(self, amount: float, field_name: str) -> None:
        if amount <= 0:
            raise InvalidAmountError(f"{field_name} must be positive")

    def _validate_positive_quantity(self, quantity: int) -> None:
        if not isinstance(quantity, int) or quantity <= 0:
            raise InvalidAmountError("Quantity must be a positive integer")

    def _require_created(self) -> None:
        if not self._is_created:
            raise AccountNotCreatedError("Account not created. Call create_account first.")

    def _record_transaction(
        self,
        transaction_type: TransactionType,
        amount: float = 0.0,
        symbol: Optional[str] = None,
        quantity: int = 0,
        share_price: Optional[float] = None,
        description: str = "",
    ) -> Transaction:
        transaction = Transaction(
            transaction_id=self._next_transaction_id,
            timestamp=datetime.now(timezone.utc),
            transaction_type=transaction_type,
            amount=amount,
            symbol=symbol,
            quantity=quantity,
            share_price=share_price,
            cash_balance_after=self._cash_balance,
            description=description,
        )
        self._transactions.append(transaction)
        self._next_transaction_id += 1
        return transaction

    # Public methods
    def create_account(self, initial_deposit: float) -> Transaction:
        if self._is_created:
            raise AccountAlreadyCreatedError("Account already created")
        self._validate_positive_amount(initial_deposit, "Initial deposit")

        self._is_created = True
        self._cash_balance = initial_deposit
        self._net_deposits = initial_deposit

        return self._record_transaction(
            TransactionType.CREATE_ACCOUNT,
            amount=initial_deposit,
            description=f"Account created with initial deposit of ${initial_deposit:.2f}",
        )

    def deposit(self, amount: float) -> Transaction:
        self._require_created()
        self._validate_positive_amount(amount, "Deposit amount")

        self._cash_balance += amount
        self._net_deposits += amount

        return self._record_transaction(
            TransactionType.DEPOSIT,
            amount=amount,
            description=f"Deposited ${amount:.2f}",
        )

    def withdraw(self, amount: float) -> Transaction:
        self._require_created()
        self._validate_positive_amount(amount, "Withdrawal amount")

        if amount > self._cash_balance:
            raise InsufficientFundsError(
                f"Insufficient funds: cannot withdraw ${amount:.2f} (balance: ${self._cash_balance:.2f})"
            )

        self._cash_balance -= amount
        self._net_deposits -= amount

        return self._record_transaction(
            TransactionType.WITHDRAW,
            amount=amount,
            description=f"Withdrew ${amount:.2f}",
        )

    def buy(self, symbol: str, quantity: int) -> Transaction:
        self._require_created()
        normalized_symbol = self._normalize_symbol(symbol)
        self._validate_positive_quantity(quantity)

        share_price = self._price_provider(normalized_symbol)
        total_cost = share_price * quantity

        if total_cost > self._cash_balance:
            raise InsufficientFundsError(
                f"Insufficient funds: need ${total_cost:.2f} to buy {quantity} {normalized_symbol} "
                f"(balance: ${self._cash_balance:.2f})"
            )

        self._cash_balance -= total_cost
        self._holdings[normalized_symbol] = self._holdings.get(normalized_symbol, 0) + quantity

        return self._record_transaction(
            TransactionType.BUY,
            amount=total_cost,
            symbol=normalized_symbol,
            quantity=quantity,
            share_price=share_price,
            description=f"Bought {quantity} {normalized_symbol} @ ${share_price:.2f}",
        )

    def sell(self, symbol: str, quantity: int) -> Transaction:
        self._require_created()
        normalized_symbol = self._normalize_symbol(symbol)
        self._validate_positive_quantity(quantity)

        current_holding = self._holdings.get(normalized_symbol, 0)
        if current_holding < quantity:
            raise InsufficientHoldingsError(
                f"Insufficient holdings: cannot sell {quantity} {normalized_symbol} (owned: {current_holding})"
            )

        share_price = self._price_provider(normalized_symbol)
        total_value = share_price * quantity

        self._holdings[normalized_symbol] = current_holding - quantity
        if self._holdings[normalized_symbol] == 0:
            del self._holdings[normalized_symbol]

        self._cash_balance += total_value

        return self._record_transaction(
            TransactionType.SELL,
            amount=total_value,
            symbol=normalized_symbol,
            quantity=quantity,
            share_price=share_price,
            description=f"Sold {quantity} {normalized_symbol} @ ${share_price:.2f}",
        )

    def get_cash_balance(self) -> float:
        self._require_created()
        return self._cash_balance

    def get_net_deposits(self) -> float:
        self._require_created()
        return self._net_deposits

    def get_holdings(self) -> dict[str, int]:
        self._require_created()
        return dict(self._holdings)

    def get_holdings_report(self) -> list[HoldingReport]:
        self._require_created()
        reports = []
        for symbol in sorted(self._holdings.keys()):
            quantity = self._holdings[symbol]
            current_price = self._price_provider(symbol)
            market_value = quantity * current_price
            reports.append(HoldingReport(symbol, quantity, current_price, market_value))
        return reports

    def calculate_holdings_value(self) -> float:
        self._require_created()
        total = 0.0
        for symbol, quantity in self._holdings.items():
            current_price = self._price_provider(symbol)
            total += quantity * current_price
        return total

    def calculate_portfolio_value(self) -> float:
        self._require_created()
        return self._cash_balance + self.calculate_holdings_value()

    def calculate_profit_loss(self) -> float:
        self._require_created()
        return self.calculate_portfolio_value() - self._net_deposits

    def get_portfolio_report(self) -> PortfolioReport:
        self._require_created()
        holdings_report = self.get_holdings_report()
        holdings_value = self.calculate_holdings_value()
        return PortfolioReport(
            cash_balance=self._cash_balance,
            holdings_value=holdings_value,
            total_portfolio_value=self._cash_balance + holdings_value,
            net_deposits=self._net_deposits,
            profit_loss=self.calculate_profit_loss(),
            holdings=holdings_report,
        )

    def get_transactions(self) -> list[Transaction]:
        self._require_created()
        return list(self._transactions)

    def is_created(self) -> bool:
        return self._is_created