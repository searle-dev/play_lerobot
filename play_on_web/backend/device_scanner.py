"""
设备扫描模块 - 扫描串口和相机设备
"""
import sys
import platform
import time
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


class DeviceScanner:
    """设备扫描器"""
    
    @staticmethod
    def find_available_ports(include_cu: bool = False) -> list[str]:
        """
        查找所有可用的串口
        参考：lerobot_find_port.py
        
        Args:
            include_cu: 在 macOS 上是否包含 cu.* 设备（默认只返回 tty.* 设备）
        
        注意：
        - 在 macOS 上，每个 USB 串口会创建两个设备文件：
          * /dev/tty.usbmodem* - TTY 设备（推荐使用）
          * /dev/cu.usbmodem* - Callout 设备
          默认只返回 tty.* 设备以避免重复
        - 过滤掉系统虚拟终端
        """
        try:
            from serial.tools import list_ports
            
            if platform.system() == "Windows":
                # Windows: 使用 pyserial 扫描 COM 端口
                ports = [port.device for port in list_ports.comports()]
            elif platform.system() == "Darwin":  # macOS
                # macOS: 扫描 USB 串口设备
                usb_ports = []
                
                # 总是包含 tty.usb* 设备（推荐使用）
                usb_ports.extend(Path("/dev").glob("tty.usb*"))
                
                # 可选包含 cu.usb* 设备
                if include_cu:
                    usb_ports.extend(Path("/dev").glob("cu.usb*"))
                
                ports = sorted([str(path) for path in usb_ports])
            else:  # Linux
                # Linux: 扫描 ttyUSB* 和 ttyACM* 设备
                usb_ports = []
                usb_ports.extend(Path("/dev").glob("ttyUSB*"))
                usb_ports.extend(Path("/dev").glob("ttyACM*"))
                ports = sorted([str(path) for path in usb_ports])
            
            logger.info(f"找到 {len(ports)} 个串口: {ports}")
            return ports
        except Exception as e:
            logger.error(f"扫描串口时出错: {e}")
            return []
    
    @staticmethod
    def find_port_by_disconnect(timeout: float = 30.0) -> dict[str, Any]:
        """
        通过断开连接的方式识别串口
        
        Returns:
            包含状态和端口信息的字典
        """
        try:
            # 在 macOS 上，需要扫描 tty 和 cu 设备以便正确检测断开
            include_cu = platform.system() == "Darwin"
            ports_before = DeviceScanner.find_available_ports(include_cu=include_cu)
            
            return {
                "status": "waiting_disconnect",
                "message": "请拔出 USB 线缆",
                "ports_before": ports_before,
                "timeout": timeout
            }
        except Exception as e:
            logger.error(f"识别串口时出错: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def find_port_after_disconnect(ports_before: list[str]) -> dict[str, Any]:
        """
        在断开连接后识别端口
        
        Args:
            ports_before: 断开前的端口列表
            
        Returns:
            包含状态和端口信息的字典
        
        注意：在 macOS 上，每个 USB 串口会创建两个设备文件：
        - /dev/tty.usbmodem* (TTY 设备)
        - /dev/cu.usbmodem* (Callout 设备)
        它们指向同一个物理设备。拔出一个 USB 时，两个设备文件都会消失。
        """
        try:
            logger.info(f"断开前的端口: {ports_before}")
            time.sleep(0.5)  # 等待端口释放
            
            # 在 macOS 上，需要扫描 tty 和 cu 设备以便正确检测断开
            include_cu = platform.system() == "Darwin"
            ports_after = DeviceScanner.find_available_ports(include_cu=include_cu)
            logger.info(f"断开后的端口: {ports_after}")
            
            ports_diff = list(set(ports_before) - set(ports_after))
            logger.info(f"检测到的端口差异: {ports_diff}")
            
            if len(ports_diff) == 0:
                logger.warning("未检测到端口变化")
                return {
                    "status": "error",
                    "message": f"未检测到端口变化。断开前: {len(ports_before)} 个，断开后: {len(ports_after)} 个"
                }
            
            # 在 macOS 上，处理 tty 和 cu 设备对
            # 如果检测到成对的 tty/cu 设备，只返回 tty 设备
            if platform.system() == "Darwin" and len(ports_diff) == 2:
                # 检查是否是成对的 tty/cu 设备
                tty_ports = [p for p in ports_diff if '/tty.' in p]
                cu_ports = [p for p in ports_diff if '/cu.' in p]
                
                if len(tty_ports) == 1 and len(cu_ports) == 1:
                    # 提取设备名称（去掉 tty. 或 cu. 前缀）
                    tty_name = tty_ports[0].split('/tty.')[1]
                    cu_name = cu_ports[0].split('/cu.')[1]
                    
                    if tty_name == cu_name:
                        # 确认是同一个物理设备，返回 tty 版本
                        port = tty_ports[0]
                        logger.info(f"检测到成对的 tty/cu 设备，使用: {port}")
                        return {
                            "status": "success",
                            "message": f"成功识别端口: {port}",
                            "port": port
                        }
            
            # 其他情况
            if len(ports_diff) == 1:
                port = ports_diff[0]
                logger.info(f"成功识别端口: {port}")
                return {
                    "status": "success",
                    "message": f"成功识别端口: {port}",
                    "port": port
                }
            else:
                logger.warning(f"检测到多个端口变化: {ports_diff}")
                return {
                    "status": "error",
                    "message": f"检测到多个端口变化: {ports_diff}。请只拔出一个 USB 设备。"
                }
        except Exception as e:
            logger.error(f"识别端口时出错: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def find_opencv_cameras() -> list[dict[str, Any]]:
        """
        查找所有 OpenCV 相机
        参考：lerobot_find_cameras.py
        """
        all_cameras = []
        
        try:
            # 动态导入 lerobot 模块
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lerobot" / "src"))
            
            from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
            
            opencv_cameras = OpenCVCamera.find_cameras()
            for cam_info in opencv_cameras:
                all_cameras.append({
                    "type": "opencv",
                    "id": cam_info.get("id"),
                    "name": cam_info.get("name", "Unknown"),
                    "width": cam_info.get("width"),
                    "height": cam_info.get("height"),
                    "fps": cam_info.get("fps"),
                })
            
            logger.info(f"找到 {len(opencv_cameras)} 个 OpenCV 相机")
        except ImportError as e:
            logger.warning(f"无法导入 OpenCV 相机模块: {e}")
        except Exception as e:
            logger.error(f"扫描 OpenCV 相机时出错: {e}")
        
        return all_cameras
    
    @staticmethod
    def find_realsense_cameras() -> list[dict[str, Any]]:
        """
        查找所有 RealSense 相机
        参考：lerobot_find_cameras.py
        """
        all_cameras = []
        
        try:
            # 检查 pyrealsense2 是否可用
            try:
                import pyrealsense2 as rs
            except ImportError:
                logger.warning("pyrealsense2 未安装，跳过 RealSense 相机扫描")
                return all_cameras
            
            # 动态导入 lerobot 模块
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lerobot" / "src"))
            
            from lerobot.cameras.realsense.camera_realsense import RealSenseCamera
            
            realsense_cameras = RealSenseCamera.find_cameras()
            for cam_info in realsense_cameras:
                all_cameras.append({
                    "type": "realsense",
                    "id": cam_info.get("serial_number_or_name"),
                    "name": cam_info.get("name", "Unknown"),
                    "width": cam_info.get("default_stream_profile", {}).get("width"),
                    "height": cam_info.get("default_stream_profile", {}).get("height"),
                    "fps": cam_info.get("default_stream_profile", {}).get("fps"),
                })
            
            logger.info(f"找到 {len(realsense_cameras)} 个 RealSense 相机")
        except ImportError as e:
            logger.warning(f"无法导入 RealSense 模块: {e}")
        except Exception as e:
            logger.error(f"扫描 RealSense 相机时出错: {e}")
        
        return all_cameras
    
    @staticmethod
    def find_all_cameras() -> list[dict[str, Any]]:
        """
        查找所有相机（OpenCV + RealSense）
        """
        all_cameras = []
        all_cameras.extend(DeviceScanner.find_opencv_cameras())
        all_cameras.extend(DeviceScanner.find_realsense_cameras())
        return all_cameras

