# Global Coding Style

## Languages
- **Primary**: TypeScript (Node/Next.js), Python (scripts/ML), MATLAB (school/engineering), Markdown (docs)
- **Prefer strongly typed TS with strict mode**
- **Use**: `eslint:recommended`, `@typescript-eslint/recommended`

## Formatting
- **Prettier defaults** (printWidth 100)
- **Filenames**: 
  - kebab-case for TS/JS
  - snake_case for Python
  - UpperCamelCase.m for MATLAB

## Commits (Conventional)
- **Types**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `perf:`
- **Example**: `feat(assistant): add calendar summarizer`

## Comments
- **TS/JS**: JSDoc for exported funcs
- **Python**: docstrings (NumPy style)
- **MATLAB**: header block with purpose, inputs, outputs

## Error Handling
- **Never swallow errors**
- **Wrap API calls** with `try/catch` and return structured failures `{ ok: false, error }`
- **Log concise context**; redact secrets/PII

## Security
- **Never hardcode keys**. Load via env/Secrets
- **Strip PII** from logs and artifacts

## TypeScript/JavaScript Style Guidelines

### General Principles
- Use TypeScript for all new code
- Prefer explicit types over `any`
- Use meaningful variable and function names
- Follow camelCase for variables and functions
- Use PascalCase for classes and interfaces
- Use UPPER_SNAKE_CASE for constants

### Code Formatting
- Use 2 spaces for indentation
- Use semicolons consistently
- Use single quotes for strings
- Use trailing commas in objects and arrays
- Use const/let instead of var
- Prefer arrow functions for callbacks

### Type Definitions
```typescript
// Good
interface UserData {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// Avoid
const user: any = { ... };
```

### Function Guidelines
- Keep functions small and focused
- Use descriptive parameter names
- Prefer pure functions when possible
- Use async/await over promises
- Handle errors explicitly

### File Organization
- One main export per file
- Use named exports over default exports
- Group imports: external libraries, internal modules, relative imports
- Keep files under 200 lines when possible

### Documentation
- Use JSDoc for public APIs
- Include examples for complex functions
- Document async operations and error conditions
- Keep comments up-to-date with code changes

## AI Research Specific Guidelines

### Research Code
- Make research scripts reproducible
- Include clear logging and progress indicators
- Use configuration files for parameters
- Version control all research data
- Document methodology and assumptions

### Data Handling
- Use consistent data structures
- Validate input data
- Handle missing data gracefully
- Use appropriate data types for research metrics
- Include data provenance information

### Error Handling
- Use try-catch blocks for async operations
- Log errors with context
- Provide meaningful error messages
- Implement retry logic for network operations
- Gracefully handle API rate limits

## Python Guidelines

### Code Style
- Follow PEP 8 conventions
- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_SNAKE_CASE for constants

### Documentation
```python
def process_data(input_data: List[str]) -> Dict[str, Any]:
    """
    Process input data and return structured results.
    
    Parameters
    ----------
    input_data : List[str]
        List of input strings to process
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing processed results
        
    Examples
    --------
    >>> data = ["item1", "item2"]
    >>> result = process_data(data)
    >>> print(result["count"])
    2
    """
    # Implementation here
    pass
```

## MATLAB Guidelines

### File Structure
```matlab
function [output1, output2] = FunctionName(input1, input2)
% FUNCTIONNAME Brief description of what the function does
%
% Purpose: Detailed description of the function's purpose
% Inputs:  input1 - description of first input
%          input2 - description of second input
% Outputs: output1 - description of first output
%          output2 - description of second output
%
% Author: Your Name
% Date: YYYY-MM-DD
%
% Example:
%   [result1, result2] = FunctionName(data1, data2);

    % Implementation here
    
end
```

## Security Best Practices

### Environment Variables
```typescript
// Good
const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error('API_KEY environment variable is required');
}

// Bad
const apiKey = 'hardcoded-key-here';
```

### Error Handling with Structured Responses
```typescript
interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
}

async function apiCall(): Promise<ApiResponse<Data>> {
  try {
    const response = await fetch('/api/endpoint');
    const data = await response.json();
    return { ok: true, data };
  } catch (error) {
    console.error('API call failed:', error);
    return { ok: false, error: 'Failed to fetch data' };
  }
}
```

### Logging Best Practices
```typescript
// Good - redact sensitive information
console.log('User login attempt:', { userId: user.id, timestamp: new Date() });

// Bad - exposes sensitive data
console.log('User login:', { email: user.email, password: user.password });
```
