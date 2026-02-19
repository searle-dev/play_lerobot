/* eslint-disable @typescript-eslint/no-explicit-any */
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

/** Swizzle MuJoCo position to Three.js coordinate system */
function getPosition(buffer: any, index: number, target: THREE.Vector3): THREE.Vector3 {
  return target.set(
     buffer[(index * 3) + 0],
     buffer[(index * 3) + 2],
    -buffer[(index * 3) + 1]
  )
}

/** Swizzle MuJoCo quaternion to Three.js coordinate system */
function getQuaternion(buffer: any, index: number, target: THREE.Quaternion): THREE.Quaternion {
  return target.set(
    -buffer[(index * 4) + 1],
    -buffer[(index * 4) + 3],
     buffer[(index * 4) + 2],
    -buffer[(index * 4) + 0]
  )
}

export class SimRenderer {
  private renderer: THREE.WebGLRenderer
  private scene: THREE.Scene
  private camera: THREE.PerspectiveCamera
  private controls: OrbitControls
  private bodies: Record<number, THREE.Group> = {}
  private lights: THREE.Light[] = []
  private tmpVec = new THREE.Vector3()

  constructor(container: HTMLElement) {
    // Scene
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0.15, 0.25, 0.35)

    // Camera
    this.camera = new THREE.PerspectiveCamera(
      45, container.clientWidth / container.clientHeight, 0.001, 100
    )
    this.camera.position.set(0.5, 1.7, -3)
    this.scene.add(this.camera)

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.1 * Math.PI)
    this.scene.add(ambient)

    const spot = new THREE.SpotLight()
    spot.angle = 1.11
    spot.penumbra = 0.5
    spot.castShadow = true
    spot.intensity = spot.intensity * Math.PI * 10
    spot.position.set(0, 3, 3)
    spot.shadow.mapSize.width = 1024
    spot.shadow.mapSize.height = 1024
    this.scene.add(spot)

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    this.renderer.setPixelRatio(window.devicePixelRatio)
    this.renderer.setSize(container.clientWidth, container.clientHeight)
    this.renderer.shadowMap.enabled = true
    container.appendChild(this.renderer.domElement)

    // Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement)
    this.controls.target.set(0, 0.7, 0)
    this.controls.enableDamping = true
    this.controls.dampingFactor = 0.1
    this.controls.update()
  }

  /**
   * Build Three.js meshes from loaded MuJoCo scene.
   * Ported from mujocoUtils.js::loadSceneFromURL()
   */
  buildScene(model: any, _data: any, mujoco: any): void {
    const mujocoRoot = new THREE.Group()
    mujocoRoot.name = 'MuJoCo Root'
    this.scene.add(mujocoRoot)

    const meshes: Record<number, THREE.BufferGeometry> = {}

    // Loop through MuJoCo geoms and recreate in Three.js
    for (let g = 0; g < model.ngeom; g++) {
      if (!(model.geom_group[g] < 3)) continue

      const b = model.geom_bodyid[g]
      const type = model.geom_type[g]
      const size = [
        model.geom_size[(g * 3) + 0],
        model.geom_size[(g * 3) + 1],
        model.geom_size[(g * 3) + 2],
      ]

      // Create body group if it doesn't exist
      if (!(b in this.bodies)) {
        this.bodies[b] = new THREE.Group()
        this.bodies[b].name = `body_${b}`
      }

      // Create geometry based on type
      let geometry: THREE.BufferGeometry = new THREE.SphereGeometry(size[0] * 0.5)

      if (type === mujoco.mjtGeom.mjGEOM_PLANE.value) {
        // Plane handled specially below
      } else if (type === mujoco.mjtGeom.mjGEOM_SPHERE.value) {
        geometry = new THREE.SphereGeometry(size[0])
      } else if (type === mujoco.mjtGeom.mjGEOM_CAPSULE.value) {
        geometry = new THREE.CapsuleGeometry(size[0], size[1] * 2.0, 20, 20)
      } else if (type === mujoco.mjtGeom.mjGEOM_ELLIPSOID.value) {
        geometry = new THREE.SphereGeometry(1)
      } else if (type === mujoco.mjtGeom.mjGEOM_CYLINDER.value) {
        geometry = new THREE.CylinderGeometry(size[0], size[0], size[1] * 2.0)
      } else if (type === mujoco.mjtGeom.mjGEOM_BOX.value) {
        geometry = new THREE.BoxGeometry(size[0] * 2.0, size[2] * 2.0, size[1] * 2.0)
      } else if (type === mujoco.mjtGeom.mjGEOM_MESH.value) {
        const meshID = model.geom_dataid[g]

        if (!(meshID in meshes)) {
          geometry = new THREE.BufferGeometry()

          const vertex_buffer = model.mesh_vert.subarray(
            model.mesh_vertadr[meshID] * 3,
            (model.mesh_vertadr[meshID] + model.mesh_vertnum[meshID]) * 3
          )
          // Swizzle Y/Z for Three.js coordinate system
          for (let v = 0; v < vertex_buffer.length; v += 3) {
            const temp = vertex_buffer[v + 1]
            vertex_buffer[v + 1] = vertex_buffer[v + 2]
            vertex_buffer[v + 2] = -temp
          }

          const normal_buffer = model.mesh_normal.subarray(
            model.mesh_normaladr[meshID] * 3,
            (model.mesh_normaladr[meshID] + model.mesh_normalnum[meshID]) * 3
          )
          for (let v = 0; v < normal_buffer.length; v += 3) {
            const temp = normal_buffer[v + 1]
            normal_buffer[v + 1] = normal_buffer[v + 2]
            normal_buffer[v + 2] = -temp
          }

          const uv_buffer = model.mesh_texcoord.subarray(
            model.mesh_texcoordadr[meshID] * 2,
            (model.mesh_texcoordadr[meshID] + model.mesh_texcoordnum[meshID]) * 2
          )

          const face_to_vertex_buffer = model.mesh_face.subarray(
            model.mesh_faceadr[meshID] * 3,
            (model.mesh_faceadr[meshID] + model.mesh_facenum[meshID]) * 3
          )
          const face_to_uv_buffer = model.mesh_facetexcoord.subarray(
            model.mesh_faceadr[meshID] * 3,
            (model.mesh_faceadr[meshID] + model.mesh_facenum[meshID]) * 3
          )
          const face_to_normal_buffer = model.mesh_facenormal.subarray(
            model.mesh_faceadr[meshID] * 3,
            (model.mesh_faceadr[meshID] + model.mesh_facenum[meshID]) * 3
          )

          // Swizzle UV and normals into per-vertex format
          const swizzled_uv_buffer = new Float32Array((vertex_buffer.length / 3) * 2)
          const swizzled_normal_buffer = new Float32Array(vertex_buffer.length)
          for (let t = 0; t < face_to_vertex_buffer.length / 3; t++) {
            const vi0 = face_to_vertex_buffer[(t * 3) + 0]
            const vi1 = face_to_vertex_buffer[(t * 3) + 1]
            const vi2 = face_to_vertex_buffer[(t * 3) + 2]
            const uvi0 = face_to_uv_buffer[(t * 3) + 0]
            const uvi1 = face_to_uv_buffer[(t * 3) + 1]
            const uvi2 = face_to_uv_buffer[(t * 3) + 2]
            const nvi0 = face_to_normal_buffer[(t * 3) + 0]
            const nvi1 = face_to_normal_buffer[(t * 3) + 1]
            const nvi2 = face_to_normal_buffer[(t * 3) + 2]

            swizzled_uv_buffer[(vi0 * 2) + 0] = uv_buffer[(uvi0 * 2) + 0]
            swizzled_uv_buffer[(vi0 * 2) + 1] = uv_buffer[(uvi0 * 2) + 1]
            swizzled_uv_buffer[(vi1 * 2) + 0] = uv_buffer[(uvi1 * 2) + 0]
            swizzled_uv_buffer[(vi1 * 2) + 1] = uv_buffer[(uvi1 * 2) + 1]
            swizzled_uv_buffer[(vi2 * 2) + 0] = uv_buffer[(uvi2 * 2) + 0]
            swizzled_uv_buffer[(vi2 * 2) + 1] = uv_buffer[(uvi2 * 2) + 1]

            swizzled_normal_buffer[(vi0 * 3) + 0] = normal_buffer[(nvi0 * 3) + 0]
            swizzled_normal_buffer[(vi0 * 3) + 1] = normal_buffer[(nvi0 * 3) + 1]
            swizzled_normal_buffer[(vi0 * 3) + 2] = normal_buffer[(nvi0 * 3) + 2]
            swizzled_normal_buffer[(vi1 * 3) + 0] = normal_buffer[(nvi1 * 3) + 0]
            swizzled_normal_buffer[(vi1 * 3) + 1] = normal_buffer[(nvi1 * 3) + 1]
            swizzled_normal_buffer[(vi1 * 3) + 2] = normal_buffer[(nvi1 * 3) + 2]
            swizzled_normal_buffer[(vi2 * 3) + 0] = normal_buffer[(nvi2 * 3) + 0]
            swizzled_normal_buffer[(vi2 * 3) + 1] = normal_buffer[(nvi2 * 3) + 1]
            swizzled_normal_buffer[(vi2 * 3) + 2] = normal_buffer[(nvi2 * 3) + 2]
          }

          geometry.setAttribute('position', new THREE.BufferAttribute(vertex_buffer, 3))
          geometry.setAttribute('normal', new THREE.BufferAttribute(swizzled_normal_buffer, 3))
          geometry.setAttribute('uv', new THREE.BufferAttribute(swizzled_uv_buffer, 2))
          geometry.setIndex(Array.from(face_to_vertex_buffer))
          geometry.computeVertexNormals()
          meshes[meshID] = geometry
        } else {
          geometry = meshes[meshID]
        }
      }

      // Material
      const color = [
        model.geom_rgba[(g * 4) + 0],
        model.geom_rgba[(g * 4) + 1],
        model.geom_rgba[(g * 4) + 2],
        model.geom_rgba[(g * 4) + 3],
      ]

      let texture: THREE.Texture | undefined
      if (model.geom_matid[g] !== -1) {
        const matId = model.geom_matid[g]
        color[0] = model.mat_rgba[(matId * 4) + 0]
        color[1] = model.mat_rgba[(matId * 4) + 1]
        color[2] = model.mat_rgba[(matId * 4) + 2]
        color[3] = model.mat_rgba[(matId * 4) + 3]

        const mjNTEXROLE = 10
        const mjTEXROLE_RGB = 1
        const texId = model.mat_texid[(matId * mjNTEXROLE) + mjTEXROLE_RGB]

        if (texId !== -1) {
          const width = model.tex_width[texId]
          const height = model.tex_height[texId]
          const offset = model.tex_adr[texId]
          const channels = model.tex_nchannel[texId]
          const texData = model.tex_data
          const rgbaArray = new Uint8Array(width * height * 4)
          for (let p = 0; p < width * height; p++) {
            rgbaArray[(p * 4) + 0] = texData[offset + ((p * channels) + 0)]
            rgbaArray[(p * 4) + 1] = channels > 1 ? texData[offset + ((p * channels) + 1)] : rgbaArray[(p * 4) + 0]
            rgbaArray[(p * 4) + 2] = channels > 2 ? texData[offset + ((p * channels) + 2)] : rgbaArray[(p * 4) + 0]
            rgbaArray[(p * 4) + 3] = channels > 3 ? texData[offset + ((p * channels) + 3)] : 255
          }
          texture = new THREE.DataTexture(rgbaArray, width, height, THREE.RGBAFormat, THREE.UnsignedByteType)
          texture.repeat = new THREE.Vector2(
            model.mat_texrepeat[(matId * 2) + 0],
            model.mat_texrepeat[(matId * 2) + 1]
          )
          texture.wrapS = THREE.RepeatWrapping
          texture.wrapT = THREE.RepeatWrapping
          texture.needsUpdate = true
        }
      }

      const material = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(color[0], color[1], color[2]),
        transparent: color[3] < 1.0,
        opacity: color[3] < 1.0 ? color[3] : 1.0,
        map: texture ?? null,
      })

      let mesh: THREE.Object3D
      if (type === mujoco.mjtGeom.mjGEOM_PLANE.value) {
        // Reflective floor plane
        mesh = new THREE.Mesh(
          new THREE.PlaneGeometry(100, 100),
          new THREE.MeshPhysicalMaterial({
            color: new THREE.Color(color[0], color[1], color[2]),
            map: texture ?? null,
            roughness: 0.8,
          })
        )
        mesh.rotateX(-Math.PI / 2)
      } else {
        mesh = new THREE.Mesh(geometry, material)
      }

      mesh.castShadow = g !== 0
      mesh.receiveShadow = type !== mujoco.mjtGeom.mjGEOM_MESH.value
      this.bodies[b].add(mesh)
      getPosition(model.geom_pos, g, mesh.position)
      if (type !== mujoco.mjtGeom.mjGEOM_PLANE.value) {
        getQuaternion(model.geom_quat, g, mesh.quaternion)
      }
      if (type === mujoco.mjtGeom.mjGEOM_ELLIPSOID.value) {
        mesh.scale.set(size[0], size[2], size[1])
      }
    }

    // Parse lights from model
    for (let l = 0; l < model.nlight; l++) {
      let light: THREE.Light
      if (model.light_type[l] === 0) {
        const spotLight = new THREE.SpotLight()
        spotLight.angle = 1.11
        light = spotLight
      } else if (model.light_type[l] === 1) {
        light = new THREE.DirectionalLight()
      } else if (model.light_type[l] === 2) {
        light = new THREE.PointLight()
      } else {
        light = new THREE.HemisphereLight()
      }
      light.castShadow = true
      light.intensity = light.intensity * Math.PI
      if (this.bodies[0]) {
        this.bodies[0].add(light)
      } else {
        mujocoRoot.add(light)
      }
      this.lights.push(light)
    }
    if (model.nlight === 0) {
      const light = new THREE.DirectionalLight()
      mujocoRoot.add(light)
    }

    // Add bodies to root
    for (let b = 0; b < model.nbody; b++) {
      if (b === 0 || !this.bodies[0]) {
        mujocoRoot.add(this.bodies[b])
      } else if (this.bodies[b]) {
        this.bodies[0].add(this.bodies[b])
      } else {
        this.bodies[b] = new THREE.Group()
        this.bodies[b].name = `body_${b}`
        this.bodies[0].add(this.bodies[b])
      }
    }
  }

  /** Update mesh transforms from MuJoCo simulation state */
  updateFromPhysics(model: any, data: any): void {
    for (let b = 0; b < model.nbody; b++) {
      if (this.bodies[b]) {
        getPosition(data.xpos, b, this.bodies[b].position)
        getQuaternion(data.xquat, b, this.bodies[b].quaternion)
      }
    }
    // Update lights
    for (let l = 0; l < model.nlight && l < this.lights.length; l++) {
      getPosition(data.light_xpos, l, this.lights[l].position)
      getPosition(data.light_xdir, l, this.tmpVec)
      this.lights[l].lookAt(this.tmpVec.add(this.lights[l].position))
    }
  }

  /** Render one frame */
  render(): void {
    this.controls.update()
    this.renderer.render(this.scene, this.camera)
  }

  /** Handle container resize */
  resize(width: number, height: number): void {
    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(width, height)
  }

  /** Get the Three.js scene */
  getScene(): THREE.Scene { return this.scene }

  /** Clean up WebGL resources */
  dispose(): void {
    this.renderer.domElement.remove()
    this.renderer.dispose()
    this.controls.dispose()
    this.bodies = {}
    this.lights = []
  }
}
