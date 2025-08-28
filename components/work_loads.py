#!/usr/bin/env python3

# Import functions as requested
from work_loads.url_generator import generate_urls
from work_loads.en_word_generator import generate_random_words, gen_words_with_prefix_freq


def test_imported_functions():
    """Test the imported functions to verify they work correctly."""
    print("Testing imported functions...\n")
    
    # Test generate_urls function
    print("1. Testing generate_urls function:")
    try:
        urls = generate_urls(3, seed=42)  # Generate 3 URLs with fixed seed
        print(f"   ✓ Successfully generated {len(urls)} URLs:")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")
        print()
    except Exception as e:
        print(f"   ✗ Error testing generate_urls: {e}\n")
    
    # Test generate_random_words function
    print("2. Testing generate_random_words function:")
    try:
        words = generate_random_words(5, seed=42)  # Generate 5 words with fixed seed
        print(f"   ✓ Successfully generated {len(words)} random words:")
        print(f"   Words: {', '.join(words)}")
        print()
    except Exception as e:
        print(f"   ✗ Error testing generate_random_words: {e}\n")
    
    # Test gen_words_with_prefix_freq function
    print("3. Testing gen_words_with_prefix_freq function:")
    try:
        prefix_words = gen_words_with_prefix_freq(8, prefix_freq=0.7, seed=42)
        print(f"   ✓ Successfully generated {len(prefix_words)} words with prefix frequency:")
        print(f"   Words: {', '.join(prefix_words)}")
        print("   (Higher prefix frequency should show more words with common prefixes)")
        print()
    except Exception as e:
        print(f"   ✗ Error testing gen_words_with_prefix_freq: {e}\n")
    
    print("All function import tests completed!")


if __name__ == "__main__":
    test_imported_functions()