# Testing Rules

## TypeScript
- **Framework**: Vitest or Jest (choose what repo uses)
- **Pattern**: `file.spec.ts` alongside source
- **Generate tests for**:
  - API wrappers (Perplexity/OpenAI/GitHub)
  - Date/time utilities (scheduling)
  - Parsing and serialization (issue templates)
- **Mock external calls**; assert minimal surface (status, mapping)

## Python
- Use **pytest**. Structure `tests/` mirroring `src/`
- **Fixtures** for sample API payloads and edge cases

## MATLAB
- Use **`runtests`** with local function tests for calculations (ODEs, statics)

## Coverage
- Target **≥85%** for pure functions
- **Critical paths only** for external I/O

## TypeScript Testing Examples

### API Wrapper Tests
```typescript
// api-client.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PerplexityClient } from './api-client';

describe('PerplexityClient', () => {
  let client: PerplexityClient;
  
  beforeEach(() => {
    client = new PerplexityClient('test-key');
  });

  it('should make research request with correct parameters', async () => {
    const mockResponse = {
      choices: [{ message: { content: 'Research result' } }]
    };
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    });

    const result = await client.research('AI safety');
    
    expect(fetch).toHaveBeenCalledWith(
      'https://api.perplexity.ai/chat/completions',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-key'
        })
      })
    );
    
    expect(result).toBe('Research result');
  });

  it('should handle API errors gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      statusText: 'Rate Limited'
    });

    await expect(client.research('topic')).rejects.toThrow('Rate Limited');
  });
});
```

### Date/Time Utility Tests
```typescript
// date-utils.spec.ts
import { describe, it, expect, vi } from 'vitest';
import { formatScheduleDate, parseCronExpression } from './date-utils';

describe('Date Utils', () => {
  it('should format schedule date correctly', () => {
    const date = new Date('2024-01-15T09:00:00Z');
    const formatted = formatScheduleDate(date);
    expect(formatted).toBe('2024-01-15T09:00:00Z');
  });

  it('should parse cron expression', () => {
    const cron = '0 9 * * 1'; // Every Monday at 9 AM
    const parsed = parseCronExpression(cron);
    expect(parsed.minute).toBe(0);
    expect(parsed.hour).toBe(9);
    expect(parsed.dayOfWeek).toBe(1);
  });

  it('should handle invalid cron expressions', () => {
    expect(() => parseCronExpression('invalid')).toThrow('Invalid cron expression');
  });
});
```

### Parsing and Serialization Tests
```typescript
// issue-parser.spec.ts
import { describe, it, expect } from 'vitest';
import { parseIssueTemplate, serializeIssue } from './issue-parser';

describe('Issue Parser', () => {
  it('should parse issue template correctly', () => {
    const template = `---
labels: type:schedule, course:MAP2302
dueDate: 2024-01-15T23:59:59Z
---

# Task Description
Complete the assignment`;

    const parsed = parseIssueTemplate(template);
    
    expect(parsed.labels).toEqual(['type:schedule', 'course:MAP2302']);
    expect(parsed.dueDate).toBe('2024-01-15T23:59:59Z');
    expect(parsed.description).toBe('Complete the assignment');
  });

  it('should serialize issue to GitHub format', () => {
    const issue = {
      title: 'Test Issue',
      body: 'Test Description',
      labels: ['bug', 'high-priority']
    };

    const serialized = serializeIssue(issue);
    expect(serialized.title).toBe('Test Issue');
    expect(serialized.body).toBe('Test Description');
    expect(serialized.labels).toEqual(['bug', 'high-priority']);
  });
});
```

## Python Testing Examples

### Project Structure
```
src/
├── research/
│   ├── __init__.py
│   ├── api_client.py
│   └── data_processor.py
tests/
├── __init__.py
├── conftest.py
├── test_api_client.py
└── test_data_processor.py
```

### Fixtures for API Payloads
```python
# conftest.py
import pytest
from typing import Dict, Any

@pytest.fixture
def sample_perplexity_response() -> Dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "content": "Research findings about AI safety"
                }
            }
        ]
    }

@pytest.fixture
def sample_openai_response() -> Dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "content": "Synthesis of research findings"
                }
            }
        ]
    }

@pytest.fixture
def edge_case_payloads():
    return {
        "empty_response": {"choices": []},
        "malformed_response": {"invalid": "structure"},
        "rate_limited": {"error": {"message": "Rate limit exceeded"}}
    }
```

### API Client Tests
```python
# test_api_client.py
import pytest
from unittest.mock import Mock, patch
from src.research.api_client import PerplexityClient

class TestPerplexityClient:
    def test_research_request_success(self, sample_perplexity_response):
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = sample_perplexity_response
            mock_response.ok = True
            mock_post.return_value = mock_response
            
            client = PerplexityClient("test-key")
            result = client.research("AI safety")
            
            assert result == "Research findings about AI safety"
            mock_post.assert_called_once()
    
    def test_research_request_failure(self, edge_case_payloads):
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = edge_case_payloads["rate_limited"]
            mock_response.ok = False
            mock_post.return_value = mock_response
            
            client = PerplexityClient("test-key")
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                client.research("AI safety")
```

## MATLAB Testing Examples

### Local Function Tests
```matlab
% test_calculations.m
function tests = test_calculations
    tests = functiontests(localfunctions);
end

function test_ode_solver(testCase)
    % Test ODE solver with known solution
    tspan = [0 1];
    y0 = 1;
    [t, y] = ode45(@(t,y) -y, tspan, y0);
    
    % Verify solution approaches zero
    verifyLessThan(testCase, abs(y(end)), 0.1);
end

function test_static_analysis(testCase)
    % Test static analysis calculations
    forces = [100, 200, 150]; % N
    distances = [1, 2, 1.5]; % m
    
    moments = forces .* distances;
    total_moment = sum(moments);
    
    verifyEqual(testCase, total_moment, 550, 'AbsTol', 0.01);
end

function test_matrix_operations(testCase)
    % Test matrix operations
    A = [1 2; 3 4];
    B = [2 0; 0 2];
    
    C = A * B;
    expected = [2 4; 6 8];
    
    verifyEqual(testCase, C, expected);
end
```

## Coverage Guidelines

### TypeScript Coverage Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        global: {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85
        }
      },
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.spec.ts',
        '**/*.test.ts'
      ]
    }
  }
});
```

### Python Coverage Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### Critical Path Testing
```typescript
// Focus on critical paths for external I/O
describe('Critical Paths', () => {
  it('should handle API rate limiting', async () => {
    // Test rate limiting behavior
    const client = new ApiClient();
    
    // Simulate rate limit response
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 429,
      statusText: 'Too Many Requests'
    });
    
    const result = await client.makeRequest();
    expect(result.ok).toBe(false);
    expect(result.error).toContain('Rate limited');
  });

  it('should retry on network failures', async () => {
    const client = new ApiClient({ maxRetries: 3 });
    
    // Simulate network failure then success
    vi.mocked(fetch)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) });
    
    const result = await client.makeRequest();
    expect(result.ok).toBe(true);
  });
});
```

## Test Commands

### TypeScript
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- research.spec.ts

# Watch mode
npm run test:watch
```

### Python
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_api_client.py

# Verbose output
pytest -v
```

### MATLAB
```bash
# Run tests
runtests

# Run specific test file
runtests('test_calculations')

# Run with coverage
runtests('test_calculations', 'Coverage', true)
```
