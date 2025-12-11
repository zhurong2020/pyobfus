"""
Configuration templates for common project types.

Provides pre-configured YAML templates for Django, Flask, library, and general projects.
"""

from typing import Dict

# Template definitions
TEMPLATES: Dict[str, str] = {
    "django": """# pyobfus configuration for Django projects
# Generated with: pyobfus --init-config django

obfuscation:
  level: community

  # Preserve Django-required names
  exclude_names:
    # Django settings
    - settings
    - urlpatterns
    - app_name
    - default_app_config
    # Django models
    - Meta
    - objects
    - DoesNotExist
    - MultipleObjectsReturned
    # Django views
    - get_queryset
    - get_context_data
    - form_valid
    - form_invalid
    # Django admin
    - list_display
    - list_filter
    - search_fields
    - ordering
    # Django forms
    - clean
    - clean_*
    - is_valid
    # Common Django patterns
    - request
    - response
    - queryset

  # Skip Django-specific files
  exclude_patterns:
    - "**/migrations/*.py"
    - "**/migrations/**/*.py"
    - "manage.py"
    - "**/settings/*.py"
    - "**/settings.py"
    - "**/*_settings.py"
    - "**/wsgi.py"
    - "**/asgi.py"
    - "**/apps.py"
    - "**/admin.py"
    - "**/tests/*.py"
    - "**/tests.py"
    - "**/__init__.py"

  # String encoding for sensitive data
  string_encoding: true

  # Keep docstrings for Django admin
  remove_docstrings: false
  remove_comments: true

# Verbose output recommended for first run
verbose: false
""",
    "flask": """# pyobfus configuration for Flask projects
# Generated with: pyobfus --init-config flask

obfuscation:
  level: community

  # Preserve Flask-required names
  exclude_names:
    # Flask app
    - app
    - create_app
    - init_app
    # Flask routes
    - route
    - endpoint
    - methods
    - url_for
    # Flask blueprints
    - blueprint
    - bp
    # Flask extensions
    - db
    - migrate
    - login_manager
    - mail
    # Flask-Login
    - current_user
    - login_required
    - load_user
    # Flask-WTF
    - FlaskForm
    - validate_on_submit
    # Common patterns
    - request
    - response
    - session
    - g
    - config

  # Skip Flask-specific files
  exclude_patterns:
    - "config.py"
    - "**/config/*.py"
    - "wsgi.py"
    - "run.py"
    - "**/tests/*.py"
    - "**/test_*.py"
    - "**/__init__.py"
    - "**/migrations/*.py"

  # String encoding for API keys, secrets
  string_encoding: true

  remove_docstrings: true
  remove_comments: true

verbose: false
""",
    "library": """# pyobfus configuration for Python libraries/packages
# Generated with: pyobfus --init-config library

obfuscation:
  level: community

  # Preserve public API names
  # Add your public API names here
  exclude_names:
    # Example public API (customize for your library)
    # - MyPublicClass
    # - public_function
    # - PUBLIC_CONSTANT

    # Common patterns to preserve
    - __version__
    - __author__
    - __all__

  # Skip non-distribution files
  exclude_patterns:
    - "**/tests/*.py"
    - "**/test_*.py"
    - "**/*_test.py"
    - "setup.py"
    - "setup.cfg"
    - "conftest.py"
    - "**/examples/*.py"
    - "**/docs/*.py"
    - "**/__init__.py"

  # Preserve parameter names for public API keyword arguments
  preserve_param_names: true

  # String encoding for internal strings
  string_encoding: true

  # Keep docstrings for public API documentation
  remove_docstrings: false
  remove_comments: true

verbose: false
""",
    "general": """# pyobfus configuration - General purpose
# Generated with: pyobfus --init-config general

obfuscation:
  level: community

  # Names to preserve from obfuscation
  # Add names that must remain unchanged (e.g., external API calls)
  exclude_names:
    - main
    - logger
    - config
    # Add your custom names here
    # - my_public_function
    # - MyPublicClass

  # File patterns to exclude from obfuscation
  exclude_patterns:
    - "**/tests/*.py"
    - "**/test_*.py"
    - "**/*_test.py"
    - "conftest.py"
    - "setup.py"
    - "**/__init__.py"

  # Enable string encoding (Base64)
  string_encoding: true

  # Remove documentation
  remove_docstrings: true
  remove_comments: true

  # Naming prefix for obfuscated identifiers
  name_prefix: "I"

  # Preserve function parameter names for keyword argument support
  # Set to true if your code uses keyword arguments externally
  preserve_param_names: false

# Show detailed output
verbose: false

# Note: For Pro features (AES encryption, anti-debugging), use:
#   level: pro
#   string_encryption: true
#   anti_debug: true
""",
}


def get_template(template_name: str) -> str:
    """
    Get configuration template by name.

    Args:
        template_name: Template name (django, flask, library, general)

    Returns:
        str: YAML configuration content

    Raises:
        ValueError: If template name is not found
    """
    if template_name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_name}'. Available: {available}")
    return TEMPLATES[template_name]


def list_templates() -> list:
    """
    List all available template names.

    Returns:
        list: List of template names
    """
    return list(TEMPLATES.keys())
