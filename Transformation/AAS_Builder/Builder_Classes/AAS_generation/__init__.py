# Re-export the v2-aligned generator for `from generation.AAS_generation import main`.
try:
    from .cli.generate_aas import main  # type: ignore[import-not-found]
except ImportError:
    main = None  # type: ignore[assignment]
