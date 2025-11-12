"""
Integration tests for pyobfus using external projects (e.g., ml-research).

This allows testing pyobfus on real-world code without leaving the development environment.
"""

import sys
import tempfile
from pathlib import Path
from typing import List, Optional

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.parser import ASTParser
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.transformers.name_mangler import NameMangler
from pyobfus.transformers.string_encoder import StringEncoder
from pyobfus.core.generator import CodeGenerator


# Configure the path to your ml-research project
ML_RESEARCH_PATH = Path(r"c:\onedrive\msft\OneDrive - MSFT\rong\3-job\program\cardiac-ml-research")

# Add ml-research to Python path for importing
if ML_RESEARCH_PATH.exists():
    sys.path.insert(0, str(ML_RESEARCH_PATH))


class TestMLResearchModules:
    """Test pyobfus on real modules from ml-research project."""

    @pytest.fixture(autouse=True)
    def check_ml_research(self):
        """Check if ml-research project is available."""
        if not ML_RESEARCH_PATH.exists():
            pytest.skip(f"ml-research project not found at {ML_RESEARCH_PATH}")

    def obfuscate_file(
        self,
        file_path: Path,
        config: Optional[ObfuscationConfig] = None
    ) -> tuple[str, str]:
        """
        Obfuscate a Python file and return both original and obfuscated code.

        Args:
            file_path: Path to the Python file to obfuscate
            config: Obfuscation configuration (uses default if None)

        Returns:
            tuple: (original_code, obfuscated_code)
        """
        if config is None:
            config = ObfuscationConfig.community_edition()
            config.string_encoding = True  # Enable string encoding

        # Read original code
        original_code = file_path.read_text(encoding='utf-8')

        # Parse
        tree = ASTParser.parse_file(file_path)

        # Analyze
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        # Transform
        transformed_tree = tree

        # 1. Name mangling
        mangler = NameMangler(config, analyzer)
        transformed_tree = mangler.transform(transformed_tree)

        # 2. String encoding (if enabled)
        if config.string_encoding:
            encoder = StringEncoder(config, analyzer)
            transformed_tree = encoder.transform(transformed_tree)

        # Generate obfuscated code
        obfuscated_code = CodeGenerator.generate(transformed_tree)

        return original_code, obfuscated_code

    def test_obfuscation_preserves_functionality(self):
        """
        Test that obfuscated code maintains the same functionality as original.

        This is a template - customize for your specific ml-research modules.
        """
        # Example: Test a specific module from ml-research
        # Adjust the path to match your actual module structure

        # Find Python files in ml-research (non-recursively to start)
        python_files = list(ML_RESEARCH_PATH.glob("*.py"))

        if not python_files:
            pytest.skip("No Python files found in ml-research root")

        # Test the first file as an example
        test_file = python_files[0]
        print(f"\n🧪 Testing: {test_file.name}")

        try:
            original_code, obfuscated_code = self.obfuscate_file(test_file)

            # Verify obfuscation happened
            assert original_code != obfuscated_code
            assert len(obfuscated_code) > 0

            # Try to execute both (basic syntax check)
            # This catches syntax errors but not runtime errors
            compile(original_code, test_file.name, 'exec')
            compile(obfuscated_code, f"{test_file.name}_obf", 'exec')

            print(f"✅ Successfully obfuscated {test_file.name}")
            print(f"   Original size: {len(original_code)} chars")
            print(f"   Obfuscated size: {len(obfuscated_code)} chars")

        except Exception as e:
            pytest.fail(f"Failed to obfuscate {test_file.name}: {e}")

    def test_specific_ml_modules(self):
        """
        Test specific modules from ml-research.

        Customize this method to test your specific modules.
        """
        # Example: List of specific modules to test
        modules_to_test = [
            # "data_processing.py",
            # "model_training.py",
            # "utils/helpers.py",
        ]

        if not modules_to_test:
            pytest.skip("No specific modules configured for testing")

        for module_name in modules_to_test:
            module_path = ML_RESEARCH_PATH / module_name

            if not module_path.exists():
                print(f"⚠️  Skipping {module_name} (not found)")
                continue

            print(f"\n🧪 Testing: {module_name}")

            try:
                original_code, obfuscated_code = self.obfuscate_file(module_path)

                # Basic validations
                assert len(obfuscated_code) > 0
                compile(obfuscated_code, module_name, 'exec')

                print(f"✅ {module_name} obfuscated successfully")

            except Exception as e:
                pytest.fail(f"Failed to obfuscate {module_name}: {e}")

    def test_obfuscate_and_execute(self):
        """
        Test obfuscation and execution of a simple module.

        This template shows how to test execution equivalence.
        """
        # Create a simple test module
        test_code = """
def calculate_sum(a, b):
    return a + b

def calculate_product(a, b):
    return a * b

result_sum = calculate_sum(5, 3)
result_product = calculate_product(5, 3)
"""

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = Path(f.name)

        try:
            # Obfuscate
            original_code, obfuscated_code = self.obfuscate_file(temp_file)

            # Execute original
            original_namespace = {}
            exec(original_code, original_namespace)

            # Execute obfuscated
            obfuscated_namespace = {}
            exec(obfuscated_code, obfuscated_namespace)

            # Compare results
            assert original_namespace['result_sum'] == obfuscated_namespace['result_sum']
            assert original_namespace['result_product'] == obfuscated_namespace['result_product']

            print("✅ Execution equivalence verified")

        finally:
            temp_file.unlink()

    def test_batch_obfuscation(self):
        """
        Test batch obfuscation of multiple files from ml-research.
        """
        # Find all Python files (you can customize the pattern)
        python_files = list(ML_RESEARCH_PATH.rglob("*.py"))[:5]  # Test first 5 files

        if not python_files:
            pytest.skip("No Python files found in ml-research")

        results = {
            'success': [],
            'failed': [],
        }

        for file_path in python_files:
            # Skip __pycache__ and other special directories
            if '__pycache__' in str(file_path) or '.git' in str(file_path):
                continue

            print(f"\n🧪 Testing: {file_path.relative_to(ML_RESEARCH_PATH)}")

            try:
                original_code, obfuscated_code = self.obfuscate_file(file_path)

                # Verify compilation
                compile(obfuscated_code, file_path.name, 'exec')

                results['success'].append(file_path.name)
                print(f"✅ Success")

            except Exception as e:
                results['failed'].append((file_path.name, str(e)))
                print(f"❌ Failed: {e}")

        # Print summary
        print("\n" + "="*70)
        print(f"📊 Batch Obfuscation Summary")
        print("="*70)
        print(f"✅ Successful: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")

        if results['failed']:
            print("\nFailed files:")
            for filename, error in results['failed']:
                print(f"  - {filename}: {error[:50]}...")

        # Assert that at least some files succeeded
        assert len(results['success']) > 0, "No files were successfully obfuscated"


class TestMLResearchIntegration:
    """
    Integration tests that actually import and test ml-research modules.
    """

    @pytest.fixture(autouse=True)
    def check_ml_research(self):
        """Check if ml-research project is available."""
        if not ML_RESEARCH_PATH.exists():
            pytest.skip(f"ml-research project not found at {ML_RESEARCH_PATH}")

    def test_import_and_use_ml_module(self):
        """
        Example: Import a module from ml-research and test it.

        Customize this to match your actual ml-research structure.
        """
        pytest.skip("Template - customize for your ml-research modules")

        # Example template:
        # try:
        #     # Import a module from ml-research
        #     from your_ml_module import some_function
        #
        #     # Test the original function
        #     result_original = some_function(test_input)
        #
        #     # Now obfuscate the module and test
        #     # ... obfuscation logic ...
        #
        #     # Compare results
        #     assert result_original == result_obfuscated
        #
        # except ImportError as e:
        #     pytest.skip(f"Could not import ml-research module: {e}")


# Utility function for manual testing
def obfuscate_ml_research_module(
    module_path: str,
    output_path: Optional[str] = None,
    enable_string_encoding: bool = True
) -> str:
    """
    Manually obfuscate a module from ml-research.

    Usage:
        from integration_tests.test_external_projects import obfuscate_ml_research_module

        obfuscated = obfuscate_ml_research_module(
            "path/to/module.py",
            "path/to/output.py"
        )

    Args:
        module_path: Path to the module (relative to ml-research root)
        output_path: Where to save obfuscated code (optional)
        enable_string_encoding: Enable Base64 string encoding

    Returns:
        str: Obfuscated code
    """
    full_path = ML_RESEARCH_PATH / module_path

    if not full_path.exists():
        raise FileNotFoundError(f"Module not found: {full_path}")

    # Configure obfuscation
    config = ObfuscationConfig.community_edition()
    config.string_encoding = enable_string_encoding

    # Parse and analyze
    tree = ASTParser.parse_file(full_path)
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    # Transform
    transformed_tree = tree

    # Name mangling
    mangler = NameMangler(config, analyzer)
    transformed_tree = mangler.transform(transformed_tree)

    # String encoding
    if config.string_encoding:
        encoder = StringEncoder(config, analyzer)
        transformed_tree = encoder.transform(transformed_tree)

    # Generate
    obfuscated_code = CodeGenerator.generate(transformed_tree)

    # Save if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(obfuscated_code, encoding='utf-8')
        print(f"✅ Saved to: {output_file}")

    return obfuscated_code


if __name__ == "__main__":
    # Manual testing
    print("🧪 Integration Testing for ml-research")
    print("="*70)

    if not ML_RESEARCH_PATH.exists():
        print(f"❌ ml-research not found at: {ML_RESEARCH_PATH}")
        print("   Please update ML_RESEARCH_PATH in this file")
        sys.exit(1)

    print(f"✅ ml-research found at: {ML_RESEARCH_PATH}")
    print("\nRun with pytest:")
    print("  pytest integration_tests/test_external_projects.py -v")
