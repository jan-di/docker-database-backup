# docker-database-backup

A dockerized service to automatically backup all of your database containers.

Docker Image: `ghcr.io/jan-di/database-backup`

## Service Configuration

Configure the backup service by specifying environment variables:

Settings:
- `INTERVAL` Amount of seconds to wait between each backup cycle. Set to `0` to make a one-time backup. Default: `3600`

Defaults:
- `DEFAULT_USERNAME` Default login username. Default: `root`
- `DEFAULT_PASSWORD` Default login password. Default: (empty)

## Database Configuration

Configure each database container by specifying labels:

- `jan-di.database-backup.enable` Enable backup for this container. Default: `false`
- `jan-di.database-backup.type` Specify type of database. Possible values: `auto, mysql, mariadb, postgres`. Default: `auto`. Auto tries to get the type from the image name (for specific well known images)
- `jan-di.database-backup.username` Login user. Default: setting `DEFAULT_USERNAME`
- `jan-di.database-backup.password` Login password. Default: setting `DEFAULT_PASSWORD`
- `jan-di.database-backup.port` Port (inside container). Default: `3306` (mysql/mariadb), `5432` (postgres)

## Example

Example docker-compose.yml:

```yml
version: '3.8'

services:
  db-backup: # backup service
    image: ghcr.io/jan-di/database-backup
    environment:
      - INTERVAL=600
      - DEFAULT_PASSWORD=secret-password
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  database1: # well known database image
    image: mariadb:latest
    environment:
      - MYSQL_ROOT_PASSWORD=secret-password
    labels:
      - jan-di.database-backup.enable=true

  database2: # custom database image
    image: user/my-database:latest
    environment:
      - DB_PASSWORD=secret-password
    labels:
      - jan-di.database-backup.enable=true
      - jan-di.database-backup.type=postgres
      - jan-di.database-backup.password=other-password
```

## Credits

Inspired by [kibatic/docker-mysql-backup](https://github.com/kibatic/docker-mysql-backup)