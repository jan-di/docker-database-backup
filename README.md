# docker-database-backup

A dockerized service to automatically backup all of your database containers.

Docker Image: `ghcr.io/jan-di/database-backup`

## Service Configuration

Configure the backup service by specifying environment variables:

Name | Default | Description
--- | --- | ---
`INTERVAL` | `3600` | Amount of seconds to wait between each backup cycle. Set to `0` to make a one-time backup.
`VERBOSE` | `false` | Increased output
`DUMP_UID` | `-1` | UID of dump files. `-1` means default (docker executing user)
`DUMP_GID` | `-1` | GID of dump files. `-1` means default (docker executing user)
`TZ` | UTC | Time Zone for times in log messages
`HEALTHCHECKS_IO_URL` | None | Base Url for [Healthchecks.io](https://healthchecks.io) integration

You can also define global default values for all container specific labels. Do this by prepending the label name by `GLOBAL_`. For example, to provide a default username, you can set a default value for `jan-di.database-backup.username` by specifying the environment variable `GLOBAL_USERNAME`. See next chapter for reference.

## Database Configuration

Configure each database container by specifying labels. Every label must be prefixed by `jan-di.database-backup.`:

Name | Default | Description
--- | --- | ---
`enable` | `false` | Enable backup for this container
`type` | `auto` | Specify type of database. Possible values: `auto, mysql, mariadb, postgres`. Auto tries to get the type from the image name (for specific well known images)
`username` | `root` | Login user
`password` | (none) | Login password
`port` | `auto` | Port (inside container). Possible values: `auto` or a valid port number. Auto gets the default port corresponding to the type.
`compress` | `false` | Compress SQL Dump with gzip

## Example

Example docker-compose.yml:

```yml
version: '3.8'

services:
  db-backup: # backup service
    image: ghcr.io/jan-di/database-backup
    environment:
      - TZ=Europe/Berlin
      - INTERVAL=600
      - GLOBAL_PASSWORD=secret-password
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