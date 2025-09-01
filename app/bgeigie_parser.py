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
            
            # Try to parse altitude if present; many logs don't include it
            altitude = None
            try:
                # Heuristic: after longitude components, some formats include altitude in meters
                # Commonly around index 11-13; pick the first parsable float there
                for idx in (11, 12, 13):
                    if len(fields) > idx and fields[idx]:
                        try:
                            altitude_candidate = float(fields[idx])
                            # Filter out obviously invalid values
                            if -5000.0 <= altitude_candidate <= 50000.0:
                                altitude = altitude_candidate
                                break
                        except ValueError:
                            continue
            except Exception:
                altitude = None

            measurement = {
                'captured_at': captured_at,
                'cpm': int(fields[3]) if fields[3] else 0,
                'latitude': ddm_to_dd(fields[7], fields[8]) if len(fields) > 8 else 0.0,
                'longitude': ddm_to_dd(fields[9], fields[10]) if len(fields) > 10 else 0.0,
                'altitude': altitude,
            }
            measurements.append(measurement)
        except (ValueError, IndexError) as e:
            # Log the error and the line that caused it
            print(f"Error parsing line: {line}\nError: {e}")
            continue

    return measurements
