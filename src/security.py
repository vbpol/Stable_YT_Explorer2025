import importlib
import inspect
import pkgutil

SECURE_TAG = "SECURE_BLOCK_v1"

def _tag_object(obj):
    try:
        setattr(obj, "__secure_tag__", SECURE_TAG)
    except Exception:
        pass

def _tag_class(cls):
    _tag_object(cls)
    try:
        for name, member in vars(cls).items():
            if inspect.isfunction(member) or inspect.ismethod(member):
                _tag_object(member)
    except Exception:
        pass

def apply_security_tag(package_name: str = "src"):
    try:
        pkg = importlib.import_module(package_name)
        for modinfo in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            mod_name = modinfo.name
            try:
                mod = importlib.import_module(mod_name)
            except Exception:
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
    except Exception:
        pass

def is_secure(obj) -> bool:
    try:
        return getattr(obj, "__secure_tag__", None) == SECURE_TAG
    except Exception:
        return False
