# check_model.py
import tensorflow as tf
import os


def check_model():
    """Check if the model file is valid"""
    model_path = 'models/final_Attention_CNN_V4.h5'

    print(f"\n{'=' * 50}")
    print(f"Checking model: {model_path}")
    print(f"{'=' * 50}")

    # Check if file exists
    if not os.path.exists(model_path):
        print(f"❌ Model file not found at: {model_path}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in models/: {os.listdir('models') if os.path.exists('models') else 'models folder not found'}")
        return False

    print(f"✅ Model file found: {os.path.getsize(model_path)} bytes")

    # Try to load the model
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
        print(f"✅ Model loaded successfully")
        print(f"   Model type: {type(model)}")
        print(f"   Input shape: {model.input_shape}")
        print(f"   Output shape: {model.output_shape}")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False


if __name__ == "__main__":
    check_model()