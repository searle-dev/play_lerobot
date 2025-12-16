export interface RecordingFrame {
  timestamp: number;
  joint_positions: Record<string, number>;
}

export interface Recording {
  id: string;
  robot_id: string;
  name: string;
  frames: RecordingFrame[];
  duration: number;
  created_at: string;
}

export interface RecordingMetadata {
  id: string;
  robot_id: string;
  name: string;
  duration: number;
  frame_count: number;
  created_at: string;
}
