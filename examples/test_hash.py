#!/usr/bin/env python3
"""Test file hash implementation."""

import hashlib


def test_hash_generation():
    """Test that hash generation works as expected."""
    
    # Sample file content
    content = """FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
    
    # Calculate hash
    file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    hash_prefix = file_hash[:8]
    
    print("Content:")
    print(content)
    print("\nFull SHA256 hash:")
    print(file_hash)
    print("\nFirst 8 characters:")
    print(hash_prefix)
    
    # Test filename construction
    repo = "docker-test"
    filename = "Dockerfile"
    
    if '.' in filename:
        name_part, ext_part = filename.rsplit('.', 1)
        custom_filename = f"{repo}__{name_part}__{hash_prefix}.{ext_part}"
    else:
        custom_filename = f"{repo}__{filename}__{hash_prefix}"
    
    print(f"\nGenerated filename:")
    print(custom_filename)
    
    # Test with extension
    filename2 = "config.json"
    name_part, ext_part = filename2.rsplit('.', 1)
    custom_filename2 = f"{repo}__{name_part}__{hash_prefix}.{ext_part}"
    
    print(f"\nWith extension:")
    print(f"{filename2} → {custom_filename2}")


def test_collision_probability():
    """Show collision probability for 8-char hex."""
    
    possible_values = 16 ** 8
    print("\nHash Collision Analysis:")
    print(f"8 hex characters = {possible_values:,} possible values")
    print(f"That's {possible_values / 1_000_000:.1f} million combinations")
    
    # Birthday paradox approximation
    import math
    
    for n in [100, 1000, 10000, 100000]:
        # P(collision) ≈ 1 - e^(-n²/2m) where m = possible values
        prob = 1 - math.exp(-(n**2) / (2 * possible_values))
        print(f"With {n:,} files: {prob*100:.4f}% collision probability")


if __name__ == '__main__':
    test_hash_generation()
    test_collision_probability()
