import datetime

def calculate_checksum(sentence: str) -> str:
    """Calculates the checksum for a NMEA sentence."""
    # The checksum is a XOR of all the ASCII characters bytes between '$' and '*' (these excluded).
    payload = sentence.split('$')[1].split('*')[0]
    checksum = 0
    for char in payload:
        checksum ^= ord(char)
    return f"{checksum:02X}"

def ddm_to_dd(ddm: str, direction: str) -> float:
    """Converts a latitude or longitude from DDMM.MMMM format to decimal degrees."""
    if not ddm:
        return 0.0
    try:
        parts = ddm.split('.')
        degrees = int(parts[0][:-2])
        minutes = float(f"{parts[0][-2:]}.{parts[1]}")
        dd = degrees + minutes / 60
        if direction in ['S', 'W']:
            dd *= -1
        return dd
    except (ValueError, IndexError):
        return 0.0

def parse_bgeigie_log(content: str):
    """Parses the content of a bGeigie log file."""
    measurements = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line.startswith('$BNXRDD') or '*' not in line:
            continue

        parts = line.split('*')
        sentence = parts[0]
        try:
            checksum = parts[1]
        except IndexError:
            continue # Skip lines without a checksum

        if calculate_checksum(sentence) != checksum:
            # You might want to log this for debugging
            continue

        fields = sentence.split(',')

        try:
            measurement = {
                'device_id': int(fields[1]),
                'captured_at': datetime.datetime.fromisoformat(fields[2].replace('Z', '+00:00')),
                'cpm': int(fields[3]), # This is the 1-minute count
                'cp5s': int(fields[4]), # This is the 5-second count
                'total_count': int(fields[5]),
                'cpm_validity': fields[6],
                'latitude': ddm_to_dd(fields[7], fields[8]),
                'longitude': ddm_to_dd(fields[9], fields[10]),
                'altitude': float(fields[11]) if fields[11] else 0.0,
                'gps_validity': fields[12],
                'hdop': float(fields[13]) if fields[13] else 0.0,
                'gps_fix_quality': int(fields[14]) if fields[14] else 0,
            }
            measurements.append(measurement)
        except (ValueError, IndexError) as e:
            # Log the error and the line that caused it
            print(f"Error parsing line: {line}\nError: {e}")
            continue

    return measurements
