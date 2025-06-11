from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date

from src.database.connection import engine
from src.database.model import (
    Measure, Country, MeasureDate, MeasureDetail, MeasurePolicyLink, PolicyMeasureLevel
)
from src.utils.log import get_logger

log = get_logger(__name__)


def get_filtered_measures(
    session,
    country=None,
    date_from=None,  
    date_to=None,  
    policy_type=None,
    target_group=None,
    level=None,
):
    log.info(f"Filtering measures with parameters: {locals()}")

    query = session.query(Measure)\
        .join(Country)\
        .join(MeasureDate)\
        .join(MeasureDetail)\
        .join(MeasurePolicyLink)\
        .join(PolicyMeasureLevel)

    filters = []

    if country:
        if isinstance(country, list):
            filters.append(Country.name.in_(country))
        else:
            filters.append(Country.name == country)

    if date_from:
        filters.append(MeasureDate.date >= date_from)
    if date_to:
        filters.append(MeasureDate.date <= date_to)

    if policy_type:
        if isinstance(policy_type, list):
            filters.append(PolicyMeasureLevel.name.in_(policy_type))
        else:
            filters.append(PolicyMeasureLevel.name == policy_type)

    if target_group:
        if isinstance(target_group, list):
            filters.append(PolicyMeasureLevel.name.in_(target_group))
        else:
            filters.append(PolicyMeasureLevel.name == target_group)

    if level:
        if isinstance(level, list):
            filters.append(PolicyMeasureLevel.level_type.in_(level))
        else:
            filters.append(PolicyMeasureLevel.level_type == level)

    if filters:
        query = query.filter(and_(*filters))

    results = query.all()
    log.info(f"Total measures found: {len(results)}")
    return results


if __name__ == "__main__":
    # ---- Set your filter values here ----
    FILTER_COUNTRY = "China"  # Country name or None
    FILTER_DATE_FROM = date(2020, 1, 1)  # Start date or None
    FILTER_DATE_TO = date(2020, 2, 29)   # End date or None
    FILTER_POLICY_TYPE = None  # Level 1 policy measure or None
    FILTER_TARGET_GROUP = None    # Level 1 policy measure or None
    FILTER_LEVEL = None  # Level of intervention (customize as per your data) or None
    # -------------------------------------

    with Session(engine) as session:
        results = get_filtered_measures(
            session,
            country=FILTER_COUNTRY,
            date_from=FILTER_DATE_FROM,
            date_to=FILTER_DATE_TO,
            policy_type=FILTER_POLICY_TYPE,
            target_group=FILTER_TARGET_GROUP,
            level=FILTER_LEVEL
        )

        for m in results:
            print({
                "id": m.id,
                "country": m.country.name,
                "date": m.date_ref.date if m.date_ref else None,
                "policy_type": [pl.policy.name for pl in m.policy_links],
                "details": m.detail_ref.details if m.detail_ref else None,
                "level": [pl.policy.level_type for pl in m.policy_links],
            })