"""录制回放 API"""
from fastapi import APIRouter, HTTPException
from typing import List
from ..models.recording import RecordingMetadata
from ..services.recording_service import recording_service

router = APIRouter(prefix="/api/recording", tags=["recording"])


@router.post("/{robot_id}/start")
async def start_recording(robot_id: str):
    """开始录制"""
    try:
        recording_id = await recording_service.start_recording(robot_id)
        return {"recording_id": recording_id, "status": "recording"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始录制失败: {str(e)}")


@router.post("/{recording_id}/stop")
async def stop_recording(recording_id: str, name: str = "未命名录制"):
    """停止录制"""
    try:
        recording = await recording_service.stop_recording(recording_id, name)
        return {
            "id": recording.id,
            "name": recording.name,
            "duration": recording.duration,
            "frame_count": len(recording.frames)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止录制失败: {str(e)}")


@router.get("/{robot_id}", response_model=List[RecordingMetadata])
async def list_recordings(robot_id: str):
    """列出所有录制"""
    try:
        return recording_service.list_recordings(robot_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出录制失败: {str(e)}")


@router.post("/{recording_id}/playback")
async def playback_recording(recording_id: str, speed: float = 1.0):
    """回放录制"""
    try:
        await recording_service.playback(recording_id, speed=speed)
        return {"status": "playback_completed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回放失败: {str(e)}")
