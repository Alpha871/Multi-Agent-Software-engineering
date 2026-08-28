import test_backend
import unittest

# Run all tests
loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(test_backend)

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
print(f'\nTests run: {result.testsRun}')
print(f'Failures: {len(result.failures)}')
print(f'Errors: {len(result.errors)}')

if result.failures:
    print('\nFailures:')
    for test, traceback in result.failures:
        print(f'  {test}: {traceback}')

if result.errors:
    print('\nErrors:')
    for test, traceback in result.errors:
        print(f'  {test}: {traceback}')