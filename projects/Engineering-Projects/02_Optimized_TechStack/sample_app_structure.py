#!/usr/bin/env python3
"""
Sample Application Structure for Optimized Tech Stack
MATLAB + Python + SQL + Web Framework
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import numpy as np
from typing import List, Optional
import uvicorn

# Database setup
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/engineering_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sensor_type = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    location = Column(String)

class PatientData(Base):
    __tablename__ = "patient_data"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    heart_rate = Column(Float)
    blood_pressure_systolic = Column(Float)
    blood_pressure_diastolic = Column(Float)
    temperature = Column(Float)

# Pydantic models
class SensorDataCreate(BaseModel):
    sensor_type: str
    value: float
    unit: str
    location: str

class PatientDataCreate(BaseModel):
    patient_id: str
    heart_rate: float
    blood_pressure_systolic: float
    blood_pressure_diastolic: float
    temperature: float

class SensorDataResponse(BaseModel):
    id: int
    timestamp: datetime
    sensor_type: str
    value: float
    unit: str
    location: str

# FastAPI app
app = FastAPI(title="Biomedical Engineering Data API", version="1.0.0")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Signal Processing Functions (MATLAB-like functionality in Python)
def filter_signal(data: List[float], cutoff_freq: float = 0.1) -> List[float]:
    """Simple low-pass filter implementation"""
    from scipy import signal
    b, a = signal.butter(4, cutoff_freq, 'low')
    return signal.filtfilt(b, a, data).tolist()

def calculate_statistics(data: List[float]) -> dict:
    """Calculate basic statistics"""
    return {
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data)),
        "median": float(np.median(data))
    }

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Biomedical Engineering Data API", "version": "1.0.0"}

@app.post("/sensor-data/", response_model=SensorDataResponse)
async def create_sensor_data(data: SensorDataCreate, db: Session = Depends(get_db)):
    """Create new sensor data entry"""
    db_data = SensorData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@app.get("/sensor-data/", response_model=List[SensorDataResponse])
async def get_sensor_data(
    sensor_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get sensor data with optional filtering"""
    query = db.query(SensorData)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    return query.limit(limit).all()

@app.get("/sensor-data/analysis/{sensor_type}")
async def analyze_sensor_data(sensor_type: str, db: Session = Depends(get_db)):
    """Analyze sensor data using signal processing"""
    # Get data from database
    data = db.query(SensorData).filter(SensorData.sensor_type == sensor_type).all()
    
    if not data:
        raise HTTPException(status_code=404, detail="No data found for sensor type")
    
    # Extract values
    values = [d.value for d in data]
    
    # Apply signal processing
    filtered_values = filter_signal(values)
    statistics = calculate_statistics(values)
    
    return {
        "sensor_type": sensor_type,
        "total_samples": len(values),
        "statistics": statistics,
        "filtered_data": filtered_values[:10],  # Return first 10 filtered values
        "analysis_timestamp": datetime.utcnow()
    }

@app.post("/patient-data/")
async def create_patient_data(data: PatientDataCreate, db: Session = Depends(get_db)):
    """Create new patient data entry"""
    db_data = PatientData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@app.get("/patient-data/{patient_id}/analysis")
async def analyze_patient_data(patient_id: str, db: Session = Depends(get_db)):
    """Analyze patient data for biomedical insights"""
    # Get patient data
    data = db.query(PatientData).filter(PatientData.patient_id == patient_id).all()
    
    if not data:
        raise HTTPException(status_code=404, detail="No data found for patient")
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame([{
        'timestamp': d.timestamp,
        'heart_rate': d.heart_rate,
        'bp_systolic': d.blood_pressure_systolic,
        'bp_diastolic': d.blood_pressure_diastolic,
        'temperature': d.temperature
    } for d in data])
    
    # Calculate trends and statistics
    analysis = {
        "patient_id": patient_id,
        "total_records": len(data),
        "date_range": {
            "start": df['timestamp'].min().isoformat(),
            "end": df['timestamp'].max().isoformat()
        },
        "heart_rate": {
            "current": float(df['heart_rate'].iloc[-1]),
            "average": float(df['heart_rate'].mean()),
            "trend": "increasing" if df['heart_rate'].iloc[-1] > df['heart_rate'].mean() else "decreasing"
        },
        "blood_pressure": {
            "current_systolic": float(df['bp_systolic'].iloc[-1]),
            "current_diastolic": float(df['bp_diastolic'].iloc[-1]),
            "average_systolic": float(df['bp_systolic'].mean()),
            "average_diastolic": float(df['bp_diastolic'].mean())
        },
        "temperature": {
            "current": float(df['temperature'].iloc[-1]),
            "average": float(df['temperature'].mean()),
            "fever_risk": "high" if df['temperature'].iloc[-1] > 100.4 else "normal"
        }
    }
    
    return analysis

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# MATLAB Integration Example (would require MATLAB Engine for Python)
def matlab_integration_example():
    """
    Example of how to integrate MATLAB with Python
    This would require MATLAB Engine for Python to be installed
    """
    try:
        import matlab.engine
        eng = matlab.engine.start_matlab()
        
        # Example: Use MATLAB for advanced signal processing
        # result = eng.signal_processing_function(data)
        # eng.quit()
        
        return "MATLAB integration available"
    except ImportError:
        return "MATLAB Engine for Python not installed"

if __name__ == "__main__":
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=8000)
