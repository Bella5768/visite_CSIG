#!/usr/bin/env python3
"""
PythonAnywhere deployment script for visite_CSIG
Run this script on PythonAnywhere to deploy/update your application
"""

import os
import subprocess
import sys

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Executing: {description}")
    print(f"Command: {command}")
    print('='*50)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SUCCESS:")
        print(result.stdout)
    else:
        print("❌ ERROR:")
        print(result.stderr)
        return False
    
    return True

def main():
    """Main deployment function"""
    print("🚀 Starting deployment of visite_CSIG to PythonAnywhere...")
    
    # Configuration
    app_name = "menaetfp"  # Your PythonAnywhere web app name
    project_dir = f"/home/{app_name}/visite_CSIG"
    
    # Create project directory if it doesn't exist
    os.makedirs(project_dir, exist_ok=True)
    
    # Change to project directory
    os.chdir(project_dir)
    
    # Steps
    steps = [
        ("git pull origin master", "Pulling latest code from GitHub"),
        ("python3 -m venv venv", "Creating virtual environment"),
        ("source venv/bin/activate && pip install -r requirements.txt", "Installing dependencies"),
        ("source venv/bin/activate && python manage.py migrate", "Running database migrations"),
        ("source venv/bin/activate && python manage.py collectstatic --noinput", "Collecting static files"),
        ("source venv/bin/activate && python manage.py check", "Checking Django configuration"),
    ]
    
    for command, description in steps:
        if not run_command(command, description):
            print(f"\n❌ Deployment failed at: {description}")
            sys.exit(1)
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📋 Next steps:")
    print("1. Reload your web app on PythonAnywhere dashboard")
    print("2. Visit your app at: https://menaetfp.pythonanywhere.com")
    print("3. Check the error logs if you encounter any issues")

if __name__ == "__main__":
    main()
