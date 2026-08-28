import test_backend
import unittest

# Create a test suite manually
suite = unittest.TestSuite()

# Add tests from TestTradingAccount
suite.addTest(test_backend.TestTradingAccount('test_create_account_sets_initial_cash_and_net_deposits'))
suite.addTest(test_backend.TestTradingAccount('test_create_account_twice_raises'))

# Run the tests
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
print(f'Tests run: {result.testsRun}')
print(f'Failures: {len(result.failures)}')
print(f'Errors: {len(result.errors)}')