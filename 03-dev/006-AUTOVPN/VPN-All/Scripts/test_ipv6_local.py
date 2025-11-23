#!/usr/bin/env python3
"""
Local test for IPv6 functionality in get_clean_ips_v2.py
"""

import os
import sys
import subprocess
import tempfile

def test_ipv6_local():
    """Test IPv6 functionality with local files"""
    print("Testing IPv6 functionality with local files...")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f_input:
        f_input.write("google.com\n")
        f_input.write("cloudflare.com\n") 
        f_input.write("facebook.com\n")
        input_file = f_input.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f_output:
        output_file = f_output.name
    
    try:
        # Test with IPv6 enabled
        print(f"Running with IPv6 enabled...")
        result = subprocess.run([
            sys.executable, "get_clean_ips_v2.py", 
            input_file, output_file, "--ipv6"
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout[-500:] if len(result.stdout) > 500 else result.stdout}")  # Last 500 chars
        
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        # Check if output file exists and has content
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"✓ Success! Generated {len(content.split())} IP-domain pairs")
                    print(f"Sample output:\n{content[:200]}...")
                    return True
                else:
                    print("✗ Output file is empty")
        else:
            print("✗ Output file was not created")
            
    except subprocess.TimeoutExpired:
        print("✗ Script timed out")
    except Exception as e:
        print(f"✗ Exception: {e}")
    finally:
        # Cleanup
        for file in [input_file, output_file]:
            if os.path.exists(file):
                os.remove(file)
    
    return False

if __name__ == "__main__":
    if test_ipv6_local():
        print("\n🎉 IPv6 functionality test PASSED!")
    else:
        print("\n⚠️  IPv6 functionality test FAILED!")
        sys.exit(1)