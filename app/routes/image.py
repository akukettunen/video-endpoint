from fastapi import APIRouter, HTTPException # type: ignore
from pydantic import BaseModel, conlist # type: ignore
import subprocess
import os
from typing import Optional, List
from datetime import datetime
from .. utils.video import get_video_duration, validate_timestamps

router = APIRouter(
    prefix="/image",
    tags=["image"]
)

class M3U8Request(BaseModel):
    url: str
    timestamps: conlist(float, min_items=1) # type: ignore
    output_format: Optional[str] = "jpg"

@router.post("/extract-frames-m3u8")
async def extract_frames(request: M3U8Request):
    try:
        duration = get_video_duration(request.url)
        validated_timestamps = validate_timestamps(request.timestamps, duration)

        invalid_timestamps = [t for t in validated_timestamps if not t["valid"]]
        if invalid_timestamps:
            print("Invalid timestamps found:", invalid_timestamps)

        valid_timestamps = [t["timestamp"] for t in validated_timestamps if t["valid"]]

        if not valid_timestamps:
            return {
                "success": False,
                "message": "No valid timestamps provided",
                "invalid_timestamps": invalid_timestamps
            }

        output_dir = "extracted_frames"
        os.makedirs(output_dir, exist_ok=True)

        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extracted_frames = []

        for idx, timestamp in enumerate(valid_timestamps):
            # Format timestamp for ffmpeg
            hours = int(timestamp // 3600)
            minutes = int((timestamp % 3600) // 60)
            seconds = timestamp % 60
            timestamp_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

            output_file = os.path.join(
                output_dir,
                f"frame_{batch_timestamp}_{idx}.{request.output_format}"
            )

            # FFmpeg command with -ss before input for faster seeking
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
                "-ss", timestamp_str,
                "-i", request.url,
                "-vframes", "1",
                "-vf", "format=rgb24",
                "-pix_fmt", "rgb24",
                output_file
            ]

            process = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                extracted_frames.append({
                    "file_path": output_file,
                    "requested_timestamp": timestamp,
                    "status": "success"
                })
            else:
                print(f"Failed to extract frame at timestamp {timestamp}")
                print(f"FFmpeg output: {process.stderr}")

        response = {
            "success": bool(extracted_frames),
            "frames": extracted_frames,
            "message": f"Successfully extracted {len(extracted_frames)} frames",
            "invalid_timestamps": invalid_timestamps if invalid_timestamps else None
        }

        if not extracted_frames:
            response["message"] = "Failed to extract any frames"
            response["success"] = False

        return response

    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )