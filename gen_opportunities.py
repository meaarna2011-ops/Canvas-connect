
import json
from pathlib import Path
from datetime import date

DATA_FILE = Path("verified_opportunities.json")
OUTPUT_FILE = Path("replace_opportunities.sql")

REQUIRED_FIELDS = {
    "title",
    "organization",
    "description",
    "source_url",
    "application_url",
    "opportunity_type",
    "media",
    "categories",
    "country",
}

def sql_text(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"

def sql_array(values):
    values = values or []
    return (
        "ARRAY[" + ", ".join(sql_text(v) for v in values) + "]"
        if values else "ARRAY[]::text[]"
    )

def main():
    if not DATA_FILE.exists():
        raise SystemExit(
            "Missing verified_opportunities.json. "
            "Add reviewed records before generating SQL."
        )

    records = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    if not isinstance(records, list) or not records:
        raise SystemExit("The dataset must be a non-empty JSON list.")

    seen_urls = set()

    for i, record in enumerate(records, start=1):
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            raise SystemExit(f"Record {i} is missing: {sorted(missing)}")

        url = record["source_url"]
        if not url.startswith("https://"):
            raise SystemExit(f"Record {i} has a non-HTTPS source URL.")

        if url in seen_urls:
            raise SystemExit(f"Duplicate source URL: {url}")
        seen_urls.add(url)

        if record.get("verification_status") != "verified":
            raise SystemExit(
                f"Record {i} must be checked against its official source "
                "before being marked verified."
            )

    columns = [
        "title", "description", "organization", "opportunity_type",
        "media", "categories", "location_text", "country", "region",
        "city", "format", "scope", "eligibility_age",
        "eligibility_residency", "eligibility_notes", "has_entry_fee",
        "entry_fee_amount", "compensation", "deadline_date", "status",
        "source_url", "source_name", "application_url",
        "verification_status", "canonical_url", "last_checked"
    ]

    statements = []

    for record in records:
        values = []
        for column in columns:
            value = record.get(column)

            if column in ("media", "categories"):
                values.append(sql_array(value))
            elif column == "has_entry_fee":
                values.append(
                    "TRUE" if value is True else
                    "FALSE" if value is False else "NULL"
                )
            elif column in ("deadline_date", "last_checked"):
                values.append(
                    f"'{value}'" if value else "NULL"
                )
            elif column == "entry_fee_amount":
                values.append(str(value) if value is not None else "NULL")
            else:
                values.append(sql_text(value))

        statements.append(
            f"INSERT INTO public.opportunities ({', '.join(columns)})\n"
            f"VALUES ({', '.join(values)});"
        )

    OUTPUT_FILE.write_text(
        "-- Generated from reviewed opportunity records.\n"
        "-- Review the schema and backup before execution.\n\n"
        + "\n\n".join(statements) + "\n",
        encoding="utf-8"
    )

    print(f"Generated SQL for {len(records)} reviewed opportunities.")
    print(f"Output: {OUTPUT_FILE.resolve()}")

if __name__ == "__main__":
    main()
