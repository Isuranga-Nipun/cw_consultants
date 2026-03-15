# test_ocr_direct.py - Updated with better debug output and "Other Names" field

import os
import sys
from utils import HybridOCR
import json


def test_ocr_direct(image_path, doc_type='passport'):
    """Test OCR directly without Flask"""

    print(f"\n{'=' * 60}")
    print(f"🔍 OCR DIRECT TEST")
    print(f"{'=' * 60}")
    print(f"Testing OCR on: {image_path}")
    print(f"Document type: {doc_type}")
    print(f"{'=' * 60}")

    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ Error: File not found: {image_path}")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Please make sure the path is correct")
        return False

    file_size = os.path.getsize(image_path)
    print(f"✅ File found: {file_size} bytes")
    print(f"   Absolute path: {os.path.abspath(image_path)}")

    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    file_ext = os.path.splitext(image_path)[1]
    if file_ext.lower() not in [ext.lower() for ext in valid_extensions]:
        print(f"⚠️ Warning: File extension '{file_ext}' may not be supported")

    # Initialize OCR
    try:
        model_path = 'models/final_Attention_CNN_V4.h5'
        if not os.path.exists(model_path):
            print(f"⚠️ Model not found at {model_path}, using Tesseract only")
            ocr = HybridOCR(None)  # Pass None to use Tesseract only
        else:
            ocr = HybridOCR(model_path)
            print(f"✅ Model loaded from: {model_path}")
        print("✅ OCR engine initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OCR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Process image
    try:
        print(f"\n📄 Processing image with {doc_type.upper()} OCR...")

        if doc_type == 'passport':
            result = ocr.extract_text_from_passport(image_path)

            print(f"\n📄 Passport OCR Result:")
            print(f"   {'─' * 50}")
            print(f"   Full Name:     {result.get('full_name', 'N/A')}")
            print(f"   Surname:       {result.get('surname', 'N/A')}")
            print(f"   Other Names:   {result.get('other_names', 'N/A')}")
            print(f"   Passport ID:   {result.get('passport_id', 'N/A')}")
            print(f"   Birthday:      {result.get('birthday', 'N/A')}")
            print(f"   Age:           {result.get('age', 'N/A')}")
            print(f"   NIC:           {result.get('nic_no', 'N/A')}")
            print(f"   {'─' * 50}")

            # Show raw OCR text for debugging
            if hasattr(ocr.tesseract, 'last_extracted_text'):
                print(f"\n📝 Raw OCR Text (full):")
                print(f"   {ocr.tesseract.last_extracted_text}")

        else:
            result = ocr.extract_from_document(image_path, doc_type)
            print(f"\n📄 {doc_type.capitalize()} OCR Result:")
            print(f"   {'─' * 50}")
            print(f"   Success:      {result.get('success', False)}")
            print(f"   Prediction:   {result.get('raw_prediction', 'N/A')}")
            print(f"   Confidence:   {result.get('confidence', 0):.2%}")
            print(f"   Needs Review: {result.get('needs_review', False)}")

            if result.get('alternatives'):
                print(f"   Alternatives: {result['alternatives']}")

        print(f"\n{'=' * 60}")
        print(f"✅ OCR TEST COMPLETED SUCCESSFULLY")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ OCR processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_image():
    """Test with the specific image path"""
    image_path = "test/Isuranga-pasport_bio.jpg"
    print(f"\n{'=' * 60}")
    print(f"🎯 TESTING SPECIFIC IMAGE")
    print(f"{'=' * 60}")
    print(f"Image path: {image_path}")

    # Check if test directory exists
    if not os.path.exists("test"):
        print("📁 Creating test directory...")
        os.makedirs("test", exist_ok=True)
        print(f"✅ Created test directory: {os.path.abspath('test')}")
        print(f"⚠️ Please place your test image at: {os.path.abspath(image_path)}")
        return

    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Test image not found at: {os.path.abspath(image_path)}")
        print(f"\nPlease place your test image in the 'test' folder:")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Expected path: {os.path.abspath('test')}")
        print(f"\nFiles in test directory:")
        if os.path.exists("test"):
            files = os.listdir("test")
            if files:
                for f in files:
                    print(f"   - {f}")
            else:
                print("   (empty)")
        return

    # Run the test
    test_ocr_direct(image_path, 'passport')


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OCR DIRECT TEST SCRIPT")
    print("=" * 60)

    # Check command line arguments
    if len(sys.argv) > 1:
        # Use provided image path
        image_path = sys.argv[1]
        doc_type = sys.argv[2] if len(sys.argv) > 2 else 'passport'
        test_ocr_direct(image_path, doc_type)
    else:
        # Use default test image
        test_specific_image()

    print("\n" + "=" * 60)