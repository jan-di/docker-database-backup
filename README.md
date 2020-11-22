# docker-database-backup

## Configuration

Configure the database containers by specifying labels:

- `jan-di.database-backup.enable` Enable backup for this container. Default: `false`
- `jan-di.database-backup.type` Specify type of database. Possible values: `auto, mysql, mariadb, postgres`. Default: `auto`. Auto tries to get the type from the image name (for specific well known images)
- `jan-di.database-backup.username` Login user. Default: `root`
- `jan-di.database-backup.password` Login password

## Example

Example docker-compose.yml:

```yml
version: '3.8'

services:
  db-backup: # backup service
    image: jan-di/database-backup

  database1: # well known database image
    image: mariadb:latest
    environment:
      - MYSQL_ROOT_PASSWORD=secret-password
    labels:
      - jan-di.database-backup.enable=true
      - jan-di.database-backup.password=secret-password

  database2: # custom database image
    image: user/my-database:latest
    environment:
      - DB_PASSWORD=secret-password
    labels:
      - jan-di.database-backup.enable=true
      - jan-di.database-backup.type=postgres
      - jan-di.database-backup.password=secret-password

```

## Credits

Inspired by [kibatic/docker-mysql-backup](https://github.com/kibatic/docker-mysql-backup)