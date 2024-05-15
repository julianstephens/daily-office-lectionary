import json
from datetime import datetime
from os import path

import pandas as pd
import tika
from dateutil.easter import *  # noqa: F403

from daily_office_lectionary.db import db

DATA_DIR = "./data"
DOC_START = 840
DOC_END = 18437
tika.initVM()


def create_collects_json():
    def is_date(text: str) -> bool:
        try:
            datetime.strptime(text, "%B %d")
            return True
        except ValueError:
            return False

    def is_page_break(pageNo: str, date: str) -> bool:
        return pageNo.isdigit() and is_date(date.strip())

    def read_pdf() -> list[str]:
        from tika import parser

        parsed: dict[str, str] = parser.from_file(
            path.join(DATA_DIR, "lm_great_cloud_of_witnesses.pdf")
        )  # type: ignore
        lines = [
            line.lstrip()
            for line in list(filter(lambda x: x, parsed["content"].split("\n")))
        ][DOC_START:DOC_END]
        return lines

    def format_entries(lines: list[str]) -> dict[str, str]:
        entries = {}
        i = 0

        while i < len(lines) - 1:
            date = lines[i + 1]
            if is_page_break(lines[i], date):
                page_content = lines[i + 2] + "\n"
                for j in range(i + 3, len(lines)):
                    if j + 1 < len(lines) and is_page_break(lines[j], lines[j + 1]):
                        i = j - 1
                        break
                    if j == i + 3 and lines[j][-1].isdigit():
                        page_content += lines[j] + "\n"
                    else:
                        page_content += lines[j]
                entries[date.strip()] = page_content

            i += 1
        return entries

    lines = read_pdf()
    entries = format_entries(lines)
    collects = {}

    for k, v in entries.items():
        rite = v.split("II")
        collects[k] = rite[1].lstrip().split("Amen.")[0] + "Amen."

    return json.loads(json.dumps(collects))


def create_lectionary_json():
    df = pd.read_csv(path.join(DATA_DIR, "lectionary.csv"), encoding="utf-8-sig")
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("morning prayer", "mp")
    df.columns = df.columns.str.replace("evening prayer", "ep")
    df.columns = df.columns.str.replace("1st reading", "1")
    df.columns = df.columns.str.replace("2nd reading", "2")
    df.columns = df.columns.str.replace("reading 1", "1")
    df.columns = df.columns.str.replace("reading 2", "2")
    df.columns = df.columns.str.replace(" ", "_")
    df.drop(columns=["psaltar", "rite"], inplace=True)
    df["date"] = df["date"].apply(
        lambda x: datetime.strftime(
            datetime.strptime(f"{x} {datetime.now().year}", "%B %d %Y"), "%Y-%m-%d"
        )
    )

    return df.to_dict(orient="records")


def seed_lectionary():
    lectionary = create_lectionary_json()
    for day in lectionary:
        date = day["date"]
        del day["date"]
        db.set(date, json.dumps(day))


def seed_special_collects():
    collects = create_collects_json()
    for k, v in collects.items():
        date = datetime.strptime(f"{k} {datetime.now().year}", "%B %d %Y").strftime(
            "%Y-%m-%d"
        )

        data = db.get(date)
        if data:
            json_data = json.loads(str(data, "utf-8"))  # type: ignore
            json_data["collect"] = v
            db.set(date, json.dumps(json_data))


def seed_season_collects():
    with open(path.join(DATA_DIR, "seasonal_collects.json")) as f:
        seasonal_collects = json.load(f)

    for collect in seasonal_collects:
        db.set(collect["id"], collect["text"])


if __name__ == "__main__":
    db.flushdb()
    seed_lectionary()
    seed_special_collects()
    seed_season_collects()
