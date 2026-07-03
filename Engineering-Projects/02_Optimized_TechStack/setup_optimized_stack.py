#!/usr/bin/env python3
"""
Setup Script for Optimized Tech Stack
MATLAB + Python + SQL + Web Framework
"""

import subprocess
import sys
import os
from pathlib import Path

def install_python_packages():
    """Install Python packages for the optimized stack"""
    print("🐍 Installing Python packages for optimized tech stack...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_optimized.txt"])
        print("✅ Python packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python packages: {e}")
        return False

def setup_database():
    """Setup PostgreSQL database"""
    print("🗄️ Setting up PostgreSQL database...")
    
    # Check if PostgreSQL is installed
    try:
        subprocess.run(["psql", "--version"], check=True, capture_output=True)
        print("✅ PostgreSQL is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PostgreSQL not found. Please install PostgreSQL:")
        print("   Windows: Download from postgresql.org")
        print("   macOS: brew install postgresql")
        print("   Ubuntu: sudo apt install postgresql postgresql-contrib")
        return False
    
    # Create database
    try:
        subprocess.run([
            "psql", "-U", "postgres", "-c", 
            "CREATE DATABASE engineering_db;"
        ], check=True, capture_output=True)
        print("✅ Database 'engineering_db' created")
    except subprocess.CalledProcessError:
        print("⚠️ Database might already exist or connection failed")
    
    return True

def create_project_structure():
    """Create optimized project structure"""
    print("📁 Creating optimized project structure...")
    
    directories = [
        "backend",
        "frontend",
        "database",
        "matlab_scripts",
        "data_processing",
        "api",
        "tests",
        "docs",
        "deployment"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create essential files
    files_to_create = {
        "backend/main.py": "# FastAPI backend application",
        "frontend/package.json": '{"name": "engineering-frontend", "version": "1.0.0"}',
        "database/schema.sql": "-- Database schema for engineering applications",
        "matlab_scripts/signal_processing.m": "% MATLAB signal processing scripts",
        "data_processing/etl.py": "# Data processing and ETL scripts",
        "api/endpoints.py": "# API endpoint definitions",
        "tests/test_api.py": "# API tests",
        "docs/README.md": "# Project documentation",
        "deployment/docker-compose.yml": "# Docker deployment configuration"
    }
    
    for filepath, content in files_to_create.items():
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Created file: {filepath}")

def create_matlab_integration():
    """Create MATLAB integration examples"""
    print("🔢 Creating MATLAB integration examples...")
    
    matlab_script = """%% MATLAB Integration with Python
% This script demonstrates how to work with Python data

function result = process_engineering_data(data)
    % Process engineering data using MATLAB
    % Input: data (from Python)
    % Output: processed result
    
    % Signal processing
    filtered_data = lowpass(data, 0.1);
    
    % Statistical analysis
    stats.mean = mean(data);
    stats.std = std(data);
    stats.max = max(data);
    stats.min = min(data);
    
    % Control system analysis
    s = tf('s');
    sys = 1/(s+1);
    step_response = step(sys);
    
    % Return results
    result.filtered_data = filtered_data;
    result.statistics = stats;
    result.step_response = step_response;
    
    fprintf('MATLAB processing complete\\n');
end

% Example usage
% data = [1, 2, 3, 4, 5];  % This would come from Python
% result = process_engineering_data(data);
"""
    
    with open("matlab_scripts/process_engineering_data.m", 'w') as f:
        f.write(matlab_script)
    
    print("✅ Created MATLAB integration script")

def create_docker_setup():
    """Create Docker configuration for deployment"""
    print("🐳 Creating Docker setup...")
    
    dockerfile_content = """FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements_optimized.txt .
RUN pip install --no-cache-dir -r requirements_optimized.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    docker_compose_content = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/engineering_db
    depends_on:
      - db
    
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=engineering_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
"""
    
    with open("Dockerfile", 'w') as f:
        f.write(dockerfile_content)
    
    with open("docker-compose.yml", 'w') as f:
        f.write(docker_compose_content)
    
    print("✅ Created Docker configuration")

def create_react_frontend():
    """Create React frontend setup"""
    print("⚛️ Creating React frontend setup...")
    
    package_json = """{
  "name": "engineering-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.4.0",
    "plotly.js": "^2.24.0",
    "react-plotly.js": "^2.6.0",
    "antd": "^5.8.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}"""
    
    with open("frontend/package.json", 'w') as f:
        f.write(package_json)
    
    print("✅ Created React frontend configuration")

def main():
    """Main setup function"""
    print("🚀 Setting up Optimized Tech Stack")
    print("=" * 50)
    print("MATLAB + Python + SQL + Web Framework")
    print("=" * 50)
    
    success = True
    
    # Install Python packages
    if not install_python_packages():
        success = False
    
    # Setup database
    if not setup_database():
        success = False
    
    # Create project structure
    create_project_structure()
    
    # Create MATLAB integration
    create_matlab_integration()
    
    # Create Docker setup
    create_docker_setup()
    
    # Create React frontend
    create_react_frontend()
    
    if success:
        print("\n🎉 Optimized Tech Stack Setup Complete!")
        print("\nNext steps:")
        print("1. Install PostgreSQL if not already installed")
        print("2. Install MATLAB with required toolboxes")
        print("3. Run: python sample_app_structure.py")
        print("4. Navigate to frontend/ and run: npm install && npm start")
        print("5. Open http://localhost:3000 for frontend")
        print("6. Open http://localhost:8000/docs for API documentation")
    else:
        print("\n⚠️ Setup completed with some issues. Please check the messages above.")

if __name__ == "__main__":
    main()
