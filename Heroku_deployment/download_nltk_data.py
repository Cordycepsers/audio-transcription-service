#!/usr/bin/env python3
"""
Download required NLTK data for the application.
This script ensures all necessary NLTK corpora are available.
"""

import nltk
import os
import sys

def download_nltk_data():
    """Download required NLTK data packages."""
    
    # Set NLTK data path to a writable location
    nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)
    
    # Add the directory to NLTK's data path
    nltk.data.path.append(nltk_data_dir)
    
    # List of required NLTK packages
    required_packages = [
        'punkt',
        'punkt_tab',
        'stopwords',
        'wordnet',
        'averaged_perceptron_tagger'
    ]
    
    print("Downloading NLTK data packages...")
    
    for package in required_packages:
        try:
            print(f"Downloading {package}...")
            nltk.download(package, download_dir=nltk_data_dir, quiet=False)
            print(f"✅ Successfully downloaded {package}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to download {package}: {e}")
            # Don't fail the entire process for optional packages
            continue
    
    print("NLTK data download completed!")
    
    # Verify critical packages
    try:
        from nltk.tokenize import sent_tokenize, word_tokenize
        test_text = "Hello world. This is a test."
        sentences = sent_tokenize(test_text)
        words = word_tokenize(test_text)
        print(f"✅ NLTK verification successful: {len(sentences)} sentences, {len(words)} words")
    except Exception as e:
        print(f"❌ NLTK verification failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = download_nltk_data()
    sys.exit(0 if success else 1)