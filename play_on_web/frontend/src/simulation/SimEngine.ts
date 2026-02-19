/* eslint-disable @typescript-eslint/no-explicit-any */
import { XLeRobotController } from './controllers/XLeRobotController'
import type { BaseController, KeyStates } from './controllers/BaseController'

type MuJoCoModule = any
type MjModel = any
type MjData = any

export interface SimConfig {
  robot: string
  environment: string
}

interface RobotConfig {
  xmlPath: string
  objectsPath: string | null
  robotDir: string
  meshDir: string | null
  controllerFactory: (() => BaseController) | null
}

const ROBOT_CONFIGS: Record<string, RobotConfig> = {
  'xlerobot': {
    xmlPath: 'xlerobot.xml',
    objectsPath: 'objects.xml',
    robotDir: 'xlerobot',
    meshDir: 'assets',
    controllerFactory: () => new XLeRobotController(),
  },
  'SO101': {
    xmlPath: 'SO101.xml',
    objectsPath: 'objects_SO101.xml',
    robotDir: 'xlerobot',
    meshDir: 'assets',
    controllerFactory: null,
  },
}

const ASSET_BASE = '/sim-assets'

export class SimEngine {
  private mujoco: MuJoCoModule | null = null
  private model: MjModel | null = null
  private data: MjData | null = null
  private controller: BaseController | null = null
  private keyStates: KeyStates = {}
  private _initialized = false
  private downloadedRobots = new Set<string>()

  get initialized() { return this._initialized }

  async loadMuJoCo(): Promise<void> {
    if (this.mujoco) return
    const loadModule = (await import('mujoco-js')).default
    this.mujoco = await loadModule()
    this.mujoco.FS.mkdir('/working')
    this.mujoco.FS.mount(this.mujoco.MEMFS, { root: '.' }, '/working')
  }

  async downloadRobotAssets(robotDir: string): Promise<void> {
    if (this.downloadedRobots.has(robotDir)) return
    if (!this.mujoco) throw new Error('MuJoCo not loaded')

    console.log(`Downloading robot assets: ${robotDir}...`)

    // Ensure base robots directory exists
    this._ensureDir('/working/robots')
    this._ensureDir(`/working/robots/${robotDir}`)

    // Load the robot's index.json listing all files
    const indexResponse = await fetch(`${ASSET_BASE}/robots/${robotDir}/index.json`)
    if (!indexResponse.ok) {
      throw new Error(`Failed to load index.json for robot: ${robotDir}`)
    }
    const files: string[] = await indexResponse.json()
    const normalizedFiles = files.map((f: string) => f.replace(/\\/g, '/'))

    // Fetch all files in parallel
    const fileDataPromises = normalizedFiles.map(async (file: string) => {
      const response = await fetch(`${ASSET_BASE}/robots/${robotDir}/${file}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch ${file}: ${response.status}`)
      }
      const lowerFile = file.toLowerCase()
      const isBinary = lowerFile.endsWith('.png') ||
                       lowerFile.endsWith('.stl') ||
                       lowerFile.endsWith('.skn') ||
                       lowerFile.endsWith('.obj') ||
                       lowerFile.endsWith('.ply')
      const data = isBinary
        ? new Uint8Array(await response.arrayBuffer())
        : await response.text()
      return { file, data }
    })

    const filesData = await Promise.all(fileDataPromises)

    // Write files to virtual filesystem
    for (const { file, data } of filesData) {
      const filePath = `/working/robots/${robotDir}/${file}`
      // Ensure subdirectories exist
      const parts = file.split('/')
      let working = `/working/robots/${robotDir}`
      for (let p = 0; p < parts.length - 1; p++) {
        working += '/' + parts[p]
        this._ensureDir(working)
      }
      this.mujoco.FS.writeFile(filePath, data)
    }

    this.downloadedRobots.add(robotDir)
    console.log(`Robot ${robotDir} downloaded (${normalizedFiles.length} files)`)
  }

  async loadScene(config: SimConfig): Promise<void> {
    await this.loadMuJoCo()

    const robotConfig = ROBOT_CONFIGS[config.robot]
    if (!robotConfig) {
      throw new Error(`Unknown robot: ${config.robot}`)
    }

    // Download robot assets to VFS
    await this.downloadRobotAssets(robotConfig.robotDir)

    // Set up scene directory
    const vfsSceneDir = `/working/scenes/${config.robot}`
    this._ensureDir('/working/scenes')
    this._ensureDir(vfsSceneDir)

    // Copy robot files to scene directory
    const hasObjects = await this._copyRobotToDir(config.robot, robotConfig, vfsSceneDir)

    // Fetch environment XML
    let envXmlPath: string
    if (config.environment === 'basic') {
      envXmlPath = `${ASSET_BASE}/environments/basic.xml`
    } else {
      envXmlPath = `${ASSET_BASE}/environments/${config.environment}/scene.xml`
    }
    const envResponse = await fetch(envXmlPath)
    if (!envResponse.ok) {
      throw new Error(`Environment XML not found: ${envXmlPath}`)
    }
    const envXml = await envResponse.text()

    // Compose scene XML with includes
    const sceneXml = this._createSceneXml(envXml, config.robot, hasObjects, `${config.environment}_${config.robot}`)
    this._writeToFS(`${vfsSceneDir}/scene.xml`, sceneXml)

    // Load model from XML
    const scenePath = `/working/scenes/${config.robot}/scene.xml`
    this.model = this.mujoco.MjModel.loadFromXML(scenePath)
    this.data = new this.mujoco.MjData(this.model)

    // Initialize controller
    if (robotConfig.controllerFactory) {
      this.controller = robotConfig.controllerFactory()
      await this.controller.initialize(this.model, this.data, this.mujoco)
      for (const key of this.controller.getControlKeys()) {
        this.keyStates[key] = false
      }
    }

    this._initialized = true
  }

  step(): void {
    if (!this.model || !this.data || !this.mujoco) return

    this.controller?.step(this.keyStates, this.model, this.data, this.mujoco)

    const timestep = this.model.opt.timestep
    const stepsPerFrame = Math.round(1 / (60 * timestep))
    for (let i = 0; i < stepsPerFrame; i++) {
      this.mujoco.mj_step(this.model, this.data)
    }
  }

  setKeyState(code: string, pressed: boolean): void {
    if (code in this.keyStates) {
      this.keyStates[code] = pressed
    }
  }

  getModel(): MjModel | null { return this.model }
  getData(): MjData | null { return this.data }
  getMuJoCo(): MuJoCoModule | null { return this.mujoco }

  getObservation(): Record<string, number> {
    if (!this.model || !this.data) return {}
    const obs: Record<string, number> = {}
    for (let i = 0; i < this.model.nq; i++) {
      obs[`qpos_${i}`] = this.data.qpos[i]
    }
    return obs
  }

  reset(): void {
    if (!this.model || !this.data || !this.mujoco) return
    this.mujoco.mj_resetData(this.model, this.data)
    this.controller?.reset(this.model, this.data)
  }

  dispose(): void {
    this.model = null
    this.data = null
    this.controller = null
    this.keyStates = {}
    this._initialized = false
  }

  // --- Private helpers ---

  private _ensureDir(path: string): void {
    try {
      if (!this.mujoco.FS.analyzePath(path).exists) {
        this.mujoco.FS.mkdir(path)
      }
    } catch {
      // Directory may already exist
    }
  }

  private _writeToFS(path: string, content: string | Uint8Array): void {
    try { this.mujoco.FS.unlink(path) } catch { /* file doesn't exist */ }
    this.mujoco.FS.writeFile(path, content)
  }

  private async _copyRobotToDir(robotName: string, robotConfig: RobotConfig, targetDir: string): Promise<boolean> {
    if (robotConfig.meshDir) {
      this._ensureDir(`${targetDir}/assets`)
    }

    // Copy robot XML
    const robotXmlResponse = await fetch(`${ASSET_BASE}/robots/${robotConfig.robotDir}/${robotConfig.xmlPath}`)
    let robotXml = await robotXmlResponse.text()
    if (robotConfig.meshDir) {
      robotXml = robotXml.replace(/meshdir="[^"]*"/g, `meshdir="./assets/"`)
    }
    this._writeToFS(`${targetDir}/${robotName}.xml`, robotXml)

    // Copy objects if exists
    let hasObjects = false
    if (robotConfig.objectsPath) {
      try {
        const objectsResponse = await fetch(`${ASSET_BASE}/robots/${robotConfig.robotDir}/${robotConfig.objectsPath}`)
        if (objectsResponse.ok) {
          const objectsXml = await objectsResponse.text()
          this._writeToFS(`${targetDir}/objects.xml`, objectsXml)
          hasObjects = true
        }
      } catch {
        // No objects file
      }
    }

    // Copy mesh files from downloaded robot assets
    if (robotConfig.meshDir) {
      const srcMeshDir = `/working/robots/${robotConfig.robotDir}/assets`
      try {
        const meshFiles: string[] = this.mujoco.FS.readdir(srcMeshDir)
        for (const file of meshFiles) {
          if (file === '.' || file === '..') continue
          try {
            const content = this.mujoco.FS.readFile(`${srcMeshDir}/${file}`)
            this.mujoco.FS.writeFile(`${targetDir}/assets/${file}`, content)
          } catch {
            console.warn(`Failed to copy mesh file: ${file}`)
          }
        }
      } catch (e) {
        console.error('Failed to read mesh directory:', srcMeshDir, e)
      }
    }

    return hasObjects
  }

  private _createSceneXml(envXml: string, robotName: string, hasObjects: boolean, sceneName: string): string {
    const parser = new DOMParser()
    const doc = parser.parseFromString(envXml, 'text/xml')

    if (doc.querySelector('parsererror')) {
      throw new Error('Failed to parse environment XML')
    }

    const mujocoEl = doc.documentElement
    mujocoEl.setAttribute('model', sceneName)

    // Create include element for robot
    const robotInclude = doc.createElement('include')
    robotInclude.setAttribute('file', `${robotName}.xml`)
    mujocoEl.insertBefore(robotInclude, mujocoEl.firstChild)

    // Add objects include if exists
    if (hasObjects) {
      const objectsInclude = doc.createElement('include')
      objectsInclude.setAttribute('file', 'objects.xml')
      mujocoEl.insertBefore(objectsInclude, robotInclude.nextSibling)
    }

    const serializer = new XMLSerializer()
    let result = serializer.serializeToString(doc)
    result = result.replace(/(<\?xml[^?]*\?>)/g, '')
    result = result.replace(/\s+xmlns="[^"]*"/g, '')
    result = result.replace(/\s+xmlns:[a-z]+="[^"]*"/g, '')
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + result.trim()

    return result
  }
}
