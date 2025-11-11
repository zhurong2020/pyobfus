"""
Direct test of Pro features without CLI.

NOTE: This test is EXCLUDED from CI via pyproject.toml because it requires
pyobfus_pro module which is not in the public repository.

To run locally (with pyobfus_pro available):
    python -m pytest tests/test_pro_features.py -v
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pyobfus.config import ObfuscationConfig
from pyobfus.core.parser import ASTParser
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.transformers.name_mangler import NameMangler
from pyobfus_pro.string_aes import StringAESEncryptor
from pyobfus_pro.anti_debug import AntiDebugInjector


def test_pro_features():
    """Test Pro features directly."""
    # Input file
    input_file = Path("examples/pro_example.py")
    output_file = Path("examples/pro_example_test.py")

    print(f"Testing Pro features on: {input_file}\n")

    # Parse
    tree = ASTParser.parse_file(input_file)
    print("[OK] Parsed AST")

    # Configure for Pro (now with fixed infrastructure name handling)
    config = ObfuscationConfig.pro_edition()
    config.string_encryption = True  # Fixed: infrastructure names now excluded
    config.anti_debug = True  # Fixed: infrastructure names now excluded
    print(
        f"[OK] Config: level={config.level}, string_encryption={config.string_encryption}, anti_debug={config.anti_debug}"
    )

    # Analyze
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)
    stats = analyzer.get_statistics()
    print(f"[OK] Analyzed: {stats['obfuscatable_names']} names to obfuscate")

    # Transform 1: Name mangling
    mangler = NameMangler(config, analyzer)
    tree = mangler.transform(tree)
    print(f"[OK] Name mangling: {mangler.get_transformation_count()} transformations")

    # Transform 2: String encryption (if enabled)
    if config.string_encryption:
        encryptor = StringAESEncryptor(config, analyzer)
        tree = encryptor.transform(tree)
        enc_stats = encryptor.get_statistics()
        print(
            f"[OK] String encryption: {enc_stats['encrypted_strings']} strings encrypted ({enc_stats['total_bytes']} bytes)"
        )
        assert enc_stats["encrypted_strings"] > 0
    else:
        print("[SKIP] String encryption disabled")

    # Transform 3: Anti-debugging (if enabled)
    if config.anti_debug:
        anti_debug = AntiDebugInjector(config, analyzer)
        tree = anti_debug.transform(tree)
        debug_stats = anti_debug.get_statistics()
        print(f"[OK] Anti-debugging: {debug_stats['injected_functions']} function checks")
        assert debug_stats["injected_functions"] > 0
    else:
        print("[SKIP] Anti-debugging disabled")

    # Generate
    CodeGenerator.generate_to_file(tree, output_file)
    print(f"\n[OK] Output written to: {output_file}")

    # Verify the file was created
    assert output_file.exists()

    # Clean up
    if output_file.exists():
        output_file.unlink()


if __name__ == "__main__":
    try:
        # Run the test
        test_pro_features()
        print("\n" + "=" * 60)
        print("[SUCCESS] All Pro features working correctly!")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
