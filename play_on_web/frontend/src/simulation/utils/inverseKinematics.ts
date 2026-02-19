/**
 * Calculate inverse kinematics for a 2-link robotic arm
 * @param x - End effector x coordinate
 * @param y - End effector y coordinate
 * @param l1 - Upper arm length (default 0.1159 m)
 * @param l2 - Lower arm length (default 0.1350 m)
 * @returns [joint2, joint3] angles in radians
 */
export function inverseKinematics2Link(
  x: number, y: number,
  l1 = 0.1159, l2 = 0.1350
): [number, number] {
  // Calculate joint offsets based on arm geometry
  const theta1Offset = Math.atan2(0.028, 0.11257)
  const theta2Offset = Math.atan2(0.0052, 0.1349) + theta1Offset

  // Calculate distance from origin to target point
  let r = Math.sqrt(x * x + y * y)
  const rMax = l1 + l2
  const rMin = Math.abs(l1 - l2)

  // Clamp to workspace boundaries
  if (r > rMax) {
    const scale = rMax / r
    x *= scale
    y *= scale
    r = rMax
  }
  if (r < rMin && r > 0) {
    const scale = rMin / r
    x *= scale
    y *= scale
    r = rMin
  }

  // Use law of cosines to calculate theta2 (elbow angle)
  const cosTheta2 = -(r * r - l1 * l1 - l2 * l2) / (2 * l1 * l2)
  const clampedCos = Math.max(-1, Math.min(1, cosTheta2))
  const theta2 = Math.PI - Math.acos(clampedCos)

  // Calculate theta1 (shoulder angle)
  const beta = Math.atan2(y, x)
  const gamma = Math.atan2(l2 * Math.sin(theta2), l1 + l2 * Math.cos(theta2))
  const theta1 = beta + gamma

  // Convert to joint angles with offsets
  let joint2 = theta1 + theta1Offset
  let joint3 = theta2 + theta2Offset

  // Clamp to URDF limits
  joint2 = Math.max(-0.1, Math.min(3.45, joint2))
  joint3 = Math.max(-0.2, Math.min(Math.PI, joint3))

  return [joint2, joint3]
}
