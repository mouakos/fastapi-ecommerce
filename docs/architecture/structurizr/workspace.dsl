workspace "E-commerce system" {

    !identifiers hierarchical

    model {
        user = person "Customer" "An e-commerce customer who browses and buys products online." {
            tags "Person"
        }
        admin = person "Administrator" "System administrator who manages products, categories, orders, and users." {
            tags "Person" "Admin"
        }
        shopping = softwareSystem "Shopping System" "Allows customers to search, view and buy products." {
            tags "Main System"
            
            !docs docs
            !adrs adrs
            
            web = container "API Application" {
                tags "Web"
                technology "FastAPI"
                description "Allows customers to browse products, view product details, and make purchases. Handles JWT authentication."
                
                api = component "REST API" {
                    technology "FastAPI Routes"
                    description "RESTful API endpoints for all business operations"
                    tags "Component"
                }
                services = component "Services" {
                    technology "Python"
                    description "Business logic for users, products, orders, cart, payments, and reviews"
                    tags "Component"
                }
                domain = component "Domain Models" {
                    technology "SQLModel"
                    description "Core domain models"
                    tags "Component"
                }
                repositories = component "Repositories" {
                    technology "SQLModel/SQLAlchemy"
                    description "Data access layer with unit of work pattern"
                    tags "Component"
                }
                securityComponent = component "Security Component" {
                    technology "PyJWT"
                    description "Authentication and authorization using JWT tokens"
                    tags "Component" "Security"
                }
            }
            db = container "Database Schema" {
                technology "PostgreSQL"
                tags "Database"
                description "Stores product information, user data, and order details."
            }
            cache = container "Cache Storage" {
                technology "Redis"
                tags "Database"
                description "Caches the most popular product lists to improve performance."
            }
        }
        email = softwareSystem "E-mail System" {
            tags "External System"
            description "Handles sending e-mail notifications to customers."
        }
        payment = softwareSystem "Payment Gateway" {
            tags "External System"
            description "Processes payments and manages checkout sessions."
        }

        user -> shopping.web "Views products and does shopping" "HTTPS"
        user -> shopping.web.api "Makes API requests" "HTTPS/JSON"
        admin -> shopping.web "Manages products, orders, and system" "HTTPS"
        admin -> shopping.web.api "Makes admin API requests" "HTTPS/JSON"
        shopping.web.api -> shopping.web.securityComponent "Validates JWT tokens" "Python"
        shopping.web.api -> shopping.web.services "Delegates business logic to" "Python"
        shopping.web.services -> shopping.web.repositories "Persists data using" "Python"
        shopping.web.services -> shopping.web.domain "Uses domain models" "Python"
        shopping.web.repositories -> shopping.db "Reads from and writes to" "SQL"
        shopping.web.api -> shopping.cache "Caches data in" "Redis Protocol"
        shopping.web.services -> payment "Processes payments using" "HTTPS/API"
        payment -> shopping.web.services "Sends payment webhooks to" "HTTPS"
        shopping.web.services -> email "Sends notifications using" "SMTP/API"
        email -> user "Sends e-mails to" "SMTP"
        email -> admin "Sends notifications to" "SMTP"
    }

    views {
        systemContext shopping "ShoppingSystemContextDiagram" {
            include *
        }

        container shopping "ShoppingContainerDiagram" {
            include *
        }

        component shopping.web "WebApplicationComponentDiagram" {
            include *

        }

        styles {
            element "Element" {
                color #FFFFFF
            }
            element "Person" {
                background #1560BD
                shape Person
            }
            element "Admin" {
                background #FF6B6B
                shape Person
            }
            element "Container" {
                background #1560BD
            }
            element "Main System" {
                background #002366
                color #FFFFFF
            }
            element "Internal System" {
                background #1560BD
            }
            element "External System" {
                background #616569
            }
            element "Web" {
                shape WebBrowser
            }
            element "Database" {
                shape Cylinder
            }
            element "Security" {
                background #28A745
                shape RoundedBox
            }
            element "Component" {
                background #85C1E9
            }
        }
    }

    configuration {
        scope softwaresystem
    }

}