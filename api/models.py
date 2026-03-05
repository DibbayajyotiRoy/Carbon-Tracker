from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FoodEmissionFactor(Base):
    __tablename__ = "food_emission_factors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    food_type = Column(String, unique=True)
    food_type_normalized = Column(String, unique=True, index=True)
    kgco2e_per_kg = Column(Float)

class FoodEmission(Base):
    __tablename__ = "food_emissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    session_id = Column(String)
    food_type = Column(String)
    quantity_grams = Column(Float)
    kgco2e_per_kg = Column(Float)
    co2_kg = Column(Float)
    ate_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class GPSLog(Base):
    __tablename__ = "gps_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    distance_km = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    vin = Column(String, unique=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    emission_factor = Column(Float, nullable=True)
    
    user = relationship("User")

class ElectricityBill(Base):
    __tablename__ = "electricity_bills"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    file_name = Column(String)
    file_type = Column(String)
    bill_data = Column(LargeBinary, nullable=True) # Binary data for the PDF/Image
    extracted_data = Column(JSON) # Store JSON fields like consumerName, unitsConsumed etc.
    carbon_emitted = Column(Float)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class LPGRecord(Base):
    __tablename__ = "lpg_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    consumer_number = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    connection_type = Column(String, nullable=True)
    subsidy_status = Column(String, nullable=True)
    cylinders_consumed = Column(Float)
    lpg_in_kg = Column(Float)
    carbon_emitted = Column(Float)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
