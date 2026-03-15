# check_environment.py
import os
import sys
from pathlib import Path


def check_environment():
    """Check if everything is set up correctly"""

    print("\n" + "=" * 60)
    print("ENVIRONMENT CHECK")
    print("=" * 60)

    # Check current directory
    current_dir = os.getcwd()
    print(f"\n📁 Current directory: {current_dir}")

    # Check for test image
    test_image = "Isuranga-pasport_bio.jpg"
    if os.path.exists(test_image):
        print(f"✅ Test image found: {test_image} ({os.path.getsize(test_image)} bytes)")
    else:
        print(f"❌ Test image not found: {test_image}")
        # Look for any JPG files
        jpg_files = list(Path('.').glob('*.jpg')) + list(Path('.').glob('*.jpeg'))
        if jpg_files:
            print(f"   Found other JPG files: {[f.name for f in jpg_files]}")

    # Check models directory
    if os.path.exists('models'):
        print(f"\n📁 Models directory found")
        model_files = list(Path('models').glob('*.h5'))
        if model_files:
            print(f"✅ Model files found:")
            for f in model_files:
                size_mb = os.path.getsize(f) / (1024 * 1024)
                print(f"   - {f.name} ({size_mb:.2f} MB)")
        else:
            print(f"❌ No .h5 model files found in models/")
    else:
        print(f"\n❌ Models directory not found")

    # Check uploads directory
    upload_dirs = ['static/uploads', 'static/uploads/photos', 'static/uploads/videos', 'static/uploads/documents']
    print(f"\n📁 Upload directories:")
    for d in upload_dirs:
        if os.path.exists(d):
            print(f"✅ {d}")
        else:
            print(f"❌ {d}")

    # Check Python packages
    print(f"\n📦 Python packages:")
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow {tf.__version__}")
    except:
        print("❌ TensorFlow not installed")

    try:
        import cv2
        print(f"✅ OpenCV {cv2.__version__}")
    except:
        print("❌ OpenCV not installed")

    try:
        import pytesseract
        print(f"✅ pytesseract installed")
    except:
        print("❌ pytesseract not installed")

    try:
        import PIL
        print(f"✅ Pillow {PIL.__version__}")
    except:
        print("❌ Pillow not installed")

    print("\n" + "=" * 60)
    print("CHECK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    check_environment()