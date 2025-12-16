"""端口扫描服务"""
import serial.tools.list_ports
from typing import List
from ..models.robot import PortInfo, ScanResult


class PortScanner:
    """端口扫描器"""

    @staticmethod
    def list_ports() -> List[PortInfo]:
        """列出所有可用串口"""
        ports = serial.tools.list_ports.comports()
        return [
            PortInfo(
                port=p.device,
                description=p.description or "",
                hwid=p.hwid or ""
            )
            for p in ports
        ]

    @staticmethod
    async def scan_port(port: str) -> List[ScanResult]:
        """
        扫描指定端口上的电机

        Args:
            port: 串口路径

        Returns:
            扫描结果列表
        """
        import asyncio

        def _scan():
            try:
                # 尝试使用 Feetech 总线扫描
                from lerobot.motors.feetech import FeetechMotorsBus
                baudrate_ids = FeetechMotorsBus.scan_port(port)
                return [
                    ScanResult(port=port, baudrate=br, motor_ids=list(ids))
                    for br, ids in baudrate_ids.items()
                ]
            except Exception as e:
                print(f"Feetech 扫描失败: {e}")
                # 尝试使用 Dynamixel 总线扫描
                try:
                    from lerobot.motors.dynamixel import DynamixelMotorsBus
                    baudrate_ids = DynamixelMotorsBus.scan_port(port)
                    return [
                        ScanResult(port=port, baudrate=br, motor_ids=list(ids))
                        for br, ids in baudrate_ids.items()
                    ]
                except Exception as e2:
                    print(f"Dynamixel 扫描失败: {e2}")
                    return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _scan)
