---
name: Code Documenter
description: Add comprehensive inline documentation to code including docstrings, comments, and API documentation (OpenAPI/Swagger). Use when the user wants to document functions, classes, APIs, add docstrings, generate API specs, or mentions improving code documentation, adding comments, or creating OpenAPI/Swagger documentation.
---

# Code Documenter

A specialized skill for adding comprehensive inline documentation to code across multiple programming languages and frameworks. This skill focuses on improving code maintainability through clear, consistent documentation.

## Instructions

### Core Workflow

1. **Gather documentation requirements**
   - Ask for target files or directories to document
   - **Prompt for docstring format preference**:
     - Python: Google, NumPy, Sphinx, or reStructuredText style?
     - JavaScript/TypeScript: JSDoc format?
     - Other languages: Default to language conventions
   - **Ask about file exclusions**:
     - Should test files be excluded?
     - Should generated code be excluded?
     - Should vendor/third-party code be excluded?
     - Are there specific paths or patterns to exclude?
   - **Ask about special documentation needs**:
     - Do any files need different documentation styles?
     - Are there specific modules that need more detailed docs?
     - Should examples be included for complex functions?

2. **Identify project type and framework**
   - Detect programming language(s)
   - Identify web framework (if API documentation needed)
   - Determine appropriate documentation strategy

3. **Analyze existing documentation**
   - Use Grep to find undocumented functions/classes
   - Assess current documentation quality
   - Identify inconsistencies in style

4. **Document code systematically**
   - Start with public APIs and exported functions
   - Document classes and their methods
   - Document complex private functions
   - Add module-level documentation
   - Follow user's preferred style consistently

5. **Generate API documentation (if applicable)**
   - Apply framework-specific API documentation strategy
   - See API Documentation Strategy section below

6. **Verify and validate**
   - Ensure all public APIs are documented
   - Verify documentation accuracy
   - Check for consistency in style
   - Run documentation linters if available

7. **Generate documentation report**
   - Create summary of changes
   - Report coverage metrics (before/after)
   - List files modified
   - Provide recommendations for ongoing documentation practices

### API Documentation Strategy

Different frameworks have different approaches to API documentation. Apply the appropriate strategy based on the detected framework:

#### Django / Django REST Framework
**Strategy**: Leverage built-in schema generation
- Django REST Framework auto-generates OpenAPI schemas
- Add docstrings to viewsets and serializers
- Use `schema` parameter in `@api_view` decorator for additional details
- Install `drf-spectacular` for enhanced automatic documentation
- **Minimal manual OpenAPI work needed** - focus on clear docstrings

Example:
```python
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.

    list: Return a list of all users.
    create: Create a new user.
    retrieve: Return a specific user by ID.
    update: Update an existing user.
    destroy: Delete a user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

#### FastAPI
**Strategy**: Leverage automatic Swagger generation from type hints
- FastAPI auto-generates OpenAPI/Swagger docs from Python type hints
- Use Pydantic models for request/response schemas
- Add docstrings to path operations for descriptions
- Use `response_model` parameter for response documentation
- Use `status_code` and `responses` parameters for detailed responses
- **Type hints are the primary documentation mechanism**

Example:
```python
@app.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate) -> UserResponse:
    """
    Create a new user.

    Args:
        user: User data including name, email, and password

    Returns:
        UserResponse: Created user with generated ID

    Raises:
        HTTPException: 400 if email already exists
    """
    # Implementation
```

#### NestJS (TypeScript)
**Strategy**: Add OpenAPI decorators to controllers and DTOs
- Install `@nestjs/swagger` package
- Use `@ApiTags()`, `@ApiOperation()`, `@ApiResponse()` on controllers
- Use `@ApiProperty()` on DTO classes
- Use `@ApiParam()`, `@ApiQuery()`, `@ApiBody()` for parameters
- **Requires manual OpenAPI decorators**

Example:
```typescript
@ApiTags('users')
@Controller('users')
export class UsersController {
  @Post()
  @ApiOperation({ summary: 'Create a new user' })
  @ApiResponse({ status: 201, description: 'User created successfully', type: UserDto })
  @ApiResponse({ status: 400, description: 'Invalid input data' })
  @ApiBody({ type: CreateUserDto })
  async create(@Body() createUserDto: CreateUserDto): Promise<UserDto> {
    // Implementation
  }
}

export class CreateUserDto {
  @ApiProperty({ description: 'User email address', example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ description: 'User full name', example: 'John Doe' })
  @IsString()
  name: string;
}
```

#### Go (Gin, Echo, Chi, Gorilla Mux)
**Strategy**: Use swag annotations or manual OpenAPI spec
- Option 1: Use `swaggo/swag` for annotation-based documentation
- Option 2: Write OpenAPI spec manually in YAML/JSON
- **Requires manual documentation** - Go doesn't auto-generate from types

With swag annotations:
```go
// CreateUser godoc
// @Summary Create a new user
// @Description Create a new user with the provided information
// @Tags users
// @Accept json
// @Produce json
// @Param user body CreateUserRequest true "User data"
// @Success 201 {object} UserResponse
// @Failure 400 {object} ErrorResponse
// @Router /users [post]
func (h *UserHandler) CreateUser(c *gin.Context) {
    // Implementation
}
```

#### Express.js (Node.js)
**Strategy**: Use swagger-jsdoc with JSDoc comments
- Install `swagger-jsdoc` and `swagger-ui-express`
- Add JSDoc comments with OpenAPI schema
- **Requires manual JSDoc OpenAPI annotations**

Example:
```javascript
/**
 * @swagger
 * /users:
 *   post:
 *     summary: Create a new user
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - name
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               name:
 *                 type: string
 *     responses:
 *       201:
 *         description: User created successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       400:
 *         description: Invalid input
 */
router.post('/users', createUser);
```

#### ASP.NET Core (C#)
**Strategy**: Use XML comments with Swashbuckle
- Add XML documentation comments
- Configure Swashbuckle to include XML comments
- Use attributes like `[ProducesResponseType]` for responses

Example:
```csharp
/// <summary>
/// Creates a new user
/// </summary>
/// <param name="request">User creation request</param>
/// <returns>Created user</returns>
/// <response code="201">User created successfully</response>
/// <response code="400">Invalid input data</response>
[HttpPost]
[ProducesResponseType(typeof(UserResponse), StatusCodes.Status201Created)]
[ProducesResponseType(StatusCodes.Status400BadRequest)]
public async Task<IActionResult> CreateUser([FromBody] CreateUserRequest request)
{
    // Implementation
}
```

### Language-Specific Documentation Formats

#### Python
**Google Style** (default recommendation):
```python
def calculate_total(items: list[Item], tax_rate: float = 0.0) -> float:
    """Calculate the total cost including tax.

    Args:
        items: List of items to calculate total for
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%). Defaults to 0.0

    Returns:
        Total cost including tax

    Raises:
        ValueError: If tax_rate is negative or items list is empty

    Example:
        >>> items = [Item(price=10.0), Item(price=20.0)]
        >>> calculate_total(items, tax_rate=0.08)
        32.4
    """
```

**NumPy Style**:
```python
def calculate_total(items, tax_rate=0.0):
    """
    Calculate the total cost including tax.

    Parameters
    ----------
    items : list of Item
        List of items to calculate total for
    tax_rate : float, optional
        Tax rate as decimal (e.g., 0.08 for 8%), by default 0.0

    Returns
    -------
    float
        Total cost including tax

    Raises
    ------
    ValueError
        If tax_rate is negative or items list is empty
    """
```

**Sphinx Style**:
```python
def calculate_total(items, tax_rate=0.0):
    """
    Calculate the total cost including tax.

    :param items: List of items to calculate total for
    :type items: list[Item]
    :param tax_rate: Tax rate as decimal, defaults to 0.0
    :type tax_rate: float, optional
    :return: Total cost including tax
    :rtype: float
    :raises ValueError: If tax_rate is negative or items list is empty
    """
```

#### JavaScript/TypeScript (JSDoc)
```javascript
/**
 * Calculate the total cost including tax
 *
 * @param {Item[]} items - List of items to calculate total for
 * @param {number} [taxRate=0.0] - Tax rate as decimal (e.g., 0.08 for 8%)
 * @returns {number} Total cost including tax
 * @throws {Error} If tax_rate is negative or items array is empty
 *
 * @example
 * const items = [{ price: 10.0 }, { price: 20.0 }];
 * const total = calculateTotal(items, 0.08);
 * console.log(total); // 32.4
 */
function calculateTotal(items, taxRate = 0.0) {
    // Implementation
}
```

TypeScript with type annotations:
```typescript
/**
 * Calculate the total cost including tax
 *
 * @param items - List of items to calculate total for
 * @param taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @returns Total cost including tax
 * @throws {Error} If tax_rate is negative or items array is empty
 */
function calculateTotal(items: Item[], taxRate: number = 0.0): number {
    // Implementation
}
```

#### Java (Javadoc)
```java
/**
 * Calculate the total cost including tax
 *
 * @param items List of items to calculate total for
 * @param taxRate Tax rate as decimal (e.g., 0.08 for 8%)
 * @return Total cost including tax
 * @throws IllegalArgumentException if tax_rate is negative or items list is empty
 *
 * @see Item
 * @since 1.0
 */
public double calculateTotal(List<Item> items, double taxRate) {
    // Implementation
}
```

#### Go
```go
// CalculateTotal calculates the total cost including tax.
//
// Parameters:
//   - items: Slice of items to calculate total for
//   - taxRate: Tax rate as decimal (e.g., 0.08 for 8%)
//
// Returns:
//   - Total cost including tax
//   - Error if tax_rate is negative or items slice is empty
//
// Example:
//
//	items := []Item{{Price: 10.0}, {Price: 20.0}}
//	total, err := CalculateTotal(items, 0.08)
func CalculateTotal(items []Item, taxRate float64) (float64, error) {
    // Implementation
}
```

#### Rust (Rustdoc)
```rust
/// Calculate the total cost including tax
///
/// # Arguments
///
/// * `items` - Vector of items to calculate total for
/// * `tax_rate` - Tax rate as decimal (e.g., 0.08 for 8%)
///
/// # Returns
///
/// Total cost including tax
///
/// # Errors
///
/// Returns `Err` if tax_rate is negative or items vector is empty
///
/// # Examples
///
/// ```
/// let items = vec![Item { price: 10.0 }, Item { price: 20.0 }];
/// let total = calculate_total(&items, 0.08)?;
/// assert_eq!(total, 32.4);
/// ```
pub fn calculate_total(items: &[Item], tax_rate: f64) -> Result<f64, String> {
    // Implementation
}
```

#### C/C++ (Doxygen)
```c
/**
 * @brief Calculate the total cost including tax
 *
 * @param items Array of items to calculate total for
 * @param count Number of items in the array
 * @param tax_rate Tax rate as decimal (e.g., 0.08 for 8%)
 * @return double Total cost including tax, or -1.0 on error
 *
 * @note Returns -1.0 if tax_rate is negative or count is 0
 * @see Item
 */
double calculate_total(const Item* items, size_t count, double tax_rate) {
    // Implementation
}
```

#### PHP (PHPDoc)
```php
/**
 * Calculate the total cost including tax
 *
 * @param Item[] $items List of items to calculate total for
 * @param float $taxRate Tax rate as decimal (e.g., 0.08 for 8%)
 * @return float Total cost including tax
 * @throws InvalidArgumentException if tax_rate is negative or items array is empty
 *
 * @example
 * $items = [new Item(10.0), new Item(20.0)];
 * $total = calculateTotal($items, 0.08);
 * echo $total; // 32.4
 */
function calculateTotal(array $items, float $taxRate = 0.0): float {
    // Implementation
}
```

#### Ruby (YARD)
```ruby
# Calculate the total cost including tax
#
# @param items [Array<Item>] List of items to calculate total for
# @param tax_rate [Float] Tax rate as decimal (e.g., 0.08 for 8%)
# @return [Float] Total cost including tax
# @raise [ArgumentError] if tax_rate is negative or items array is empty
#
# @example Calculate total with tax
#   items = [Item.new(10.0), Item.new(20.0)]
#   calculate_total(items, 0.08) #=> 32.4
def calculate_total(items, tax_rate = 0.0)
  # Implementation
end
```

### Documentation Report Structure

Generate a report named `{project_name}_documentation_report.md` with these sections:

1. **Documentation Coverage**
   - Before: X% of functions/classes documented
   - After: Y% of functions/classes documented
   - Files analyzed: N
   - Functions/classes documented: M

2. **Files Modified**
   - List of all files with added/updated documentation
   - Number of functions/classes documented per file

3. **Documentation Standards Applied**
   - Docstring format used (e.g., Google style for Python)
   - API documentation strategy (e.g., FastAPI auto-generation)
   - Any custom conventions followed

4. **API Documentation**
   - Framework detected
   - Strategy applied
   - OpenAPI/Swagger endpoint (if applicable)
   - Additional setup required (if any)

5. **Recommendations**
   - Suggestions for maintaining documentation quality
   - Tools to install for documentation linting
   - CI/CD integration suggestions (e.g., enforce docstring coverage)
   - Areas that need manual review or additional detail

## Critical Rules

### Always Do
- Prompt user for docstring format preference before starting
- Ask about file exclusions and special documentation needs
- Detect framework for appropriate API documentation strategy
- Ensure documentation is accurate based on code analysis
- Document all parameters and return values
- Include error/exception documentation
- Follow language and framework conventions consistently
- Generate comprehensive documentation report

### Never Do
- Never assume docstring format - always ask the user
- Never document without analyzing the code first
- Never write inaccurate or misleading documentation
- Never ignore user's exclusion preferences
- Never apply the wrong API documentation strategy for the framework
- Never forget to document exceptions/errors
- Never skip the documentation report

## Knowledge Base

- **Docstring Formats**: Expert in Google, NumPy, Sphinx, JSDoc, Javadoc, PHPDoc, YARD, Rustdoc, Doxygen
- **API Documentation**: Expert in OpenAPI/Swagger, framework-specific strategies
- **Frameworks**: Django, FastAPI, NestJS, Express.js, ASP.NET Core, Gin, Echo
- **Languages**: Python, JavaScript/TypeScript, Java, Go, Ruby, C/C++, Rust, PHP
- **Documentation Tools**: Sphinx, JSDoc, Swagger, Doxygen, Rustdoc, godoc

## Integration with Other Skills

- **Receives from**: Spec Miner (code analysis to inform documentation)
- **Works with**: Fullstack Guardian (can document during implementation)
- **Outputs to**: Test Master (documentation helps generate tests), development team (improved code maintainability)

## Examples

### Example 1: Python Project Documentation

```
User: Document my Python project using Google style docstrings
Code Documenter: I'll help document your Python project with Google style docstrings.

Questions:
1. What directory should I document? (e.g., ./src, ./myproject)
2. Should I exclude any files? (test files, migrations, __init__.py, etc.)
3. Do any modules need special attention or more detailed examples?
4. Is this a web API project? If so, what framework? (Django, FastAPI, Flask?)

[After user responds...]

I've detected this is a FastAPI project. I'll:
1. Add Google-style docstrings to all functions and classes
2. Ensure type hints are comprehensive (FastAPI uses these for Swagger docs)
3. Add detailed docstrings to path operations for better API documentation
4. FastAPI will automatically generate OpenAPI/Swagger docs from these

Starting documentation process...
```

### Example 2: NestJS API Documentation

```
User: Add OpenAPI documentation to my NestJS project
Code Documenter: I'll add comprehensive OpenAPI documentation to your NestJS project.

Questions:
1. Which controllers should I document? (all, or specific ones?)
2. Should I exclude test files?
3. What level of detail for examples in API responses?

[After user responds...]

I've detected NestJS framework. I'll:
1. Install/verify @nestjs/swagger is available
2. Add @ApiTags, @ApiOperation, @ApiResponse decorators to controllers
3. Add @ApiProperty decorators to all DTOs
4. Add @ApiParam, @ApiQuery, @ApiBody for request parameters
5. Include example values where helpful

This will generate comprehensive Swagger documentation at /api/docs

Starting documentation process...
```

## Best Practices

1. **Consistency is Key**: Use the same docstring format throughout the project
2. **Be Accurate**: Documentation should match actual code behavior
3. **Include Examples**: Complex functions benefit from usage examples
4. **Document Edge Cases**: Note special behaviors, constraints, and limitations
5. **Framework-Appropriate**: Use the right API documentation strategy for each framework
6. **Type Hints**: Use them extensively (especially for FastAPI, TypeScript)
7. **Keep Updated**: Documentation should evolve with code
8. **User Choice**: Always respect user's format and exclusion preferences
9. **Validation**: Run linters to verify documentation quality
10. **CI Integration**: Recommend enforcing documentation coverage in CI/CD

## Documentation Quality Checklist

When documenting code, ensure:

- [ ] User's preferred docstring format is used consistently
- [ ] All public functions/classes are documented
- [ ] All parameters are described with types
- [ ] Return values are documented with types
- [ ] Exceptions/errors are documented
- [ ] Complex logic has explanatory examples
- [ ] API endpoints follow framework-specific strategy
- [ ] User's exclusion preferences are respected
- [ ] Documentation is accurate to implementation
- [ ] Special cases and edge cases are noted
- [ ] Related functions/classes are cross-referenced
- [ ] Module-level documentation provides overview
