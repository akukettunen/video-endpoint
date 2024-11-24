import subprocess
import json
from typing import List

def get_video_duration(url: str) -> float:
    """Get video duration using FFmpeg."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError(f"FFprobe error: {result.stderr}")

        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        raise ValueError(f"Failed to get video duration: {str(e)}")

def validate_timestamps(timestamps: List[float], duration: float) -> List[dict]:
    """Validate timestamps and return valid ones with status."""
    validated = []
    for ts in timestamps:
        if ts < 0:
            validated.append({
                "timestamp": ts,
                "valid": False,
                "reason": "Timestamp cannot be negative"
            })
        elif ts > duration:
            validated.append({
                "timestamp": ts,
                "valid": False,
                "reason": f"Timestamp exceeds video duration of {duration:.2f} seconds"
            })
        else:
            validated.append({
                "timestamp": ts,
                "valid": True,
                "reason": None
            })
    return validated