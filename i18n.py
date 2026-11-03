"""Windows display-language detection and shared Chinese/English messages."""
import ctypes
import json
import os
from pathlib import Path
import re
import sys

_current = None
_english = None


def system_language():
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        count, size = ctypes.c_ulong(), ctypes.c_ulong()
        if kernel.GetUserPreferredUILanguages(8, ctypes.byref(count), None, ctypes.byref(size)) and size.value:
            buffer = ctypes.create_unicode_buffer(size.value)
            if kernel.GetUserPreferredUILanguages(8, ctypes.byref(count), buffer, ctypes.byref(size)):
                return 'zh-CN' if buffer.value.lower().startswith('zh') else 'en-US'
        return 'zh-CN' if kernel.GetUserDefaultUILanguage() & 0x3ff == 4 else 'en-US'
    return 'en-US'


def set_language(choice='auto'):
    global _current
    _current = system_language() if choice == 'auto' else choice
    return _current


def language():
    global _current
    if _current is None:
        from app_runtime import load_settings
        set_language(os.environ.get('NBA_ROSTER_SYNC_LANGUAGE', load_settings().get('language', 'auto')))
    return _current


def english_messages():
    global _english
    if _english is None:
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
        _english = json.loads((root/'locales/en-US.json').read_text('utf-8'))
    return _english


def tr(text, **values):
    translated = text if language() == 'zh-CN' else english_messages().get(text, text)
    return translated.format(**values) if values else translated


def localize(text):
    """Translate domain errors, including variable-bearing legacy messages."""
    text = str(text)
    if language() == 'zh-CN' or not any('\u4e00' <= c <= '\u9fff' for c in text):
        return text
    if text in english_messages():
        return english_messages()[text]
    for source, target in sorted(english_messages().items(), key=lambda item: -len(item[0])):
        if '{' in source:
            pieces = re.split(r'(\{[a-z_]+\})', source)
            names = [part[1:-1] for part in pieces if re.fullmatch(r'\{[a-z_]+\}',part)]
            if not names:
                continue
            pattern = ''.join('(?P<'+p[1:-1]+'>[^\r\n]+?)' if p.startswith('{') and p.endswith('}') else re.escape(p) for p in pieces)
            if source.endswith('}'):
                pattern += '(?=\r?$)'
            if re.search(pattern,text,flags=re.M):
                return re.sub(pattern, lambda match: target.format(**match.groupdict()), text, count=1, flags=re.M)
        elif source in text:
            return text.replace(source,target,1)
    return text
