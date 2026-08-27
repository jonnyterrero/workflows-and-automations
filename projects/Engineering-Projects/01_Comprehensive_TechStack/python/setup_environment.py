#!/usr/bin/env python3
"""
Biomedical & Mechanical Engineering Python Environment Setup
This script helps set up the Python environment with all necessary packages.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install all required packages from requirements.txt"""
    print("🚀 Setting up Python environment for Biomedical & Mechanical Engineering...")
    
    # Check if requirements.txt exists
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        # Install packages
        print("📦 Installing packages from requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def create_sample_scripts():
    """Create sample Python scripts for common engineering tasks"""
    print("📝 Creating sample scripts...")
    
    # Data Analysis Sample
    data_analysis_script = """#!/usr/bin/env python3
\"\"\"
Sample Data Analysis Script for Biomedical/Mechanical Engineering
\"\"\"

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def analyze_sensor_data(data_file):
    \"\"\"
    Analyze sensor data from biomedical or mechanical systems
    \"\"\"
    # Load data
    df = pd.read_csv(data_file)
    
    # Basic statistics
    print("Data Summary:")
    print(df.describe())
    
    # Plot time series
    plt.figure(figsize=(12, 6))
    for column in df.columns[1:]:  # Skip timestamp column
        plt.plot(df.iloc[:, 0], df[column], label=column)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('Sensor Data Time Series')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    # Statistical analysis
    for column in df.columns[1:]:
        print(f"\\n{column} Statistics:")
        print(f"Mean: {df[column].mean():.4f}")
        print(f"Std: {df[column].std():.4f}")
        print(f"Min: {df[column].min():.4f}")
        print(f"Max: {df[column].max():.4f}")

if __name__ == "__main__":
    # Example usage
    print("Data Analysis Script for Engineering Applications")
    # analyze_sensor_data("your_data.csv")
"""
    
    # Signal Processing Sample
    signal_processing_script = """#!/usr/bin/env python3
\"\"\"
Sample Signal Processing Script for Biomedical/Mechanical Engineering
\"\"\"

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fft, fftfreq

def filter_biomedical_signal(data, fs, filter_type='lowpass', cutoff=50):
    \"\"\"
    Filter biomedical signals (ECG, EMG, etc.)
    \"\"\"
    # Design filter
    nyquist = fs / 2
    normalized_cutoff = cutoff / nyquist
    
    if filter_type == 'lowpass':
        b, a = signal.butter(4, normalized_cutoff, btype='low')
    elif filter_type == 'highpass':
        b, a = signal.butter(4, normalized_cutoff, btype='high')
    elif filter_type == 'bandpass':
        b, a = signal.butter(4, [normalized_cutoff*0.8, normalized_cutoff*1.2], btype='band')
    
    # Apply filter
    filtered_data = signal.filtfilt(b, a, data)
    return filtered_data

def analyze_frequency_content(data, fs):
    \"\"\"
    Analyze frequency content of signals
    \"\"\"
    # FFT
    fft_data = fft(data)
    freqs = fftfreq(len(data), 1/fs)
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(data)
    plt.title('Time Domain')
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    
    plt.subplot(1, 2, 2)
    plt.plot(freqs[:len(freqs)//2], np.abs(fft_data[:len(fft_data)//2]))
    plt.title('Frequency Domain')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Example usage
    print("Signal Processing Script for Biomedical Applications")
    # Generate sample ECG-like signal
    fs = 1000  # Sampling frequency
    t = np.linspace(0, 1, fs)
    signal_data = np.sin(2*np.pi*1*t) + 0.5*np.sin(2*np.pi*60*t) + 0.1*np.random.randn(fs)
    
    # Filter and analyze
    filtered = filter_biomedical_signal(signal_data, fs, 'lowpass', 30)
    analyze_frequency_content(filtered, fs)
"""
    
    # Machine Learning Sample
    ml_script = """#!/usr/bin/env python3
\"\"\"
Sample Machine Learning Script for Biomedical/Mechanical Engineering
\"\"\"

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def classify_biomedical_data(X, y):
    \"\"\"
    Classify biomedical data using machine learning
    \"\"\"
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Evaluate
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': range(len(model.feature_importances_)),
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance.head(10), x='importance', y='feature')
    plt.title('Feature Importance')
    plt.show()
    
    return model

def predict_mechanical_failure(features):
    \"\"\"
    Predict mechanical system failure based on sensor data
    \"\"\"
    # This would typically use real sensor data
    # For demonstration, we'll create synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    # Generate synthetic data
    X = np.random.randn(n_samples, n_features)
    # Create failure labels based on some combination of features
    y = (X[:, 0] + X[:, 1] + np.random.randn(n_samples) * 0.1 > 0).astype(int)
    
    model = classify_biomedical_data(X, y)
    return model

if __name__ == "__main__":
    print("Machine Learning Script for Engineering Applications")
    # predict_mechanical_failure(None)
"""
    
    # Write scripts to appropriate directories
    scripts = {
        "data_analysis/sample_data_analysis.py": data_analysis_script,
        "signal_processing/sample_signal_processing.py": signal_processing_script,
        "machine_learning/sample_ml_classification.py": ml_script
    }
    
    for filepath, content in scripts.items():
        full_path = Path(filepath)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {filepath}")

def main():
    """Main setup function"""
    print("🔧 Biomedical & Mechanical Engineering Python Environment Setup")
    print("=" * 60)
    
    # Install requirements
    if install_requirements():
        # Create sample scripts
        create_sample_scripts()
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Activate your virtual environment")
        print("2. Run the sample scripts to test your setup")
        print("3. Start working on your engineering projects!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    main()

