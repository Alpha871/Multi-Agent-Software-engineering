"""
Frontend module for the trading simulation account manager.
Gradio 6 UI that demonstrates the backend functionality.
"""

import gradio as gr
from backend import (
    TradingAccount,
    TransactionType,
    AccountError,
    InvalidAmountError,
    InsufficientFundsError,
    InsufficientHoldingsError,
    UnknownSymbolError,
    AccountAlreadyCreatedError,
    AccountNotCreatedError,
)


# Color palette as CSS variables for light/dark mode support
CSS = """
:root {
    --color-primary: #ecad0a;
    --color-secondary: #209dd7;
    --color-accent: #753991;
    --color-bg: #f8f9fa;
    --color-surface: #ffffff;
    --color-text: #212529;
    --color-text-muted: #6c757d;
    --color-border: #dee2e6;
    --color-success: #28a745;
    --color-error: #dc3545;
    --color-warning: #ffc107;
}

@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #1a1a2e;
        --color-surface: #16213e;
        --color-text: #eaeaea;
        --color-text-muted: #a0a0a0;
        --color-border: #2d3a4f;
    }
}

.gradio-container {
    background-color: var(--color-bg);
    color: var(--color-text);
}

.gr-button-primary {
    background-color: var(--color-primary) !important;
    border-color: var(--color-primary) !important;
    color: #000 !important;
}

.gr-button-primary:hover {
    background-color: #d49a09 !important;
    border-color: #d49a09 !important;
}

.gr-button-secondary {
    background-color: var(--color-secondary) !important;
    border-color: var(--color-secondary) !important;
    color: #fff !important;
}

.gr-button-secondary:hover {
    background-color: #1d8cc4 !important;
    border-color: #1d8cc4 !important;
}

.gr-input, .gr-textbox, .gr-number {
    background-color: var(--color-surface) !important;
    border-color: var(--color-border) !important;
    color: var(--color-text) !important;
}

.gr-dataframe {
    background-color: var(--color-surface) !important;
}

.gr-tab-nav button {
    background-color: var(--color-surface) !important;
    color: var(--color-text) !important;
    border-color: var(--color-border) !important;
}

.gr-tab-nav button.selected {
    background-color: var(--color-primary) !important;
    color: #000 !important;
}

.status-success {
    color: var(--color-success);
    font-weight: 500;
}

.status-error {
    color: var(--color-error);
    font-weight: 500;
}

.status-info {
    color: var(--color-secondary);
    font-weight: 500;
}

.report-value {
    font-size: 1.1em;
    font-weight: 600;
}
"""


# Frontend helper functions
def create_new_account() -> TradingAccount:
    """Create a new TradingAccount instance."""
    return TradingAccount()


def get_or_create_account(account: object | None) -> TradingAccount:
    """Get existing account or create new one."""
    if account is None:
        return TradingAccount()
    return account


def format_currency(value: float) -> str:
    """Format a value as currency string."""
    return f"${value:,.2f}"


def format_transaction_type(transaction_type: TransactionType) -> str:
    """Format transaction type for display."""
    mapping = {
        TransactionType.CREATE_ACCOUNT: "Create Account",
        TransactionType.DEPOSIT: "Deposit",
        TransactionType.WITHDRAW: "Withdraw",
        TransactionType.BUY: "Buy",
        TransactionType.SELL: "Sell",
    }
    return mapping.get(transaction_type, transaction_type.value)


def empty_holdings_rows() -> list[list[object]]:
    """Return empty holdings rows."""
    return []


def empty_transaction_rows() -> list[list[object]]:
    """Return empty transaction rows."""
    return []


def build_holdings_rows(account: TradingAccount) -> list[list[object]]:
    """Build holdings table rows from account."""
    rows = []
    for holding in account.get_holdings_report():
        rows.append([
            holding.symbol,
            holding.quantity,
            holding.current_price,
            holding.market_value,
        ])
    return rows


def build_transaction_rows(account: TradingAccount) -> list[list[object]]:
    """Build transaction table rows from account."""
    rows = []
    for txn in account.get_transactions():
        rows.append([
            txn.transaction_id,
            txn.timestamp.isoformat(),
            format_transaction_type(txn.transaction_type),
            txn.symbol if txn.symbol else "",
            txn.quantity if txn.quantity else 0,
            f"{txn.share_price:.2f}" if txn.share_price is not None else "",
            txn.amount,
            txn.cash_balance_after,
            txn.description,
        ])
    return rows


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
    """Build all report output values from account."""
    if account is None or not account.is_created():
        return (
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            [],
            [],
            "Create an account to view reports.",
        )

    try:
        report = account.get_portfolio_report()
        holdings_rows = build_holdings_rows(account)
        transaction_rows = build_transaction_rows(account)
        status = "Report refreshed successfully."
        return (
            report.cash_balance,
            report.holdings_value,
            report.total_portfolio_value,
            report.net_deposits,
            report.profit_loss,
            holdings_rows,
            transaction_rows,
            status,
        )
    except AccountError as e:
        return (
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            [],
            [],
            f"Error: {str(e)}",
        )


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
    """Handle create account button click."""
    if initial_deposit is None:
        return (
            account,
            "Error: Please enter an initial deposit amount.",
            0.0, 0.0, 0.0, 0.0, 0.0,
            [], [], "Error: Please enter an initial deposit amount.",
        )

    try:
        if account is None:
            account = TradingAccount()

        account.create_account(initial_deposit)
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, status = build_report_outputs(account)
        return (
            account,
            f"Success: Account created with initial deposit of {format_currency(initial_deposit)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, status,
        )
    except AccountError as e:
        return (
            account,
            f"Error: {str(e)}",
            0.0, 0.0, 0.0, 0.0, 0.0,
            [], [], f"Error: {str(e)}",
        )


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
    """Handle deposit button click."""
    if account is None or not account.is_created():
        return (
            account,
            "Error: Create an account first.",
            0.0, 0.0, 0.0, 0.0, 0.0,
            [], [], "Error: Create an account first.",
        )

    if amount is None:
        return (
            account,
            "Error: Please enter a deposit amount.",
            *build_report_outputs(account)[:5],
            *build_report_outputs(account)[5:],
        )

    try:
        account.deposit(amount)
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, status = build_report_outputs(account)
        return (
            account,
            f"Success: Deposited {format_currency(amount)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, status,
        )
    except AccountError as e:
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, _ = build_report_outputs(account)
        return (
            account,
            f"Error: {str(e)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, f"Error: {str(e)}",
        )


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
    """Handle withdraw button click."""
    if account is None or not account.is_created():
        return (
            account,
            "Error: Create an account first.",
            0.0, 0.0, 0.0, 0.0, 0.0,
            [], [], "Error: Create an account first.",
        )

    if amount is None:
        return (
            account,
            "Error: Please enter a withdrawal amount.",
            *build_report_outputs(account)[:5],
            *build_report_outputs(account)[5:],
        )

    try:
        account.withdraw(amount)
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, status = build_report_outputs(account)
        return (
            account,
            f"Success: Withdrew {format_currency(amount)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, status,
        )
    except AccountError as e:
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, _ = build_report_outputs(account)
        return (
            account,
            f"Error: {str(e)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, f"Error: {str(e)}",
        )


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
    """Handle buy button click."""
    if account is None or not account.is_created():
        return (
            account,
            "Error: Create an account first.",
            0.0, 0.0, 0.0, 0.0, 0.0,
            [], [], "Error: Create an account first.",
        )

    if not symbol or not symbol.strip():
        return (
            account,
            "Error: Please enter a symbol.",
            *build_report_outputs(account)[:5],
            *build_report_outputs(account)[5:],
        )

    if quantity is None:
        return (
            account,
            "Error: Please enter a quantity.",
            *build_report_outputs(account)[:5],
            *build_report_outputs(account)[5:],
        )

    try:
        qty_int = int(quantity)
        if qty_int != quantity or qty_int <= 0:
            raise InvalidAmountError("Quantity must be a positive integer")

        account.buy(symbol.strip(), qty_int)
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, status = build_report_outputs(account)
        return (
            account,
            f"Success: Bought {qty_int} shares of {symbol.strip().upper()}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, status,
        )
    except AccountError as e:
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, _ = build_report_outputs(account)
        return (
            account,
            f"Error: {str(e)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, f"Error: {str(e)}",
        )


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
    """Handle sell button click."""
    if account is None or not account.is_created():
        return (
            account,
            "Error: Create an account first.",
            0.0, 0.0, 0.0, 0.0, 0.0,
            [], [], "Error: Create an account first.",
        )

    if not symbol or not symbol.strip():
        return (
            account,
            "Error: Please enter a symbol.",
            *build_report_outputs(account)[:5],
            *build_report_outputs(account)[5:],
        )

    if quantity is None:
        return (
            account,
            "Error: Please enter a quantity.",
            *build_report_outputs(account)[:5],
            *build_report_outputs(account)[5:],
        )

    try:
        qty_int = int(quantity)
        if qty_int != quantity or qty_int <= 0:
            raise InvalidAmountError("Quantity must be a positive integer")

        account.sell(symbol.strip(), qty_int)
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, status = build_report_outputs(account)
        return (
            account,
            f"Success: Sold {qty_int} shares of {symbol.strip().upper()}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, status,
        )
    except AccountError as e:
        cash, holdings_val, portfolio, net_dep, pnl, holdings_rows, txn_rows, _ = build_report_outputs(account)
        return (
            account,
            f"Error: {str(e)}",
            cash, holdings_val, portfolio, net_dep, pnl,
            holdings_rows, txn_rows, f"Error: {str(e)}",
        )


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
    """Handle refresh report button click."""
    return build_report_outputs(account)


# Gradio UI
with gr.Blocks(title="Trading Simulation Account Manager", css=CSS) as demo:
    # Header
    gr.Markdown(
        """
        # Trading Simulation Account Manager
        Manage a simulated trading account using fixed prices for **AAPL ($150.00)**, **TSLA ($250.00)**, and **GOOGL ($2,800.00)**.
        """
    )

    # State
    account_state = gr.State(value=None)

    with gr.Tabs():
        # Tab 1: Account
        with gr.Tab("Account"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Create Account")
                    initial_deposit_input = gr.Number(
                        label="Initial Deposit",
                        minimum=0.01,
                        value=1000.0,
                        precision=2,
                    )
                    create_account_button = gr.Button(
                        "Create Account",
                        variant="primary",
                        size="lg",
                    )

                    gr.Markdown("---")
                    gr.Markdown("### Deposit Funds")
                    deposit_amount_input = gr.Number(
                        label="Deposit Amount",
                        minimum=0.01,
                        value=100.0,
                        precision=2,
                    )
                    deposit_button = gr.Button("Deposit", variant="secondary")

                    gr.Markdown("---")
                    gr.Markdown("### Withdraw Funds")
                    withdraw_amount_input = gr.Number(
                        label="Withdrawal Amount",
                        minimum=0.01,
                        value=100.0,
                        precision=2,
                    )
                    withdraw_button = gr.Button("Withdraw", variant="secondary")

                with gr.Column(scale=1):
                    status_output = gr.Textbox(
                        label="Status",
                        interactive=False,
                        lines=4,
                    )

        # Tab 2: Trade
        with gr.Tab("Trade"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Buy / Sell Shares")
                    trade_symbol_input = gr.Textbox(
                        label="Symbol",
                        placeholder="AAPL",
                        value="AAPL",
                    )
                    trade_quantity_input = gr.Number(
                        label="Quantity",
                        minimum=1,
                        value=1,
                        precision=0,
                    )
                    with gr.Row():
                        buy_button = gr.Button("Buy", variant="primary", size="lg")
                        sell_button = gr.Button("Sell", variant="secondary", size="lg")

                with gr.Column(scale=1):
                    trade_status_output = gr.Textbox(
                        label="Status",
                        interactive=False,
                        lines=4,
                    )

        # Tab 3: Reports
        with gr.Tab("Reports"):
            with gr.Row():
                with gr.Column(scale=1):
                    refresh_report_button = gr.Button("Refresh Report", variant="primary")

                    gr.Markdown("### Portfolio Summary")
                    cash_balance_output = gr.Number(
                        label="Cash Balance",
                        interactive=False,
                        precision=2,
                    )
                    holdings_value_output = gr.Number(
                        label="Holdings Value",
                        interactive=False,
                        precision=2,
                    )
                    portfolio_value_output = gr.Number(
                        label="Total Portfolio Value",
                        interactive=False,
                        precision=2,
                    )
                    net_deposits_output = gr.Number(
                        label="Net Deposits",
                        interactive=False,
                        precision=2,
                    )
                    profit_loss_output = gr.Number(
                        label="Profit / Loss",
                        interactive=False,
                        precision=2,
                    )

                with gr.Column(scale=2):
                    gr.Markdown("### Current Holdings")
                    holdings_table = gr.Dataframe(
                        headers=["Symbol", "Quantity", "Current Price", "Market Value"],
                        datatype=["str", "number", "number", "number"],
                        interactive=False,
                        label="Holdings",
                    )

                    gr.Markdown("### Transaction History")
                    transactions_table = gr.Dataframe(
                        headers=[
                            "ID", "Timestamp", "Type", "Symbol",
                            "Quantity", "Share Price", "Amount",
                            "Cash Balance After", "Description"
                        ],
                        datatype=[
                            "number", "str", "str", "str",
                            "number", "str", "number",
                            "number", "str"
                        ],
                        interactive=False,
                        label="Transactions",
                    )

                    report_status_output = gr.Textbox(
                        label="Report Status",
                        interactive=False,
                        lines=2,
                    )

    # Report outputs tuple for reuse
    report_outputs = [
        cash_balance_output,
        holdings_value_output,
        portfolio_value_output,
        net_deposits_output,
        profit_loss_output,
        holdings_table,
        transactions_table,
        report_status_output,
    ]

    # Event wiring
    create_account_button.click(
        fn=handle_create_account,
        inputs=[account_state, initial_deposit_input],
        outputs=[account_state, status_output] + report_outputs,
    )

    deposit_button.click(
        fn=handle_deposit,
        inputs=[account_state, deposit_amount_input],
        outputs=[account_state, status_output] + report_outputs,
    )

    withdraw_button.click(
        fn=handle_withdraw,
        inputs=[account_state, withdraw_amount_input],
        outputs=[account_state, status_output] + report_outputs,
    )

    buy_button.click(
        fn=handle_buy,
        inputs=[account_state, trade_symbol_input, trade_quantity_input],
        outputs=[account_state, trade_status_output] + report_outputs,
    )

    sell_button.click(
        fn=handle_sell,
        inputs=[account_state, trade_symbol_input, trade_quantity_input],
        outputs=[account_state, trade_status_output] + report_outputs,
    )

    refresh_report_button.click(
        fn=handle_refresh_report,
        inputs=[account_state],
        outputs=report_outputs,
    )

if __name__ == "__main__":
    demo.launch()