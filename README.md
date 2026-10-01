# Thai Payment Toolkit

Small, dependency-free Python toolkit for producing and validating PromptPay EMVCo payloads. It extracts the payment boundary of my LINE commerce work so protocol logic can be tested independently before an application renders a QR image or sends an order confirmation.

## Why it exists

Payment payloads are protocol data, not UI strings. A malformed amount, incorrectly normalized Thai mobile number, or stale checksum should fail before reaching a customer. The core path is pure and auditable.

```python
from decimal import Decimal
from thai_payment_toolkit import payload, is_valid

qr_data = payload("081-234-5678", Decimal("185.00"))
assert is_valid(qr_data)
```

It supports static and dynamic QR payloads, Thai mobile numbers, 13-digit national/tax IDs, EMV TLV parsing, and CRC-16/CCITT-FALSE validation. PNG rendering is intentionally optional so the protocol core has no image dependency.

## Verify

```sh
python -m pip install -e ".[test]"
python -m pytest
```

The tests cover the published CRC vector, number normalization, static and dynamic payloads, tampering, invalid identifiers, invalid amounts, and malformed TLV data.

## Scope

This is a protocol utility, not a payment processor. It does not initiate transfers, validate a bank account, or guarantee that a QR code will be accepted by a particular banking app. A production integration still needs merchant verification, HTTPS, webhook authentication, idempotent order handling, and reconciliation against a payment provider.

MIT © Yavin Songkham
