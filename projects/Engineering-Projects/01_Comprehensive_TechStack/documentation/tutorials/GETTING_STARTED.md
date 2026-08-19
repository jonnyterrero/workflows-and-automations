# Getting Started Tutorial

Welcome to the Biomedical & Mechanical Engineering Tech Stack! This tutorial will guide you through your first engineering project using the tools in this stack.

## 🎯 Tutorial Overview

In this tutorial, you'll learn to:
1. Analyze sensor data from a biomedical device
2. Process signals to remove noise
3. Create a simple control system
4. Design a basic mechanical component
5. Run a finite element analysis

## 📊 Part 1: Data Analysis with Python

### Step 1: Set up your environment
```bash
# Activate your virtual environment
source engineering_env/bin/activate  # or engineering_env\Scripts\activate on Windows

# Navigate to the project directory
cd "path/to/biomedical-mechanical-tech-stack"
```

### Step 2: Create sample sensor data
```python
# Create a new file: tutorial_sensor_analysis.py
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal

# Generate sample ECG-like data
fs = 1000  # Sampling frequency (Hz)
t = np.linspace(0, 10, fs*10)  # 10 seconds of data

# Create ECG-like signal with noise
heart_rate = 1.2  # Hz (72 BPM)
ecg_signal = np.sin(2*np.pi*heart_rate*t) + 0.3*np.sin(2*np.pi*60*t) + 0.1*np.random.randn(len(t))

# Save to CSV
df = pd.DataFrame({
    'time': t,
    'ecg': ecg_signal
})
df.to_csv('tutorial_data.csv', index=False)
print("Sample data created: tutorial_data.csv")
```

### Step 3: Analyze the data
```python
# Load and analyze the data
df = pd.read_csv('tutorial_data.csv')

# Basic statistics
print("Data Summary:")
print(f"Duration: {df['time'].max():.1f} seconds")
print(f"Sampling rate: {1/(df['time'][1]-df['time'][0]):.0f} Hz")
print(f"Mean ECG value: {df['ecg'].mean():.3f}")
print(f"ECG standard deviation: {df['ecg'].std():.3f}")

# Plot the data
plt.figure(figsize=(12, 6))
plt.plot(df['time'], df['ecg'], 'b-', linewidth=1)
plt.xlabel('Time (s)')
plt.ylabel('ECG Amplitude')
plt.title('Raw ECG Signal')
plt.grid(True)
plt.show()
```

### Step 4: Filter the signal
```python
# Design and apply a low-pass filter
fc = 40  # Cutoff frequency (Hz)
b, a = signal.butter(4, fc/(fs/2), 'low')
filtered_ecg = signal.filtfilt(b, a, df['ecg'])

# Plot comparison
plt.figure(figsize=(12, 8))
plt.subplot(2, 1, 1)
plt.plot(df['time'], df['ecg'], 'b-', alpha=0.7, label='Original')
plt.plot(df['time'], filtered_ecg, 'r-', linewidth=2, label='Filtered')
plt.xlabel('Time (s)')
plt.ylabel('ECG Amplitude')
plt.title('ECG Signal Filtering')
plt.legend()
plt.grid(True)

# Frequency domain analysis
N = len(df['ecg'])
f = np.fft.fftfreq(N, 1/fs)
fft_original = np.abs(np.fft.fft(df['ecg']))
fft_filtered = np.abs(np.fft.fft(filtered_ecg))

plt.subplot(2, 1, 2)
plt.semilogy(f[:N//2], fft_original[:N//2], 'b-', alpha=0.7, label='Original')
plt.semilogy(f[:N//2], fft_filtered[:N//2], 'r-', linewidth=2, label='Filtered')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.title('Frequency Spectrum')
plt.legend()
plt.grid(True)
plt.xlim([0, 100])
plt.tight_layout()
plt.show()
```

## 🔢 Part 2: Control System with MATLAB

### Step 1: Open MATLAB and run setup
```matlab
% Run the setup script
run matlab/setup_matlab.m

% Create a new script: tutorial_control_system.m
```

### Step 2: Design a PID controller
```matlab
%% Tutorial: PID Control System Design
clear; clc; close all;

%% Define plant (DC motor model)
s = tf('s');
K = 1;          % Motor gain
tau = 0.5;      % Time constant
plant = K / (tau*s + 1);

%% Design PID controller
% Tuning parameters (Ziegler-Nichols method)
Kp = 2.4;       % Proportional gain
Ki = 1.2;       % Integral gain
Kd = 0.3;       % Derivative gain

pid_controller = pid(Kp, Ki, Kd);

%% Create closed-loop system
closed_loop = feedback(pid_controller * plant, 1);

%% Analyze system response
% Step response
t = 0:0.01:10;
[y, t] = step(closed_loop, t);

% Plot results
figure('Position', [100, 100, 1200, 400]);
subplot(1, 2, 1);
plot(t, y, 'b-', 'LineWidth', 2);
xlabel('Time (s)');
ylabel('Output');
title('Step Response');
grid on;

% Bode plot
subplot(1, 2, 2);
bode(closed_loop);
grid on;

%% System performance metrics
step_info = stepinfo(closed_loop);
fprintf('Control System Performance:\n');
fprintf('Rise Time: %.3f s\n', step_info.RiseTime);
fprintf('Settling Time: %.3f s\n', step_info.SettlingTime);
fprintf('Overshoot: %.1f%%\n', step_info.Overshoot);
```

## 🛠️ Part 3: CAD Design with FreeCAD

### Step 1: Install and open FreeCAD
```bash
# Install FreeCAD (if not already installed)
# Windows: Download from freecadweb.org
# macOS: brew install --cask freecad
# Ubuntu: sudo apt install freecad
```

### Step 2: Create a simple bracket
1. Open FreeCAD
2. Switch to Part Design workbench
3. Create a new document
4. Create a sketch on the XY plane
5. Draw a rectangle (50mm x 30mm)
6. Pad the sketch to 10mm thickness
7. Add mounting holes:
   - Create sketches on the faces
   - Draw circles for holes (5mm diameter)
   - Use Pocket operation to create holes
8. Save the file as `tutorial_bracket.FCStd`

### Step 3: Export for 3D printing
1. Select the final part
2. File → Export → STL
3. Save as `tutorial_bracket.stl`

## 🔬 Part 4: Finite Element Analysis

### Step 1: Prepare geometry for FEA
```python
# Create a simple FEA model using Python
import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import spsolve

# Simple 1D bar element example
def simple_fea_example():
    # Define problem
    L = 1.0  # Length (m)
    E = 200e9  # Young's modulus (Pa)
    A = 0.01  # Cross-sectional area (m²)
    F = 1000  # Applied force (N)
    
    # Discretize into elements
    n_elements = 10
    n_nodes = n_elements + 1
    element_length = L / n_elements
    
    # Element stiffness matrix
    k = E * A / element_length
    K_element = k * np.array([[1, -1], [-1, 1]])
    
    # Global stiffness matrix
    K_global = np.zeros((n_nodes, n_nodes))
    for i in range(n_elements):
        K_global[i:i+2, i:i+2] += K_element
    
    # Apply boundary conditions (fixed at left end)
    K_global[0, 0] = 1e12  # Large number for fixed boundary
    K_global[0, 1:] = 0
    K_global[1:, 0] = 0
    
    # Load vector
    F_global = np.zeros(n_nodes)
    F_global[-1] = F  # Force at right end
    
    # Solve system
    u = np.linalg.solve(K_global, F_global)
    
    # Calculate stress
    stress = E * np.diff(u) / element_length
    
    # Plot results
    x = np.linspace(0, L, n_nodes)
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1);
    plt.plot(x, u*1000, 'b-o', linewidth=2);
    plt.xlabel('Position (m)');
    plt.ylabel('Displacement (mm)');
    plt.title('Displacement');
    plt.grid(True);
    
    plt.subplot(1, 2, 2);
    x_stress = np.linspace(element_length/2, L-element_length/2, n_elements);
    plt.plot(x_stress, stress/1e6, 'r-o', linewidth=2);
    plt.xlabel('Position (m)');
    plt.ylabel('Stress (MPa)');
    plt.title('Stress');
    plt.grid(True);
    
    plt.tight_layout();
    plt.show();
    
    print(f"Maximum displacement: {u[-1]*1000:.3f} mm");
    print(f"Maximum stress: {np.max(stress)/1e6:.1f} MPa");

# Run the example
simple_fea_example();
```

## 📈 Part 5: Data Visualization

### Step 1: Create comprehensive plots
```python
# Create a dashboard-style visualization
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Create subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('ECG Signal', 'Frequency Spectrum', 'Control Response', 'Stress Distribution'),
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

# ECG signal
fig.add_trace(
    go.Scatter(x=df['time'], y=df['ecg'], name='ECG', line=dict(color='blue')),
    row=1, col=1
)

# Frequency spectrum
fig.add_trace(
    go.Scatter(x=f[:N//2], y=fft_original[:N//2], name='Spectrum', line=dict(color='red')),
    row=1, col=2
)

# Control system response (from MATLAB results)
t_control = np.linspace(0, 10, 1000)
y_control = 1 - np.exp(-2*t_control) * np.cos(3*t_control)
fig.add_trace(
    go.Scatter(x=t_control, y=y_control, name='Control Response', line=dict(color='green')),
    row=2, col=1
)

# Stress distribution (from FEA)
x_stress = np.linspace(0, 1, 20)
stress_data = 100 * (1 - x_stress)  # Linear stress distribution
fig.add_trace(
    go.Scatter(x=x_stress, y=stress_data, name='Stress', line=dict(color='orange')),
    row=2, col=2
)

# Update layout
fig.update_layout(
    title_text="Engineering Analysis Dashboard",
    showlegend=False,
    height=800
)

# Update axes labels
fig.update_xaxes(title_text="Time (s)", row=1, col=1)
fig.update_yaxes(title_text="Amplitude", row=1, col=1)
fig.update_xaxes(title_text="Frequency (Hz)", row=1, col=2)
fig.update_yaxes(title_text="Magnitude", row=1, col=2)
fig.update_xaxes(title_text="Time (s)", row=2, col=1)
fig.update_yaxes(title_text="Output", row=2, col=1)
fig.update_xaxes(title_text="Position (m)", row=2, col=2)
fig.update_yaxes(title_text="Stress (MPa)", row=2, col=2)

# Show the plot
fig.show()
```

## 🎉 Congratulations!

You've completed your first engineering project using the tech stack! You've learned to:

1. ✅ Analyze sensor data with Python
2. ✅ Design control systems with MATLAB
3. ✅ Create CAD models with FreeCAD
4. ✅ Perform finite element analysis
5. ✅ Create professional visualizations

## 🚀 Next Steps

### Beginner Projects
- Design a simple mechanical linkage
- Analyze vibration data from a motor
- Create a PID controller for temperature control
- Model heat transfer in a simple geometry

### Intermediate Projects
- Design a prosthetic hand mechanism
- Analyze blood flow in a simplified vessel
- Create a feedback control system for a robot arm
- Perform stress analysis on a loaded beam

### Advanced Projects
- Develop a complete medical device prototype
- Create a multiphysics simulation
- Design an adaptive control system
- Perform fatigue analysis on a component

## 📚 Additional Resources

- Review the sample scripts in each directory
- Explore the documentation in the `documentation/` folder
- Check out the resources in the `resources/` directory
- Join engineering communities and forums
- Take online courses in your areas of interest

Remember: Engineering is about solving real-world problems. Use these tools to tackle challenges that interest you, and don't be afraid to experiment and learn from your mistakes!

