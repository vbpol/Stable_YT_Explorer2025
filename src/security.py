import importlib
import inspect
import pkgutil
from typing import Any, Optional

SECURE_TAG = "SECURE_BLOCK_v1"

def _tag_object(obj: Any) -> None:
    """Helper to tag a single object."""
    try:
        setattr(obj, "__secure_tag__", SECURE_TAG)
    except (AttributeError, TypeError):
        pass

def _tag_class(cls: Any) -> None:
    """Helper to tag a class and its methods."""
    _tag_object(cls)
    try:
        for name, member in vars(cls).items():
            if inspect.isfunction(member) or inspect.ismethod(member):
                _tag_object(member)
    except Exception:
        pass

def apply_security_tag(package_name: str = "src") -> None:
    """
    Recursively apply security tags to a package and its submodules.
    
    Args:
        package_name: The name of the package to tag.
        
    Raises:
        ImportError: If the package cannot be imported.
    """
    pkg = importlib.import_module(package_name)
    
    # Tag the package itself
    _tag_object(pkg)
    
    if not hasattr(pkg, "__path__"):
        return

    for modinfo in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        mod_name = modinfo.name
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
            
        _tag_object(mod)
        try:
            for attr_name in dir(mod):
                try:
                    attr = getattr(mod, attr_name)
                except Exception:
                    continue
                    
                if inspect.isclass(attr):
                    _tag_class(attr)
                elif inspect.isfunction(attr):
                    _tag_object(attr)
        except Exception:
            pass

def is_secure(obj: Any) -> bool:
    """Check if an object has the security tag."""
    try:
        return getattr(obj, "__secure_tag__", None) == SECURE_TAG
    except Exception:
        return False
