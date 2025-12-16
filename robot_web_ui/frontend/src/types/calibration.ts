export enum CalibrationStep {
  NOT_STARTED = "not_started",
  MOVE_TO_CENTER = "move_to_center",
  RECORDING_RANGE = "recording_range",
  COMPLETED = "completed"
}

export interface CalibrationStatus {
  robot_id: string;
  step: CalibrationStep;
  current_positions: Record<string, number>;
  range_mins?: Record<string, number>;
  range_maxes?: Record<string, number>;
  message: string;
}
