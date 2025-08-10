# data_utils.py
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def clean_text(text: Optional[str]) -> str:
    """Remove newline sequences and clean text."""
    if not text:
        return ""
    return re.sub(r'(\\r\\n|\r\n|\n|\r)', ' ', str(text)).strip()


def parse_characteristic(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    value = symbol = ''
    for line in lines:
        if line.startswith('VALUE'):
            parts = line.split()
            if len(parts) > 1:
                value = parts[1]
        elif line.startswith('SYMBOL_LINK'):
            m = re.search(r'"([^\"]+)"', line)
            if m:
                symbol = m.group(1)
    return {
        'Type': 'Characteristic',
        'Name': name,
        'Comment': clean_text(desc),
        'Value': value,
        'Symbol_Link': symbol
    }


def parse_measurement(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    dtype = conversion = ''
    params: List[str] = []
    addr = symbol = ''
    for line in lines:
        toks = line.split()
        if toks and toks[0] in ('UBYTE', 'UWORD', 'SWORD', 'ULONG', 'SLONG'):
            dtype = toks[0]
            if len(toks) > 1:
                conversion = toks[1]
            if len(toks) > 2:
                params = toks[2:]
        elif line.startswith('ECU_ADDRESS'):
            parts = line.split()
            addr = parts[1] if len(parts) > 1 else ''
        elif line.startswith('SYMBOL_LINK'):
            m = re.search(r'"([^\"]+)"', line)
            if m:
                symbol = m.group(1)
    return {
        'Type': 'Measurement',
        'Name': name,
        'Comment': clean_text(desc),
        'Data_Type': dtype,
        'Conversion': conversion,
        'Measurement_Params': ' '.join(params),
        'ECU_Address': addr,
        'Symbol_Link': symbol
    }


def parse_measurement_array(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    details = ' '.join(lines)
    return {
        'Type': 'MeasurementArray',
        'Name': name,
        'Comment': clean_text(desc),
        'Details': clean_text(details)
    }


def parse_a2l_file(filepath: str) -> Dict[str, Dict[str, Any]]:
    """Parse a .a2l file into a dict of data blocks."""
    logger.info('Parsing A2L: %s', filepath)
    begin_re = re.compile(r'/begin\s+(\w+)\s+([^\s]+)(?:\s+"([^"]+)")?')
    end_re = re.compile(r'/end\s+(\w+)')
    data: Dict[str, Dict[str, Any]] = {}
    current = name = desc = ''
    lines: List[str] = []

    with open(filepath, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            m_begin = begin_re.match(line)
            if m_begin:
                current = m_begin.group(1).upper()
                name = m_begin.group(2)
                desc = m_begin.group(3) or ''
                lines = []
                continue
            m_end = end_re.match(line)
            if m_end and current:
                block = m_end.group(1).upper()
                if block == current:
                    if block == 'CHARACTERISTIC':
                        data[name] = parse_characteristic(name, desc, lines)
                    elif block == 'MEASUREMENT':
                        content = ' '.join(lines).lower()
                        if 'array' in content:
                            data[name] = parse_measurement_array(name, desc, lines)
                        else:
                            data[name] = parse_measurement(name, desc, lines)
                    elif block == 'MEASUREMENT_ARRAY':
                        data[name] = parse_measurement_array(name, desc, lines)
                current = ''
                continue
            if current:
                lines.append(line)
    logger.info('Finished parsing; %d items', len(data))
    return data


def load_data(path: str) -> Dict[str, Dict[str, Any]]:
    """Load data only from .a2l files."""
    if not path.lower().endswith('.a2l'):
        raise ValueError('Only .a2l files are supported')
    return parse_a2l_file(path)


def search_parameters(data: Dict[str, Dict[str, Any]], query: str) -> Dict[str, Dict[str, Any]]:
    q = query.lower()
    return {name: det for name, det in data.items() if q in name.lower() or q in str(det.get('Comment', '')).lower()}