# Data & Secrets

- **Never commit tokens/PII**. Use `.env` + `.env.example`
- **Redact names beyond first name** in docs; for school files, anonymize dataset IDs
- For **health/symptom projects**, store only aggregates or pseudonyms
- Add **`.gitattributes`** to auto-LFS large binaries if needed (≥50MB)

## Notebooks

- **Python notebooks**: place under `school/<course>/notebooks/`
- Include a **deterministic** `requirements.txt` or `environment.yml`
- **MATLAB**: provide `.m` scripts and `Live Scripts (.mlx)` export to PDF under `docs/school/...`
- Always add a **"Reproduce" cell** with:
  - seed setting
  - data path assumptions
  - CLI equivalent (prefer scripts/)

## Data Protection Implementation

### Environment Variables Management
```typescript
// assistant/guardrails/data-protection.ts
export class DataProtectionGuard {
  static checkForSecrets(code: string): {
    hasSecrets: boolean;
    secretTypes: string[];
    recommendations: string[];
  } {
    const secretPatterns = [
      /(?:password|pwd|pass)\s*[:=]\s*['"][^'"]+['"]/gi,
      /(?:token|key|secret)\s*[:=]\s*['"][^'"]+['"]/gi,
      /(?:api_key|apikey)\s*[:=]\s*['"][^'"]+['"]/gi,
      /(?:private_key|privatekey)\s*[:=]\s*['"][^'"]+['"]/gi,
      /(?:secret_key|secretkey)\s*[:=]\s*['"][^'"]+['"]/gi
    ];
    
    const foundSecrets: string[] = [];
    secretPatterns.forEach(pattern => {
      const matches = code.match(pattern);
      if (matches) {
        foundSecrets.push(...matches);
      }
    });
    
    const recommendations = foundSecrets.length > 0 ? [
      'Move secrets to environment variables',
      'Add .env to .gitignore',
      'Create .env.example template',
      'Use process.env.VARIABLE_NAME instead of hardcoded values'
    ] : [];
    
    return {
      hasSecrets: foundSecrets.length > 0,
      secretTypes: foundSecrets,
      recommendations
    };
  }
  
  static generateEnvExample(secrets: string[]): string {
    const envVars = secrets.map(secret => {
      const match = secret.match(/(\w+)\s*[:=]/);
      return match ? match[1].toUpperCase() : 'SECRET_VAR';
    });
    
    return `# Environment Variables
# Copy this file to .env and fill in your values

${envVars.map(varName => `# ${varName} - [Description]
${varName}=your_${varName.toLowerCase()}_here
`).join('\n')}

# Never commit .env files to version control
`;
  }
}
```

### PII Redaction
```typescript
// assistant/formatters/pii-redactor.ts
export class PIIRedactor {
  static redactNames(text: string): string {
    // Redact names beyond first name
    return text
      .replace(/\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b/g, (match) => {
        const parts = match.split(' ');
        return `${parts[0]} [REDACTED]`;
      })
      .replace(/\b[A-Z][a-z]+ [A-Z][a-z]+\b/g, (match) => {
        const parts = match.split(' ');
        return `${parts[0]} [REDACTED]`;
      });
  }
  
  static anonymizeDatasetIDs(text: string): string {
    // Anonymize dataset IDs
    return text
      .replace(/dataset[_-]?id[:\s]*[a-zA-Z0-9_-]+/gi, 'dataset_id: [ANONYMIZED]')
      .replace(/patient[_-]?id[:\s]*[a-zA-Z0-9_-]+/gi, 'patient_id: [ANONYMIZED]')
      .replace(/subject[_-]?id[:\s]*[a-zA-Z0-9_-]+/gi, 'subject_id: [ANONYMIZED]');
  }
  
  static redactHealthData(text: string): string {
    // Redact health/symptom data
    return text
      .replace(/symptom[:\s]*[^.\n]+/gi, 'symptom: [REDACTED]')
      .replace(/diagnosis[:\s]*[^.\n]+/gi, 'diagnosis: [REDACTED]')
      .replace(/medical[_-]?history[:\s]*[^.\n]+/gi, 'medical_history: [REDACTED]');
  }
  
  static redactAll(text: string): string {
    return this.redactNames(
      this.anonymizeDatasetIDs(
        this.redactHealthData(text)
      )
    );
  }
}
```

### .gitattributes for Large Files
```gitattributes
# .gitattributes
# Auto-LFS for large binaries (≥50MB)
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text
*.wmv filter=lfs diff=lfs merge=lfs -text
*.flv filter=lfs diff=lfs merge=lfs -text

# Large data files
*.h5 filter=lfs diff=lfs merge=lfs -text
*.hdf5 filter=lfs diff=lfs merge=lfs -text
*.nc filter=lfs diff=lfs merge=lfs -text
*.mat filter=lfs diff=lfs merge=lfs -text

# Large model files
*.pkl filter=lfs diff=lfs merge=lfs -text
*.joblib filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text

# Large images
*.tiff filter=lfs diff=lfs merge=lfs -text
*.tif filter=lfs diff=lfs merge=lfs -text
*.bmp filter=lfs diff=lfs merge=lfs -text

# Large documents
*.pdf filter=lfs diff=lfs merge=lfs -text
*.docx filter=lfs diff=lfs merge=lfs -text
*.pptx filter=lfs diff=lfs merge=lfs -text
```

## Notebook Management

### Python Notebook Structure
```
school/
├── CS101/
│   ├── notebooks/
│   │   ├── assignment-1/
│   │   │   ├── analysis.ipynb
│   │   │   ├── requirements.txt
│   │   │   └── README.md
│   │   └── assignment-2/
│   │       ├── data-analysis.ipynb
│   │       ├── requirements.txt
│   │       └── README.md
│   └── scripts/
│       ├── data-processing.py
│       └── analysis.py
```

### Deterministic Requirements
```txt
# requirements.txt
# Deterministic versions for reproducibility
numpy==1.24.3
pandas==2.0.3
matplotlib==3.7.2
seaborn==0.12.2
scikit-learn==1.3.0
jupyter==1.0.0
ipykernel==6.25.0
```

### Environment.yml for Conda
```yaml
# environment.yml
name: cs101-assignment1
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - numpy=1.24.3
  - pandas=2.0.3
  - matplotlib=3.7.2
  - seaborn=0.12.2
  - scikit-learn=1.3.0
  - jupyter=1.0.0
  - pip
  - pip:
    - ipykernel==6.25.0
```

### Reproduce Cell Template
```python
# Reproduce Cell - Always include this in notebooks
import os
import numpy as np
import random

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)
os.environ['PYTHONHASHSEED'] = '0'

# Data path assumptions
DATA_PATH = '../data/'  # Adjust as needed
OUTPUT_PATH = '../results/'

# CLI equivalent
# python scripts/data-processing.py --input ../data/raw --output ../results/processed

# Verify environment
print(f"Python version: {sys.version}")
print(f"NumPy version: {np.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"Data path exists: {os.path.exists(DATA_PATH)}")
```

### MATLAB Script Structure
```
school/
├── MAP2302/
│   ├── assignment-1/
│   │   ├── solution.m
│   │   ├── helper_functions.m
│   │   ├── test_calculations.m
│   │   ├── analysis.mlx
│   │   └── README.md
│   └── assignment-2/
│       ├── ode_solver.m
│       ├── visualization.m
│       ├── report.mlx
│       └── README.md
└── docs/
    └── school/
        ├── MAP2302/
        │   ├── assignment-1/
        │   │   └── analysis.pdf
        │   └── assignment-2/
        │       └── report.pdf
```

### MATLAB Reproduce Section
```matlab
% Reproduce Section - Always include this in MATLAB scripts
% Set random seed for reproducibility
rng(42);

% Data path assumptions
data_path = '../data/';
output_path = '../results/';

% CLI equivalent
% matlab -batch "run('solution.m')"

% Verify environment
fprintf('MATLAB version: %s\n', version);
fprintf('Data path exists: %d\n', exist(data_path, 'dir'));
fprintf('Output path exists: %d\n', exist(output_path, 'dir'));
```

### Live Script Export to PDF
```matlab
% Export Live Script to PDF
% Include this in your .mlx files
function exportToPDF(mlx_file, output_dir)
    % Export Live Script to PDF
    export(mlx_file, 'pdf', 'OutputFolder', output_dir);
    
    % Move to docs/school structure
    [~, name, ~] = fileparts(mlx_file);
    source_pdf = fullfile(output_dir, [name '.pdf']);
    dest_pdf = fullfile('docs/school/MAP2302/assignment-1/', [name '.pdf']);
    
    if exist(source_pdf, 'file')
        copyfile(source_pdf, dest_pdf);
        fprintf('PDF exported to: %s\n', dest_pdf);
    end
end
```

## Data Protection Scripts

### Pre-commit Hook for Secrets
```bash
#!/bin/bash
# .git/hooks/pre-commit
# Check for secrets before committing

echo "Checking for secrets..."

# Check for hardcoded secrets
if grep -r -E "(password|token|key|secret)\s*[:=]\s*['\"][^'\"]+['\"]" --exclude-dir=.git .; then
    echo "❌ Found potential secrets in code!"
    echo "Please move secrets to environment variables."
    exit 1
fi

# Check for PII
if grep -r -E "\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b" --exclude-dir=.git .; then
    echo "⚠️  Found potential PII in code!"
    echo "Please redact names beyond first name."
fi

echo "✅ No secrets found. Proceeding with commit."
exit 0
```

### Data Anonymization Script
```python
# scripts/anonymize-data.py
import pandas as pd
import numpy as np
import hashlib
import re

def anonymize_dataset(df, id_columns=None):
    """Anonymize dataset by hashing IDs and redacting PII"""
    if id_columns is None:
        id_columns = [col for col in df.columns if 'id' in col.lower()]
    
    # Anonymize ID columns
    for col in id_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(
                lambda x: hashlib.md5(x.encode()).hexdigest()[:8]
            )
    
    # Redact names (keep first name only)
    name_columns = [col for col in df.columns if 'name' in col.lower()]
    for col in name_columns:
        if col in df.columns:
            df[col] = df[col].apply(redact_name)
    
    return df

def redact_name(name):
    """Redact name keeping only first name"""
    if pd.isna(name):
        return name
    
    parts = str(name).split()
    if len(parts) > 1:
        return f"{parts[0]} [REDACTED]"
    return name

def redact_health_data(df):
    """Redact health-related data"""
    health_columns = [col for col in df.columns if any(
        keyword in col.lower() for keyword in 
        ['symptom', 'diagnosis', 'medical', 'health']
    )]
    
    for col in health_columns:
        df[col] = '[REDACTED]'
    
    return df

if __name__ == "__main__":
    # Example usage
    df = pd.read_csv('data/raw/health_data.csv')
    df_anonymized = anonymize_dataset(df)
    df_anonymized = redact_health_data(df_anonymized)
    df_anonymized.to_csv('data/processed/anonymized_data.csv', index=False)
    print("Data anonymized and saved.")
```

## Documentation Templates

### School Project README
```markdown
# <Course>: <Assignment Title>

## Problem Statement
[Clear description of the problem]

## Approach
[Methodology and approach used]

## Reproducibility
### Environment Setup
```bash
# Python
pip install -r requirements.txt

# MATLAB
# Ensure MATLAB R2023a or later
```

### Data Requirements
- [ ] Data file 1: [Description]
- [ ] Data file 2: [Description]
- [ ] Data file 3: [Description]

### Running the Code
```bash
# Python
python scripts/data-processing.py
jupyter notebook analysis.ipynb

# MATLAB
matlab -batch "run('solution.m')"
```

## Results
[Findings and outcomes]

## References
[Academic references and sources]

## Ethics Statement
[If applicable: ethical considerations, data protection measures]

---
*Course: [Course Code] | Assignment: [Assignment Name] | Due: [Date]*
```

### Data Protection Checklist
```markdown
# Data Protection Checklist

## Before Committing
- [ ] No hardcoded API keys or tokens
- [ ] No PII beyond first names
- [ ] Dataset IDs anonymized
- [ ] Health data redacted or aggregated
- [ ] Large files (>50MB) using LFS
- [ ] .env.example created
- [ ] .gitignore updated

## For Health Projects
- [ ] Only aggregate data stored
- [ ] Individual records pseudonymized
- [ ] No direct identifiers
- [ ] Ethics approval documented
- [ ] Data retention policy defined

## For School Projects
- [ ] Student names redacted
- [ ] Dataset IDs anonymized
- [ ] No personal information in code
- [ ] Results anonymized
- [ ] References properly cited
```
