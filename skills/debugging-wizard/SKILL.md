---
name: Debugging Wizard
description: Expert in systematic debugging across all languages and frameworks. Use when debugging issues, troubleshooting errors, investigating bugs, analyzing logs, using debuggers, or when the user mentions debugging, troubleshooting, errors, bugs, or issues.
---

# Debugging Wizard

A specialized skill for systematic debugging and troubleshooting across all programming languages and frameworks.

## Instructions

### Core Workflow

1. **Understand the problem**
   - Gather error messages, stack traces, logs
   - Identify when the issue started
   - Determine reproduction steps
   - Understand expected vs actual behavior

2. **Reproduce the issue**
   - Create minimal reproducible example
   - Document exact steps to reproduce
   - Test in different environments
   - Isolate variables

3. **Investigate systematically**
   - Use appropriate debugging tools
   - Add strategic logging/breakpoints
   - Test hypotheses methodically
   - Eliminate possibilities

4. **Fix and verify**
   - Implement fix
   - Test thoroughly
   - Document the issue and solution
   - Add regression tests

### Debugging Strategies

#### The Scientific Method
1. **Observe**: What is happening?
2. **Hypothesize**: Why might this be happening?
3. **Test**: How can we verify the hypothesis?
4. **Analyze**: What did the test reveal?
5. **Iterate**: Repeat until root cause found

#### Binary Search Debugging
- Comment out half the code
- Determine which half has the bug
- Repeat until bug is isolated

#### Rubber Duck Debugging
- Explain the problem out loud (or in writing)
- Often reveals the solution

### Common Debugging Tools

#### TypeScript/JavaScript
```bash
# Node.js debugger
node --inspect app.js

# VS Code debugger (launch.json)
{
  "type": "node",
  "request": "launch",
  "name": "Debug Program",
  "program": "${workspaceFolder}/app.ts",
  "outFiles": ["${workspaceFolder}/dist/**/*.js"]
}

# Chrome DevTools
# Add 'debugger;' statement in code
debugger;

# Console debugging
console.log('Value:', value);
console.table(arrayOfObjects);
console.trace('Execution path');
```

#### Python
```python
# Built-in debugger
import pdb; pdb.set_trace()  # Python < 3.7
breakpoint()  # Python >= 3.7

# IPython debugger
from IPdb import set_trace; set_trace()

# Logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {var}")

# Print debugging
print(f"DEBUG: {variable}")
import pprint
pprint.pprint(complex_object)
```

#### Go
```go
// Delve debugger
dlv debug main.go

// Print debugging
import "fmt"
fmt.Printf("DEBUG: %+v\n", variable)

// Log debugging
import "log"
log.Printf("Value: %v", value)
```

### Debugging Patterns

#### Stack Trace Analysis
```
Error: Cannot read property 'name' of undefined
    at getUserName (app.js:45:18)
    at processUser (app.js:32:10)
    at main (app.js:15:3)
```
- Start at the top (most recent call)
- Work backwards through the call stack
- Identify the first occurrence in your code

#### Network Debugging
```bash
# cURL with verbose output
curl -v https://api.example.com/users

# Network tab in browser DevTools
# Check: Status code, Headers, Response, Timing

# Proxy tools
# Charles Proxy, Fiddler, mitmproxy
```

#### Database Query Debugging
```sql
-- Add EXPLAIN to understand query execution
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'test@example.com';

-- Check slow query log
-- Enable query logging in development
```

### Common Issues and Solutions

#### Race Conditions
```typescript
// Problem: Race condition
let data = null;
fetchData().then(d => data = d);
console.log(data); // null - fetchData not done yet

// Solution: Await the promise
const data = await fetchData();
console.log(data); // Correct value
```

#### Memory Leaks
```typescript
// Problem: Event listener not cleaned up
useEffect(() => {
  window.addEventListener('resize', handleResize);
  // Missing cleanup!
}, []);

// Solution: Cleanup in effect
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

#### Off-by-One Errors
```python
# Problem: Missing last item
for i in range(len(items) - 1):  # Missing last item!
    process(items[i])

# Solution: Correct range
for i in range(len(items)):
    process(items[i])

# Better: Iterate directly
for item in items:
    process(item)
```

### Debugging Checklist

- [ ] Can you reproduce the issue consistently?
- [ ] Do you have the complete error message/stack trace?
- [ ] Have you checked the logs?
- [ ] Have you tested in isolation?
- [ ] Have you verified inputs/outputs?
- [ ] Have you checked for typos?
- [ ] Have you read the documentation?
- [ ] Have you searched for similar issues?
- [ ] Have you tried the rubber duck method?
- [ ] Have you taken a break and come back fresh?

## Critical Rules

### Always Do
- Reproduce the issue first
- Gather all error messages and logs
- Create minimal reproducible examples
- Test hypotheses systematically
- Document findings
- Add regression tests after fixing
- Commit fixes with clear messages
- Share knowledge with team

### Never Do
- Never guess without testing
- Never make multiple changes at once
- Never skip reproduction steps
- Never assume the problem
- Never ignore warnings
- Never debug in production without backups
- Never commit debug code (console.logs, debugger statements)

## Knowledge Base

- **Tools**: Debuggers, profilers, network analyzers, log aggregators
- **Techniques**: Binary search, rubber duck, scientific method
- **Languages**: TypeScript, Python, Go, Java, etc.
- **Platforms**: Browser DevTools, VS Code, Chrome, Node.js

## Integration with Other Skills

- **Works with**: All development skills
- **Essential for**: Fullstack Guardian, Test Master

## Best Practices Summary

1. **Systematic**: Follow structured approach
2. **Reproducible**: Always reproduce first
3. **Isolated**: Test in isolation
4. **Documented**: Document findings
5. **Tested**: Add regression tests
6. **Tools**: Use appropriate debugging tools
7. **Logs**: Strategic logging
8. **Patience**: Take breaks when stuck
9. **Communication**: Share findings
10. **Learning**: Document for future reference
