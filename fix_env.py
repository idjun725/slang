#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

# .env 파일 읽기 및 수정
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
env_path = os.path.join(backend_dir, '.env')

print(f"Reading .env file: {env_path}")

try:
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} bytes")
    print(f"First 100 chars: {repr(content[:100])}")
    
    # 줄바꿈 정리
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            cleaned_lines.append(line)
    
    print(f"\nCleaned lines: {len(cleaned_lines)}")
    for line in cleaned_lines:
        if 'OPENAI_API_KEY' in line:
            key_part = line.split('=', 1)
            if len(key_part) == 2:
                key_value = key_part[1].strip()
                print(f"\nFound OPENAI_API_KEY:")
                print(f"  Length: {len(key_value)}")
                print(f"  Starts with: {key_value[:20]}...")
                print(f"  Has newlines: {'\\n' in key_value}")
                print(f"  Has carriage return: {'\\r' in key_value}")
                
                # 정리된 .env 파일로 저장
                with open(env_path, 'w', encoding='utf-8') as f_out:
                    for clean_line in cleaned_lines:
                        f_out.write(clean_line + '\n')
                print(f"\n.env file cleaned and saved!")
                break
except Exception as e:
    print(f"Error: {e}")



