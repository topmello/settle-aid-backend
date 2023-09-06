# Settle-Aid-backend 🚠

👉 [Backend Dev doc](https://topmello.github.io/docs/category/backend)

👉 [API doc](https://api.settle-aid.tech/)

- username: topmello
- password: da7da0df508738e37f18

## Development container

### Start containers

```bash
docker-compose -f docker-compose-dev.yaml up -d
```

To force rebuild: add `--build` tag

### Stop containers

```bash
docker-compose -f docker-compose-dev.yaml down
```

To delete volume(this will delete data in the database): add `-v` tag

## Local Swagger Docs

After start the container, it will be available at
http://localhost:8000/

## Update database schema (inside backend container)

```bash
alembic upgrade head
```

## Clean up database

```bash
alembic downgrade base
```

## Manually access DB

```bash
psql -U db_user -d database
```

## Backup database

```bash
docker exec -t db pg_dump -U db_user -d database > backup.sql
```

## Restore database

```bash
cat backup.sql | docker exec -i db psql -U db_user -d database
```

## Insert data (inside backend container)

```bash
python -m scripts.insert_data
```

## For deployment in VM

```bash
sudo docker-compose pull
```

```bash
sudo docker-compose -p settle-aid up -d
```
