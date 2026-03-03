---
name: ddev
description: Manage DDEV local development environments. Use when the user asks to start, stop, configure, debug, or interact with a DDEV project, run commands inside containers, query or manipulate databases, manage snapshots, run Composer/npm/yarn, view logs, or perform any DDEV-related task.
---

# DDEV Skill

DDEV is a Docker-based local development tool. All commands below must be run from the project root directory (where `.ddev/config.yaml` lives).

## Project Info

| Command | Description |
|---------|-------------|
| `ddev status` | Show project status, URLs, ports, database credentials |
| `ddev describe` | Detailed project description (alias: `ddev st`, `ddev desc`) |
| `ddev list` | List all DDEV projects |
| `ddev config` | View or modify `.ddev/config.yaml` interactively |

The `.ddev/config.yaml` file contains the project configuration (type, PHP version, database type/version, docroot, hostnames, etc.). Read it directly for quick reference.

## Lifecycle

| Command | Description |
|---------|-------------|
| `ddev start` | Start the project containers |
| `ddev stop` | Stop containers (data is preserved) |
| `ddev restart` | Restart the project |
| `ddev poweroff` | Stop ALL DDEV projects and containers |
| `ddev delete` | Remove project info and database (destructive!) |

## Executing Commands in Containers

```bash
ddev exec <command>                    # Run command in web container
ddev exec -s db <command>              # Run command in db container
ddev exec -s <service> <command>       # Run command in any service container
ddev ssh                               # Open shell in web container
ddev ssh -s db                         # Open shell in db container
```

**Shorthand:** `ddev . <command>` is an alias for `ddev exec`.

## Database Access

### Quick Queries with ddev mysql

Run MySQL/MariaDB queries directly:

```bash
ddev mysql -e "SHOW DATABASES;"
ddev mysql -e "SHOW TABLES;"
ddev mysql -e "DESCRIBE <table_name>;"
ddev mysql -e "SELECT * FROM <table> LIMIT 10;"
ddev mysql -e "SELECT COUNT(*) FROM <table>;"
```

The default database is `db` with user `db`/password `db` (or `root`/`root`).

### Connection Details

From `ddev status` output, the db service shows:
- **Inside containers:** host=`db`, port=`3306`, user=`db`, password=`db`, database=`db`
- **From host:** host=`127.0.0.1`, port=shown in `ddev status` output (dynamic), user=`db`, password=`db`

### Database Export

```bash
ddev export-db --file=/tmp/db.sql.gz           # Export as gzipped SQL
ddev export-db --gzip=false --file=/tmp/db.sql  # Export as plain SQL
ddev export-db --gzip=false > /tmp/db.sql       # Export to stdout
ddev export-db --database=other_db --file=dump.sql.gz  # Export specific database
```

### Database Import

```bash
ddev import-db --file=dump.sql                  # Import SQL file
ddev import-db --file=dump.sql.gz               # Import gzipped SQL
ddev import-db --file=dump.tar.gz               # Import tar archive
ddev import-db --database=other_db --file=dump.sql  # Import into specific database
ddev import-db < dump.sql                       # Import from stdin
ddev import-db --no-drop --file=dump.sql        # Import without dropping existing db
```

Supported formats: `.sql`, `.sql.gz`, `.sql.bz2`, `.sql.xz`, `.mysql`, `.mysql.gz`, `.zip`, `.tgz`, `.tar.gz`

### Database Snapshots

Snapshots are instant backups using mariabackup/xtrabackup:

```bash
ddev snapshot                                   # Create snapshot
ddev snapshot --name my-snapshot                 # Create named snapshot
ddev snapshot --list                             # List all snapshots
ddev snapshot restore                            # Restore most recent snapshot
ddev snapshot restore --latest                   # Restore most recent snapshot
ddev snapshot restore my-snapshot                # Restore specific snapshot
ddev snapshot --cleanup                          # Remove all snapshots
```

**Best practice:** Always create a snapshot before importing a database or making destructive changes.

## Package Managers & Build Tools

```bash
ddev composer <command>        # Run Composer (e.g. ddev composer install, ddev composer require)
ddev npm <command>             # Run npm
ddev npx <command>             # Run npx
ddev yarn <command>            # Run yarn
ddev php <command>             # Run PHP CLI
```

## CMS-Specific Commands

For Craft CMS projects (type: `craftcms`):

```bash
ddev craft <command>           # Run Craft CLI commands (e.g. ddev craft project-config/apply)
```

For other CMS types, DDEV provides similar wrappers (e.g. `ddev drush` for Drupal, `ddev wp` for WordPress).

## Logs

```bash
ddev logs                      # Web server logs
ddev logs -s db                # Database logs
ddev logs -f                   # Follow logs in real time
ddev logs --tail 50            # Show last 50 lines
```

## Xdebug

```bash
ddev xdebug                   # Enable Xdebug
ddev xdebug off                # Disable Xdebug
```

## Sharing & URLs

```bash
ddev launch                    # Open project in browser
ddev share                     # Share via ngrok/cloudflared tunnel
ddev mailpit                   # Open Mailpit email testing UI
```

## File Import

```bash
ddev import-files --source=/path/to/files  # Import uploaded files into the project
```

## Tips

- **Database type:** Check `.ddev/config.yaml` for `database.type` (mysql, mariadb, postgres) and `database.version` to know which SQL dialect to use.
- **PostgreSQL projects:** Use `ddev psql` instead of `ddev mysql`.
- **Multiple databases:** Use `--database=<name>` flag with import-db/export-db.
- **Custom services:** Check `.ddev/docker-compose.*.yaml` for additional services (Redis, Solr, Elasticsearch, etc.).
- **Environment variables:** Set in `web_environment` in `.ddev/config.yaml` or in `.ddev/.env`.
- **Custom commands:** Check `.ddev/commands/` for project-specific custom commands.
- **Add-ons:** Use `ddev add-on list` to see installed add-ons and `ddev add-on get` to install new ones.

## Common Workflows

### Inspect Database Schema
```bash
ddev mysql -e "SHOW TABLES;"
ddev mysql -e "DESCRIBE <table>;"
ddev mysql -e "SHOW CREATE TABLE <table>;"
```

### Search Database Content
```bash
ddev mysql -e "SELECT * FROM <table> WHERE <column> LIKE '%search%' LIMIT 20;"
```

### Backup Before Risky Operations
```bash
ddev snapshot --name before-migration
# ... do risky thing ...
ddev snapshot restore before-migration   # if something goes wrong
```

### Check Project Health
```bash
ddev status
ddev logs --tail 20
ddev mysql -e "SELECT 1;"   # verify db connection
```
