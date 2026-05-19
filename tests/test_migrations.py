import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.migrations import run_migrations


class FakeMigrationDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE schema_version(id INTEGER PRIMARY KEY AUTOINCREMENT, version INTEGER NOT NULL UNIQUE, updated_at TEXT NOT NULL)"
        )
        self.calls = []

    def _get_schema_version(self):
        row = self.conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] if row and row[0] else 0

    def transaction(self):
        class Transaction:
            def __init__(self, conn):
                self.conn = conn

            def __enter__(self):
                self.conn.execute("BEGIN")
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.conn.rollback()
                else:
                    self.conn.commit()

        return Transaction(self.conn)


class TestMigrationVersioning(unittest.TestCase):
    def test_incremental_patch_numbers_start_at_v2(self):
        db = FakeMigrationDB()

        def patch(db_obj):
            db_obj.calls.append("v2")

        original_patches = run_migrations.__globals__["_migration_v2"]
        try:
            run_migrations.__globals__["_migration_v2"] = patch
            # Keep the test narrow: mark current schema at v1 and temporarily
            # replace later migrations with no-op functions.
            later_names = [
                name
                for name in run_migrations.__globals__
                if name.startswith("_migration_v") and name != "_migration_v2"
            ]
            originals = {name: run_migrations.__globals__[name] for name in later_names}
            for name in later_names:
                run_migrations.__globals__[name] = lambda _db: None
            db.conn.execute("INSERT INTO schema_version(version, updated_at) VALUES(1, 'seed')")
            db.conn.commit()
            run_migrations(db)
        finally:
            run_migrations.__globals__["_migration_v2"] = original_patches
            for name, fn in locals().get("originals", {}).items():
                run_migrations.__globals__[name] = fn

        self.assertEqual(db.calls, ["v2"])
        self.assertEqual(db._get_schema_version(), 19)
        db.conn.close()


if __name__ == "__main__":
    unittest.main()
