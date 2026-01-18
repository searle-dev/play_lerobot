/**
 * 键位映射配置相关的 TypeScript 类型定义
 */

/**
 * 键盘键位映射
 */
export interface KeyboardKeymap {
  left_arm: Record<string, string>
  right_arm: Record<string, string>
  base: Record<string, string>
}

/**
 * 键位配置预设
 */
export interface KeymapProfile {
  name: string
  description: string
  keyboard: KeyboardKeymap
}

/**
 * 完整的键位配置
 */
export interface KeymapConfig {
  version: string
  current_profile: string
  profiles: Record<string, KeymapProfile>
}

/**
 * API 响应：所有配置预设
 */
export interface KeymapProfilesResponse {
  status: string
  profiles: Record<string, KeymapProfile>
  current_profile: string
}

/**
 * API 响应：当前键位配置
 */
export interface CurrentKeymapResponse {
  status: string
  keymap: KeymapProfile
  profile: string
}

/**
 * API 响应：完整配置
 */
export interface KeymapConfigResponse {
  status: string
  config: KeymapConfig
}

/**
 * API 响应：通用操作结果
 */
export interface KeymapOperationResponse {
  status: string
  message: string
  current_profile?: string
}

/**
 * API 响应：配置验证结果
 */
export interface KeymapValidationResponse {
  status: string
  message: string
  valid: boolean
}

/**
 * API 请求：切换配置预设
 */
export interface SwitchProfileRequest {
  profile: string
}

/**
 * API 请求：创建配置预设
 */
export interface CreateProfileRequest {
  profile_name: string
  name: string
  description: string
  keymap: KeyboardKeymap
}

/**
 * API 请求：更新配置预设
 */
export interface UpdateProfileRequest {
  keymap: KeyboardKeymap
}

/**
 * API 请求：验证配置
 */
export interface ValidateKeymapRequest {
  keymap: KeyboardKeymap
}
