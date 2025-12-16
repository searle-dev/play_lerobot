export enum RobotType {
  SO100_FOLLOWER = "so100_follower",
  SO101_FOLLOWER = "so101_follower",
  KOCH_FOLLOWER = "koch_follower",
  LEKIWI = "lekiwi"
}

export enum RobotStatus {
  DISCONNECTED = "disconnected",
  CONNECTED = "connected",
  CALIBRATING = "calibrating",
  READY = "ready",
  ERROR = "error"
}

export interface PortInfo {
  port: string;
  description: string;
  hwid: string;
}

export interface ScanResult {
  port: string;
  baudrate: number;
  motor_ids: number[];
}

export interface RobotConfig {
  id: string;
  robot_type: RobotType;
  port: string;
  nickname?: string;
  notes?: string;
}

export interface RobotState extends RobotConfig {
  status: RobotStatus;
  is_calibrated: boolean;
  joint_positions?: Record<string, number>;
  last_updated?: string;
}

export interface JointPosition {
  [jointName: string]: number;
}
