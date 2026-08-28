# Design: Simple Account Management System for Trading Simulation

## Goals

Build a single-user trading simulation account manager that supports:

- Creating an account with an initial deposit.
- Depositing funds.
- Withdrawing funds.
- Buying shares.
- Selling shares.
- Preventing invalid actions:
  - Withdrawals that would make cash balance negative.
  - Purchases that exceed available cash.
  - Sales of shares not owned.
- Reporting:
  - Current cash balance.
  - Current holdings.
  - Current portfolio market value.
  - Profit/loss relative to net deposited funds.
  - Full transaction history over time.
- Using a provided `get_share_price(symbol)` function with fixed test prices for `AAPL`, `TSLA`, and `GOOGL`.

All files must live in the same sandbox directory. No packages or subdirectories.

---

# File Structure

All files should be placed in the same directory:

```text
backend.py
app.py
test_backend.py
```

Optional if desired, but not required:

```text
README.md
```

---

# Backend Design

Assigned to: `backend_engineer`

Implement all core trading/account logic in `backend.py`.

The backend must be framework-independent and must not import Gradio.

Only standard library modules may be used.

Recommended standard library imports:

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional
```

Do not use third-party packages.

---

## Module: `backend.py`

### Responsibilities

`backend.py` owns:

- Account state.
- Cash balance.
- Net deposits.
- Holdings.
- Transactions.
- Validation rules.
- Portfolio valuation.
- Profit/loss calculation.
- Price lookup abstraction.

The frontend and tests should interact with the backend through a clean service class.

---

## Constants

Define the fixed test price map in `backend.py`.

```python
TEST_SHARE_PRICES: dict[str, float]
```

Expected values:

```text
AAPL  -> 150.00
TSLA  -> 250.00
GOOGL -> 2800.00
```

---

## Function: `get_share_price`

This is the provided/test implementation used by default.

Signature:

```python
def get_share_price(symbol: str) -> float:
```

Behavior:

- Normalize `symbol` by stripping whitespace and converting to uppercase.
- Return the fixed price for:
  - `AAPL`
  - `TSLA`
  - `GOOGL`
- Raise `UnknownSymbolError` for unsupported symbols.

---

## Enum: `TransactionType`

Use an enum for transaction types.

Signature:

```python
class TransactionType(Enum):
```

Members:

```text
CREATE_ACCOUNT
DEPOSIT
WITHDRAW
BUY
SELL
```

---

## Data Class: `Transaction`

Represents one account activity.

Signature:

```python
@dataclass(frozen=True)
class Transaction:
```

Fields:

```python
transaction_id: int
timestamp: datetime
transaction_type: TransactionType
amount: float = 0.0
symbol: Optional[str] = None
quantity: int = 0
share_price: Optional[float] = None
cash_balance_after: float = 0.0
description: str = ""
```

Notes:

- `amount` should be positive for deposits/withdrawals and total trade value for buys/sells.
- `quantity` should be positive for buys/sells.
- `share_price` should be populated for buys/sells.
- `cash_balance_after` captures the account cash balance immediately after the transaction.
- `timestamp` should use timezone-aware UTC time.

---

## Data Class: `HoldingReport`

Represents one row in the holdings report.

Signature:

```python
@dataclass(frozen=True)
class HoldingReport:
```

Fields:

```python
symbol: str
quantity: int
current_price: float
market_value: float
```

---

## Data Class: `PortfolioReport`

Represents a full account snapshot.

Signature:

```python
@dataclass(frozen=True)
class PortfolioReport:
```

Fields:

```python
cash_balance: float
holdings_value: float
total_portfolio_value: float
net_deposits: float
profit_loss: float
holdings: list[HoldingReport]
```

Definitions:

- `cash_balance`: uninvested cash.
- `holdings_value`: sum of current market values of all holdings.
- `total_portfolio_value`: `cash_balance + holdings_value`.
- `net_deposits`: total deposits minus total withdrawals.
- `profit_loss`: `total_portfolio_value - net_deposits`.

---

## Exceptions

Create custom exceptions for clear error handling.

### Base Exception

```python
class AccountError(Exception):
```

### Invalid Amount

```python
class InvalidAmountError(AccountError):
```

Raised when:

- Initial deposit is less than or equal to zero.
- Deposit amount is less than or equal to zero.
- Withdrawal amount is less than or equal to zero.
- Trade quantity is less than or equal to zero.

### Insufficient Funds

```python
class InsufficientFundsError(AccountError):
```

Raised when:

- Withdrawal amount exceeds cash balance.
- Buy total cost exceeds cash balance.

### Insufficient Holdings

```python
class InsufficientHoldingsError(AccountError):
```

Raised when:

- User attempts to sell more shares than they currently hold.

### Unknown Symbol

```python
class UnknownSymbolError(AccountError):
```

Raised when:

- Price lookup fails for an unsupported symbol.

### Account Already Created

```python
class AccountAlreadyCreatedError(AccountError):
```

Raised when:

- `create_account` is called more than once on the same account service.

### Account Not Created

```python
class AccountNotCreatedError(AccountError):
```

Raised when:

- Deposit, withdrawal, buy, sell, or reporting operation is attempted before account creation.

---

## Class: `TradingAccount`

Primary backend service class.

Signature:

```python
class TradingAccount:
```

### Constructor

```python
def __init__(
    self,
    price_provider: Callable[[str], float] = get_share_price,
) -> None:
```

Behavior:

- Store `price_provider`.
- Initialize:
  - created flag to `False`.
  - cash balance to `0.0`.
  - net deposits to `0.0`.
  - holdings to empty dictionary.
  - transactions to empty list.
  - next transaction id to `1`.

Internal state:

```python
self._price_provider: Callable[[str], float]
self._is_created: bool
self._cash_balance: float
self._net_deposits: float
self._holdings: dict[str, int]
self._transactions: list[Transaction]
self._next_transaction_id: int
```

---

## Public Methods

### Create Account

```python
def create_account(self, initial_deposit: float) -> Transaction:
```

Behavior:

- Raise `AccountAlreadyCreatedError` if account already exists.
- Validate `initial_deposit > 0`.
- Set account as created.
- Increase cash balance by initial deposit.
- Increase net deposits by initial deposit.
- Record a `CREATE_ACCOUNT` transaction.
- Return the created transaction.

---

### Deposit Funds

```python
def deposit(self, amount: float) -> Transaction:
```

Behavior:

- Require account to be created.
- Validate `amount > 0`.
- Increase cash balance.
- Increase net deposits.
- Record a `DEPOSIT` transaction.
- Return the created transaction.

---

### Withdraw Funds

```python
def withdraw(self, amount: float) -> Transaction:
```

Behavior:

- Require account to be created.
- Validate `amount > 0`.
- If `amount > cash_balance`, raise `InsufficientFundsError`.
- Decrease cash balance.
- Decrease net deposits.
- Record a `WITHDRAW` transaction.
- Return the created transaction.

Important:

- Withdrawal should only consider available cash.
- Do not automatically sell holdings to fund withdrawals.

---

### Buy Shares

```python
def buy(self, symbol: str, quantity: int) -> Transaction:
```

Behavior:

- Require account to be created.
- Normalize symbol to uppercase.
- Validate `quantity > 0`.
- Use `price_provider(symbol)` to get current share price.
- Calculate `total_cost = share_price * quantity`.
- If `total_cost > cash_balance`, raise `InsufficientFundsError`.
- Decrease cash balance by total cost.
- Increase holdings for the symbol by quantity.
- Record a `BUY` transaction.
- Return the created transaction.

---

### Sell Shares

```python
def sell(self, symbol: str, quantity: int) -> Transaction:
```

Behavior:

- Require account to be created.
- Normalize symbol to uppercase.
- Validate `quantity > 0`.
- Validate current holding quantity for symbol is at least `quantity`.
- Use `price_provider(symbol)` to get current share price.
- Calculate `total_value = share_price * quantity`.
- Decrease holding quantity.
- Remove symbol from holdings if resulting quantity is zero.
- Increase cash balance by total value.
- Record a `SELL` transaction.
- Return the created transaction.

Important:

- Selling shares does **not** change `net_deposits`.
- Profit/loss changes naturally through total portfolio value.

---

### Get Cash Balance

```python
def get_cash_balance(self) -> float:
```

Behavior:

- Require account to be created.
- Return current cash balance.

---

### Get Net Deposits

```python
def get_net_deposits(self) -> float:
```

Behavior:

- Require account to be created.
- Return net deposits.

---

### Get Raw Holdings

```python
def get_holdings(self) -> dict[str, int]:
```

Behavior:

- Require account to be created.
- Return a shallow copy of holdings.
- Must not expose mutable internal dictionary.

---

### Get Holdings Report

```python
def get_holdings_report(self) -> list[HoldingReport]:
```

Behavior:

- Require account to be created.
- For each held symbol:
  - Get current price.
  - Calculate market value.
- Return list sorted alphabetically by symbol.

---

### Calculate Holdings Value

```python
def calculate_holdings_value(self) -> float:
```

Behavior:

- Require account to be created.
- Sum `quantity * current_price` across all holdings.
- Return the total.

---

### Calculate Portfolio Value

```python
def calculate_portfolio_value(self) -> float:
```

Behavior:

- Require account to be created.
- Return `cash_balance + calculate_holdings_value()`.

---

### Calculate Profit/Loss

```python
def calculate_profit_loss(self) -> float:
```

Behavior:

- Require account to be created.
- Return `calculate_portfolio_value() - net_deposits`.

---

### Get Portfolio Report

```python
def get_portfolio_report(self) -> PortfolioReport:
```

Behavior:

- Require account to be created.
- Return complete portfolio snapshot:
  - cash balance.
  - holdings value.
  - total portfolio value.
  - net deposits.
  - profit/loss.
  - holdings report.

---

### Get Transactions

```python
def get_transactions(self) -> list[Transaction]:
```

Behavior:

- Require account to be created.
- Return a shallow copy of transactions.
- Must not expose mutable internal list.

---

### Is Created

```python
def is_created(self) -> bool:
```

Behavior:

- Return account-created flag.
- Does not raise if account is not created.

---

## Private Helper Methods

These should be internal implementation details.

### Normalize Symbol

```python
def _normalize_symbol(self, symbol: str) -> str:
```

Behavior:

- Strip whitespace.
- Convert to uppercase.
- Validate not empty.
- Raise `UnknownSymbolError` for empty symbol.

---

### Validate Positive Amount

```python
def _validate_positive_amount(self, amount: float, field_name: str) -> None:
```

Behavior:

- Raise `InvalidAmountError` if amount is not greater than zero.

---

### Validate Positive Quantity

```python
def _validate_positive_quantity(self, quantity: int) -> None:
```

Behavior:

- Raise `InvalidAmountError` if quantity is not an integer greater than zero.
- Reject floats such as `1.5`.

---

### Require Created

```python
def _require_created(self) -> None:
```

Behavior:

- Raise `AccountNotCreatedError` if account has not been created.

---

### Record Transaction

```python
def _record_transaction(
    self,
    transaction_type: TransactionType,
    amount: float = 0.0,
    symbol: Optional[str] = None,
    quantity: int = 0,
    share_price: Optional[float] = None,
    description: str = "",
) -> Transaction:
```

Behavior:

- Create a `Transaction`.
- Assign next transaction id.
- Use current UTC timestamp.
- Include current cash balance after operation.
- Append to internal transaction list.
- Increment next transaction id.
- Return transaction.

---

# Frontend Design

Assigned to: `frontend_engineer`

Implement the Gradio application in `app.py`.

The Gradio app should import and use the backend service from `backend.py`.

No business rules should be duplicated in the frontend. All validation and state mutation must happen through `TradingAccount`.

---

## Module: `app.py`

### Responsibilities

`app.py` owns:

- User interface layout.
- Calling backend methods from button handlers.
- Formatting backend reports for Gradio display.
- Displaying success/error messages.
- Maintaining per-session account state using `gr.State`.

---

## Gradio 6 API Guidance

Use Gradio 6 style APIs.

### Import

```python
import gradio as gr
```

### Blocks App

Use:

```python
with gr.Blocks(title="Trading Simulation Account Manager") as demo:
```

Launch with:

```python
if __name__ == "__main__":
    demo.launch()
```

### Component Creation

Use these components:

```python
gr.Markdown(...)
gr.State(...)
gr.Number(...)
gr.Textbox(...)
gr.Button(...)
gr.Dataframe(...)
gr.Row()
gr.Column()
gr.Tabs()
gr.Tab()
```

### Button Events

Use the Gradio 6 event listener style:

```python
button.click(
    fn=handler_function,
    inputs=[...],
    outputs=[...],
)
```

Important:

- `fn` should be passed by keyword.
- `inputs` can be a single component, a list of components, or `None`.
- `outputs` can be a single component, a list of components, or `None`.
- For multiple outputs, the handler must return the exact same number of values in the same order.
- Use direct return values to update components.
- Avoid relying on older patterns that return component `.update(...)` objects unless absolutely necessary.

### State

Use:

```python
account_state = gr.State(value=None)
```

Handlers that mutate the account should take the current state as input and return the possibly updated account state as one of the outputs.

Example pattern to follow conceptually:

```python
handler(account_state, user_input_1, user_input_2) -> tuple[object, ...]
```

The returned `TradingAccount` object should be assigned back to `account_state`.

### Dataframe

Use:

```python
gr.Dataframe(
    headers=[...],
    datatype=[...],
    row_count=...,
    col_count=...,
    interactive=False,
    label="...",
)
```

Important Gradio 6 notes:

- Prefer `gr.Dataframe`, not pandas-specific output.
- Do not require pandas.
- Return a `list[list[object]]` from handlers.
- Configure `headers` explicitly.
- Set `interactive=False` for report tables.
- Use `datatype=["str", "number", ...]` where useful.
- If row counts are dynamic, avoid fixed restrictive row limits; allow returned list length to vary.

### Number Inputs

Use:

```python
gr.Number(label="Amount", minimum=0)
```

or:

```python
gr.Number(label="Quantity", minimum=1, precision=0)
```

Notes:

- `gr.Number` may return `None` if empty.
- Quantity should still be validated by backend.
- Convert quantity to `int` in the frontend handler only after checking it is not `None`.
- Backend remains final source of validation.

### Textbox Inputs

Use:

```python
gr.Textbox(label="Symbol", placeholder="AAPL")
```

Normalize display can be handled by backend.

---

## Frontend Layout

Recommended layout:

### Header

```text
# Trading Simulation Account Manager
Manage a simulated trading account using fixed prices for AAPL, TSLA, and GOOGL.
```

### Account State

Use one `gr.State`:

```python
account_state = gr.State(value=None)
```

This should hold either:

- `None`, before account creation.
- A `TradingAccount` instance, after account creation.

---

## Main Sections

Use tabs for clarity.

### Tab 1: Account

Components:

```python
initial_deposit_input: gr.Number
create_account_button: gr.Button

deposit_amount_input: gr.Number
deposit_button: gr.Button

withdraw_amount_input: gr.Number
withdraw_button: gr.Button

status_output: gr.Textbox
```

Purpose:

- Create account.
- Deposit funds.
- Withdraw funds.
- Display success/errors.

---

### Tab 2: Trade

Components:

```python
trade_symbol_input: gr.Textbox
trade_quantity_input: gr.Number
buy_button: gr.Button
sell_button: gr.Button
trade_status_output: gr.Textbox
```

Purpose:

- Buy shares.
- Sell shares.
- Display success/errors.

---

### Tab 3: Reports

Components:

```python
refresh_report_button: gr.Button

cash_balance_output: gr.Number
holdings_value_output: gr.Number
portfolio_value_output: gr.Number
net_deposits_output: gr.Number
profit_loss_output: gr.Number

holdings_table: gr.Dataframe
transactions_table: gr.Dataframe

report_status_output: gr.Textbox
```

Purpose:

- Show current cash balance.
- Show holdings value.
- Show total portfolio value.
- Show net deposits.
- Show profit/loss.
- Show holdings table.
- Show transaction history.

---

## Frontend Helper Functions

Implement these in `app.py`.

### Create New Account Object

```python
def create_new_account() -> TradingAccount:
```

Behavior:

- Return a new `TradingAccount()`.

---

### Get Or Create Account

```python
def get_or_create_account(account: object | None) -> TradingAccount:
```

Behavior:

- If `account` is `None`, return `TradingAccount()`.
- If `account` is already a `TradingAccount`, return it.

Use this only for account creation. For deposit/trade/report operations, if account is `None`, display an error instead of silently creating.

---

### Format Currency

```python
def format_currency(value: float) -> str:
```

Behavior:

- Return value formatted with two decimals, e.g. `"$1,250.00"`.

This is for messages only. Numeric report fields should stay numeric.

---

### Format Transaction Type

```python
def format_transaction_type(transaction_type: TransactionType) -> str:
```

Behavior:

- Return a display-friendly string.

Examples:

```text
CREATE_ACCOUNT -> Create Account
DEPOSIT        -> Deposit
WITHDRAW       -> Withdraw
BUY            -> Buy
SELL           -> Sell
```

---

### Build Empty Holdings Rows

```python
def empty_holdings_rows() -> list[list[object]]:
```

Return:

```text
[]
```

---

### Build Empty Transaction Rows

```python
def empty_transaction_rows() -> list[list[object]]:
```

Return:

```text
[]
```

---

### Build Holdings Rows

```python
def build_holdings_rows(account: TradingAccount) -> list[list[object]]:
```

Each row:

```text
[
  symbol,
  quantity,
  current_price,
  market_value
]
```

---

### Build Transaction Rows

```python
def build_transaction_rows(account: TradingAccount) -> list[list[object]]:
```

Each row:

```text
[
  transaction_id,
  timestamp_iso_string,
  transaction_type_display,
  symbol_or_empty_string,
  quantity,
  share_price_or_empty_string,
  amount,
  cash_balance_after,
  description
]
```

Timestamp format should be readable, for example ISO format.

---

### Build Report Outputs

```python
def build_report_outputs(
    account: TradingAccount | None,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Returns, in order:

```text
cash_balance
holdings_value
portfolio_value
net_deposits
profit_loss
holdings_rows
transaction_rows
status_message
```

If account is `None` or not created:

```text
0.0
0.0
0.0
0.0
0.0
[]
[]
"Create an account to view reports."
```

---

## Frontend Event Handlers

All frontend handlers should catch `AccountError` and return user-friendly error messages.

Avoid catching broad exceptions unless used as a final fallback with a generic error message.

---

### Handle Create Account

```python
def handle_create_account(
    account: TradingAccount | None,
    initial_deposit: float | None,
) -> tuple[
    TradingAccount | None,
    str,
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Inputs:

```text
account_state
initial_deposit_input
```

Outputs:

```text
account_state
status_output
cash_balance_output
holdings_value_output
portfolio_value_output
net_deposits_output
profit_loss_output
holdings_table
transactions_table
report_status_output
```

Behavior:

- If account is `None`, create `TradingAccount()`.
- Call `create_account(initial_deposit)`.
- Return updated account and refreshed report outputs.
- On error, return original account and error message.

---

### Handle Deposit

```python
def handle_deposit(
    account: TradingAccount | None,
    amount: float | None,
) -> tuple[
    TradingAccount | None,
    str,
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Behavior:

- If account is `None`, return error message.
- Call `account.deposit(amount)`.
- Return updated account and refreshed report outputs.

---

### Handle Withdraw

```python
def handle_withdraw(
    account: TradingAccount | None,
    amount: float | None,
) -> tuple[
    TradingAccount | None,
    str,
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Behavior:

- If account is `None`, return error message.
- Call `account.withdraw(amount)`.
- Return updated account and refreshed report outputs.

---

### Handle Buy

```python
def handle_buy(
    account: TradingAccount | None,
    symbol: str,
    quantity: float | None,
) -> tuple[
    TradingAccount | None,
    str,
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Behavior:

- If account is `None`, return error message.
- Convert `quantity` to integer only if provided and whole-number-like.
- Call `account.buy(symbol, quantity_int)`.
- Return updated account and refreshed report outputs.

---

### Handle Sell

```python
def handle_sell(
    account: TradingAccount | None,
    symbol: str,
    quantity: float | None,
) -> tuple[
    TradingAccount | None,
    str,
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Behavior:

- If account is `None`, return error message.
- Convert `quantity` to integer only if provided and whole-number-like.
- Call `account.sell(symbol, quantity_int)`.
- Return updated account and refreshed report outputs.

---

### Handle Refresh Report

```python
def handle_refresh_report(
    account: TradingAccount | None,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    list[list[object]],
    list[list[object]],
    str,
]:
```

Behavior:

- Call `build_report_outputs(account)`.
- Return report values.

---

## Event Wiring

Use this style in `app.py`.

### Create Account Button

```python
create_account_button.click(
    fn=handle_create_account,
    inputs=[account_state, initial_deposit_input],
    outputs=[
        account_state,
        status_output,
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ],
)
```

### Deposit Button

```python
deposit_button.click(
    fn=handle_deposit,
    inputs=[account_state, deposit_amount_input],
    outputs=[
        account_state,
        status_output,
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ],
)
```

### Withdraw Button

```python
withdraw_button.click(
    fn=handle_withdraw,
    inputs=[account_state, withdraw_amount_input],
    outputs=[
        account_state,
        status_output,
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ],
)
```

### Buy Button

```python
buy_button.click(
    fn=handle_buy,
    inputs=[account_state, trade_symbol_input, trade_quantity_input],
    outputs=[
        account_state,
        trade_status_output,
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ],
)
```

### Sell Button

```python
sell_button.click(
    fn=handle_sell,
    inputs=[account_state, trade_symbol_input, trade_quantity_input],
    outputs=[
        account_state,
        trade_status_output,
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ],
)
```

### Refresh Report Button

```python
refresh_report_button.click(
    fn=handle_refresh_report,
    inputs=[account_state],
    outputs=[
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ],
)
```

---

## Recommended Dataframe Headers

### Holdings Table

```python
headers=[
    "Symbol",
    "Quantity",
    "Current Price",
    "Market Value",
]
```

Datatypes:

```python
datatype=[
    "str",
    "number",
    "number",
    "number",
]
```

---

### Transactions Table

```python
headers=[
    "ID",
    "Timestamp",
    "Type",
    "Symbol",
    "Quantity",
    "Share Price",
    "Amount",
    "Cash Balance After",
    "Description",
]
```

Datatypes:

```python
datatype=[
    "number",
    "str",
    "str",
    "str",
    "number",
    "str",
    "number",
    "number",
    "str",
]
```

Use string datatype for `Share Price` if empty string is used for non-trade transactions.

---

# Test Design

Assigned to: `test_engineer`

Implement backend unit tests in `test_backend.py`.

Use Python standard library `unittest`.

Do not test Gradio UI.

Tests should import from `backend.py`.

---

## Module: `test_backend.py`

### Responsibilities

- Verify account creation.
- Verify deposits and withdrawals.
- Verify buy and sell behavior.
- Verify holdings reports.
- Verify portfolio value.
- Verify profit/loss.
- Verify transaction history.
- Verify invalid operations raise the correct custom exceptions.
- Verify symbol normalization.

---

## Test Price Provider

Use either the backend default `get_share_price` or a deterministic custom provider.

Recommended helper:

```python
def fixed_price_provider(symbol: str) -> float:
```

Behavior:

- Return fixed prices:
  - `AAPL`: `150.0`
  - `TSLA`: `250.0`
  - `GOOGL`: `2800.0`
- Raise `UnknownSymbolError` for unsupported symbols.

---

## Test Class

```python
class TestTradingAccount(unittest.TestCase):
```

---

## Test Cases

### Account Creation

```python
def test_create_account_sets_initial_cash_and_net_deposits(self) -> None:
```

Verify:

- Account is created.
- Cash balance equals initial deposit.
- Net deposits equals initial deposit.
- One transaction exists.
- Transaction type is `CREATE_ACCOUNT`.

---

### Cannot Create Account Twice

```python
def test_create_account_twice_raises(self) -> None:
```

Verify:

- Second `create_account` call raises `AccountAlreadyCreatedError`.

---

### Initial Deposit Must Be Positive

```python
def test_create_account_with_non_positive_initial_deposit_raises(self) -> None:
```

Verify:

- `0` raises `InvalidAmountError`.
- Negative value raises `InvalidAmountError`.

---

### Deposit Increases Cash And Net Deposits

```python
def test_deposit_increases_cash_and_net_deposits(self) -> None:
```

Verify:

- Cash increases.
- Net deposits increases.
- Transaction count increases.
- Transaction type is `DEPOSIT`.

---

### Deposit Requires Created Account

```python
def test_deposit_before_account_creation_raises(self) -> None:
```

Verify:

- `AccountNotCreatedError`.

---

### Deposit Must Be Positive

```python
def test_deposit_non_positive_amount_raises(self) -> None:
```

Verify:

- `0` and negative values raise `InvalidAmountError`.

---

### Withdraw Decreases Cash And Net Deposits

```python
def test_withdraw_decreases_cash_and_net_deposits(self) -> None:
```

Verify:

- Cash decreases.
- Net deposits decreases.
- Transaction type is `WITHDRAW`.

---

### Cannot Withdraw More Than Cash

```python
def test_withdraw_more_than_cash_raises(self) -> None:
```

Verify:

- `InsufficientFundsError`.
- Cash remains unchanged.
- Transaction count remains unchanged after failed operation.

---

### Withdraw Must Be Positive

```python
def test_withdraw_non_positive_amount_raises(self) -> None:
```

Verify:

- `0` and negative values raise `InvalidAmountError`.

---

### Buy Shares Decreases Cash And Adds Holdings

```python
def test_buy_decreases_cash_and_adds_holdings(self) -> None:
```

Example:

- Create account with `1000`.
- Buy `2` `AAPL` at `150`.
- Cash becomes `700`.
- Holdings `AAPL` equals `2`.
- Transaction type is `BUY`.
- Transaction amount equals `300`.

---

### Buy Multiple Times Accumulates Holdings

```python
def test_buy_multiple_times_accumulates_holdings(self) -> None:
```

Verify:

- Buying `AAPL` twice accumulates quantities.

---

### Cannot Buy More Than Cash Allows

```python
def test_buy_more_than_cash_allows_raises(self) -> None:
```

Verify:

- `InsufficientFundsError`.
- Cash unchanged.
- Holdings unchanged.
- Transaction count unchanged after failed operation.

---

### Buy Requires Positive Integer Quantity

```python
def test_buy_requires_positive_integer_quantity(self) -> None:
```

Verify:

- `0` raises `InvalidAmountError`.
- Negative quantity raises `InvalidAmountError`.
- Non-integer quantity raises `InvalidAmountError`.

---

### Sell Shares Increases Cash And Reduces Holdings

```python
def test_sell_increases_cash_and_reduces_holdings(self) -> None:
```

Example:

- Create account with `1000`.
- Buy `3` `AAPL`.
- Sell `1` `AAPL`.
- Cash reflects sale proceeds.
- Holdings `AAPL` equals `2`.
- Transaction type is `SELL`.

---

### Selling All Shares Removes Holding

```python
def test_selling_all_shares_removes_holding(self) -> None:
```

Verify:

- Holding key is removed or no longer present after quantity reaches zero.

---

### Cannot Sell More Shares Than Owned

```python
def test_sell_more_than_owned_raises(self) -> None:
```

Verify:

- `InsufficientHoldingsError`.
- Cash unchanged.
- Holdings unchanged.
- Transaction count unchanged after failed operation.

---

### Sell Requires Positive Integer Quantity

```python
def test_sell_requires_positive_integer_quantity(self) -> None:
```

Verify:

- `0` raises `InvalidAmountError`.
- Negative quantity raises `InvalidAmountError`.
- Non-integer quantity raises `InvalidAmountError`.

---

### Unknown Symbol Raises

```python
def test_unknown_symbol_raises(self) -> None:
```

Verify:

- Buying unsupported symbol raises `UnknownSymbolError`.

---

### Symbol Is Normalized

```python
def test_symbol_is_normalized(self) -> None:
```

Example:

- Buy `" aapl "` quantity `1`.
- Holdings should contain `"AAPL"`.

---

### Holdings Report Calculates Market Values

```python
def test_holdings_report_calculates_market_values(self) -> None:
```

Example:

- Buy `2` `AAPL`.
- Holdings report row has:
  - symbol `AAPL`
  - quantity `2`
  - current price `150`
  - market value `300`

---

### Portfolio Value Includes Cash And Holdings

```python
def test_portfolio_value_includes_cash_and_holdings(self) -> None:
```

Example:

- Create account with `1000`.
- Buy `2` `AAPL` for `300`.
- Cash is `700`.
- Holdings value is `300`.
- Portfolio value is `1000`.

---

### Profit Loss Is Portfolio Value Minus Net Deposits

```python
def test_profit_loss_is_portfolio_value_minus_net_deposits(self) -> None:
```

Example using constant prices:

- Create account with `1000`.
- Buy `2` `AAPL`.
- Portfolio value remains `1000`.
- Net deposits is `1000`.
- Profit/loss is `0`.

Also test with custom price provider if desired:

- Buy at one price.
- Then use mutable test provider or separate account behavior to simulate current price change.
- Verify profit/loss changes when current valuation changes.

---

### Transactions Are Listed In Order

```python
def test_transactions_are_listed_in_order(self) -> None:
```

Verify:

- Create account.
- Deposit.
- Buy.
- Sell.
- Withdraw.
- Transaction IDs are sequential.
- Transaction types are in the expected order.

---

### Returned Holdings Are Defensive Copy

```python
def test_get_holdings_returns_copy(self) -> None:
```

Verify:

- Mutating returned dictionary does not affect internal account holdings.

---

### Returned Transactions Are Defensive Copy

```python
def test_get_transactions_returns_copy(self) -> None:
```

Verify:

- Appending to returned transaction list does not affect internal transaction list.

---

# Business Rules Summary

## Cash Balance

Cash balance changes as follows:

```text
Create account: +initial_deposit
Deposit:        +amount
Withdraw:       -amount
Buy:            -(share_price * quantity)
Sell:           +(share_price * quantity)
```

---

## Net Deposits

Net deposits changes as follows:

```text
Create account: +initial_deposit
Deposit:        +amount
Withdraw:       -amount
Buy:             no change
Sell:            no change
```

---

## Holdings

Holdings changes as follows:

```text
Buy:  holdings[symbol] += quantity
Sell: holdings[symbol] -= quantity
```

If a holding reaches zero, remove it from the holdings dictionary.

---

## Portfolio Value

```text
holdings_value = sum(current_price(symbol) * quantity for each holding)
portfolio_value = cash_balance + holdings_value
```

---

## Profit/Loss

```text
profit_loss = portfolio_value - net_deposits
```

This means:

- Depositing more money does not count as profit.
- Withdrawing money does not count as loss.
- Buying or selling at unchanged prices does not create profit/loss.
- Price changes in holdings affect profit/loss.

---

# Engineer Assignments

## `backend_engineer`

Implement `backend.py`.

Deliverables:

- `TEST_SHARE_PRICES`
- `get_share_price`
- `TransactionType`
- `Transaction`
- `HoldingReport`
- `PortfolioReport`
- All custom exceptions
- `TradingAccount`

Must ensure:

- All invalid actions raise correct exceptions.
- Failed operations do not mutate state.
- Reports use current prices.
- Returned collections are defensive copies.
- Backend has no Gradio dependency.

---

## `frontend_engineer`

Implement `app.py`.

Deliverables:

- Gradio 6 app using `gr.Blocks`.
- Account creation UI.
- Deposit/withdraw UI.
- Buy/sell UI.
- Reports UI.
- Holdings dataframe.
- Transactions dataframe.
- Per-session state using `gr.State`.
- Event handlers that call backend methods.
- User-friendly success/error messages.

Must ensure:

- No business rules duplicated beyond minimal input conversion.
- All backend `AccountError` exceptions are caught and displayed.
- Report tables refresh after each successful operation.
- App launches with `demo.launch()` under `if __name__ == "__main__":`.

---

## `test_engineer`

Implement `test_backend.py`.

Deliverables:

- Standard-library `unittest` test suite.
- Tests covering happy paths and failure paths.
- Tests for account creation, deposits, withdrawals, buys, sells.
- Tests for portfolio valuation and profit/loss.
- Tests for holdings and transactions reporting.
- Tests for defensive copies.
- Tests for symbol normalization and unknown symbols.

Must ensure:

- Tests can run with:

```text
uv run python -m unittest test_backend.py
```

No Gradio tests required.

---

# Acceptance Criteria

The system is complete when:

1. `backend.py` implements all required account/trading behavior.
2. `app.py` launches a working Gradio 6 UI.
3. `test_backend.py` passes all backend unit tests.
4. Users can:
   - Create an account.
   - Deposit funds.
   - Withdraw funds.
   - Buy shares.
   - Sell shares.
   - View current holdings.
   - View current portfolio value.
   - View current profit/loss.
   - View transaction history.
5. The system prevents:
   - Negative-balance withdrawals.
   - Purchases exceeding available cash.
   - Sales exceeding held quantity.
   - Invalid non-positive amounts or quantities.
   - Unsupported share symbols.
6. All files are in the same directory.
7. No third-party packages are used except Gradio for the frontend.