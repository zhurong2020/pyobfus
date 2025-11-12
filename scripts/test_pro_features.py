#!/usr/bin/env python3
"""
Test script for Pro features (AES-256 encryption + Anti-debugging).

This script tests Pro features on real-world code from external projects
to ensure they work correctly in production scenarios.

Usage:
    python scripts/test_pro_features.py <file_path> [options]
    python scripts/test_pro_features.py --all [options]

Examples:
    # Test a single file
    python scripts/test_pro_features.py applications/clinical_menu.py -v

    # Test all files (limit to 5)
    python scripts/test_pro_features.py --all --max-files 5 -v

    # Test with specific Pro features
    python scripts/test_pro_features.py file.py --aes-only
    python scripts/test_pro_features.py file.py --anti-debug-only
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyobfus.core.parser import ASTParser
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.config import ObfuscationConfig
from pyobfus.exceptions import PyObfusError

# Pro features
try:
    from pyobfus_pro.string_aes import StringAESEncryptor
    from pyobfus_pro.anti_debug import AntiDebugInjector

    PRO_AVAILABLE = True
except ImportError:
    PRO_AVAILABLE = False
    print("⚠️  Warning: Pro features not available. Install pyobfus_pro to test Pro features.")


class UTF8Writer:
    """UTF-8 wrapper for Windows console output."""

    def __init__(self, stream):
        self.stream = stream
        self.encoding = "utf-8"

    def write(self, text):
        if isinstance(text, str):
            self.stream.buffer.write(text.encode("utf-8"))
        else:
            self.stream.buffer.write(text)

    def flush(self):
        self.stream.flush()


# Wrap stdout for UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = UTF8Writer(sys.stdout)


# Path to cardiac-ml-research project
ML_RESEARCH_BASE = Path(r"c:\onedrive\msft\OneDrive - MSFT\rong\3-job\program\cardiac-ml-research")


def obfuscate_with_pro_features(
    file_path: Path,
    aes_encryption: bool = True,
    anti_debug: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Obfuscate a file using Pro features.

    Args:
        file_path: Path to the Python file to obfuscate
        aes_encryption: Enable AES-256 string encryption
        anti_debug: Enable anti-debugging checks
        verbose: Print detailed information

    Returns:
        dict: Test results including success status, stats, and any errors
    """
    result = {
        "file": str(file_path),
        "success": False,
        "error": None,
        "stats": {},
        "obfuscated_code": None,
    }

    try:
        if verbose:
            print(f"\n{'=' * 70}")
            print(f"📄 Testing: {file_path.name}")
            print(f"{'=' * 70}")

        # Read and parse the file
        tree = ASTParser.parse_file(file_path)
        original_code = file_path.read_text(encoding="utf-8")
        line_count = len(original_code.splitlines())

        if verbose:
            print(f"📊 Original: {line_count} lines, {len(original_code)} bytes")

        # Configure for Pro features
        config = ObfuscationConfig()
        config.level = "pro"
        config.string_encryption = aes_encryption
        config.anti_debug = anti_debug

        # Analyze symbols
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        if verbose:
            stats = analyzer.get_statistics()
            print(f"🔍 Analysis:")
            print(f"   - Total names: {stats['total_names']}")
            print(f"   - Obfuscatable: {stats['obfuscatable_names']}")
            print(f"   - Excluded: {stats['excluded_names']}")

        # Transform with Pro features
        transformed_tree = tree

        # Apply AES encryption
        if aes_encryption and PRO_AVAILABLE:
            if verbose:
                print(f"\n🔐 Applying AES-256 encryption...")
            encryptor = StringAESEncryptor(config, analyzer)
            transformed_tree = encryptor.transform(transformed_tree)
            aes_stats = encryptor.get_statistics()
            result["stats"]["aes"] = aes_stats
            if verbose:
                print(f"   ✅ Encrypted strings: {aes_stats['encrypted_strings']}")
                print(f"   ✅ Total encrypted bytes: {aes_stats['total_bytes']}")
                if aes_stats["skipped_fstrings"] > 0:
                    print(f"   ⏭️  Skipped f-strings: {aes_stats['skipped_fstrings']}")

        # Apply anti-debugging
        if anti_debug and PRO_AVAILABLE:
            if verbose:
                print(f"\n🛡️  Applying anti-debugging checks...")
            injector = AntiDebugInjector(config, analyzer)
            transformed_tree = injector.transform(transformed_tree)
            anti_debug_stats = injector.get_statistics()
            result["stats"]["anti_debug"] = anti_debug_stats
            if verbose:
                print(f"   ✅ Functions injected: {anti_debug_stats['injected_functions']}")

        # Generate obfuscated code
        obfuscated_code = CodeGenerator.generate(transformed_tree)
        result["obfuscated_code"] = obfuscated_code

        if verbose:
            print(f"\n📈 Result:")
            print(f"   - Obfuscated: {len(obfuscated_code.splitlines())} lines")
            print(f"   - Size: {len(obfuscated_code)} bytes")

        # Verify the obfuscated code is valid Python
        try:
            ast.parse(obfuscated_code)
            if verbose:
                print(f"   ✅ Syntax valid")
        except SyntaxError as e:
            raise PyObfusError(f"Generated invalid Python syntax: {e}")

        # Try to execute the obfuscated code (basic smoke test)
        try:
            # Disable trace for anti-debug testing
            old_trace = sys.gettrace()
            sys.settrace(None)
            try:
                compile(obfuscated_code, "<obfuscated>", "exec")
                if verbose:
                    print(f"   ✅ Compiles successfully")
            finally:
                sys.settrace(old_trace)
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Compilation warning: {e}")

        result["success"] = True
        if verbose:
            print(f"\n✅ SUCCESS: Pro features test passed")

    except Exception as e:
        result["error"] = str(e)
        if verbose:
            print(f"\n❌ FAILED: {e}")
            import traceback

            traceback.print_exc()

    return result


def test_single_file(
    file_path: Path,
    aes_encryption: bool = True,
    anti_debug: bool = True,
    verbose: bool = False,
) -> bool:
    """Test Pro features on a single file."""
    result = obfuscate_with_pro_features(file_path, aes_encryption, anti_debug, verbose)
    return result["success"]


def test_all_files(
    max_files: Optional[int] = None,
    aes_encryption: bool = True,
    anti_debug: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Test Pro features on multiple files from cardiac-ml-research."""
    if not ML_RESEARCH_BASE.exists():
        print(f"❌ Error: cardiac-ml-research not found at {ML_RESEARCH_BASE}")
        return {"total": 0, "passed": 0, "failed": 0, "results": []}

    # Find all Python files
    python_files = sorted(ML_RESEARCH_BASE.rglob("*.py"))

    # Exclude certain patterns
    excluded_patterns = ["__pycache__", ".venv", "venv", "test_", "_test.py"]
    python_files = [
        f
        for f in python_files
        if not any(pattern in str(f) for pattern in excluded_patterns)
    ]

    if max_files:
        python_files = python_files[:max_files]

    print(f"\n{'=' * 70}")
    print(f"🧪 Testing Pro Features on {len(python_files)} files")
    print(f"{'=' * 70}")
    print(f"Features: ", end="")
    if aes_encryption:
        print("AES-256 Encryption ", end="")
    if anti_debug:
        print("Anti-Debugging", end="")
    print()

    results = []
    passed = 0
    failed = 0

    for i, file_path in enumerate(python_files, 1):
        if not verbose:
            print(f"\n[{i}/{len(python_files)}] {file_path.name}... ", end="", flush=True)

        result = obfuscate_with_pro_features(file_path, aes_encryption, anti_debug, verbose)
        results.append(result)

        if result["success"]:
            passed += 1
            if not verbose:
                print("✅ PASS")
        else:
            failed += 1
            if not verbose:
                print(f"❌ FAIL: {result['error']}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"📊 Pro Features Test Summary")
    print(f"{'=' * 70}")
    print(f"Total files: {len(python_files)}")
    print(f"✅ Passed: {passed} ({passed / len(python_files) * 100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed / len(python_files) * 100:.1f}%)")

    if failed > 0:
        print(f"\n❌ Failed files:")
        for result in results:
            if not result["success"]:
                print(f"   - {Path(result['file']).name}: {result['error']}")

    return {"total": len(python_files), "passed": passed, "failed": failed, "results": results}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Pro features on real-world Python code"
    )
    parser.add_argument("file", nargs="?", help="Python file to test (relative to ml-research)")
    parser.add_argument("--all", action="store_true", help="Test all files")
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to test (with --all)"
    )
    parser.add_argument("--aes-only", action="store_true", help="Test only AES encryption")
    parser.add_argument(
        "--anti-debug-only", action="store_true", help="Test only anti-debugging"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not PRO_AVAILABLE:
        print("❌ Error: Pro features not available")
        print("Please install pyobfus in development mode: pip install -e .")
        return 1

    # Determine which features to test
    aes_encryption = not args.anti_debug_only
    anti_debug = not args.aes_only

    if args.all:
        # Test all files
        summary = test_all_files(args.max_files, aes_encryption, anti_debug, args.verbose)
        return 0 if summary["failed"] == 0 else 1
    elif args.file:
        # Test single file
        file_path = ML_RESEARCH_BASE / args.file
        if not file_path.exists():
            print(f"❌ Error: File not found: {file_path}")
            return 1

        success = test_single_file(file_path, aes_encryption, anti_debug, args.verbose)
        return 0 if success else 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
