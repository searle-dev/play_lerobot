"""端口扫描 API"""
from fastapi import APIRouter, HTTPException
from typing import List
from ..models.robot import PortInfo, ScanResult
from ..services.port_scanner import PortScanner

router = APIRouter(prefix="/api/ports", tags=["ports"])
scanner = PortScanner()


@router.get("/", response_model=List[PortInfo])
async def list_ports():
    """列出所有可用串口"""
    try:
        return scanner.list_ports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出端口失败: {str(e)}")


@router.post("/scan", response_model=List[ScanResult])
async def scan_port(port: str):
    """扫描指定端口上的电机"""
    try:
        return await scanner.scan_port(port)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描端口失败: {str(e)}")
