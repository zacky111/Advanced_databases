from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class PolicyMeasureLevel(Base):
    __tablename__ = 'policy_measure_levels'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    level_type = Column(String)


class Country(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    iso3 = Column(String(3), nullable=False)
    name = Column(String, nullable=False)
    income_level = Column(String, nullable=True)

    measures = relationship('Measure', back_populates='country')


class Measure(Base):
    __tablename__ = 'measures'

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_id = Column(Integer)
    country_id = Column(Integer, ForeignKey('countries.id'))

    country = relationship('Country', back_populates='measures')
    date_ref = relationship('MeasureDate', uselist=False, back_populates='measure')
    detail_ref = relationship('MeasureDetail', uselist=False, back_populates='measure')
    modification_ref = relationship('MeasureModification', uselist=False, back_populates='measure')
    policy_links = relationship('MeasurePolicyLink', back_populates='measure')


class MeasureDate(Base):
    __tablename__ = 'measure_dates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    measure_id = Column(Integer, ForeignKey('measures.id'))
    date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)

    measure = relationship('Measure', back_populates='date_ref')


class MeasureDetail(Base):
    __tablename__ = 'measure_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    measure_id = Column(Integer, ForeignKey('measures.id'))
    authority = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    reference = Column(Text, nullable=True)

    measure = relationship('Measure', back_populates='detail_ref')


class MeasureModification(Base):
    __tablename__ = 'measure_modifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    measure_id = Column(Integer, ForeignKey('measures.id'))
    was_modified = Column(String, nullable=True)
    modification_of_parent = Column(String, nullable=True)
    parent_measure = Column(String, nullable=True)

    measure = relationship('Measure', back_populates='modification_ref')


class MeasurePolicyLink(Base):
    __tablename__ = 'measure_policy_links'

    id = Column(Integer, primary_key=True, autoincrement=True)
    measure_id = Column(Integer, ForeignKey('measures.id'))
    policy_measure_level_id = Column(Integer, ForeignKey('policy_measure_levels.id'))

    measure = relationship('Measure', back_populates='policy_links')
    policy = relationship('PolicyMeasureLevel')
