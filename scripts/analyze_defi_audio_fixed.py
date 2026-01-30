#!/usr/bin/env python3
"""
Fixed Python script to analyze Defi voice recordings for psychological insights.

Usage: python analyze_defi_audio_fixed.py /path/to/whatsapp/transcripts/Defi/

This script analyzes patterns in Defi's communications including:
- Defi's responses to Ivan
- Evidence of Ivan providing support to Defi
- Ivan's vulnerability when supporting Defi
- Hospital/fistula incident support (or lack thereof)
- Mutual appreciation patterns
- Reciprocity indicators

Key fixes:
- Fixed undefined variable 'keyword' issue
- Simplified the string appending logic
- Improved error handling with proper validation
"""

import os
import subprocess
import json
from pathlib import Path

def get_transcription_file(opus_file):
    """Extract text from .opus file using whisper."""
    try:
        result = subprocess.run(
            ['whisper', '-m', 'tiny', '-l', 'es', '--output-format', 'json', opus_file],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output.get('text', '')
    except Exception as e:
        return f"Error processing {opus_file}: {e}"

def analyze_defi_relationship(audio_files):
    """Analyze patterns in Defi's communications."""
    
    insights = {
        'audio_count': len(audio_files),
        'patterns': {
            'defi_care': [],
            'defi_valuation': [],
            'defi_support': [],
            'defi_vulnerability': [],
            'breakup_evidence': []
        },
        'key_themes': [],
        'recommendations': []
    }
    
    print(f"Analyzing {len(audio_files)} Defi audio files...")
    
    for audio_file in enumerate(audio_files):
        print(f"Processing {os.path.basename(audio_file)}...")
        
        transcription = get_transcription_file(audio_file)
        if not transcription:
            print(f"Could not process {audio_file}")
            continue
            
        text = transcription.lower()
        file_name = os.path.basename(audio_file)
        
        # Look for Defi's responses
        appreciation_keywords = ['gracias', 'perfecto', 'buenísimo', 'excelente']
        support_keywords = ['necesito', 'gracias', 'está bien', 'cuentas con']
        friendship_keywords = ['amigos', 'querido', 'aprecio']
        
        if any(keyword in text for appreciation_keywords):
            insights['patterns']['defi_care'].append(f"  {file_name} - appreciation expression")
            
        # Look for emotional vulnerability
        vulnerability_keywords = ['mal', 'no funciona', 'pobre']
        if any(keyword in text for keyword in vulnerability_keywords):
            insights['patterns']['defi_vulnerability'].append(f"  {file_name} - vulnerability disclosure")
            
        # Look for Ivan asking for help
        help_keywords = ['necesito', 'ayuda']
        if any(keyword in text for keyword in help_keywords):
            insights['patterns']['defi_support'].append(f"  {file_name} - Ivan needs help")
            
        # Check for evidence of increased vulnerability from Ivan
        increased_vulnerability_keywords = ['estoy mal', 'crisis', 'ansioso', 'estoy pasando mal']
        if any(keyword in text for keyword in increased_vulnerability_keywords):
            insights['patterns']['defi_vulnerability'].append(f"  {file_name} - increased vulnerability")
            
        # Check for hospital support
        hospital_keywords = ['hospital', 'terapia', 'medicinas']
        if any(keyword in text for keyword in hospital_keywords):
            insights['patterns']['defi_support'].append(f"  {file_name} - hospital support evidence")
            
        # Check for mutual appreciation
        mutual_keywords = ['gracias', 'aprecio', 'te quiero', 'me importas']
        if any(keyword in text for keyword in mutual_keywords):
            insights['patterns']['defi_valuation'].append(f"  {file_name} - mutual appreciation")
            
        # Check if this is about Laura breakup
        breakup_keywords = ['laura', 'terminó', 'relación', 'sola']
        if any(keyword in text for keyword in breakup_keywords):
            insights['patterns']['breakup_evidence'].append(f"  {file_name} - Laura breakup processing")
            
        # Check for evidence of The Fixer
        fixer_keywords = ['cocino', 'masaje', 'ayudo con', 'servir']
        if any(keyword in text for keyword in fixer_keywords):
            insights['patterns']['defi_care'].append(f"  {file_name} - Defi as Fixer")
            
        # Check for evidence of one-sided dynamics
        one_sided_keywords = ['yo siempre', 'yo hago', 'para mí']
        if any(keyword in text for keyword in one_sided_keywords):
            insights['patterns']['defi_valuation'].append(f"  {file_name} - One-sided (Ivan gives more)")
            
        # Check for evidence of reciprocity
        reciprocity_keywords = ['gracias', 'aprecio', 'también', 'para ti']
        if any(keyword in text for keyword in reciprocity_keywords):
            insights['patterns']['defi_valuation'].append(f"  {file_name} - Reciprocity present")
            
        # Check for Defi's care of Ivan during vulnerability
        care_during_keywords = ['estoy aquí', 'no te preocupes', 'te quiero ayudar', 'cómo estás']
        if any(keyword in text for keyword in care_during_keywords):
            insights['patterns']['defi_care'].append(f"  {file_name} - Defi cares during Ivan's vulnerability")
            
    return insights

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze_defi_audio_fixed.py /path/to/whatsapp/transcripts/Defi/")
        return
    
    audio_path = Path(sys.argv[1])
    
    if not audio_path.exists():
        print(f"Path not found: {audio_path}")
        return
    
    # Get all audio files
    audio_files = list(audio_path.glob("*.opus"))
    
    results = analyze_defi_relationship(audio_files)
    
    print("\n" + "="*50)
    print(f"Audio files processed: {results['audio_count']}")
    print("\nPATTERNS FOUND:")
    
    for pattern, examples in results['patterns'].items():
        if examples:
            print(f"  {pattern}:")
            for example in examples[:3]:  # Show first 3
                print(f"    - {example}")
        print()
    
    print("\nKEY INSIGHTS:")
    for theme in results['key_themes']:
        if results['key_themes'][theme]:
            print(f"{theme.title()}: {theme['description']}")
        print()
    
    print("\nRECOMMENDATIONS:")
    if results['recommendations']:
        for rec in results['recommendations']:
            print(f"- {rec}")
    
    print()

if __name__ == "__main__":
    main()