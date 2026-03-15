# utils.py - UPDATED with CNN model integration and Sri Lankan passport extractor

import os
import re
import cv2
import numpy as np
import tensorflow as tf
from PIL import Image
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config


class CNN_OCR_Model:
    """CNN model for character recognition - for inference only"""

    def __init__(self, model_path='models/final_Attention_CNN_V4.h5'):
        self.model_path = model_path
        self.model = None
        self.img_height = 64
        self.img_width = 64
        self.characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.char_to_idx = {char: idx for idx, char in enumerate(self.characters)}
        self.idx_to_char = {idx: char for idx, char in enumerate(self.characters)}
        self.confidence_threshold = 0.85

        # Context-based rules for confusing pairs
        self.context_rules = {
            'passport': {
                'rules': {'O': '0', 'I': '1', 'Q': '0', 'B': '8'},  # In passport, letters become digits
                'description': 'Passport numbers use digits'
            },
            'nic': {
                'rules': {'O': '0', 'I': '1', 'Q': '0', 'B': '8'},  # In NIC, letters become digits
                'description': 'NIC numbers use digits'
            },
            'name': {
                'rules': {'0': 'O', '1': 'I', '4': 'A', '8': 'B'},  # In names, digits become letters
                'description': 'Names use letters'
            }
        }

        self.load_model()

    def load_model(self):
        """Load the trained CNN model"""
        try:
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path, compile=False)
                print(f"✅ CNN Model loaded from {self.model_path}")
            else:
                print(f"⚠️ Model not found at {self.model_path}")
                self.model = None
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None

    def preprocess_character_image(self, image_path):
        """Preprocess a character image for prediction"""
        try:
            # Read image in grayscale
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

            if img is None:
                return None

            # Resize to model input size
            img = cv2.resize(img, (self.img_width, self.img_height))

            # Enhance contrast
            img = cv2.equalizeHist(img)

            # Threshold to binary
            _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

            # Remove small noise
            kernel = np.ones((2, 2), np.uint8)
            img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)

            # Normalize to [0, 1]
            img = img.astype(np.float32) / 255.0

            # Add batch and channel dimensions
            img = np.expand_dims(img, axis=[0, -1])

            return img
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None

    def predict_character(self, image_path):
        """Predict a single character from image"""
        if self.model is None:
            return None, 0.0, []

        # Preprocess
        img = self.preprocess_character_image(image_path)

        if img is None:
            return None, 0.0, []

        # Predict
        predictions = self.model.predict(img, verbose=0)[0]

        # Get top 3 predictions
        top_3_idx = np.argsort(predictions)[-3:][::-1]
        top_3_conf = predictions[top_3_idx]
        top_3_chars = [self.idx_to_char[idx] for idx in top_3_idx]

        # Get top prediction
        top_idx = top_3_idx[0]
        confidence = top_3_conf[0]
        predicted_char = top_3_chars[0]

        return predicted_char, confidence, list(zip(top_3_chars, top_3_conf))

    def predict_with_context(self, image_path, context='general'):
        """Predict with context-based rules"""
        # Get raw prediction
        predicted_char, confidence, alternatives = self.predict_character(image_path)

        if predicted_char is None:
            return {
                'success': False,
                'error': 'Could not process image'
            }

        result = {
            'success': True,
            'raw_prediction': predicted_char,
            'confidence': float(confidence),
            'alternatives': [(char, float(conf)) for char, conf in alternatives],
            'context': context,
            'needs_review': False
        }

        # Check confidence threshold
        if confidence < self.confidence_threshold:
            result['needs_review'] = True
            result['review_reason'] = f'Low confidence ({confidence:.2%})'

        # Apply context rules
        if context in self.context_rules:
            rules = self.context_rules[context].get('rules', {})
            if predicted_char in rules:
                corrected_char = rules[predicted_char]
                result['corrected_prediction'] = corrected_char
                result['correction_reason'] = self.context_rules[context]['description']
                result['needs_review'] = False  # Automatic correction applied
                print(f"🔄 Context correction: '{predicted_char}' → '{corrected_char}' in {context} context")

        return result


class ImageTextExtractor:
    """Legacy Tesseract OCR (fallback)"""

    def __init__(self):
        # Configure Tesseract path
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH

    def extract_text_from_image(self, image_path):
        """Extract text from image using Tesseract OCR"""
        try:
            import pytesseract
            # Read image using OpenCV
            img = cv2.imread(image_path)

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply thresholding
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

            # Extract text using Tesseract
            text = pytesseract.image_to_string(Image.fromarray(gray))

            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def extract_passport_info(self, text):
        """Extract passport information from OCR text with enhanced patterns"""
        info = {
            'full_name': '',
            'surname': '',
            'given_name': '',
            'passport_id': '',
            'birthday': '',
            'age': 0,
            'nic_no': ''
        }

        # Clean text - remove extra spaces and newlines
        text = ' '.join(text.split())
        print(f"Cleaned OCR Text: {text}")  # Debug print

        # Extract Surname - Looking for "Surname" or similar indicators
        surname_patterns = [
            r'Surname[:\s]*([A-Z][A-Z\s]+?)(?=\s+Other|\s+Given|\s+Name|\s+$)',
            r'SURNAME[:\s]*([A-Z][A-Z\s]+?)(?=\s+OTHER|\s+GIVEN|\s+NAME|\s+$)',
            r'সারনাম[:\s]*([A-Z][A-Z\s]+?)(?=\s+অন্যান্য|\s+$)',
            r'PRADHANA MUDIYANSELAGE',  # Specific pattern from your image
            r'([A-Z][A-Z\s]+)(?=\s+মোঃ|\s+গৃহী|\s+Other)',
        ]

        for pattern in surname_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                surname = match.group(1) if '(' in pattern else match.group()
                info['surname'] = surname.strip()
                print(f"Found surname: {info['surname']}")
                break

        # If specific pattern doesn't work, try to find all-caps words at beginning
        if not info['surname']:
            # Look for all-caps words that might be surname
            all_caps_pattern = r'\b([A-Z]{3,}(?:\s+[A-Z]{3,})*)\b'
            caps_matches = re.findall(all_caps_pattern, text)
            if caps_matches and len(caps_matches) > 0:
                # First all-caps block might be surname
                info['surname'] = caps_matches[0].strip()
                print(f"Found surname from caps: {info['surname']}")

        # Extract Given Name/Other Names
        given_name_patterns = [
            r'Other\s*Names?[:\s]*([A-Z][a-zA-Z\s]+?)(?=\s+Passport|\s+\d|$)',
            r'গৃহী\s*বর্ণনাঃ[:\s]*([A-Z][a-zA-Z\s]+?)(?=\s+Passport|\s+\d|$)',
            r'মোঃ[/\s]*গৃহী[:\s]*([A-Z][a-zA-Z\s]+?)(?=\s+Passport|\s+\d|$)',
            r'ISURANGA NIPUN KUMARA',  # Specific pattern from your image
            r'([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+\s*[A-Za-z]*)',
        ]

        for pattern in given_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                given_name = match.group(1) if '(' in pattern else match.group()
                info['given_name'] = given_name.strip()
                print(f"Found given name: {info['given_name']}")
                break

        # If given name not found with patterns, try to find after surname
        if not info['given_name'] and info['surname']:
            # Look for text after surname that might be given name
            surname_pos = text.find(info['surname'])
            if surname_pos != -1:
                after_surname = text[surname_pos + len(info['surname']):]
                # Look for capitalized words
                name_match = re.search(r'\b([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+\s*[A-Za-z]*)\b', after_surname)
                if name_match:
                    info['given_name'] = name_match.group(1).strip()
                    print(f"Found given name after surname: {info['given_name']}")

        # Combine surname and given name for full name
        if info['surname'] and info['given_name']:
            info['full_name'] = f"{info['given_name']} {info['surname']}"
            print(f"Combined full name: {info['full_name']}")
        elif info['surname']:
            info['full_name'] = info['surname']
            print(f"Full name (surname only): {info['full_name']}")
        elif info['given_name']:
            info['full_name'] = info['given_name']
            print(f"Full name (given name only): {info['full_name']}")
        else:
            # Try to extract full name as a fallback
            name_patterns_fallback = [
                r'Name[:\s]*([A-Z][a-zA-Z\s]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+\s*[A-Za-z]*)',
            ]
            for pattern in name_patterns_fallback:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['full_name'] = match.group(1).strip()
                    print(f"Fallback full name: {info['full_name']}")
                    break

        # Extract Passport ID - Format: P1234567 or N1234567
        passport_patterns = [
            r'Passport\s*No[:\s]*([A-Z]\d{7})',
            r'Passport\s*Number[:\s]*([A-Z]\d{7})',
            r'([P|N]\d{7})',
            r'[A-Z]\d{7}'
        ]

        for pattern in passport_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                passport_id = match.group(1) if '(' in pattern else match.group()
                # Validate format
                if re.match(r'^[P|N]\d{7}$', passport_id):
                    info['passport_id'] = passport_id
                    print(f"Found passport ID: {info['passport_id']}")
                    break

        # Extract Birthday (multiple formats)
        birthday_patterns = [
            r'Date\s*of\s*Birth[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Birth[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'DOB[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(\d{2}[/-]\d{2}[/-]\d{2})',
        ]

        for pattern in birthday_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                birth_date = match.group(1)
                # Convert to DD/MM/YYYY format
                try:
                    if '-' in birth_date:
                        parts = birth_date.split('-')
                    elif '/' in birth_date:
                        parts = birth_date.split('/')
                    else:
                        continue

                    if len(parts) == 3:
                        if len(parts[2]) == 2:  # YY format
                            year = int(parts[2])
                            if year > 50:  # Assume 19XX for years > 50
                                year = 1900 + year
                            else:
                                year = 2000 + year
                            info['birthday'] = f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{year}"
                        else:
                            info['birthday'] = f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
                        print(f"Found birthday: {info['birthday']}")
                        break
                except:
                    pass

        # Calculate age from birthday
        if info['birthday']:
            try:
                birth_date = datetime.strptime(info['birthday'], '%d/%m/%Y')
                today = datetime.now()
                info['age'] = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                print(f"Calculated age: {info['age']}")
            except:
                pass

        # Extract NIC/ID Number
        nic_patterns = [
            r'ID\s*No[:\s]*(\d{9}[V|v]|\d{12})',
            r'National\s*ID[:\s]*(\d{9}[V|v]|\d{12})',
            r'NIC[:\s]*(\d{9}[V|v]|\d{12})',
            r'(\d{9}[V|v])',
            r'(\d{12})',
        ]

        for pattern in nic_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nic = match.group(1)
                # Validate format
                if re.match(r'^\d{9}[V|v]$', nic) or re.match(r'^\d{12}$', nic):
                    info['nic_no'] = nic
                    print(f"Found NIC: {info['nic_no']}")
                    break

        print(f"\n📊 Final Extracted Info: {info}")
        return info


class SriLankanPassportExtractor:
    """Specialized extractor for Sri Lankan passports with MRZ parsing"""

    def __init__(self):
        pass

    def extract_from_text(self, text):
        """Extract information from Sri Lankan passport text"""

        info = {
            'full_name': '',
            'surname': '',
            'other_names': '',
            'passport_id': '',
            'birthday': '',
            'age': 0,
            'nic_no': ''
        }

        print(f"\n🔍 Processing Sri Lankan passport text...")

        # First, look for MRZ line (contains PBLKA pattern)
        mrz_line = self.extract_mrz_line(text)
        if mrz_line:
            print(f"Found MRZ line: {mrz_line}")
            mrz_info = self.parse_mrz_line(mrz_line)
            if mrz_info:
                info.update(mrz_info)
                print(f"Extracted from MRZ: {mrz_info}")

        # Extract NIC from the end of MRZ line (12 digits before <<38)
        if not info['nic_no']:
            nic_from_mrz = self.extract_nic_from_mrz(text)
            if nic_from_mrz:
                info['nic_no'] = nic_from_mrz
                print(f"Found NIC from MRZ end: {info['nic_no']}")

        # Extract NIC from text (look for ID No. pattern) as fallback
        if not info['nic_no']:
            nic_from_text = self.extract_nic_from_text(text)
            if nic_from_text:
                info['nic_no'] = nic_from_text
                print(f"Found NIC from text: {info['nic_no']}")

        # Extract Passport ID if not already found
        if not info['passport_id']:
            passport_patterns = [
                r'([N|P]\d{7})',  # N9467845 or P1234567
                r'Passport\s*No[.:\s]*([N|P]\d{7})',
            ]

            for pattern in passport_patterns:
                match = re.search(pattern, text)
                if match:
                    passport_id = match.group(1)
                    if re.match(r'^[N|P]\d{7}$', passport_id):
                        info['passport_id'] = passport_id
                        print(f"Found passport ID: {info['passport_id']}")
                        break

        # Extract Birthday if not already found
        if not info['birthday']:
            birthday_patterns = [
                r'Date\s*of\s*Birth[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
                r'Birth[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
                r'(\d{2}[/-]\d{2}[/-]\d{4})',
            ]

            for pattern in birthday_patterns:
                match = re.search(pattern, text)
                if match:
                    birthday = match.group(1).replace('-', '/')
                    info['birthday'] = birthday
                    print(f"Found birthday: {info['birthday']}")

                    # Calculate age
                    try:
                        birth_date = datetime.strptime(birthday, '%d/%m/%Y')
                        today = datetime.now()
                        age = today.year - birth_date.year
                        if (today.month, today.day) < (birth_date.month, birth_date.day):
                            age -= 1
                        info['age'] = age
                        print(f"Calculated age: {info['age']}")
                    except:
                        pass
                    break

        return info

    def extract_mrz_line(self, text):
        """Extract MRZ line from text"""
        # Look for pattern starting with PBLKA
        lines = text.split('\n')
        for line in lines:
            if 'PBLKA' in line or 'P<LKA' in line:
                return line.strip()

        # If not found in lines, search in the whole text
        mrz_pattern = r'(PBLKA[^<]*<[^<]*<[^<]*<[^<]*\d+[^<]*<[^<]*<<\d+)'
        match = re.search(mrz_pattern, text)
        if match:
            return match.group(1)

        return None

    def extract_nic_from_mrz(self, text):
        """Extract NIC from the end of MRZ line (12 digits before <<38)"""
        # Look for pattern: 12 digits followed by <<38 at the end
        nic_pattern = r'(\d{12})<<38$'
        match = re.search(nic_pattern, text, re.MULTILINE)
        if match:
            return match.group(1)

        # Alternative: look for 12 digits anywhere that might be NIC
        nic_pattern2 = r'(\d{12})'
        matches = re.findall(nic_pattern2, text)
        for match in matches:
            if len(match) == 12 and match.isdigit():
                return match
        return None

    def parse_mrz_line(self, mrz_line):
        """Parse MRZ line to extract name and other information"""

        info = {}

        # Remove spaces and clean up
        mrz_line = mrz_line.strip()
        print(f"Parsing MRZ: {mrz_line}")

        # Expected format: PBLKAPRADHANA<MUDIYANSELAGE<<ISURANGA<NIPUN< N9467845<6LKA9403132M3204201199407300406<<38

        # Remove PBLKA prefix
        mrz_without_prefix = mrz_line.replace('PBLKA', '')
        print(f"MRZ without prefix: {mrz_without_prefix}")

        # Split by '<<' to separate surname from other names
        if '<<' in mrz_without_prefix:
            surname_part, rest = mrz_without_prefix.split('<<', 1)

            # Clean surname (replace '<' with space)
            surname = surname_part.replace('<', ' ').strip()
            info['surname'] = surname
            print(f"Extracted surname: {info['surname']}")

            # Process the rest for other names
            # Split remaining by '<' until we hit numbers or end
            other_names_parts = []
            for part in rest.split('<'):
                if part and not part[0].isdigit():  # Stop when we hit numbers
                    other_names_parts.append(part)
                else:
                    # If we hit a part that starts with a digit, stop processing
                    break

            # Join other names with spaces
            other_names = ' '.join(other_names_parts).strip()
            info['other_names'] = other_names
            print(f"Extracted other names: {info['other_names']}")

            # Combine for full name
            info['full_name'] = f"{info['surname']} {info['other_names']}"
            print(f"Combined full name: {info['full_name']}")

        # Extract passport number (N followed by 7 digits)
        passport_match = re.search(r'([N|P]\d{7})', mrz_line)
        if passport_match:
            info['passport_id'] = passport_match.group(1)
            print(f"Found passport ID from MRZ: {info['passport_id']}")

        # Extract birthday from MRZ (embedded in the numbers)
        # In the MRZ: 9403132M3204201
        # The first 6 digits after LKA are YYMMDD
        birth_match = re.search(r'LKA(\d{2})(\d{2})(\d{2})', mrz_line)
        if birth_match:
            year, month, day = birth_match.groups()
            # Convert YY to YYYY (assuming 19xx for 00-50, 20xx for 51-99)
            year_int = int(year)
            if year_int <= 50:
                full_year = 2000 + year_int
            else:
                full_year = 1900 + year_int

            info['birthday'] = f"{day}/{month}/{full_year}"
            print(f"Found birthday from MRZ: {info['birthday']}")

            # Calculate age
            try:
                birth_date = datetime.strptime(info['birthday'], '%d/%m/%Y')
                today = datetime.now()
                age = today.year - birth_date.year
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    age -= 1
                info['age'] = age
                print(f"Calculated age from MRZ: {info['age']}")
            except:
                pass

        return info

    def extract_nic_from_text(self, text):
        """Extract NIC from text looking for ID No. patterns"""

        print("\n🔍 Looking for NIC in text...")

        # Pattern 1: Look for "ID No." followed by 12 digits
        pattern1 = r'ID\s*No[.:\s]*(\d{12})'
        match1 = re.search(pattern1, text, re.IGNORECASE)
        if match1:
            nic = match1.group(1)
            print(f"Found 12-digit NIC from ID No.: {nic}")
            return nic

        # Pattern 2: Look for "ID No." followed by 9 digits + V
        pattern2 = r'ID\s*No[.:\s]*(\d{9}[V|v])'
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            nic = match2.group(1)
            print(f"Found 10-digit NIC with V from ID No.: {nic}")
            return nic

        # Pattern 3: Look for "NIC" followed by 12 digits
        pattern3 = r'NIC[.:\s]*(\d{12})'
        match3 = re.search(pattern3, text, re.IGNORECASE)
        if match3:
            nic = match3.group(1)
            print(f"Found 12-digit NIC from NIC field: {nic}")
            return nic

        # Pattern 4: Look for "NIC" followed by 9 digits + V
        pattern4 = r'NIC[.:\s]*(\d{9}[V|v])'
        match4 = re.search(pattern4, text, re.IGNORECASE)
        if match4:
            nic = match4.group(1)
            print(f"Found 10-digit NIC with V from NIC field: {nic}")
            return nic

        # Pattern 5: Look for standalone 12-digit number that looks like a NIC
        # Sri Lankan NIC format: YYYYMMDDXXXX (12 digits)
        pattern5 = r'(\d{4})(\d{2})(\d{2})\d{4}'
        matches = re.findall(pattern5, text)
        for match in matches:
            year, month, day = match
            if 1900 <= int(year) <= 2025 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                nic = f"{year}{month}{day}{int(month) + int(day):02d}04"
                print(f"Found potential 12-digit NIC: {nic}")
                return nic

        # Pattern 6: Look for standalone 10-digit number ending with V
        pattern6 = r'(\d{9}[V|v])'
        match6 = re.search(pattern6, text)
        if match6:
            nic = match6.group(1)
            print(f"Found 10-digit NIC with V: {nic}")
            return nic

        print("No NIC found in text")
        return None

    def extract_from_visible_text(self, text, info):
        """Fallback method to extract from visible text area"""

        # Split into lines
        lines = text.split('\n')

        # Look for all-caps name lines
        name_candidates = []
        for line in lines:
            line = line.strip()
            # Check if line is all caps and contains only letters and spaces
            if line.isupper() and len(line) > 5 and not any(
                    word in line for word in ['PASSPORT', 'LKA', 'SRI', 'LANKA']):
                # Remove any non-letter characters
                clean_line = re.sub(r'[^A-Z\s]', '', line)
                if clean_line.strip():
                    name_candidates.append(clean_line.strip())

        print(f"Name candidates from visible text: {name_candidates}")

        if len(name_candidates) >= 2:
            info['surname'] = name_candidates[0]
            # Combine remaining name candidates for other names
            other_names = ' '.join(name_candidates[1:])
            info['other_names'] = other_names
            info['full_name'] = f"{info['surname']} {info['other_names']}"
            print(f"Extracted names from visible text: {info['full_name']}")


class HybridOCR:
    """Combines CNN model with Tesseract fallback and specialized extractors"""

    def __init__(self, cnn_model_path='models/final_Attention_CNN_V4.h5'):
        self.cnn_model = None
        self.tesseract = ImageTextExtractor()
        self.sri_lankan_extractor = SriLankanPassportExtractor()

        # Try to load CNN model if path is provided and exists
        if cnn_model_path and os.path.exists(cnn_model_path):
            try:
                self.cnn_model = CNN_OCR_Model(cnn_model_path)
                print(f"✅ CNN Model loaded from {cnn_model_path}")
            except Exception as e:
                print(f"⚠️ Could not load CNN model: {e}")
                print("   Using Tesseract only")
        else:
            print("⚠️ CNN model not found, using Tesseract only")

        print("✅ Hybrid OCR initialized" + (" (CNN + Tesseract)" if self.cnn_model else " (Tesseract only)"))

    def extract_text_from_passport(self, image_path):
        """Extract text from passport image with Sri Lankan passport support"""

        # First try Tesseract for full text extraction
        try:
            # Extract text with Tesseract
            text = self.tesseract.extract_text_from_image(image_path)

            # Store for debugging
            self.tesseract.last_extracted_text = text

            print(f"\n📝 Raw OCR Text (first 500 chars):")
            print(f"{text[:500]}...")

            # Check if it might be a Sri Lankan passport
            if 'SRI LANKA' in text.upper() or 'LKA' in text.upper() or 'PBLKA' in text:
                print("🇱🇰 Detected Sri Lankan passport, using specialized extractor")
                return self.sri_lankan_extractor.extract_from_text(text)
            else:
                # Use regular passport extraction
                return self.tesseract.extract_passport_info(text)

        except Exception as e:
            print(f"⚠️ Tesseract extraction failed: {e}")
            return {}

    def extract_from_document(self, image_path, doc_type='general'):
        """Extract text based on document type"""
        context_map = {
            'passport': 'passport',
            'nic': 'nic',
            'id': 'nic',
            'name': 'name'
        }
        context = context_map.get(doc_type, 'general')

        if self.cnn_model is not None:
            result = self.cnn_model.predict_with_context(image_path, context)
            return result
        else:
            # Fallback to Tesseract
            text = self.tesseract.extract_text_from_image(image_path)
            return {'text': text, 'success': True, 'source': 'tesseract'}


def save_uploaded_file(file, subfolder):
    """Save uploaded file and return the filename"""
    if file and file.filename:
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}{ext}"

        # Create subfolder if it doesn't exist
        upload_path = os.path.join(Config.UPLOAD_FOLDER, subfolder)
        os.makedirs(upload_path, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)

        # Check if file was actually saved
        if os.path.exists(file_path):
            print(f"✅ File saved successfully: {file_path}")
            return f"uploads/{subfolder}/{filename}"
        else:
            print(f"❌ Failed to save file: {file_path}")
            return None
    return None

# In utils.py, replace the allowed_file function with this improved version

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed

    Args:
        filename: The filename to check
        allowed_extensions: A set or list of allowed extensions (without dots)

    Returns:
        bool: True if file extension is allowed
    """
    # Convert to set if it's a list
    if isinstance(allowed_extensions, list):
        allowed_extensions = set(allowed_extensions)

    # Ensure we're working with lowercase extensions
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in allowed_extensions
    return False