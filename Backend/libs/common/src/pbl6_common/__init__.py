"""pbl6-common — shared library for every PBL6 backend service.

See Backend/backend.md §3 for the intended layout. Editable workspace
package: services depend on it via `pbl6-common` in their own pyproject.toml
(uv workspace resolves it to this local path, no publishing needed).
"""

__version__ = "0.1.0"
