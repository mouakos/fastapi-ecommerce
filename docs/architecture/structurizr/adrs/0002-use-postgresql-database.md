# 2. Use PostgreSQL as Primary Database

Date: 2026-01-25

## Status

Accepted

## Context

We need a reliable database system to store product catalog, user data, orders, and transactions. Requirements include:
- ACID compliance for order and payment transactions
- Support for complex queries and relationships
- Proven reliability and performance
- Good Python ecosystem support

## Decision

We will use PostgreSQL as the primary relational database.

## Consequences

### Positive
- Strong ACID guarantees for transactional integrity
- Rich feature set (JSON support, full-text search, etc.)
- Excellent performance and scalability
- Mature ecosystem with good ORMs (SQLAlchemy, SQLModel)
- Free and open source

### Negative
- Requires proper schema design and migration management
- May be overkill for simple use cases
- Needs regular maintenance (vacuuming, indexing)
