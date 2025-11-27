#!/usr/bin/env python3
"""
PrimalTechInvest.com Integration API

Automatically pushes MotorHandPro results to www.primaltechinvest.com
for public visibility, leaderboards, and firmware distribution.

Features:
- REST API client for result uploads
- Webhook notifications
- Automatic best config publishing
- Real-time leaderboard updates
- Firmware distribution endpoint

Author: Lightfoot Technology
"""

import os
import json
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class PrimalTechInvestAPI:
    """
    API client for www.primaltechinvest.com integration

    Handles:
    - Result uploads
    - Best config publishing
    - Leaderboard updates
    - Firmware distribution
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize API client

        Args:
            api_key: API key for authentication (from env var if not provided)
            base_url: Base URL for API (defaults to production)
        """
        self.api_key = api_key or os.getenv('PRIMALTECH_API_KEY', '')
        self.base_url = base_url or os.getenv(
            'PRIMALTECH_API_URL',
            'https://api.primaltechinvest.com/v1'
        )

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MotorHandPro-Sweep/1.0'
        })

    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            response = self.session.get(f'{self.base_url}/health')
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def upload_sweep_results(
        self,
        category: str,
        run_id: str,
        results: List[Dict],
        metadata: Dict
    ) -> Dict:
        """
        Upload parameter sweep results

        Args:
            category: Sweep category (control_params, emergency_scenarios, etc)
            run_id: Unique run identifier
            results: List of result dictionaries
            metadata: Run metadata (git info, timestamps, etc)

        Returns:
            API response with upload URL and status
        """
        payload = {
            'category': category,
            'run_id': run_id,
            'timestamp': datetime.utcnow().isoformat(),
            'results': results,
            'metadata': metadata,
            'result_count': len(results)
        }

        try:
            response = self.session.post(
                f'{self.base_url}/motorhand/sweeps',
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'category': category
            }

    def publish_best_config(
        self,
        config: Dict,
        version: str = None
    ) -> Dict:
        """
        Publish optimal configuration for public download

        Args:
            config: Best configuration dictionary
            version: Optional version tag (e.g., 'v1.0.0')

        Returns:
            API response with download URL
        """
        # Generate version if not provided
        if version is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            version = f'auto_{timestamp}'

        # Add version to config
        config_with_version = config.copy()
        config_with_version['version'] = version
        config_with_version['published_at'] = datetime.utcnow().isoformat()

        # Generate checksum
        config_json = json.dumps(config_with_version, sort_keys=True)
        checksum = hashlib.sha256(config_json.encode()).hexdigest()
        config_with_version['checksum'] = checksum

        try:
            response = self.session.post(
                f'{self.base_url}/motorhand/firmware/publish',
                json=config_with_version
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def update_leaderboard(
        self,
        category: str,
        top_results: List[Dict],
        stats: Dict
    ) -> Dict:
        """
        Update public leaderboard

        Args:
            category: Leaderboard category
            top_results: Top N results for leaderboard
            stats: Overall statistics (total tests, success rate, etc)

        Returns:
            API response
        """
        payload = {
            'category': category,
            'top_results': top_results,
            'statistics': stats,
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            response = self.session.put(
                f'{self.base_url}/motorhand/leaderboard/{category}',
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def send_webhook(
        self,
        event_type: str,
        data: Dict
    ) -> Dict:
        """
        Send webhook notification

        Args:
            event_type: Event type (sweep_complete, best_config_updated, etc)
            data: Event data

        Returns:
            API response
        """
        payload = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }

        try:
            response = self.session.post(
                f'{self.base_url}/webhooks',
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_firmware_download_url(
        self,
        version: str = 'latest'
    ) -> Optional[str]:
        """
        Get public firmware download URL

        Args:
            version: Firmware version (default: 'latest')

        Returns:
            Download URL or None if not found
        """
        try:
            response = self.session.get(
                f'{self.base_url}/motorhand/firmware/{version}'
            )
            response.raise_for_status()
            data = response.json()
            return data.get('download_url')
        except requests.exceptions.RequestException:
            return None

    def upload_dashboard(
        self,
        dashboard_html: str,
        title: str = 'MotorHandPro Live Dashboard'
    ) -> Dict:
        """
        Upload interactive dashboard to website

        Args:
            dashboard_html: HTML content for dashboard
            title: Dashboard title

        Returns:
            API response with dashboard URL
        """
        payload = {
            'title': title,
            'html_content': dashboard_html,
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            response = self.session.post(
                f'{self.base_url}/motorhand/dashboard',
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }


def integrate_with_website(
    results_dir: str,
    api_key: str = None,
    publish_config: bool = True,
    update_leaderboard: bool = True
) -> Dict:
    """
    Complete integration workflow

    Uploads all results to www.primaltechinvest.com

    Args:
        results_dir: Directory containing sweep results
        api_key: API key (uses env var if not provided)
        publish_config: Whether to publish best config
        update_leaderboard: Whether to update leaderboards

    Returns:
        Dictionary with integration results
    """
    print("\n" + "=" * 80)
    print("PRIMALTECHINVEST.COM INTEGRATION")
    print("=" * 80)

    # Initialize API client
    api = PrimalTechInvestAPI(api_key=api_key)

    # Test connection
    print("\n1. Testing API connection...")
    if not api.test_connection():
        print("   ✗ Connection failed - check API key and network")
        return {'success': False, 'error': 'Connection failed'}
    print("   ✓ Connected to PrimalTechInvest API")

    results_summary = {
        'uploads': [],
        'leaderboards': [],
        'firmware': None
    }

    # Upload sweep results
    print("\n2. Uploading sweep results...")
    categories = [
        'motorhand_control_params',
        'motorhand_emergency_scenarios',
        'motorhand_throttle_conversion',
        'motorhand_ipu_scaling',
        'motorhand_closed_loop'
    ]

    for category in categories:
        category_dir = Path(results_dir) / category
        if not category_dir.exists():
            continue

        # Find latest run
        runs = sorted([d for d in category_dir.iterdir() if d.is_dir()])
        if not runs:
            continue

        latest_run = runs[-1]

        # Load results
        csv_path = latest_run / 'summary' / 'summary.csv'
        metadata_path = latest_run / 'metadata.json'

        if not csv_path.exists():
            continue

        # Parse CSV results
        import csv
        results = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)

        # Load metadata
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        # Upload
        print(f"   Uploading {category}... ({len(results)} results)", end='', flush=True)
        response = api.upload_sweep_results(
            category=category,
            run_id=latest_run.name,
            results=results,
            metadata=metadata
        )

        if response.get('success', False):
            print(" ✓")
            results_summary['uploads'].append({
                'category': category,
                'count': len(results),
                'url': response.get('url')
            })
        else:
            print(f" ✗ {response.get('error', 'Unknown error')}")

    # Publish best configuration
    if publish_config and Path('motorhand_best_params.json').exists():
        print("\n3. Publishing best configuration...")
        with open('motorhand_best_params.json', 'r') as f:
            best_config = json.load(f)

        response = api.publish_best_config(best_config)

        if response.get('success', False):
            print(f"   ✓ Published: {response.get('download_url')}")
            results_summary['firmware'] = response
        else:
            print(f"   ✗ Failed: {response.get('error')}")

    # Update leaderboards
    if update_leaderboard:
        print("\n4. Updating leaderboards...")

        # Control parameters leaderboard
        control_params_dir = Path(results_dir) / 'motorhand_control_params'
        if control_params_dir.exists():
            runs = sorted([d for d in control_params_dir.iterdir() if d.is_dir()])
            if runs:
                latest_run = runs[-1]
                csv_path = latest_run / 'summary' / 'summary.csv'

                if csv_path.exists():
                    # Load and parse results
                    results = []
                    with open(csv_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Convert to numeric
                            try:
                                row['comfort_index'] = float(row['comfort_index'])
                                row['settling_time'] = float(row['settling_time'])
                                row['stable'] = row['stable'].lower() == 'true'
                                results.append(row)
                            except (ValueError, KeyError):
                                continue

                    # Filter stable and get top 10
                    stable = [r for r in results if r['stable']]

                    # Compute composite scores
                    for r in stable:
                        r['score'] = (r['comfort_index'] * 0.7) - (r['settling_time'] * 3.0)

                    top_10 = sorted(stable, key=lambda x: x['score'], reverse=True)[:10]

                    stats = {
                        'total_tested': len(results),
                        'stable_count': len(stable),
                        'success_rate': len(stable) / len(results) * 100
                    }

                    response = api.update_leaderboard(
                        category='control_parameters',
                        top_results=top_10,
                        stats=stats
                    )

                    if response.get('success', False):
                        print(f"   ✓ Updated leaderboard: {response.get('url')}")
                        results_summary['leaderboards'].append(response)

    # Send completion webhook
    print("\n5. Sending webhook notification...")
    webhook_response = api.send_webhook(
        event_type='motorhand_integration_complete',
        data={
            'uploads': len(results_summary['uploads']),
            'firmware_published': results_summary['firmware'] is not None,
            'leaderboards_updated': len(results_summary['leaderboards'])
        }
    )

    if webhook_response.get('success', False):
        print("   ✓ Webhook sent")

    print("\n" + "=" * 80)
    print("✓ INTEGRATION COMPLETE")
    print("=" * 80)
    print(f"\nUploaded: {len(results_summary['uploads'])} categories")
    print(f"Leaderboards: {len(results_summary['leaderboards'])} updated")
    if results_summary['firmware']:
        print(f"Firmware: Published")
        print(f"Download URL: {results_summary['firmware'].get('download_url')}")

    print(f"\nView results at: https://www.primaltechinvest.com/motorhand")
    print("=" * 80)

    return {
        'success': True,
        'summary': results_summary
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Integrate MotorHandPro results with PrimalTechInvest.com'
    )
    parser.add_argument(
        '--results-dir',
        default=os.path.expanduser('~/Multi-Heart-Model-Results'),
        help='Results directory'
    )
    parser.add_argument(
        '--api-key',
        help='API key (or set PRIMALTECH_API_KEY env var)'
    )
    parser.add_argument(
        '--no-config',
        action='store_true',
        help='Skip best config publishing'
    )
    parser.add_argument(
        '--no-leaderboard',
        action='store_true',
        help='Skip leaderboard updates'
    )

    args = parser.parse_args()

    result = integrate_with_website(
        results_dir=args.results_dir,
        api_key=args.api_key,
        publish_config=not args.no_config,
        update_leaderboard=not args.no_leaderboard
    )

    exit(0 if result['success'] else 1)
