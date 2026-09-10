"""
Impression du rapport de qualite standard, format DATA QUALITY REPORT.
"""


def print_quality_report(table: str, total: int, valid_count: int, rejected_count: int, details: dict) -> None:
    print(f"DATA QUALITY REPORT - {table}")
    print("-" * 40)
    print(f"Rows processed  : {total:,}")
    print(f"Valid rows      : {valid_count:,}")
    print(f"Rejected rows   : {rejected_count:,}")
    print(f"Quality score   : {100 * valid_count / total:.2f}%")
    print()
    for label, count in details.items():
        print(f"{label:<24}: {count:,}")