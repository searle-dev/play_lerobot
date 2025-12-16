#!/usr/bin/env python3
"""
SO101 机械臂 Web 控制服务器
支持实时按键控制和状态显示
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'so101-web-control'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
robot = None
robot_connected = False
robot_lock = threading.Lock()
target_positions = {
    'shoulder_pan': 0.0,
    'shoulder_lift': 0.0,
    'elbow_flex': 0.0,
    'wrist_flex': 0.0,
    'wrist_roll': 0.0,
    'gripper': 0.0
}

# 机械臂端口配置
ROBOT_PORT = "/dev/tty.usbmodem5A7C1163141"  # 修改为您的端口

def init_robot():
    """初始化机械臂连接"""
    global robot, robot_connected
    try:
        from lerobot.robots.so100_follower import SO100Follower, SO100FollowerConfig
        
        logger.info(f"正在连接机械臂，端口: {ROBOT_PORT}")
        robot_config = SO100FollowerConfig(port=ROBOT_PORT)
        robot = SO100Follower(robot_config)
        robot.bus.connect()
        
        robot_connected = True
        logger.info("✅ 机械臂连接成功！")
        return True
    except Exception as e:
        logger.error(f"❌ 机械臂连接失败: {e}")
        robot_connected = False
        return False

def get_robot_state():
    """获取机械臂当前状态"""
    if not robot_connected or robot is None:
        return None
    
    try:
        with robot_lock:
            obs = robot.bus.read_positions()
            return {k: float(v) for k, v in obs.items()}
    except Exception as e:
        logger.error(f"读取状态失败: {e}")
        return None

def control_robot(joint_name, delta):
    """控制机械臂关节"""
    global target_positions
    
    if not robot_connected or robot is None:
        return False
    
    try:
        with robot_lock:
            # 更新目标位置
            current = target_positions.get(joint_name, 0.0)
            new_target = current + delta
            
            # 限制范围（根据需要调整）
            if joint_name == 'gripper':
                new_target = max(0, min(100, new_target))
            else:
                new_target = max(-180, min(180, new_target))
            
            target_positions[joint_name] = new_target
            
            # 发送命令到机械臂
            robot.bus.write_position(joint_name, new_target)
            
            logger.info(f"控制 {joint_name}: {current:.1f} -> {new_target:.1f}")
            return True
    except Exception as e:
        logger.error(f"控制失败: {e}")
        return False

# 后台任务：定期广播机械臂状态
def broadcast_state():
    """定期向所有客户端广播机械臂状态"""
    while True:
        if robot_connected:
            state = get_robot_state()
            if state:
                socketio.emit('robot_state', {
                    'positions': state,
                    'targets': target_positions,
                    'connected': True
                })
        else:
            socketio.emit('robot_state', {
                'connected': False
            })
        time.sleep(0.1)  # 10Hz 更新频率

# Web 路由
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """获取机械臂状态"""
    if robot_connected:
        state = get_robot_state()
        return jsonify({
            'connected': True,
            'positions': state,
            'targets': target_positions
        })
    else:
        return jsonify({'connected': False})

@app.route('/api/connect', methods=['POST'])
def connect():
    """连接机械臂"""
    success = init_robot()
    return jsonify({'success': success, 'connected': robot_connected})

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """断开机械臂连接"""
    global robot, robot_connected
    try:
        if robot:
            robot.bus.disconnect()
        robot_connected = False
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# SocketIO 事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info('客户端已连接')
    emit('connection_response', {'connected': robot_connected})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    logger.info('客户端已断开')

@socketio.on('control')
def handle_control(data):
    """处理控制命令"""
    joint = data.get('joint')
    delta = data.get('delta', 1.0)
    
    success = control_robot(joint, delta)
    emit('control_response', {'success': success, 'joint': joint})

@socketio.on('reset_joint')
def handle_reset(data):
    """重置关节到零位"""
    joint = data.get('joint')
    if joint and robot_connected:
        target_positions[joint] = 0.0
        control_robot(joint, -target_positions[joint])
        emit('control_response', {'success': True, 'joint': joint, 'reset': True})

if __name__ == '__main__':
    # 启动时尝试连接机械臂
    logger.info("启动 SO101 Web 控制服务器...")
    init_robot()
    
    # 启动后台状态广播线程
    state_thread = threading.Thread(target=broadcast_state, daemon=True)
    state_thread.start()
    
    # 启动 Flask 服务器
    logger.info("服务器启动在 http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
