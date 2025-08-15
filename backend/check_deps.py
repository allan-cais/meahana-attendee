#!/usr/bin/env python3
"""
Dependency Check Script for Meeting Bot Backend
This script checks if all required packages are installed and working.
"""

import importlib
import sys
from pathlib import Path


def check_package(package_name, import_name=None):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - NOT INSTALLED")
        return False


def main():
    """Check all required dependencies"""
    print("🔍 Checking Python Dependencies...")
    print("=" * 40)
    
    # Core dependencies
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("alembic", "alembic"),
        ("asyncpg", "asyncpg"),
        ("sqlalchemy", "sqlalchemy"),
        ("redis", "redis"),
        ("httpx", "httpx"),
        ("pydantic", "pydantic"),
        ("pydantic-settings", "pydantic_settings"),
        ("openai", "openai"),
        ("python-multipart", "multipart"),
        ("pyngrok", "pyngrok"),
        ("requests", "requests"),
    ]
    
    all_installed = True
    for package, import_name in required_packages:
        if not check_package(package, import_name):
            all_installed = False
    
    print("\n" + "=" * 40)
    
    if all_installed:
        print("🎉 All dependencies are installed!")
        print("\n🚀 You can now run the backend with:")
        print("   python -m uvicorn app.main:app --reload")
    else:
        print("❌ Some dependencies are missing!")
        print("\n📦 Install missing dependencies with:")
        print("   pip install -r requirements.txt")
        print("\n💡 Or create a virtual environment first:")
        print("   python -m venv venv")
        print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("   pip install -r requirements.txt")
    
    # Check Python version
    print(f"\n🐍 Python version: {sys.version}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment (recommended for development)")


if __name__ == "__main__":
    main()
