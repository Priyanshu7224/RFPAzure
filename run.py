#!/usr/bin/env python3
"""
Production runner for AI-Powered RFP BOM Generator
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_environment():
    """Check required environment variables"""
    required_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file with the required values.")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'exports', 'logs']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")

def main():
    """Main application runner"""
    print("🚀 AI-Powered RFP BOM Generator")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Import and run the Flask app
    try:
        from app import app
        
        # Get configuration
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"\n🌐 Starting server on http://{host}:{port}")
        print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
        print(f"🤖 Azure OpenAI endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT', 'Not configured')}")
        print("\n💡 Usage:")
        print("   1. Open the URL in your browser")
        print("   2. Upload your stock master file (Excel/CSV)")
        print("   3. Enter RFP line items")
        print("   4. Generate and export BOM")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except ImportError as e:
        logger.error(f"Failed to import Flask app: {e}")
        print("❌ Failed to start application. Please check dependencies.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
