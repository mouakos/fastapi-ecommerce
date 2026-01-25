# ER Diagram

```mermaid
erDiagram
    USERS {
        UUID id PK
        string email
        string hashed_password
        string first_name
        string last_name
        string phone_number
        string role
        boolean is_superuser
        boolean is_active
        datetime last_login
        datetime deleted_at
        boolean newsletter_subscribed
        datetime created_at
        datetime updated_at
    }

    ADDRESSES {
        UUID id PK
        UUID user_id FK
        string full_name
        string company
        string line1
        string line2
        string city
        string state
        string postal_code
        string country
        string phone_number
        boolean is_default_shipping
        boolean is_default_billing
        datetime created_at
        datetime updated_at
    }

    CARTS {
        UUID id PK
        UUID user_id FK
        string session_id
        datetime updated_at
        datetime created_at
    }

    CART_ITEMS {
        UUID id PK
        UUID cart_id FK
        UUID product_id FK
        int quantity
        datetime added_at
        decimal unit_price
        string product_name
        string product_image_url
    }

    CATEGORIES {
        UUID id PK
        string name
        string slug
        UUID parent_id FK
        string description
        string image_url
        datetime created_at
        datetime updated_at
    }

    PRODUCTS {
        UUID id PK
        string name
        string slug
        string description
        decimal price
        int stock
        string sku
        string image_url
        boolean is_active
        int discount_percentage
        UUID category_id FK
        datetime created_at
        datetime updated_at
    }

    ORDERS {
        UUID id PK
        UUID user_id FK
        string status
        decimal total_amount
        string order_number
        datetime shipped_at
        datetime paid_at
        datetime canceled_at
        datetime delivered_at
        decimal tax_amount
        decimal shipping_amount
        datetime created_at
        datetime updated_at
    }

    ORDER_ITEMS {
        UUID id PK
        UUID order_id FK
        UUID product_id FK
        int quantity
        decimal unit_price
        string product_name
        string product_image_url
    }

    ORDER_ADDRESSES {
        UUID id PK
        UUID order_id FK
        string kind
        string full_name
        string company
        string line1
        string line2
        string city
        string state
        string postal_code
        string country
        string phone_number
        datetime created_at
        datetime updated_at
    }

    PAYMENTS {
        UUID id PK
        UUID order_id FK
        decimal amount
        string currency
        string payment_method
        string status
        string transaction_id
        datetime created_at
        datetime updated_at
    }

    REVIEWS {
        UUID id PK
        UUID user_id FK
        UUID product_id FK
        int rating
        string comment
        string status
        datetime moderated_at
        UUID moderated_by FK
        datetime created_at
        datetime updated_at
    }

    WISHLIST_ITEMS {
        UUID id PK
        UUID user_id FK
        UUID product_id FK
        datetime created_at
    }

    %% Relationships
    USERS ||--o{ ADDRESSES : has

    %% cart can be anonymous (session_id) or user-linked; user has at most one cart
    USERS o|--o| CARTS : owns
    CARTS ||--o{ CART_ITEMS : contains
    PRODUCTS ||--o{ CART_ITEMS : in

    %% category hierarchy + product categorization
    CATEGORIES o|--o{ CATEGORIES : parent_of
    CATEGORIES o|--o{ PRODUCTS : categorizes

    USERS ||--o{ ORDERS : places
    ORDERS ||--o{ ORDER_ITEMS : includes
    PRODUCTS ||--o{ ORDER_ITEMS : ordered_as

    ORDERS ||--o{ ORDER_ADDRESSES : uses
    ORDERS ||--o{ PAYMENTS : has

    USERS ||--o{ REVIEWS : writes
    USERS o|--o{ REVIEWS : moderates
    PRODUCTS ||--o{ REVIEWS : receives

    USERS ||--o{ WISHLIST_ITEMS : keeps
    PRODUCTS ||--o{ WISHLIST_ITEMS : saved
```

Notes:
- Cardinalities reflect nullable/unique constraints in the models (e.g., `Product.category_id` is nullable, `Cart.user_id` is nullable + unique).
- `REVIEWS.moderated_by` is an optional second FK to `USERS`.
