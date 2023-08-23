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

## Update database schema (inside backend container)

```
$ alembic upgrade head
```

## Clean up database
```
$ alembic downgrade base
```

## Insert data (inside backend container)
```
$ python -m scripts.insert_data
```