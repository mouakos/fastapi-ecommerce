# Docker Compose Commands

## Starting Services

```bash
# Start all services in background
docker compose up -d

# Start specific service
docker compose up -d redis

# Start with rebuild
docker compose up -d --build
```

## Stopping Services

```bash
# Stop all services (without removing)
docker compose stop

# Stop specific service
docker compose stop redis

# Stop and remove containers, networks
docker compose down

# Stop and remove with volumes (⚠️ deletes data)
docker compose down -v
```

## Restarting Services

```bash
# Restart all services (without deleting containers)
docker compose restart

# Restart specific service
docker compose restart redis

# Force recreate containers
docker compose up -d --force-recreate
```

## Viewing Logs

```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# Logs for specific service
docker compose logs -f redis

# Last 50 lines
docker compose logs --tail 50 redis
```

## Checking Status

```bash
# List running containers
docker compose ps

# View container details
docker compose ps -a

# Check service health
docker ps
```

## Cleaning Up

```bash
# Remove stopped containers
docker compose rm

# Remove all (containers, networks, volumes)
docker compose down -v

# Remove orphan containers
docker compose up -d --remove-orphans
```
