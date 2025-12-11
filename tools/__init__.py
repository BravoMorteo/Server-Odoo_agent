"""Autoload de módulos de tools.

Cada módulo debe exponer una función:
    register(mcp: FastMCP, deps: dict) -> None

donde `deps` puede contener clientes compartidos (p.ej. {'odoo': OdooClient}).
"""
import importlib
import pkgutil
from types import ModuleType

def load_all(mcp, deps: dict, package_name: str = __name__):
    package = importlib.import_module(package_name)
    for info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        mod = importlib.import_module(info.name)
        _register_from_module(mod, mcp, deps)

def _register_from_module(mod: ModuleType, mcp, deps: dict):
    reg = getattr(mod, "register", None)
    if callable(reg):
        reg(mcp, deps)
