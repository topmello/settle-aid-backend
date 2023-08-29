# Settle-Aid-backend

## Development container

### Start containers
```
$ docker-compose -f docker-compose-dev.yaml up -d
```

To force rebuild: add `--build` tag

### Stop containers
```
$ docker-compose -f docker-compose-dev.yaml down
```

To delete volume(this will delete data in the database): add `-v` tag

## Local Swagger Docs
After start the container, it will be available at
http://localhost:8000/docs

## Update database schema (inside backend container)

```
$ alembic upgrade head
```

## Clean up database
```
$ alembic downgrade base
```

## Manually access DB
```
$ psql -U db_user -d database
```

## Backup database
```
$ docker exec -t db pg_dump -U db_user -d database > backup.sql
```

## Restore database
```
$ cat backup.sql | docker exec -i db psql -U db_user -d database
```

## Insert data (inside backend container)
```
$ python -m scripts.insert_data
```

## For deployment in VM
```
$ sudo docker-compose pull
```

```
$ sudo docker-compose -p settle-aid up -d
```