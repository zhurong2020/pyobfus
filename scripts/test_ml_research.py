#!/usr/bin/env python
"""
Convenient script to test pyobfus on ml-research modules.

Usage:
    # Test a specific file
    python scripts/test_ml_research.py path/to/module.py

    # Test all Python files
    python scripts/test_ml_research.py --all

    # Test and save obfuscated output
    python scripts/test_ml_research.py module.py --output obf/module_obf.py

    # Enable verbose mode
    python scripts/test_ml_research.py module.py -v
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import pyobfus
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfus.config import ObfuscationConfig
from pyobfus.core.parser import ASTParser
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.transformers.name_mangler import NameMangler
from pyobfus.transformers.string_encoder import StringEncoder
from pyobfus.core.generator import CodeGenerator


# Configure ml-research path
ML_RESEARCH_PATH = Path(r"c:\onedrive\msft\OneDrive - MSFT\rong\ml-research")


def obfuscate_file(file_path: Path, config: ObfuscationConfig, verbose: bool = False):
    """Obfuscate a single file."""
    if verbose:
        print(f"\n{'='*70}")
        print(f"🔄 Processing: {file_path.name}")
        print(f"{'='*70}")

    try:
        # Read original
        original_code = file_path.read_text(encoding='utf-8')
        original_lines = len(original_code.splitlines())

        if verbose:
            print(f"📄 Original: {original_lines} lines, {len(original_code)} bytes")

        # Parse
        tree = ASTParser.parse_file(file_path)

        # Analyze
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        if verbose:
            stats = analyzer.get_statistics()
            print(f"🔍 Analysis:")
            print(f"   - Total names: {stats['total_names']}")
            print(f"   - Obfuscatable: {stats['obfuscatable_names']}")
            print(f"   - Excluded: {stats['excluded_names']}")

        # Transform
        transformed_tree = tree

        # 1. Name mangling
        mangler = NameMangler(config, analyzer)
        transformed_tree = mangler.transform(transformed_tree)

        if verbose:
            print(f"🔧 Name transformations: {mangler.get_transformation_count()}")

        # 2. String encoding
        if config.string_encoding:
            encoder = StringEncoder(config, analyzer)
            transformed_tree = encoder.transform(transformed_tree)

            if verbose:
                enc_stats = encoder.get_statistics()
                print(f"🔐 String encoding:")
                print(f"   - Encoded: {enc_stats['encoded_strings']}")
                print(f"   - Skipped f-strings: {enc_stats['skipped_fstrings']}")

        # Generate
        obfuscated_code = CodeGenerator.generate(transformed_tree)
        obfuscated_lines = len(obfuscated_code.splitlines())

        if verbose:
            print(f"📝 Obfuscated: {obfuscated_lines} lines, {len(obfuscated_code)} bytes")

        # Verify compilation
        try:
            compile(obfuscated_code, file_path.name, 'exec')
            if verbose:
                print("✅ Compilation check: PASSED")
        except SyntaxError as e:
            print(f"❌ Syntax error in obfuscated code: {e}")
            return None

        return obfuscated_code

    except Exception as e:
        print(f"❌ Error processing {file_path.name}: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None


def test_single_file(file_path: Path, output_path: Path = None, verbose: bool = False):
    """Test obfuscation on a single file."""
    if not file_path.exists():
        # Try relative to ml-research
        file_path = ML_RESEARCH_PATH / file_path
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False

    # Configure obfuscation
    config = ObfuscationConfig.community_edition()
    config.string_encoding = True

    # Obfuscate
    obfuscated_code = obfuscate_file(file_path, config, verbose)

    if obfuscated_code is None:
        return False

    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(obfuscated_code, encoding='utf-8')
        print(f"\n💾 Saved to: {output_path}")

    print(f"\n✅ Successfully obfuscated {file_path.name}")
    return True


def test_all_files(verbose: bool = False, max_files: int = 10):
    """Test obfuscation on all Python files in ml-research."""
    if not ML_RESEARCH_PATH.exists():
        print(f"❌ ml-research not found at: {ML_RESEARCH_PATH}")
        return

    print(f"🔍 Scanning: {ML_RESEARCH_PATH}")
    print(f"   (Testing up to {max_files} files)")
    print()

    # Find Python files
    python_files = []
    for py_file in ML_RESEARCH_PATH.rglob("*.py"):
        # Skip special directories
        if any(part in py_file.parts for part in ['__pycache__', '.git', '.venv', 'venv']):
            continue
        python_files.append(py_file)

    if not python_files:
        print("❌ No Python files found")
        return

    # Limit to max_files
    python_files = python_files[:max_files]

    print(f"Found {len(python_files)} file(s) to test\n")

    # Configure
    config = ObfuscationConfig.community_edition()
    config.string_encoding = True

    # Test each file
    results = {'success': [], 'failed': []}

    for i, file_path in enumerate(python_files, 1):
        relative_path = file_path.relative_to(ML_RESEARCH_PATH)
        print(f"[{i}/{len(python_files)}] {relative_path}")

        obfuscated_code = obfuscate_file(file_path, config, verbose=False)

        if obfuscated_code:
            results['success'].append(str(relative_path))
            print("    ✅ Success")
        else:
            results['failed'].append(str(relative_path))
            print("    ❌ Failed")

    # Summary
    print(f"\n{'='*70}")
    print("📊 Test Summary")
    print(f"{'='*70}")
    print(f"✅ Successful: {len(results['success'])}/{len(python_files)}")
    print(f"❌ Failed: {len(results['failed'])}/{len(python_files)}")

    if results['failed']:
        print("\nFailed files:")
        for filename in results['failed']:
            print(f"  - {filename}")

    if verbose and results['success']:
        print("\nSuccessful files:")
        for filename in results['success']:
            print(f"  - {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Test pyobfus on ml-research modules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a specific file
  python scripts/test_ml_research.py data_loader.py

  # Test with full path
  python scripts/test_ml_research.py "path/to/module.py"

  # Test all files (up to 10)
  python scripts/test_ml_research.py --all

  # Test with output
  python scripts/test_ml_research.py module.py -o obf/module_obf.py

  # Verbose mode
  python scripts/test_ml_research.py module.py -v
        """
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='Python file to test (relative to ml-research or absolute path)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all Python files in ml-research'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output path for obfuscated code'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=10,
        help='Maximum number of files to test (default: 10)'
    )

    args = parser.parse_args()

    # Check ml-research path
    if not ML_RESEARCH_PATH.exists():
        print(f"❌ ml-research project not found at:")
        print(f"   {ML_RESEARCH_PATH}")
        print()
        print("Please update ML_RESEARCH_PATH in this script")
        sys.exit(1)

    print("🧪 pyobfus Integration Testing")
    print(f"📁 ml-research: {ML_RESEARCH_PATH}")
    print()

    # Test all or single file
    if args.all:
        test_all_files(args.verbose, args.max_files)
    elif args.file:
        success = test_single_file(
            Path(args.file),
            Path(args.output) if args.output else None,
            args.verbose
        )
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
