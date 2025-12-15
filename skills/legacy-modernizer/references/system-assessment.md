# System Assessment

> Reference for: Legacy Modernizer
> Load when: Code analysis, dependency mapping, risk evaluation, planning modernization

## Codebase Analysis Checklist

```python
# Automated assessment script
from pathlib import Path
import ast
import re
from collections import defaultdict

class LegacyCodeAnalyzer:
    def __init__(self, codebase_path: Path):
        self.path = codebase_path
        self.metrics = defaultdict(int)
        self.issues = []

    def analyze(self):
        """Run comprehensive analysis"""
        self.count_lines_of_code()
        self.analyze_dependencies()
        self.find_code_smells()
        self.check_test_coverage()
        self.identify_hotspots()
        return self.generate_report()

    def count_lines_of_code(self):
        """Basic size metrics"""
        for py_file in self.path.rglob("*.py"):
            with open(py_file) as f:
                lines = f.readlines()
                self.metrics['total_lines'] += len(lines)
                self.metrics['files'] += 1

                # Count code vs comments
                code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
                self.metrics['code_lines'] += len(code_lines)

    def analyze_dependencies(self):
        """Find external and internal dependencies"""
        dependencies = set()

        for py_file in self.path.rglob("*.py"):
            with open(py_file) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module.split('.')[0])

        self.metrics['dependencies'] = len(dependencies)
        self.dependencies = dependencies

    def find_code_smells(self):
        """Detect common legacy code issues"""
        for py_file in self.path.rglob("*.py"):
            with open(py_file) as f:
                content = f.read()
                tree = ast.parse(content)

            # Long functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        self.issues.append({
                            'type': 'long_function',
                            'file': str(py_file),
                            'function': node.name,
                            'lines': func_length,
                        })

            # Global variables
            if re.search(r'^[A-Z_]+ = ', content, re.MULTILINE):
                self.metrics['global_vars'] += len(
                    re.findall(r'^[A-Z_]+ = ', content, re.MULTILINE)
                )

            # SQL in code (sign of tight coupling)
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE)\s+', content, re.IGNORECASE):
                self.metrics['raw_sql'] += 1
                self.issues.append({
                    'type': 'raw_sql',
                    'file': str(py_file),
                })

    def check_test_coverage(self):
        """Calculate test coverage"""
        test_files = list(self.path.rglob("test_*.py"))
        self.metrics['test_files'] = len(test_files)
        self.metrics['test_coverage_estimate'] = (
            len(test_files) / max(self.metrics['files'], 1) * 100
        )

    def identify_hotspots(self):
        """Find files changed most often (requires git)"""
        import subprocess

        try:
            result = subprocess.run(
                ['git', 'log', '--format=format:', '--name-only'],
                cwd=self.path,
                capture_output=True,
                text=True,
            )

            file_changes = defaultdict(int)
            for line in result.stdout.split('\n'):
                if line.strip():
                    file_changes[line.strip()] += 1

            # Top 10 changed files
            self.hotspots = sorted(
                file_changes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        except Exception:
            self.hotspots = []

    def generate_report(self):
        """Generate assessment report"""
        return {
            'summary': {
                'total_files': self.metrics['files'],
                'total_lines': self.metrics['total_lines'],
                'code_lines': self.metrics['code_lines'],
                'dependencies': self.metrics['dependencies'],
                'test_coverage_estimate': f"{self.metrics['test_coverage_estimate']:.1f}%",
            },
            'issues': {
                'long_functions': len([i for i in self.issues if i['type'] == 'long_function']),
                'raw_sql_usage': self.metrics['raw_sql'],
                'global_variables': self.metrics['global_vars'],
            },
            'hotspots': self.hotspots,
            'detailed_issues': self.issues[:20],  # Top 20 issues
        }

# Usage
analyzer = LegacyCodeAnalyzer(Path('./legacy_app'))
report = analyzer.analyze()
print(json.dumps(report, indent=2))
```

## Dependency Analysis

```python
# Identify circular dependencies and tight coupling
import subprocess
import json
from pathlib import Path
from collections import defaultdict

def analyze_dependencies(project_path: Path):
    """Map internal module dependencies"""
    dependencies = defaultdict(set)

    for py_file in project_path.rglob("*.py"):
        module_name = str(py_file.relative_to(project_path)).replace('/', '.').replace('.py', '')

        with open(py_file) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and not node.module.startswith('.'):
                    # Internal imports only
                    if node.module.split('.')[0] in ['app', 'lib', 'models']:
                        dependencies[module_name].add(node.module)

    return dependencies

def find_circular_dependencies(dependencies: dict):
    """Detect circular dependencies"""
    circular = []

    def has_path(start, end, visited=None):
        if visited is None:
            visited = set()
        if start == end:
            return True
        if start in visited:
            return False
        visited.add(start)
        for dep in dependencies.get(start, []):
            if has_path(dep, end, visited):
                return True
        return False

    for module, deps in dependencies.items():
        for dep in deps:
            if has_path(dep, module):
                circular.append((module, dep))

    return circular

# Visualize dependency graph
def generate_dependency_graph(dependencies: dict, output_file: str):
    """Generate GraphViz diagram"""
    dot_lines = ["digraph dependencies {"]

    for module, deps in dependencies.items():
        for dep in deps:
            dot_lines.append(f'    "{module}" -> "{dep}";')

    dot_lines.append("}")

    Path(output_file).write_text('\n'.join(dot_lines))
    print(f"Generated {output_file} - render with: dot -Tpng {output_file} -o deps.png")
```

## Technical Debt Calculation

```python
from datetime import datetime, timedelta

class TechnicalDebtCalculator:
    """Calculate technical debt using SQALE method"""

    SEVERITY_MULTIPLIERS = {
        'critical': 1.0,   # 1 day to fix
        'major': 0.5,      # 4 hours
        'minor': 0.25,     # 2 hours
        'info': 0.1,       # 30 min
    }

    def __init__(self):
        self.debt_items = []

    def add_issue(self, issue_type: str, severity: str, count: int = 1):
        """Add technical debt item"""
        days_to_fix = self.SEVERITY_MULTIPLIERS[severity] * count
        self.debt_items.append({
            'type': issue_type,
            'severity': severity,
            'count': count,
            'effort_days': days_to_fix,
        })

    def calculate_total_debt(self):
        """Calculate total remediation effort"""
        total_days = sum(item['effort_days'] for item in self.debt_items)
        return {
            'total_days': round(total_days, 1),
            'total_weeks': round(total_days / 5, 1),
            'estimated_cost': round(total_days * 800, 2),  # $800/day avg
            'breakdown': self.debt_items,
        }

# Usage based on code analysis
debt_calc = TechnicalDebtCalculator()

# From static analysis results
debt_calc.add_issue('long_functions', 'major', count=45)
debt_calc.add_issue('circular_dependencies', 'critical', count=8)
debt_calc.add_issue('missing_tests', 'major', count=120)
debt_calc.add_issue('security_vulnerabilities', 'critical', count=12)
debt_calc.add_issue('deprecated_dependencies', 'major', count=15)
debt_calc.add_issue('code_duplication', 'minor', count=89)

report = debt_calc.calculate_total_debt()
# Output: ~95 days of work, ~19 weeks, ~$76,000
```

## Risk Assessment Matrix

```python
from enum import Enum

class Risk(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class RiskAssessment:
    def __init__(self):
        self.risks = []

    def assess(self, area: str, impact: Risk, probability: Risk, mitigation: str):
        """Assess risk for modernization area"""
        risk_score = impact.value * probability.value

        self.risks.append({
            'area': area,
            'impact': impact.name,
            'probability': probability.name,
            'score': risk_score,
            'severity': self._get_severity(risk_score),
            'mitigation': mitigation,
        })

    def _get_severity(self, score: int) -> str:
        if score >= 12:
            return 'CRITICAL'
        elif score >= 8:
            return 'HIGH'
        elif score >= 4:
            return 'MEDIUM'
        else:
            return 'LOW'

    def get_prioritized_risks(self):
        """Return risks sorted by severity"""
        return sorted(self.risks, key=lambda r: r['score'], reverse=True)

# Example risk assessment
risks = RiskAssessment()

risks.assess(
    area="Database migration",
    impact=Risk.CRITICAL,
    probability=Risk.MEDIUM,
    mitigation="Implement dual-write pattern with comprehensive monitoring"
)

risks.assess(
    area="Authentication system upgrade",
    impact=Risk.CRITICAL,
    probability=Risk.LOW,
    mitigation="Shadow testing in production, feature flags for rollback"
)

risks.assess(
    area="UI framework migration",
    impact=Risk.MEDIUM,
    probability=Risk.MEDIUM,
    mitigation="Incremental component replacement, A/B testing"
)

risks.assess(
    area="Legacy API deprecation",
    impact=Risk.HIGH,
    probability=Risk.HIGH,
    mitigation="12-month sunset period, client migration support, versioning"
)

for risk in risks.get_prioritized_risks():
    print(f"{risk['severity']}: {risk['area']}")
```

## Modernization Roadmap Template

```python
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

@dataclass
class MigrationPhase:
    name: str
    description: str
    duration_weeks: int
    dependencies: List[str]
    success_metrics: dict
    rollback_plan: str

class ModernizationRoadmap:
    def __init__(self, start_date: date):
        self.start_date = start_date
        self.phases = []

    def add_phase(self, phase: MigrationPhase):
        self.phases.append(phase)

    def generate_timeline(self):
        """Generate week-by-week timeline"""
        timeline = []
        current_date = self.start_date

        for phase in self.phases:
            end_date = current_date + timedelta(weeks=phase.duration_weeks)
            timeline.append({
                'phase': phase.name,
                'start': current_date.isoformat(),
                'end': end_date.isoformat(),
                'duration_weeks': phase.duration_weeks,
                'dependencies': phase.dependencies,
            })
            current_date = end_date

        return timeline

# Example roadmap
roadmap = ModernizationRoadmap(start_date=date(2024, 1, 1))

roadmap.add_phase(MigrationPhase(
    name="Assessment & Planning",
    description="Code analysis, dependency mapping, risk assessment",
    duration_weeks=2,
    dependencies=[],
    success_metrics={'assessment_complete': True, 'roadmap_approved': True},
    rollback_plan="N/A - planning phase"
))

roadmap.add_phase(MigrationPhase(
    name="Test Coverage",
    description="Build characterization tests for critical paths",
    duration_weeks=4,
    dependencies=["Assessment & Planning"],
    success_metrics={'coverage': '80%', 'characterization_tests': 200},
    rollback_plan="Continue with existing tests"
))

roadmap.add_phase(MigrationPhase(
    name="Database Migration Setup",
    description="Implement dual-write pattern, lazy migration",
    duration_weeks=3,
    dependencies=["Test Coverage"],
    success_metrics={'dual_write_working': True, 'data_consistency': '99.9%'},
    rollback_plan="Disable dual-write, continue legacy DB only"
))

roadmap.add_phase(MigrationPhase(
    name="Service Extraction - Phase 1",
    description="Extract payment service using strangler fig",
    duration_weeks=6,
    dependencies=["Database Migration Setup"],
    success_metrics={'service_deployed': True, 'error_rate': '<0.1%', 'traffic': '100%'},
    rollback_plan="Route 100% traffic back to monolith via feature flag"
))

timeline = roadmap.generate_timeline()
```

## Stakeholder Communication Template

```python
# Weekly status report generator
from datetime import datetime

class ModernizationStatusReport:
    def __init__(self, week_number: int):
        self.week = week_number
        self.completed = []
        self.in_progress = []
        self.blockers = []
        self.metrics = {}

    def generate_report(self) -> str:
        """Generate stakeholder-friendly report"""
        return f"""
# Legacy Modernization - Week {self.week} Status

## Executive Summary
- **Progress**: {self._calculate_progress()}% complete
- **On Track**: {'Yes' if not self.blockers else 'Blocked'}
- **Risk Level**: {self._assess_risk_level()}

## This Week's Accomplishments
{self._format_list(self.completed)}

## In Progress
{self._format_list(self.in_progress)}

## Blockers & Risks
{self._format_list(self.blockers) if self.blockers else '- None'}

## Key Metrics
{self._format_metrics()}

## Next Week's Goals
{self._format_list(self.next_week_goals)}
        """.strip()

    def _format_list(self, items: list) -> str:
        return '\n'.join(f"- {item}" for item in items)

    def _format_metrics(self) -> str:
        return '\n'.join(f"- {k}: {v}" for k, v in self.metrics.items())
```

## Quick Reference

| Assessment Area | Tools | Output |
|----------------|-------|--------|
| Code Quality | pylint, radon, sonarqube | Complexity, issues |
| Dependencies | pipdeptree, pydeps | Graph, circular deps |
| Technical Debt | SonarQube, CodeClimate | Debt hours, cost |
| Test Coverage | coverage.py, pytest-cov | Percentage, gaps |
| Security | bandit, safety | Vulnerabilities |
| Performance | cProfile, py-spy | Bottlenecks |
