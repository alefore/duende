import importlib.util
import os
from agent_plugin_interface import AgentPlugin

DUENDE_PLUGIN_PREFIX = 'duende_plugin'
DUENDE_PLUGIN_SYMBOL = 'DuendePlugin'


class NoPluginFilesFoundError(Exception):
  """Raised when no duende_plugin_*.py files are found in a directory."""
  pass


class NoPluginClassFoundError(Exception):
  """Raised when a duende_plugin_*.py file does not contain an AgentPlugin implementation."""
  pass


class InvalidPluginClassError(Exception):
  """Raised when the DuendePlugin symbol is not a valid AgentPlugin subclass."""
  pass


def load_plugins(directories: list[str]) -> list[AgentPlugin]:
  """Find all `duende_plugin_*.py` files and loads all plugins in them."""
  loaded_plugins: list[AgentPlugin] = []

  for directory in directories:
    plugin_files = [f for f in os.listdir(directory) if f.startswith(DUENDE_PLUGIN_PREFIX) and f.endswith('.py')]

    if not plugin_files:
      raise NoPluginFilesFoundError(f"No {DUENDE_PLUGIN_PREFIX}_*.py files found in directory: {directory}")

    for plugin_file in plugin_files:
      file_path = os.path.join(directory, plugin_file)
      module_name = plugin_file[:-3]  # Remove .py extension

      spec = importlib.util.spec_from_file_location(module_name, file_path)
      if spec is None:
        raise ImportError(f"Could not load spec for module {module_name} from {file_path}")
      
      if spec.loader is None:
        raise ImportError(f"Could not load module {module_name} from {file_path}: Loader is None")

      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)

      if not hasattr(module, DUENDE_PLUGIN_SYMBOL):
        raise NoPluginClassFoundError(f"No '{DUENDE_PLUGIN_SYMBOL}' class found in {plugin_file}")
      
      duende_plugin_class = getattr(module, DUENDE_PLUGIN_SYMBOL)

      if not (isinstance(duende_plugin_class, type) and 
              issubclass(duende_plugin_class, AgentPlugin) and 
              duende_plugin_class is not AgentPlugin):
        raise InvalidPluginClassError(f"'{DUENDE_PLUGIN_SYMBOL}' in {plugin_file} is not a valid AgentPlugin subclass.")
      
      loaded_plugins.append(duende_plugin_class())

  return loaded_plugins
