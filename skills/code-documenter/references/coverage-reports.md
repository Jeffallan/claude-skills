# Coverage Reports

> Reference for: Code Documenter
> Load when: Generating documentation reports

## Documentation Coverage Report Template

```markdown
# Documentation Report: {project_name}

## Summary
- **Files analyzed**: 45
- **Functions documented**: 120/150 (80%)
- **Classes documented**: 25/25 (100%)
- **API endpoints documented**: 30/30 (100%)

## Coverage Before/After
- Before: 45%
- After: 92%

## Files Modified

| File | Functions Added | Notes |
|------|-----------------|-------|
| src/services/user.ts | 8 | All public methods |
| src/services/auth.ts | 5 | Added examples |
| src/controllers/users.ts | 6 | Added @Api decorators |
| src/dto/user.dto.ts | 4 | Added @ApiProperty |

## API Documentation

- **Framework**: NestJS
- **Strategy**: @nestjs/swagger decorators
- **Swagger UI**: /api/docs
- **OpenAPI spec**: /api-json

## Documentation Style

- **Python**: Google style docstrings
- **TypeScript**: JSDoc with @param, @returns
- **API**: OpenAPI 3.0 via decorators

## Next Steps

### Recommendations
1. Run `npm run docs:lint` to validate JSDoc
2. Add `eslint-plugin-jsdoc` to enforce documentation
3. Consider adding examples for complex functions
4. Set up documentation CI checks

### Missing Documentation
| File | Missing | Priority |
|------|---------|----------|
| src/utils/crypto.ts | 3 functions | High |
| src/helpers/date.ts | 2 functions | Medium |

### CI Integration
```yaml
# Add to CI pipeline
- name: Check documentation
  run: npm run docs:check

- name: Generate API docs
  run: npm run docs:generate
```
```

## Checklist During Documentation

```markdown
## Documentation Checklist

### Before Starting
- [ ] Confirmed format preference (Google/JSDoc/etc.)
- [ ] Identified files to exclude (tests, generated)
- [ ] Detected framework for API docs

### Functions/Methods
- [ ] All public functions documented
- [ ] Parameters described with types
- [ ] Return values documented
- [ ] Exceptions/errors documented
- [ ] Examples added for complex functions

### Classes
- [ ] Class purpose described
- [ ] Constructor parameters documented
- [ ] Public methods documented
- [ ] Important attributes explained

### API Endpoints
- [ ] All endpoints have summaries
- [ ] Request bodies documented
- [ ] Response schemas defined
- [ ] Error responses documented
- [ ] Authentication requirements noted

### Final Checks
- [ ] Ran documentation linter
- [ ] Verified Swagger UI renders correctly
- [ ] No inaccurate documentation
- [ ] Coverage report generated
```

## Framework-Specific Linting

```bash
# JavaScript/TypeScript - ESLint
npm install eslint-plugin-jsdoc --save-dev
# Add to .eslintrc: "plugins": ["jsdoc"]

# Python - pydocstyle
pip install pydocstyle
pydocstyle --convention=google src/

# Python - interrogate (coverage)
pip install interrogate
interrogate -v src/
```

## Quick Reference

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Function coverage | >90% | 70-90% | <70% |
| Class coverage | 100% | >90% | <90% |
| API endpoint coverage | 100% | 100% | <100% |
| Example coverage | >50% | 30-50% | <30% |
