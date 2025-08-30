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
    valid_headers = ['$BMRDD', '$BGRDD', '$BNRDD', '$BNXRDD', '$PNTDD', '$CZRDD']
    
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line or '*' not in line:
            continue
            
        # Check if line starts with any valid bGeigie header
        if not any(line.startswith(header) for header in valid_headers):
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
            # Parse timestamp - handle different formats
            timestamp_str = fields[2]
            if 'T' in timestamp_str:
                # ISO format: 2024-11-22T07:17:00Z
                captured_at = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Alternative format handling
                try:
                    captured_at = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    captured_at = datetime.datetime.now()
            
            measurement = {
                'device_id': int(fields[1]) if fields[1] else 0,
                'captured_at': captured_at,
                'cpm': int(fields[3]) if fields[3] else 0,
                'cp5s': int(fields[4]) if len(fields) > 4 and fields[4] else 0,
                'total_count': int(fields[5]) if len(fields) > 5 and fields[5] else 0,
                'cpm_validity': fields[6] if len(fields) > 6 else 'V',
                'latitude': ddm_to_dd(fields[7], fields[8]) if len(fields) > 8 else 0.0,
                'longitude': ddm_to_dd(fields[9], fields[10]) if len(fields) > 10 else 0.0,
                'altitude': float(fields[11]) if len(fields) > 11 and fields[11] else 0.0,
                'gps_validity': fields[12] if len(fields) > 12 else 'V',
                'hdop': float(fields[13]) if len(fields) > 13 and fields[13] else 0.0,
                'gps_fix_quality': int(fields[14]) if len(fields) > 14 and fields[14] else 0,
            }
            measurements.append(measurement)
        except (ValueError, IndexError) as e:
            # Log the error and the line that caused it
            print(f"Error parsing line: {line}\nError: {e}")
            continue

    return measurements
