# Structurizr DSL

This folder contains the Architecture-as-Code model for the FastAPI E-Commerce platform using Structurizr DSL (C4 model).

## What's Included

This architecture documentation includes:

- **C4 Model Diagrams**: System Context, Container, and Component views
- **Documentation**: Business context, functional overview, quality attributes, constraints, and principles
- **Architecture Decision Records (ADRs)**: Key architectural decisions and their rationale

### Diagrams

1. **System Context**: High-level view showing the Shopping System, users, and external systems
2. **Container Diagram**: Internal containers (Web App, Database, Cache) and their interactions
3. **Component Diagram**: Detailed view of the Web Application's internal components (API, Service, Repository layers)

## File Structure

```
structurizr/
├── workspace.dsl          # Main C4 model definition
├── docs/                  # Architecture documentation
└── adrs/                  # Architecture Decision Records
```

## Run Locally

From the `architecture/` directory:

```bash
docker compose -f docker-compose.structurizr.yml up -d
```

## View the Diagrams

Once the Docker container is running:

1. Open your web browser
2. Navigate to: `http://localhost:8081`
3. You'll see the Structurizr Lite interface with:
   - **Diagrams** tab: Interactive architecture diagrams
   - **Documentation** tab: Architecture documentation
   - **Decisions** tab: Architecture Decision Records

4. Use the navigation to explore different views (System Context, Container, Component)

To stop the container:

```bash
docker compose -f docker-compose.structurizr.yml down
```

## Editing the Architecture

1. **Modify the DSL**: Edit `workspace.dsl` to update the model
2. **Update Documentation**: Edit markdown files in `docs/` folder
3. **Add ADRs**: Create new ADR files in `adrs/` folder following the numbering convention
4. **Refresh Browser**: Changes are reflected immediately in the Structurizr Lite interface

### DSL Syntax Reference

- `person` - External users or actors
- `softwareSystem` - High-level systems
- `container` - Deployable units (apps, databases)
- `component` - Internal modules within containers
- `->` - Relationships between elements
- `tags` - For styling and filtering

More info: [Structurizr DSL Documentation](https://github.com/structurizr/dsl)

## Troubleshooting

**Port already in use:**
```bash
# Check what's using port 8081
netstat -ano | findstr :8081

# Change port in docker-compose.structurizr.yml:
ports:
  - "8082:8080"  # Use 8082 instead
```

**Container not starting:**
```bash
# Check logs
docker compose -f docker-compose.structurizr.yml logs

# Restart container
docker compose -f docker-compose.structurizr.yml restart
```

**Changes not visible:**
- Refresh browser (Ctrl+F5 for hard refresh)
- Check DSL syntax errors in browser console
- Verify file is saved

