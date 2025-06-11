import csv
from datetime import datetime
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.database.connection import engine
from src.database.model import (
    Country, Measure, MeasureDate, MeasureDetail,
    MeasureModification, PolicyMeasureLevel, MeasurePolicyLink
)
from tqdm import tqdm

def get_or_create_country(session: Session, row: Dict[str, Any]) -> Country:
    country = session.query(Country).filter_by(iso3=row['Country ISO3']).first()
    if not country:
        country = Country(
            iso3=row['Country ISO3'],
            name=row['Country Name'],
            income_level=row['Income Level'] or None
        )
        session.add(country)
        session.flush()
    return country

def get_or_create_policy(session: Session, level: str, name: str) -> PolicyMeasureLevel | None:
    if not name:
        return None
    policy = session.query(PolicyMeasureLevel).filter_by(name=name, level_type=level).first()
    if not policy:
        policy = PolicyMeasureLevel(name=name, level_type=level)
        session.add(policy)
        session.flush()
    return policy

def import_data(session: Session, csv_path: str = 'sources/covid-fci-data-cleaned.csv') -> None:
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in tqdm(reader, desc="Importing data", unit="rows"):
            # Country
            country = get_or_create_country(session, row)

            # Measure
            measure = Measure(
                original_id=row['Original_ID'],
                country=country
            )
            session.add(measure)
            session.flush()

            # MeasureDate
            date = datetime.strptime(row['Date'], "%Y-%m-%d").date() if row['Date'] else None
            termination_date = (
                datetime.strptime(row['Termination Date'], "%Y-%m-%d").date()
                if row['Termination Date'] else None
            )
            measure_date = MeasureDate(
                measure=measure,
                date=date,
                termination_date=termination_date
            )
            session.add(measure_date)

            # MeasureDetail
            measure_detail = MeasureDetail(
                measure=measure,
                authority=row['Authority'] or None,
                details=row['Details of the measure'] or None,
                reference=row['Reference'] or None
            )
            session.add(measure_detail)

            # MeasureModification
            measure_mod = MeasureModification(
                measure=measure,
                was_modified=row['was_modified'] or None,
                modification_of_parent=row['Modification of Parent Measure'] or None,
                parent_measure=row['Parent Measure'] or None
            )
            session.add(measure_mod)

            # Policy Levels (up to 3)
            for level in [1, 2, 3]:
                col = f'Level {level} policy measures'
                policy = get_or_create_policy(session, f'Level {level}', row[col])
                if policy:
                    mpl = MeasurePolicyLink(
                        measure=measure,
                        policy=policy
                    )
                    session.add(mpl)

        session.commit()
        print("Data import complete.")

if __name__ == "__main__":
    with Session(engine) as session:
        import_data(session)