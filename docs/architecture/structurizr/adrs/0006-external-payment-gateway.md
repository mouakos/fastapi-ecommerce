# 6. Integrate External Payment Gateway

Date: 2026-01-25

## Status

Accepted

## Context

Handling payment processing in-house requires:
- PCI DSS compliance (extremely complex and costly)
- Security expertise for handling card data
- Integration with multiple payment methods
- Fraud detection and prevention

This is beyond the scope and capability of our small team.

## Decision

We will integrate with an external payment gateway (initially Stripe) rather than processing payments directly.

The integration will be abstracted behind a service layer to allow switching providers if needed.

## Consequences

### Positive
- No PCI DSS compliance burden
- Professional fraud detection
- Multiple payment methods supported
- Reliable and tested payment processing
- Webhook notifications for payment events
- Reduced security risk

### Negative
- Transaction fees per payment
- Dependency on third-party availability
- Limited control over payment flow
- Must handle webhook reliability
- Vendor lock-in risk (mitigated by abstraction layer)
