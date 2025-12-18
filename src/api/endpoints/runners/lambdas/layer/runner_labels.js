const fs = require('fs');
const path = require('path');

class LabelParseError extends Error {
  constructor(message) {
    super(message);
    this.name = 'LabelParseError';
  }
}

class LabelValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'LabelValidationError';
  }
}

function findConfigFile() {
  // Try ETC_PATH environment variable
  const etcPath = process.env.ETC_PATH;
  if (etcPath) {
    const configPath = path.join(etcPath, 'runners.json');
    if (fs.existsSync(configPath)) {
      return configPath;
    }
  }

  // Try relative to this file (Lambda layer deployment: /opt/nodejs/runners-layer/etc/)
  const layerPath = path.join(__dirname, 'etc', 'runners.json');
  if (fs.existsSync(layerPath)) {
    return layerPath;
  }

  // Try repo root structure (local development: src/api/endpoints/runners/lambdas/layer/)
  const repoPath = path.join(__dirname, '..', '..', '..', '..', '..', '..', 'etc', 'runners.json');
  if (fs.existsSync(repoPath)) {
    return repoPath;
  }

  // Try current working directory
  const cwdPath = path.join(process.cwd(), 'etc', 'runners.json');
  if (fs.existsSync(cwdPath)) {
    return cwdPath;
  }

  throw new Error(
    'Could not find etc/runners.json. ' +
    'Set ETC_PATH environment variable or run from repo root.'
  );
}

function loadConfig() {
  const configPath = findConfigFile();
  const content = fs.readFileSync(configPath, 'utf-8');
  return JSON.parse(content);
}

// Load configuration from JSON (single source of truth)
const config = loadConfig();
const labels = config.labels || {};

// Valid label values from JSON
const PLATFORMS = new Set(labels.platforms || ['ecs', 'ec2']);
const PRICING_MODELS = new Set(labels.pricing_models || ['spot', 'on-demand']);

// ECS labels from JSON
const ecsConfig = labels.ecs || {};
const ECS_COMPUTE = new Set(ecsConfig.compute_types || ['fargate']);
const ECS_ARCHITECTURES = new Set(ecsConfig.architectures || ['x86', 'arm']);

// EC2 labels from JSON
const ec2Config = labels.ec2 || {};
const EC2_COMPUTE = new Set(ec2Config.compute_types || []);
const EC2_ARCHITECTURES = new Set(ec2Config.architectures || []);
const EC2_COMPUTE_REQUIRES_ARCH = new Set(ec2Config.compute_requires_arch || []);
const EC2_COMPUTE_FORBIDS_ARCH = new Set(ec2Config.compute_forbids_arch || []);

// All compute types (derived)
const COMPUTE_TYPES = new Set([...ECS_COMPUTE, ...EC2_COMPUTE]);

// All architecture labels
const ALL_ARCHITECTURES = new Set([...ECS_ARCHITECTURES, ...EC2_ARCHITECTURES]);

// Instance type mapping from JSON
const instanceMap = labels.instance_type_map || {};
const INSTANCE_TYPE_MAP = {};
for (const [compute, archMap] of Object.entries(instanceMap)) {
  if (typeof archMap === 'object' && archMap !== null) {
    for (const [arch, instanceType] of Object.entries(archMap)) {
      INSTANCE_TYPE_MAP[`${compute}:${arch}`] = instanceType;
    }
  } else {
    // No architecture (gpu, fpga)
    INSTANCE_TYPE_MAP[`${compute}:null`] = archMap;
  }
}

// ECS task architecture mapping from JSON
const ECS_TASK_ARCHITECTURE_MAP = labels.ecs_task_architecture_map || {};

// ECS Fargate configuration from JSON
const fargateConfig = config.fargate || {};
const ECS_FARGATE_CONFIG = {
  cpu: fargateConfig.cpu || '4096',
  memory: fargateConfig.memory || '16384'
};

// Runner ID pattern
const RUNNER_ID_PATTERN = /^runner-(\d+)$/;

function parseLabels(labelList) {
  if (!labelList || labelList.length === 0) {
    throw new LabelParseError('Label list cannot be empty');
  }

  const labelSet = new Set(labelList);

  // Extract platform
  const platformLabels = [...labelSet].filter(l => PLATFORMS.has(l));
  if (platformLabels.length === 0) {
    throw new LabelParseError(
      `Missing platform label. Must be one of: ${[...PLATFORMS].sort().join(', ')}`
    );
  }
  if (platformLabels.length > 1) {
    throw new LabelParseError(
      `Multiple platform labels found: ${platformLabels.sort().join(', ')}`
    );
  }
  const platform = platformLabels[0];

  // Extract compute type
  const computeLabels = [...labelSet].filter(l => COMPUTE_TYPES.has(l));
  if (computeLabels.length === 0) {
    throw new LabelParseError(
      `Missing compute label. Must be one of: ${[...COMPUTE_TYPES].sort().join(', ')}`
    );
  }
  if (computeLabels.length > 1) {
    throw new LabelParseError(
      `Multiple compute labels found: ${computeLabels.sort().join(', ')}`
    );
  }
  const compute = computeLabels[0];

  // Extract architecture (may be null for gpu/fpga)
  const archLabels = [...labelSet].filter(l => ALL_ARCHITECTURES.has(l));
  if (archLabels.length > 1) {
    throw new LabelParseError(
      `Multiple architecture labels found: ${archLabels.sort().join(', ')}`
    );
  }
  const architecture = archLabels.length > 0 ? archLabels[0] : null;

  // Extract pricing model
  const pricingLabels = [...labelSet].filter(l => PRICING_MODELS.has(l));
  if (pricingLabels.length === 0) {
    throw new LabelParseError(
      `Missing pricing label. Must be one of: ${[...PRICING_MODELS].sort().join(', ')}`
    );
  }
  if (pricingLabels.length > 1) {
    throw new LabelParseError(
      `Multiple pricing labels found: ${pricingLabels.sort().join(', ')}`
    );
  }
  const pricing = pricingLabels[0];

  // Extract runner ID
  let runnerId = null;
  for (const label of labelList) {
    const match = label.match(RUNNER_ID_PATTERN);
    if (match) {
      runnerId = label;
      break;
    }
  }

  if (!runnerId) {
    throw new LabelParseError(
      'Missing runner ID label. Must match pattern: runner-{number}'
    );
  }

  return {
    platform,
    compute,
    pricing,
    runnerId,
    architecture
  };
}

function validateLabels(parsed) {
  // ECS validation
  if (parsed.platform === 'ecs') {
    if (!ECS_COMPUTE.has(parsed.compute)) {
      throw new LabelValidationError(
        `ECS platform only supports compute types: ${[...ECS_COMPUTE].sort().join(', ')}. ` +
        `Got: ${parsed.compute}`
      );
    }
    // ECS requires architecture
    if (parsed.architecture === null) {
      throw new LabelValidationError(
        `ECS platform requires architecture label. ` +
        `Must be one of: ${[...ECS_ARCHITECTURES].sort().join(', ')}`
      );
    }
    // ECS architecture must be valid
    if (!ECS_ARCHITECTURES.has(parsed.architecture)) {
      throw new LabelValidationError(
        `ECS platform only supports architectures: ${[...ECS_ARCHITECTURES].sort().join(', ')}. ` +
        `Got: ${parsed.architecture}`
      );
    }
  }

  // EC2 validation
  if (parsed.platform === 'ec2') {
    if (!EC2_COMPUTE.has(parsed.compute)) {
      throw new LabelValidationError(
        `EC2 platform only supports compute types: ${[...EC2_COMPUTE].sort().join(', ')}. ` +
        `Got: ${parsed.compute}`
      );
    }

    // Check architecture requirements based on compute type
    if (EC2_COMPUTE_REQUIRES_ARCH.has(parsed.compute)) {
      if (parsed.architecture === null) {
        throw new LabelValidationError(
          `EC2 compute type '${parsed.compute}' requires architecture label. ` +
          `Must be one of: ${[...EC2_ARCHITECTURES].sort().join(', ')}`
        );
      }
      if (!EC2_ARCHITECTURES.has(parsed.architecture)) {
        throw new LabelValidationError(
          `EC2 platform only supports architectures: ` +
          `${[...EC2_ARCHITECTURES].sort().join(', ')}. Got: ${parsed.architecture}`
        );
      }
    }

    if (EC2_COMPUTE_FORBIDS_ARCH.has(parsed.compute)) {
      if (parsed.architecture !== null) {
        throw new LabelValidationError(
          `EC2 compute type '${parsed.compute}' does not support ` +
          `architecture label. Got: ${parsed.architecture}`
        );
      }
    }
  }
}

function getInstanceType(parsed) {
  if (parsed.platform === 'ecs') {
    return null;
  }
  const key = `${parsed.compute}:${parsed.architecture}`;
  return INSTANCE_TYPE_MAP[key] || null;
}

function getEcsConfig(parsed) {
  if (parsed.platform !== 'ecs') {
    return null;
  }
  if (parsed.compute === 'fargate') {
    return { ...ECS_FARGATE_CONFIG };
  }
  return null;
}

function getTaskArchitecture(parsed) {
  if (parsed.platform !== 'ecs') {
    return null;
  }
  if (parsed.architecture === null) {
    return null;
  }
  return ECS_TASK_ARCHITECTURE_MAP[parsed.architecture] || null;
}

function isSpot(parsed) {
  return parsed.pricing === 'spot';
}

function getRunnerIdNumber(parsed) {
  const match = parsed.runnerId.match(RUNNER_ID_PATTERN);
  if (match) {
    return parseInt(match[1], 10);
  }
  throw new LabelParseError(`Invalid runner ID format: ${parsed.runnerId}`);
}

module.exports = {
  parseLabels,
  validateLabels,
  getInstanceType,
  getEcsConfig,
  getTaskArchitecture,
  isSpot,
  getRunnerIdNumber,
  LabelParseError,
  LabelValidationError,
  // Export constants for testing
  PLATFORMS,
  PRICING_MODELS,
  ECS_COMPUTE,
  ECS_ARCHITECTURES,
  EC2_COMPUTE,
  EC2_ARCHITECTURES,
  COMPUTE_TYPES,
  ALL_ARCHITECTURES
};
