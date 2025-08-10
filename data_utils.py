# data_utils.py
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_DTOK = {"UBYTE", "SBYTE", "UWORD", "SWORD", "ULONG", "SLONG", "FLOAT16_IEEE",
         "FLOAT32_IEEE", "FLOAT64_IEEE", "DOUBLE", "U64", "S64"}

_SYMLINK_RE = re.compile(r'"([^"]+)"')


def clean_text(text: Optional[str]) -> str:
    """Return a single-line, trimmed string (newline sequences -> space)."""
    if not text:
        return ""
    return re.sub(r'(\r\n|\n|\r)', ' ', str(text)).strip()


def _extract_symbol(line: str) -> str:
    m = _SYMLINK_RE.search(line)
    return m.group(1) if m else ""


def parse_characteristic(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    value = ""
    symbol = ""
    for line in lines:
        if line.startswith("VALUE"):
            # VALUE <addr>
            parts = line.split()
            if len(parts) > 1:
                value = parts[1]
        elif line.startswith("SYMBOL_LINK"):
            symbol = _extract_symbol(line)

    return {
        "Type": "Characteristic",
        "Name": name,
        "Comment": clean_text(desc),
        "Value": value,
        "Symbol_Link": symbol,
    }


def _parse_measurement_like(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    """Parse fields common to MEASUREMENT and array-typed MEASUREMENT."""
    dtype = ""
    conversion = ""
    params: List[str] = []
    addr = ""
    symbol = ""
    array_size = ""  # when present, this indicates an array measurement

    for line in lines:
        toks = line.split()
        if toks and toks[0] in _DTOK:
            dtype = toks[0]
            if len(toks) > 1:
                conversion = toks[1]
            if len(toks) > 2:
                params = toks[2:]
        elif line.startswith("ECU_ADDRESS"):
            parts = line.split()
            addr = parts[1] if len(parts) > 1 else ""
        elif line.startswith("ARRAY_SIZE"):
            parts = line.split()
            array_size = parts[1] if len(parts) > 1 else ""
        elif line.startswith("SYMBOL_LINK"):
            symbol = _extract_symbol(line)

    # Measurement_Params: prefer explicit ARRAY_SIZE if present
    meas_params = f"ARRAY_SIZE={array_size}" if array_size else " ".join(params)

    base = {
        "Name": name,
        "Comment": clean_text(desc),
        "Data_Type": dtype,
        "Conversion": conversion,
        "Measurement_Params": meas_params,
        "ECU_Address": addr,
        "Symbol_Link": symbol,
    }

    if array_size:
        base["Type"] = "MeasurementArray"
    else:
        base["Type"] = "Measurement"

    return base


def parse_measurement(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    return _parse_measurement_like(name, desc, lines)


def parse_measurement_array(name: str, desc: str, lines: List[str]) -> Dict[str, Any]:
    """Handle explicit MEASUREMENT_ARRAY blocks (rare)."""
    data = _parse_measurement_like(name, desc, lines)
    data["Type"] = "MeasurementArray"
    # Ensure ARRAY_SIZE shows in Measurement_Params even if missing in block
    if "ARRAY_SIZE=" not in data.get("Measurement_Params", ""):
        data["Measurement_Params"] = (data.get("Measurement_Params") + " ARRAY_SIZE=?").strip()
    return data


def parse_a2l_file(filepath: str) -> Dict[str, Dict[str, Any]]:
    """Parse a .a2l file into a dict keyed by block name."""
    logger.info("Parsing A2L: %s", filepath)

    begin_re = re.compile(r'/begin\s+(\w+)\s+([^\s]+)(?:\s+"([^"]+)")?', re.IGNORECASE)
    end_re = re.compile(r'/end\s+(\w+)', re.IGNORECASE)

    data: Dict[str, Dict[str, Any]] = {}
    current = ""
    name = ""
    desc = ""
    lines: List[str] = []

    # A2L files are commonly ASCII/latin-1; utf-8 also works for simple content.
    with open(filepath, encoding="latin-1") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            m_begin = begin_re.match(line)
            if m_begin:
                current = m_begin.group(1).upper()
                name = m_begin.group(2)
                desc = m_begin.group(3) or ""
                lines = []
                continue

            m_end = end_re.match(line)
            if m_end and current:
                block = m_end.group(1).upper()
                if block == current:
                    if block == "CHARACTERISTIC":
                        data[name] = parse_characteristic(name, desc, lines)
                    elif block == "MEASUREMENT":
                        # Decide array vs scalar by presence of ARRAY_SIZE line
                        is_array = any(l.strip().startswith("ARRAY_SIZE") for l in lines)
                        if is_array:
                            data[name] = parse_measurement_array(name, desc, lines)
                        else:
                            data[name] = parse_measurement(name, desc, lines)
                    elif block == "MEASUREMENT_ARRAY":
                        data[name] = parse_measurement_array(name, desc, lines)
                current = ""
                name = ""
                desc = ""
                lines = []
                continue

            if current:
                lines.append(line)

    logger.info("Finished parsing; %d items", len(data))
    return data


def load_data(path: str) -> Dict[str, Dict[str, Any]]:
    """Load data only from .a2l files."""
    if not path.lower().endswith(".a2l"):
        raise ValueError("Only .a2l files are supported")
    return parse_a2l_file(path)


def search_parameters(data: Dict[str, Dict[str, Any]], query: str) -> Dict[str, Dict[str, Any]]:
    q = query.lower()
    out: Dict[str, Dict[str, Any]] = {}
    for name, det in data.items():
        if q in name.lower():
            out[name] = det
            continue
        # Search important fields; omit very large ones
        for key in ("Comment", "Symbol_Link", "Conversion", "Data_Type", "ECU_Address", "Measurement_Params"):
            val = str(det.get(key, ""))
            if val and q in val.lower():
                out[name] = det
                break
    return out
