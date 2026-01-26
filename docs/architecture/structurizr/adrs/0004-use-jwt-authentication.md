# 4. Use JWT for Authentication

Date: 2026-01-25

## Status

Accepted

## Context

We need a secure authentication mechanism for the API. The solution should:
- Be stateless to support horizontal scaling
- Work well with modern frontend applications
- Provide both access and refresh token mechanisms
- Be industry-standard

## Decision

We will use JWT (JSON Web Tokens) for authentication and authorization.

Access tokens expire in 15 minutes, refresh tokens in 7 days.

## Consequences

### Positive
- Stateless authentication enables easy horizontal scaling
- No server-side session storage required
- Works seamlessly with SPAs and mobile apps
- Industry standard with good library support
- Token contains user claims, reducing database lookups

### Negative
- Cannot revoke tokens before expiration (without blacklist)
- Token size larger than session IDs
- Needs careful key management
- Requires HTTPS to prevent token theft
