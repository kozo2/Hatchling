"""Internationalization (i18n) loader for Hatchling.

This module provides translation loading and management functionality,
enabling runtime language switching and fallback to English for missing keys.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from threading import Lock

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import toml
except ImportError:
    toml = None


class TranslationLoader:
    """Manages loading and accessing translation files for internationalization.
    
    This class handles loading translation files from the languages directory,
    provides translation lookup with fallback to English, and supports runtime
    language switching.
    """
    
    def __init__(self, languages_dir: Optional[Path] = None, default_language: str = "en"):
        """Initialize the translation loader.
        
        Args:
            languages_dir (Optional[Path]): Directory containing translation files.
                                          Defaults to hatchling/config/languages/
            default_language (str): Default language code. Defaults to "en".
        """
        if languages_dir is None:
            # Default to the languages directory relative to this file
            current_dir = Path(__file__).parent
            languages_dir = current_dir / "languages"
        
        self.languages_dir = Path(languages_dir)
        self.default_language = default_language
        self.current_language = default_language
        
        # Cache for loaded translations
        self._translations_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = Lock()
        
        # Logger for translation operations
        self.logger = logging.getLogger(__name__)
        
        # Load default language on initialization
        self._load_language(self.default_language)
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """Get list of available language files.
        
        Returns:
            List[Dict[str, str]]: List of dictionaries with language info.
                                 Each dict contains 'code', 'name', and 'file' keys.
        """
        if not self.languages_dir.exists():
            self.logger.warning(f"Languages directory not found: {self.languages_dir}")
            return []
        
        languages = []
        for file_path in self.languages_dir.glob("*.toml"):
            language_code = file_path.stem
            try:
                translations = self._load_translation_file(file_path)
                meta = translations.get("meta", {})
                language_name = meta.get("language_name", language_code.capitalize())
                
                languages.append({
                    "code": language_code,
                    "name": language_name,
                    "file": str(file_path)
                })
            except Exception as e:
                self.logger.warning(f"Failed to load language metadata for {language_code}: {e}")
                # Add basic info even if file has issues
                languages.append({
                    "code": language_code,
                    "name": language_code.capitalize(),
                    "file": str(file_path)
                })
        
        return sorted(languages, key=lambda x: x["code"])
    
    def set_language(self, language_code: str) -> bool:
        """Set the current language.
        
        Args:
            language_code (str): Language code to set as current.
            
        Returns:
            bool: True if language was successfully set, False otherwise.
        """
        if self._load_language(language_code):
            with self._cache_lock:
                self.current_language = language_code
            self.logger.info(f"Language changed to: {language_code}")
            return True
        return False
    
    def get_current_language(self) -> str:
        """Get the current language code.
        
        Returns:
            str: Current language code.
        """
        return self.current_language
    
    def translate(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """Get translated string for the given key.
        
        Args:
            key (str): Translation key in dot notation (e.g., "settings.llm.model.name")
            language (Optional[str]): Language code to use. Defaults to current language.
            **kwargs: Format arguments for string formatting.
            
        Returns:
            str: Translated string, or the key itself if translation not found.
        """
        if language is None:
            language = self.current_language
        
        # Ensure the language is loaded
        if language not in self._translations_cache:
            if not self._load_language(language):
                # Fall back to default language
                language = self.default_language
        
        with self._cache_lock:
            translations = self._translations_cache.get(language, {})
        
        # Navigate through the nested dictionary using dot notation
        value = translations
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # Key not found, try fallback to English
                if language != self.default_language:
                    return self.translate(key, self.default_language, **kwargs)
                else:
                    # Even English doesn't have the key, return the key itself
                    self.logger.warning(f"Translation key not found: {key}")
                    return key
        
        # If we have a string, format it with any provided arguments
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Failed to format translation '{key}': {e}")
                return value
        
        return str(value) if value is not None else key
    
    def _load_language(self, language_code: str) -> bool:
        """Load a specific language into the cache.
        
        Args:
            language_code (str): Language code to load.
            
        Returns:
            bool: True if language was successfully loaded, False otherwise.
        """
        if language_code in self._translations_cache:
            return True
        
        language_file = self.languages_dir / f"{language_code}.toml"
        if not language_file.exists():
            self.logger.warning(f"Language file not found: {language_file}")
            return False
        
        try:
            translations = self._load_translation_file(language_file)
            with self._cache_lock:
                self._translations_cache[language_code] = translations
            self.logger.info(f"Loaded language: {language_code}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load language {language_code}: {e}")
            return False
    
    def _load_translation_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a TOML translation file.
        
        Args:
            file_path (Path): Path to the translation file.
            
        Returns:
            Dict[str, Any]: Parsed translation data.
            
        Raises:
            Exception: If file cannot be read or parsed.
        """
        if tomllib is not None:
            # Use tomllib (Python 3.11+) or tomli
            with open(file_path, 'rb') as f:
                return tomllib.load(f)
        elif toml is not None:
            # Fallback to toml library
            with open(file_path, 'r', encoding='utf-8') as f:
                return toml.load(f)
        else:
            raise ImportError("No TOML library available. Install tomli or toml.")
    
    def reload_translations(self) -> None:
        """Reload all cached translations from disk."""
        with self._cache_lock:
            cached_languages = list(self._translations_cache.keys())
            self._translations_cache.clear()
        
        # Reload all previously cached languages
        for language_code in cached_languages:
            self._load_language(language_code)
        
        self.logger.info("Reloaded all translations")


# Global translation loader instance
_translation_loader: Optional[TranslationLoader] = None


def get_translation_loader() -> TranslationLoader:
    """Get the global translation loader instance.
    
    Returns:
        TranslationLoader: The global translation loader instance.
    """
    global _translation_loader
    if _translation_loader is None:
        _translation_loader = TranslationLoader()
    return _translation_loader


def init_translation_loader(languages_dir: Optional[Path] = None, default_language: str = "en") -> TranslationLoader:
    """Initialize the global translation loader.
    
    Args:
        languages_dir (Optional[Path]): Directory containing translation files.
        default_language (str): Default language code.
        
    Returns:
        TranslationLoader: The initialized translation loader.
    """
    global _translation_loader
    _translation_loader = TranslationLoader(languages_dir, default_language)
    return _translation_loader


def translate(key: str, language: Optional[str] = None, **kwargs) -> str:
    """Convenience function to translate a key using the global loader.
    
    Args:
        key (str): Translation key in dot notation.
        language (Optional[str]): Language code to use.
        **kwargs: Format arguments for string formatting.
        
    Returns:
        str: Translated string.
    """
    return get_translation_loader().translate(key, language, **kwargs)


def set_language(language_code: str) -> bool:
    """Convenience function to set language using the global loader.
    
    Args:
        language_code (str): Language code to set.
        
    Returns:
        bool: True if language was successfully set.
    """
    return get_translation_loader().set_language(language_code)


def get_available_languages() -> List[Dict[str, str]]:
    """Convenience function to get available languages using the global loader.
    
    Returns:
        List[Dict[str, str]]: List of available languages.
    """
    return get_translation_loader().get_available_languages()


def get_current_language() -> str:
    """Convenience function to get current language using the global loader.
    
    Returns:
        str: Current language code.
    """
    return get_translation_loader().get_current_language()
