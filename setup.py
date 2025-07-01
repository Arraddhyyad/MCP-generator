"""
Setup script for MCP Resume + Cover Letter Generator
"""

import os
import subprocess
import sys


def check_wkhtmltopdf():
    """Check if wkhtmltopdf is installed (required for pdfkit)"""
    try:
        subprocess.run(['wkhtmltopdf', '--version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Python requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False


def create_directories():
    """Create necessary directories"""
    directories = ['profiles', 'outputs', 'mcp_modules']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")


def setup_environment():
    """Setup environment file template"""
    env_template = """# MCP Resume Generator Environment Variables
# Copy this file to .env and fill in your actual API key

OPENAI_API_KEY=your_openai_api_key_here

# Optional: Customize directories
# PROFILES_DIR=profiles
# OUTPUTS_DIR=outputs
"""
    
    env_file = '.env.template'
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write(env_template)
        print(f"✅ Created environment template: {env_file}")
    else:
        print(f"📄 Environment template already exists: {env_file}")


def main():
    """Main setup function"""
    print("🚀 Setting up MCP Resume + Cover Letter Generator")
    print("="*50)
    
    # Create directories
    create_directories()
    
    # Install Python requirements
    if not install_requirements():
        print("❌ Setup failed: Could not install Python requirements")
        return 1
    
    # Check for wkhtmltopdf
    if not check_wkhtmltopdf():
        print("\n⚠️  Warning: wkhtmltopdf not found!")
        print("   This is required for PDF generation.")
        print("   Install instructions:")
        print("   - Ubuntu/Debian: sudo apt-get install wkhtmltopdf")
        print("   - macOS: brew install wkhtmltopdf")
        print("   - Windows: Download from https://wkhtmltopdf.org/downloads.html")
        print("   - The system will fallback to HTML if PDF generation fails")
    else:
        print("✅ wkhtmltopdf is installed and ready")
    
    # Setup environment template
    setup_environment()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Set your OpenAI API key:")
    print("   export OPENAI_API_KEY='your-api-key-here'")
    print("2. Run the system:")
    print("   python main.py")
    print("3. Customize user profiles in the 'profiles/' directory")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)