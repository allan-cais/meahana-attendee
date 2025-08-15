#!/usr/bin/env python3
"""
Local Development Setup Script for Meeting Bot Backend
This script helps set up the local development environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔄 Creating virtual environment...")
    if run_command("python -m venv venv", "Creating virtual environment"):
        print("✅ Virtual environment created successfully")
        return True
    return False


def activate_virtual_environment():
    """Activate the virtual environment"""
    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate"
    else:
        activate_script = "source venv/bin/activate"
    
    print(f"🔄 Activating virtual environment...")
    print(f"   Run: {activate_script}")
    print("   Then run: pip install -r requirements.txt")
    return True


def install_dependencies():
    """Install Python dependencies"""
    if not Path("venv").exists():
        print("❌ Virtual environment not found. Please create it first.")
        return False
    
    if platform.system() == "Windows":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    return run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")


def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker detected: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Docker not found. You can still run the backend locally with PostgreSQL/Redis.")
    return False


def main():
    """Main setup function"""
    print("🚀 Meeting Bot Backend - Local Development Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check Docker
    docker_available = check_docker()
    
    print("\n📋 Setup Options:")
    print("1. Create virtual environment and install dependencies")
    print("2. Run with Docker (requires Docker)")
    print("3. Run locally with system PostgreSQL/Redis")
    
    choice = input("\nChoose an option (1-3): ").strip()
    
    if choice == "1":
        if create_virtual_environment():
            activate_virtual_environment()
            if input("\nInstall dependencies now? (y/n): ").lower() == 'y':
                install_dependencies()
    
    elif choice == "2" and docker_available:
        print("\n🐳 Running with Docker...")
        print("Run: docker-compose up --build")
    
    elif choice == "3":
        print("\n💻 Running locally...")
        print("Make sure you have PostgreSQL and Redis running locally")
        print("Then run: python -m uvicorn app.main:app --reload")
    
    else:
        print("❌ Invalid choice or Docker not available")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("\n📚 Next steps:")
    print("1. Copy env.example to .env and configure your API keys")
    print("2. Start the backend server")
    print("3. Check http://localhost:8000/docs for API documentation")


if __name__ == "__main__":
    main()
