#!/usr/bin/env python3
"""
Multi-Branch Comprehensive Execution Script
Runs all experiments across all repository branches
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class MultiBranchExecutor:
    """Execute experiments across multiple git branches"""

    def __init__(self, output_dir: str = "multi_branch_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}

    def get_all_branches(self) -> List[str]:
        """Get list of all remote branches"""
        result = subprocess.run(
            ['git', 'branch', '-r'],
            capture_output=True,
            text=True
        )

        branches = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and 'origin/' in line and '->' not in line:
                branch = line.replace('origin/', '')
                branches.append(branch)

        return branches

    def filter_branches(self, branches: List[str]) -> Dict[str, List[str]]:
        """Filter and categorize branches"""
        categories = {
            'main': [],
            'feature': [],
            'integration': [],
            'testing': [],
            'infrastructure': [],
            'other': []
        }

        for branch in branches:
            if branch == 'main':
                categories['main'].append(branch)
            elif 'bci' in branch or 'neural' in branch or 'openbci' in branch:
                categories['integration'].append(branch)
            elif 'organ-chip' in branch or 'liver' in branch or 'hepatocyte' in branch:
                categories['integration'].append(branch)
            elif 'motor' in branch or 'quant' in branch or 'arduino' in branch:
                categories['integration'].append(branch)
            elif 'surgical' in branch or 'robotics' in branch:
                categories['integration'].append(branch)
            elif 'production' in branch or 'infrastructure' in branch:
                categories['infrastructure'].append(branch)
            elif 'testing' in branch or 'validation' in branch:
                categories['testing'].append(branch)
            elif 'claude/' in branch or 'codex/' in branch:
                categories['feature'].append(branch)
            else:
                categories['other'].append(branch)

        return categories

    def checkout_branch(self, branch: str) -> bool:
        """Checkout a specific branch"""
        try:
            print(f"\n{'='*80}")
            print(f"Checking out branch: {branch}")
            print('='*80)

            # Checkout branch
            result = subprocess.run(
                ['git', 'checkout', branch],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"  ✗ Failed to checkout: {result.stderr}")
                return False

            print(f"  ✓ Successfully checked out {branch}")
            return True

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def get_branch_info(self, branch: str) -> Dict[str, Any]:
        """Get information about a branch"""
        info = {
            'branch': branch,
            'commit': None,
            'author': None,
            'date': None,
            'message': None
        }

        try:
            # Get commit info
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%H|%an|%ad|%s'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                if len(parts) == 4:
                    info['commit'] = parts[0][:8]
                    info['author'] = parts[1]
                    info['date'] = parts[2]
                    info['message'] = parts[3]

        except Exception as e:
            print(f"  ⚠️  Could not get branch info: {e}")

        return info

    def check_runnable_files(self) -> Dict[str, bool]:
        """Check which files are runnable on current branch"""
        files = {
            'validate_integration.py': Path('validate_integration.py').exists(),
            'validate_organchip.py': Path('validate_organchip.py').exists(),
            'sweep_master.py': Path('sweep_master.py').exists(),
            'run_tests_simple.py': Path('run_tests_simple.py').exists(),
            'examples/microprocessor_motorhand_demo.py': Path('examples/microprocessor_motorhand_demo.py').exists(),
        }

        return files

    def run_validations(self, branch: str) -> Dict[str, Any]:
        """Run validation scripts on current branch"""
        results = {
            'branch': branch,
            'validations': {},
            'timestamp': datetime.now().isoformat()
        }

        validations = [
            ('validate_integration.py', 'Integration Validation'),
            ('validate_organchip.py', 'Organ Chip Validation'),
            ('run_tests_simple.py', 'Simple Test Suite'),
        ]

        for script, name in validations:
            if not Path(script).exists():
                print(f"  ⊗ {name}: Script not found")
                results['validations'][name] = {'status': 'not_found'}
                continue

            print(f"  → Running {name}...")
            try:
                result = subprocess.run(
                    ['python', script],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                success = result.returncode == 0
                status = '✓' if success else '✗'
                print(f"    {status} {name}: {'PASSED' if success else 'FAILED'}")

                results['validations'][name] = {
                    'status': 'passed' if success else 'failed',
                    'returncode': result.returncode,
                    'output_length': len(result.stdout)
                }

            except subprocess.TimeoutExpired:
                print(f"    ⏱  {name}: TIMEOUT")
                results['validations'][name] = {'status': 'timeout'}
            except Exception as e:
                print(f"    ✗ {name}: ERROR - {e}")
                results['validations'][name] = {'status': 'error', 'error': str(e)}

        return results

    def run_on_branch(self, branch: str) -> Dict[str, Any]:
        """Run all experiments on a specific branch"""
        result = {
            'branch': branch,
            'success': False,
            'info': None,
            'runnable_files': {},
            'validations': {}
        }

        # Checkout branch
        if not self.checkout_branch(branch):
            return result

        # Get branch info
        result['info'] = self.get_branch_info(branch)
        print(f"  Commit: {result['info']['commit']}")
        print(f"  Message: {result['info']['message']}")

        # Check runnable files
        result['runnable_files'] = self.check_runnable_files()
        runnable_count = sum(1 for v in result['runnable_files'].values() if v)
        print(f"  Runnable files: {runnable_count}/{len(result['runnable_files'])}")

        # Run validations
        if runnable_count > 0:
            result['validations'] = self.run_validations(branch)
            result['success'] = True
        else:
            print(f"  ⊗ No runnable files found, skipping validations")

        return result

    def generate_summary(self):
        """Generate comprehensive summary of all branch executions"""
        summary_file = self.output_dir / f"multi_branch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(summary_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n{'='*80}")
        print(f"MULTI-BRANCH EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total branches processed: {len(self.results)}")
        print(f"Results saved to: {summary_file}")

        # Summary statistics
        successful = sum(1 for r in self.results.values() if r['success'])
        print(f"Successful: {successful}/{len(self.results)}")

        # Validation summary
        print(f"\nValidation Results by Branch:")
        for branch, data in self.results.items():
            if data.get('validations'):
                passed = sum(1 for v in data['validations'].get('validations', {}).values()
                           if v.get('status') == 'passed')
                total = len(data['validations'].get('validations', {}))
                print(f"  {branch}: {passed}/{total} validations passed")

    def execute_all(self, priority_branches: List[str] = None):
        """Execute experiments on all branches"""
        print("="*80)
        print("MULTI-BRANCH COMPREHENSIVE EXECUTION")
        print("="*80)

        # Get all branches
        all_branches = self.get_all_branches()
        print(f"\nFound {len(all_branches)} branches")

        # Categorize
        categories = self.filter_branches(all_branches)
        for cat, branches in categories.items():
            if branches:
                print(f"  {cat}: {len(branches)} branches")

        # Determine which branches to run
        if priority_branches:
            branches_to_run = [b for b in all_branches if b in priority_branches]
        else:
            # Run main + all integration branches + recent feature branches
            branches_to_run = (
                categories['main'] +
                categories['integration'][:5] +
                categories['infrastructure'][:3] +
                categories['feature'][:5]
            )

        print(f"\nWill execute on {len(branches_to_run)} branches")

        # Execute on each branch
        for i, branch in enumerate(branches_to_run, 1):
            print(f"\n[{i}/{len(branches_to_run)}] Processing branch: {branch}")
            self.results[branch] = self.run_on_branch(branch)

        # Generate summary
        self.generate_summary()

        return self.results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-branch execution script")
    parser.add_argument('--all', action='store_true', help='Run on all branches')
    parser.add_argument('--branches', nargs='+', help='Specific branches to run')
    parser.add_argument('--priority-only', action='store_true', help='Run only on priority branches')

    args = parser.parse_args()

    executor = MultiBranchExecutor()

    if args.branches:
        executor.execute_all(priority_branches=args.branches)
    elif args.priority_only:
        # Priority branches
        priority = [
            'main',
            'claude/run-all-repos-01Y8GXtb7N61yLM5kBWAnVhV',
            'claude/surgical-robotics-interface-01WNAtPL5TdBmssmPbZi9FxU',
            'claude/setup-production-infrastructure-01E4Z5hTygNUsU28vpAdo6xY',
            'claude/physiological-model-validation-01DN4AYiktu9BtLrrArKd7yD'
        ]
        executor.execute_all(priority_branches=priority)
    else:
        # Auto-select important branches
        executor.execute_all()

    print("\n✓ Multi-branch execution complete!")


if __name__ == "__main__":
    main()
