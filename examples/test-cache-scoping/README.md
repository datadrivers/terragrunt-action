# Test Cache Scoping

This example validates that the plugin cache is properly scoped to the working directory.

## Structure

- `stack-a/` - First stack with AWS provider v5
- `stack-b/` - Second stack with AWS provider v6

Each stack should generate a different `LOCK_HASH` and maintain independent plugin caches.

## Expected Behavior

When running with different `working-directory` inputs:

- `working-directory: examples/test-cache-scoping/stack-a` → Cache key includes hash of stack-a's lockfile only
- `working-directory: examples/test-cache-scoping/stack-b` → Cache key includes hash of stack-b's lockfile only

This prevents cache pollution and ensures each stack downloads only its required provider versions.
