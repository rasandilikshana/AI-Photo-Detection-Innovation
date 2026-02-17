# Database Migrations with Alembic

This directory contains database migrations for the A.V.A.R Competition Service.

## Prerequisites

1. Ensure PostgreSQL is running
2. Set the `DATABASE_URL` environment variable
3. Activate the virtual environment

```bash
cd src/backend/competition-service
source venv/bin/activate
```

## Common Commands

### Check Current Revision
```bash
alembic current
```

### View Migration History
```bash
alembic history
```

### Create New Migration (Auto-generate)
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create Empty Migration
```bash
alembic revision -m "Description of changes"
```

### Apply All Migrations
```bash
alembic upgrade head
```

### Apply Specific Migration
```bash
alembic upgrade <revision>
```

### Rollback One Migration
```bash
alembic downgrade -1
```

### Rollback All Migrations
```bash
alembic downgrade base
```

### Show SQL Without Executing
```bash
alembic upgrade head --sql
```

## Migration Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations** on a development database first
3. **Back up production database** before applying migrations
4. **Use descriptive migration names** that explain the change
5. **Keep migrations small** and focused on single changes
6. **Never edit migrations** that have been applied to production

## Troubleshooting

### "Target database is not up to date"
Run: `alembic upgrade head`

### "Can't locate revision"
Check if the migration file exists in `versions/` directory

### Database Connection Issues
Verify `DATABASE_URL` environment variable is set correctly
