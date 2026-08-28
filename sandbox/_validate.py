"""
Validation script to confirm the Gradio UI constructs without error.
Does not call .launch() - just imports and instantiates.
"""

import sys

def validate():
    """Validate that app.py imports and constructs the Blocks object."""
    try:
        # Import the app module
        import app
        
        # Check that demo exists and is a Blocks object
        if not hasattr(app, 'demo'):
            print("ERROR: 'demo' not found in app module")
            return False
        
        demo = app.demo
        
        # Check it's a Gradio Blocks object
        if not hasattr(demo, 'blocks'):
            print("ERROR: 'demo' does not appear to be a Gradio Blocks object")
            return False
        
        print("SUCCESS: Gradio UI constructs without error")
        print(f"  - demo type: {type(demo)}")
        print(f"  - demo title: {getattr(demo, 'title', 'N/A')}")
        
        # Verify key components exist
        if hasattr(demo, 'blocks'):
            block_count = len(demo.blocks) if demo.blocks else 0
            print(f"  - number of blocks: {block_count}")
        
        # Verify backend imports work
        import backend
        account = backend.TradingAccount()
        print(f"  - backend.TradingAccount instantiation: OK")
        
        # Test a simple backend operation
        txn = account.create_account(1000.0)
        print(f"  - backend create_account: OK (txn_id={txn.transaction_id})")
        
        balance = account.get_cash_balance()
        print(f"  - backend get_cash_balance: OK (${balance:.2f})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)