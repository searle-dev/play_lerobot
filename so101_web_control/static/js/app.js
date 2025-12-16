// SO101 机械臂网页控制 - 前端逻辑

class RobotController {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.robotConnected = false;
        this.joints = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper'];
        this.jointNames = {
            'shoulder_pan': '关节1-底座',
            'shoulder_lift': '关节2-大臂',
            'elbow_flex': '关节3-小臂',
            'wrist_flex': '关节4-腕部',
            'wrist_roll': '关节5-腕转',
            'gripper': '夹爪'
        };
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.initUI();
        this.initKeyboard();
        this.initVirtualButtons();
    }
    
    // 初始化 Socket.IO
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.connected = true;
            this.updateConnectionStatus();
            this.log('✅ WebSocket 连接成功', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.connected = false;
            this.updateConnectionStatus();
            this.log('❌ WebSocket 断开连接', 'error');
        });
        
        this.socket.on('connection_response', (data) => {
            this.log(`连接响应: ${data.status}`, 'info');
            this.robotConnected = data.robot_connected;
            this.updateConnectionStatus();
        });
        
        this.socket.on('robot_connection_result', (data) => {
            this.robotConnected = data.connected;
            this.updateConnectionStatus();
            if (data.success) {
                this.log(`✅ 机器人${data.connected ? '已连接' : '已断开'}: ${data.port || ''}`, 'success');
            } else {
                this.log('❌ 机器人连接失败', 'error');
            }
        });
        
        this.socket.on('robot_state', (data) => {
            if (data.connected && data.current && data.target) {
                this.updateJointDisplay(data.current, data.target);
            }
        });
        
        this.socket.on('position_update', (data) => {
            this.log(`${this.jointNames[data.joint]}: ${data.old.toFixed(1)}° → ${data.new.toFixed(1)}°`, 'info');
        });
        
        this.socket.on('error', (data) => {
            this.log(`❌ 错误: ${data.message}`, 'error');
        });
        
        this.socket.on('positions_reset', () => {
            this.log('✅ 所有关节已重置到零位', 'success');
        });
    }
    
    // 初始化 UI
    initUI() {
        // 连接按钮
        document.getElementById('connect-btn').addEventListener('click', () => {
            const port = document.getElementById('robot-port').value;
            this.connectRobot(port);
        });
        
        document.getElementById('disconnect-btn').addEventListener('click', () => {
            this.disconnectRobot();
        });
        
        // 重置按钮
        document.getElementById('reset-btn').addEventListener('click', () => {
            if (this.robotConnected) {
                this.socket.emit('reset_positions');
            } else {
                this.log('⚠️ 请先连接机器人', 'error');
            }
        });
        
        // 参数控制
        ['step-size', 'gripper-step', 'kp'].forEach(id => {
            document.getElementById(id).addEventListener('change', (e) => {
                this.updateControlParam(id, e.target.value);
            });
        });
        
        // 初始化关节显示
        this.initJointDisplay();
    }
    
    // 初始化键盘监听
    initKeyboard() {
        document.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            const validKeys = ['q', 'a', 'w', 's', 'e', 'd', 'r', 'f', 't', 'g', 'y', 'h'];
            
            if (validKeys.includes(key)) {
                e.preventDefault();
                this.handleKeyPress(key);
                
                // 视觉反馈
                const btn = document.querySelector(`.control-btn[data-key="${key}"]`);
                if (btn) {
                    btn.style.transform = 'translateY(-1px)';
                    setTimeout(() => {
                        btn.style.transform = '';
                    }, 100);
                }
            }
        });
    }
    
    // 初始化虚拟按钮
    initVirtualButtons() {
        document.querySelectorAll('.control-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const key = btn.getAttribute('data-key');
                this.handleKeyPress(key);
            });
        });
    }
    
    // 初始化关节显示
    initJointDisplay() {
        const container = document.getElementById('joints-status');
        container.innerHTML = '';
        
        this.joints.forEach(joint => {
            const item = document.createElement('div');
            item.className = 'joint-item';
            item.innerHTML = `
                <div class="joint-name">${this.jointNames[joint]}</div>
                <div class="joint-values">
                    <div class="joint-value">
                        <span class="joint-value-label">当前</span>
                        <span class="joint-value-number" id="${joint}-current">-</span>
                    </div>
                    <div class="joint-value">
                        <span class="joint-value-label">目标</span>
                        <span class="joint-value-number" id="${joint}-target">-</span>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    }
    
    // 更新关节显示
    updateJointDisplay(current, target) {
        this.joints.forEach(joint => {
            if (current[joint] !== undefined) {
                const currentEl = document.getElementById(`${joint}-current`);
                const targetEl = document.getElementById(`${joint}-target`);
                
                if (currentEl) {
                    currentEl.textContent = current[joint].toFixed(1) + '°';
                }
                if (targetEl) {
                    targetEl.textContent = target[joint].toFixed(1) + '°';
                }
            }
        });
    }
    
    // 更新连接状态
    updateConnectionStatus() {
        const statusEl = document.getElementById('connection-status');
        const portEl = document.getElementById('port-display');
        const connectBtn = document.getElementById('connect-btn');
        const disconnectBtn = document.getElementById('disconnect-btn');
        
        if (this.robotConnected) {
            statusEl.textContent = '已连接';
            statusEl.className = 'status-value connected';
            connectBtn.disabled = true;
            disconnectBtn.disabled = false;
            portEl.textContent = document.getElementById('robot-port').value;
        } else {
            statusEl.textContent = '未连接';
            statusEl.className = 'status-value disconnected';
            connectBtn.disabled = false;
            disconnectBtn.disabled = true;
            portEl.textContent = '-';
        }
    }
    
    // 连接机器人
    connectRobot(port) {
        this.log(`正在连接机器人: ${port}...`, 'info');
        this.socket.emit('connect_robot', { port });
    }
    
    // 断开机器人
    disconnectRobot() {
        this.log('正在断开机器人...', 'info');
        this.socket.emit('disconnect_robot');
    }
    
    // 处理按键
    handleKeyPress(key) {
        if (!this.robotConnected) {
            this.log('⚠️ 请先连接机器人', 'error');
            return;
        }
        
        this.socket.emit('key_press', { key });
    }
    
    // 更新控制参数
    updateControlParam(param, value) {
        const paramMap = {
            'step-size': 'step_size',
            'gripper-step': 'gripper_step',
            'kp': 'kp'
        };
        
        const serverParam = paramMap[param];
        if (serverParam) {
            this.socket.emit('set_control_param', {
                param: serverParam,
                value: parseFloat(value)
            });
            this.log(`⚙️ 参数更新: ${param} = ${value}`, 'info');
        }
    }
    
    // 添加日志
    log(message, type = 'info') {
        const container = document.getElementById('log-container');
        const item = document.createElement('div');
        item.className = `log-item ${type}`;
        
        const time = new Date().toLocaleTimeString();
        item.textContent = `[${time}] ${message}`;
        
        container.insertBefore(item, container.firstChild);
        
        // 限制日志数量
        while (container.children.length > 50) {
            container.removeChild(container.lastChild);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.robotController = new RobotController();
});
