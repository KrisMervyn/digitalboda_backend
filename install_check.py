#!/usr/bin/env python3
"""
Check if system dependencies are installed for photo verification
"""

import subprocess
import sys

def check_system_dependencies():
    """Check if required system packages are installed"""
    
    print("🔍 Checking System Dependencies for Photo Verification")
    print("=" * 60)
    
    # Required packages to check
    packages_to_check = [
        ('cmake', 'cmake --version'),
        ('build-essential', 'gcc --version'),
        ('libopenblas', 'dpkg -l | grep libopenblas'),
        ('tesseract', 'tesseract --version'),
        ('dlib', 'dpkg -l | grep libdlib'),
    ]
    
    results = {}
    
    for package_name, check_command in packages_to_check:
        try:
            result = subprocess.run(
                check_command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ {package_name:15}: INSTALLED")
                results[package_name] = True
            else:
                print(f"❌ {package_name:15}: NOT FOUND")
                results[package_name] = False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {package_name:15}: TIMEOUT")
            results[package_name] = False
        except Exception as e:
            print(f"❓ {package_name:15}: ERROR - {e}")
            results[package_name] = False
    
    print("\n" + "=" * 60)
    
    installed_count = sum(results.values())
    total_count = len(results)
    
    print(f"📊 Summary: {installed_count}/{total_count} dependencies installed")
    
    if installed_count >= 3:  # cmake, build-essential, and at least one other
        print("🎉 Sufficient dependencies for photo verification!")
        return True
    else:
        print("⚠️  More dependencies needed for full functionality")
        return False

if __name__ == "__main__":
    check_system_dependencies()