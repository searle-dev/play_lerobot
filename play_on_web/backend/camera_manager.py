"""
相机管理模块 - 管理多路相机流
"""
import sys
import cv2
import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """相机配置"""
    camera_id: str
    camera_type: str  # "opencv" 或 "realsense"
    width: int = 640
    height: int = 480
    fps: int = 30


class CameraManager:
    """相机管理器"""
    
    def __init__(self):
        self.cameras: dict[str, Any] = {}
        self.camera_configs: dict[str, CameraConfig] = {}
        self._streaming = False
    
    def add_camera(self, name: str, config: CameraConfig) -> dict[str, Any]:
        """
        添加相机
        
        Args:
            name: 相机名称（如 "left_wrist", "right_wrist", "head"）
            config: 相机配置
        """
        try:
            # 动态导入 lerobot 模块
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lerobot" / "src"))
            
            if config.camera_type == "opencv":
                from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
                from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
                from lerobot.cameras.configs import ColorMode
                
                cam_config = OpenCVCameraConfig(
                    index_or_path=config.camera_id,
                    color_mode=ColorMode.RGB,
                    width=config.width,
                    height=config.height,
                    fps=config.fps
                )
                camera = OpenCVCamera(cam_config)
            
            elif config.camera_type == "realsense":
                from lerobot.cameras.realsense.camera_realsense import RealSenseCamera
                from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
                from lerobot.cameras.configs import ColorMode
                
                cam_config = RealSenseCameraConfig(
                    serial_number_or_name=config.camera_id,
                    color_mode=ColorMode.RGB,
                    width=config.width,
                    height=config.height,
                    fps=config.fps
                )
                camera = RealSenseCamera(cam_config)
            else:
                return {
                    "status": "error",
                    "message": f"不支持的相机类型: {config.camera_type}"
                }
            
            # 连接相机
            camera.connect(warmup=True)
            
            self.cameras[name] = camera
            self.camera_configs[name] = config
            
            logger.info(f"相机 {name} 添加成功")
            return {
                "status": "success",
                "message": f"相机 {name} 添加成功"
            }
        except Exception as e:
            logger.error(f"添加相机 {name} 时出错: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def remove_camera(self, name: str) -> dict[str, Any]:
        """移除相机"""
        try:
            if name in self.cameras:
                camera = self.cameras[name]
                if camera.is_connected:
                    camera.disconnect()
                del self.cameras[name]
                del self.camera_configs[name]
                
                logger.info(f"相机 {name} 移除成功")
                return {
                    "status": "success",
                    "message": f"相机 {name} 移除成功"
                }
            else:
                return {
                    "status": "error",
                    "message": f"相机 {name} 不存在"
                }
        except Exception as e:
            logger.error(f"移除相机 {name} 时出错: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_frame(self, name: str) -> Optional[bytes]:
        """
        获取相机帧（JPEG 编码）
        
        Args:
            name: 相机名称
            
        Returns:
            JPEG 编码的图像数据，如果失败则返回 None
        """
        try:
            if name not in self.cameras:
                return None
            
            camera = self.cameras[name]
            frame = camera.read()
            
            # 转换为 BGR（OpenCV 格式）
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                frame_bgr = frame
            
            # 编码为 JPEG
            _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"获取相机 {name} 帧时出错: {e}")
            return None
    
    async def stream_frames(self, websocket, camera_names: list[str]):
        """
        通过 WebSocket 流式传输相机帧
        
        Args:
            websocket: WebSocket 连接
            camera_names: 相机名称列表
        """
        self._streaming = True
        
        try:
            while self._streaming:
                frames_data = {}
                
                for name in camera_names:
                    frame_bytes = self.get_frame(name)
                    if frame_bytes:
                        # 将帧编码为 base64
                        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                        frames_data[name] = frame_base64
                
                # 发送帧数据
                if frames_data:
                    await websocket.send_json({
                        "type": "camera_frames",
                        "data": frames_data
                    })
                
                # 控制帧率（大约 30 FPS）
                await asyncio.sleep(1.0 / 30.0)
        except Exception as e:
            logger.error(f"流式传输相机帧时出错: {e}")
        finally:
            self._streaming = False
    
    def stop_streaming(self):
        """停止流式传输"""
        self._streaming = False
    
    def disconnect_all(self):
        """断开所有相机"""
        for name in list(self.cameras.keys()):
            self.remove_camera(name)

