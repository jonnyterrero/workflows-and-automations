# Contributing Guidelines

## Welcome Contributors! 🎉

Thank you for your interest in contributing to this project. This document provides guidelines and information for contributors.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- Be respectful and constructive in all interactions
- Use welcoming and inclusive language
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment, trolling, or personal attacks
- Discriminatory language or behavior
- Spam or off-topic discussions
- Publishing private information without permission

## Getting Started

### Prerequisites
- Node.js 18+
- npm/pnpm
- Git
- Code editor (VS Code recommended)

### Setup Development Environment
```bash
# Fork and clone the repository
git clone https://github.com/your-username/project-name.git
cd project-name

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Run the development server
npm run dev
```

### Project Structure
```
src/
├── app/                 # Next.js App Router
├── components/          # Reusable components
│   └── ui/             # shadcn/ui components
├── lib/                # Utilities and configurations
├── hooks/              # Custom React hooks
├── types/              # TypeScript definitions
└── tests/              # Test files
```

## Development Workflow

### Branch Naming Convention
Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks

Examples:
- `feature/user-authentication`
- `fix/login-validation-error`
- `docs/api-documentation-update`

### Development Process
1. **Create a new branch** from `main`
2. **Make your changes** following coding standards
3. **Write tests** for new functionality
4. **Update documentation** if needed
5. **Run tests and linting** before committing
6. **Create a pull request** with a clear description

## Coding Standards

### TypeScript
- Use strict mode
- Define interfaces for all data structures
- Use type guards for runtime type checking
- Prefer `interface` over `type` for object shapes
- Use meaningful variable and function names

```typescript
// Good
interface User {
  id: string;
  email: string;
  name: string;
}

const getUserById = async (id: string): Promise<User | null> => {
  // Implementation
};

// Avoid
const u = async (i: string) => {
  // Implementation
};
```

### React Components
- Use functional components with hooks
- Implement proper error boundaries
- Use React.memo for performance optimization
- Follow the single responsibility principle
- Use proper prop types and default values

```typescript
// Good
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  onClick,
  disabled = false
}) => {
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
```

### CSS/Styling
- Use Tailwind CSS utility classes
- Create custom components with shadcn/ui
- Follow mobile-first responsive design
- Use CSS variables for theming
- Avoid inline styles

```typescript
// Good
<div className="flex flex-col md:flex-row gap-4 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
    Title
  </h2>
</div>

// Avoid
<div style={{ display: 'flex', padding: '24px', backgroundColor: 'white' }}>
  <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Title</h2>
</div>
```

### File Organization
- Use barrel exports for clean imports
- Group related files in folders
- Use descriptive file names
- Keep components small and focused

```
components/
├── ui/                 # shadcn/ui components
├── forms/              # Form components
│   ├── index.ts       # Barrel export
│   ├── LoginForm.tsx
│   └── RegisterForm.tsx
└── layout/            # Layout components
    ├── index.ts
    ├── Header.tsx
    └── Footer.tsx
```

## Commit Guidelines

### Commit Message Format
Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```bash
feat(auth): add user registration functionality

fix(api): resolve validation error in user endpoint

docs(readme): update installation instructions

refactor(components): extract common button logic

test(utils): add tests for date formatting functions
```

### Commit Best Practices
- Make atomic commits (one logical change per commit)
- Write clear, descriptive commit messages
- Use present tense ("add feature" not "added feature")
- Keep the first line under 50 characters
- Reference issues when applicable

## Pull Request Process

### Before Submitting
- [ ] Code follows the project's coding standards
- [ ] Tests pass locally
- [ ] No linting errors
- [ ] Documentation is updated
- [ ] Commit messages follow the guidelines

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No console.log statements left
- [ ] No commented-out code

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Related Issues
Closes #123
```

### Review Process
1. **Automated checks** must pass (tests, linting, type checking)
2. **Code review** by at least one maintainer
3. **Approval** required before merging
4. **Squash and merge** for clean commit history

## Issue Guidelines

### Bug Reports
Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Windows 10]
- Browser: [e.g. Chrome 91]
- Version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

### Feature Requests
Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## Testing

### Writing Tests
- Write tests for all new functionality
- Aim for good test coverage
- Use descriptive test names
- Test both happy path and edge cases

```typescript
// Good test example
describe('UserService', () => {
  describe('getUserById', () => {
    it('should return user when valid ID is provided', async () => {
      const user = await userService.getUserById('valid-id');
      expect(user).toBeDefined();
      expect(user.id).toBe('valid-id');
    });

    it('should return null when user does not exist', async () => {
      const user = await userService.getUserById('non-existent-id');
      expect(user).toBeNull();
    });

    it('should throw error when invalid ID format is provided', async () => {
      await expect(userService.getUserById('invalid-format'))
        .rejects
        .toThrow('Invalid user ID format');
    });
  });
});
```

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- UserService.test.ts
```

## Documentation

### Code Documentation
- Write JSDoc comments for public APIs
- Use meaningful variable and function names
- Add inline comments for complex logic
- Keep README files up to date

```typescript
/**
 * Calculates the total price including tax and discounts
 * @param basePrice - The base price of the item
 * @param taxRate - The tax rate as a decimal (e.g., 0.08 for 8%)
 * @param discount - The discount amount to apply
 * @returns The final price after tax and discount
 */
const calculateTotalPrice = (
  basePrice: number,
  taxRate: number,
  discount: number = 0
): number => {
  const priceAfterDiscount = basePrice - discount;
  const taxAmount = priceAfterDiscount * taxRate;
  return priceAfterDiscount + taxAmount;
};
```

### README Updates
- Update installation instructions
- Add new features to the features list
- Update API documentation
- Include examples and usage

## Getting Help

### Resources
- [Project Documentation](./README.md)
- [API Documentation](./README-API.md)
- [Deployment Guide](./README-DEPLOYMENT.md)

### Communication Channels
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and general discussion
- Pull Request comments for code-related discussions

### Response Times
- Bug reports: Within 48 hours
- Feature requests: Within 1 week
- Pull requests: Within 3-5 business days
- General questions: Within 1 week

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to this project! 🚀
