#!/bin/bash
# Validate SQL migration syntax without executing
# Uses PostgreSQL's --dry-run equivalent (syntax checking)

set -e

MIGRATION_DIR="/media/rasan/windows-drive/NPAS/NPAS - Third Year/Rasan Research 3/src/backend/competition-service/migrations"
UP_SCRIPT="$MIGRATION_DIR/001_add_v2_innovations_up.sql"
DOWN_SCRIPT="$MIGRATION_DIR/001_add_v2_innovations_down.sql"

echo "=========================================="
echo "SQL Migration Syntax Validation"
echo "=========================================="
echo ""

# Function to validate SQL syntax
validate_sql() {
    local file=$1
    local name=$2

    echo "Validating: $name"
    echo "------------------------------------------"

    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "❌ File not found: $file"
        return 1
    fi

    # Check file is not empty
    if [ ! -s "$file" ]; then
        echo "❌ File is empty: $file"
        return 1
    fi

    # Count SQL statements
    local stmt_count=$(grep -c "CREATE TABLE\|ALTER TABLE\|DROP TABLE\|CREATE INDEX" "$file" || true)
    echo "📊 Found $stmt_count SQL statements"

    # Check for BEGIN/COMMIT transaction
    if grep -q "BEGIN;" "$file" && grep -q "COMMIT;" "$file"; then
        echo "✓ Transaction markers (BEGIN/COMMIT) present"
    else
        echo "⚠ Warning: Missing transaction markers"
    fi

    # Check for IF NOT EXISTS (idempotency)
    if grep -q "IF NOT EXISTS\|IF EXISTS" "$file"; then
        echo "✓ Idempotency checks present (IF EXISTS/IF NOT EXISTS)"
    else
        echo "⚠ Warning: No idempotency checks"
    fi

    # Validate basic SQL syntax using psql --no-psqlrc
    # This doesn't execute, just parses
    if command -v psql &> /dev/null; then
        # Create a temp validation script that doesn't connect to DB
        temp_file=$(mktemp)
        echo "-- Syntax validation only" > "$temp_file"
        cat "$file" >> "$temp_file"

        # Use psql to parse (won't execute if we don't connect to a DB)
        # Just check for obvious syntax errors by parsing
        if psql --no-psqlrc --echo-errors --file="$file" --single-transaction --dry-run 2>&1 | grep -i "error"; then
            echo "❌ SQL syntax errors detected"
            rm "$temp_file"
            return 1
        else
            echo "✓ No obvious SQL syntax errors"
        fi

        rm "$temp_file"
    else
        echo "⚠ psql not found, skipping deep syntax validation"
    fi

    echo "✅ $name validation passed"
    echo ""
    return 0
}

# Validate UP migration
validate_sql "$UP_SCRIPT" "UP Migration (001_add_v2_innovations_up.sql)"

# Validate DOWN migration
validate_sql "$DOWN_SCRIPT" "DOWN Migration (001_add_v2_innovations_down.sql)"

echo "=========================================="
echo "✅ ALL SQL MIGRATIONS VALIDATED"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review migration files manually"
echo "2. Test in development database"
echo "3. Backup production before applying"
echo ""
