"""Print the PawMatch schema as supporting evidence for the manual DB1 test."""

import sqlite3

from database import DATABASE_PATH


if not DATABASE_PATH.exists():
    raise SystemExit("pawmatch.db does not exist. Run: python3 setup_database.py")

with sqlite3.connect(DATABASE_PATH) as connection:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()

    for table_row in tables:
        table = table_row["name"]
        print(f"\n{table}")
        print("-" * len(table))

        for column in connection.execute(f"PRAGMA table_info({table})"):
            key = " PRIMARY KEY" if column["pk"] else ""
            required = " NOT NULL" if column["notnull"] else ""
            print(f"{column['name']}: {column['type']}{required}{key}")

        foreign_keys = connection.execute(
            f"PRAGMA foreign_key_list({table})"
        ).fetchall()
        for foreign_key in foreign_keys:
            print(
                "FOREIGN KEY: "
                f"{foreign_key['from']} -> "
                f"{foreign_key['table']}.{foreign_key['to']} "
                f"ON DELETE {foreign_key['on_delete']}"
            )

