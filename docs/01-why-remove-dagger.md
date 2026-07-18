# Why Remove DAgger

DAgger addresses distribution shift between Teacher states and Student states.

The latest failure happened before that problem:

```text
initial state
    ↓
predicted improvement ≈ 0
    ↓
immediate Stop
```

The Student did not reach meaningful Student-only states. Therefore, first diagnose and improve the Multi-head Network itself.
