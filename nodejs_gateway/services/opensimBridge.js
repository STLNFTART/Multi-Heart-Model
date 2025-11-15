/**
 * OpenSim integration service for Multi-Heart-Model
 *
 * Provides Node.js-based OpenSim simulation orchestration:
 * - Generates OpenSim motion files from HBCM cardiac data
 * - Executes OpenSim CLI commands
 * - Parses biomechanical results
 * - Returns structured data for analysis
 *
 * Author: Multi-Heart-Model Team
 * License: MIT
 */

const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const { promisify } = require('util');
const execAsync = promisify(exec);

class OpenSimBridge {
    /**
     * Initialize OpenSim bridge service
     *
     * @param {Object} config - Configuration options
     * @param {string} config.opensimBin - Path to OpenSim executable (default: 'opensim-cmd')
     * @param {string} config.modelsDir - Directory containing .osim model files
     * @param {string} config.resultsDir - Directory for output files
     * @param {string} config.defaultModel - Default OpenSim model file
     */
    constructor(config = {}) {
        this.config = {
            opensimBin: config.opensimBin || 'opensim-cmd',
            modelsDir: config.modelsDir || '/opt/opensim/models',
            resultsDir: config.resultsDir || '/tmp/opensim_results',
            defaultModel: config.defaultModel || 'gait2392.osim',
            timeout: config.timeout || 300000,  // 5 minutes
            ...config
        };

        // Ensure results directory exists
        this._ensureDirectories();
    }

    async _ensureDirectories() {
        try {
            await fs.mkdir(this.config.resultsDir, { recursive: true });
        } catch (err) {
            console.error('Failed to create results directory:', err);
        }
    }

    /**
     * Generate OpenSim motion file (.mot) from HBCM cardiac trajectory
     *
     * Converts cardiac Van der Pol oscillator state to muscle activation patterns
     * suitable for OpenSim biomechanical simulation.
     *
     * @param {Object} data - Input data
     * @param {Array} data.cardiac - Cardiac trajectory {x: [], y: []}
     * @param {Array} data.neural - Neural trajectory (optional) {v: [], w: []}
     * @param {Object} data.config - Configuration {dt: 0.001, ...}
     * @returns {string} Path to generated .mot file
     */
    async generateMotion({ neural, cardiac, config }) {
        if (!cardiac || !cardiac.x || !cardiac.y) {
            throw new Error('Cardiac trajectory required with x and y arrays');
        }

        const dt = config?.dt || 0.001;
        const n_timesteps = cardiac.x.length;

        // Generate time array
        const times = Array.from({ length: n_timesteps }, (_, i) => i * dt);

        // Normalize cardiac x-values to [0, 1] activation range
        const x_values = cardiac.x;
        const x_min = Math.min(...x_values);
        const x_max = Math.max(...x_values);
        const x_norm = x_values.map(x => (x - x_min) / (x_max - x_min + 1e-10));

        // Muscle configuration
        const n_muscles = config?.n_muscles || 8;
        const muscle_names = config?.muscle_names || this._getDefaultMuscleNames(n_muscles);

        // Estimate cardiac frequency for phase distribution
        const cardiac_freq = this._estimateFrequency(times, x_values);

        // Generate phase-distributed muscle activations
        const activations = this._generateActivations(
            times,
            x_norm,
            n_muscles,
            cardiac_freq,
            config?.mapping || 'phase_distributed'
        );

        // Create .mot file content
        const motContent = this._createMotFileContent(
            times,
            activations,
            muscle_names
        );

        // Write to file
        const timestamp = Date.now();
        const motFilePath = path.join(
            this.config.resultsDir,
            `cardiac_motion_${timestamp}.mot`
        );

        await fs.writeFile(motFilePath, motContent);

        return motFilePath;
    }

    /**
     * Get default muscle names for gait simulation
     */
    _getDefaultMuscleNames(n_muscles) {
        const names = [
            'glut_max_r',
            'hamstrings_r',
            'rect_fem_r',
            'vasti_r',
            'bifemsh_r',
            'gastroc_r',
            'soleus_r',
            'tib_ant_r',
            'glut_max_l',
            'hamstrings_l',
            'rect_fem_l',
            'vasti_l'
        ];

        return names.slice(0, n_muscles);
    }

    /**
     * Estimate dominant frequency from signal
     */
    _estimateFrequency(times, signal) {
        if (signal.length < 3) return 1.0;

        // Simple zero-crossing method
        const mean = signal.reduce((a, b) => a + b, 0) / signal.length;
        const centered = signal.map(s => s - mean);

        let crossings = [];
        for (let i = 1; i < centered.length; i++) {
            if (centered[i - 1] < 0 && centered[i] >= 0) {
                crossings.push(times[i]);
            }
        }

        if (crossings.length < 2) return 1.0;

        // Calculate average period (2x half-period)
        const periods = [];
        for (let i = 1; i < crossings.length; i++) {
            periods.push(crossings[i] - crossings[i - 1]);
        }

        const avgPeriod = periods.reduce((a, b) => a + b, 0) / periods.length;
        return 1.0 / (2.0 * avgPeriod);
    }

    /**
     * Generate muscle activation patterns from cardiac rhythm
     */
    _generateActivations(times, x_norm, n_muscles, freq, mapping) {
        const n_timesteps = times.length;
        const activations = [];

        for (let t_idx = 0; t_idx < n_timesteps; t_idx++) {
            const t = times[t_idx];
            const activation_row = [];

            for (let muscle_idx = 0; muscle_idx < n_muscles; muscle_idx++) {
                let activation;

                if (mapping === 'phase_distributed') {
                    // Phase offset for each muscle
                    const phase = 2 * Math.PI * muscle_idx / n_muscles;
                    activation = x_norm[t_idx] * (0.5 + 0.5 * Math.cos(2 * Math.PI * freq * t + phase));
                } else if (mapping === 'direct') {
                    // All muscles get same activation
                    activation = x_norm[t_idx];
                } else {
                    activation = x_norm[t_idx];
                }

                // Clamp to [0, 1]
                activation_row.push(Math.max(0, Math.min(1, activation)));
            }

            activations.push(activation_row);
        }

        return activations;
    }

    /**
     * Create OpenSim .mot file content
     */
    _createMotFileContent(times, activations, muscle_names) {
        const lines = [];

        // Header
        lines.push('Cardiac-Derived Muscle Activations');
        lines.push(`nRows=${times.length}`);
        lines.push(`nColumns=${muscle_names.length + 1}`);
        lines.push('inDegrees=no');
        lines.push('endheader');

        // Column headers
        lines.push(['time', ...muscle_names].join('\t'));

        // Data rows
        for (let i = 0; i < times.length; i++) {
            const row = [
                times[i].toFixed(6),
                ...activations[i].map(a => a.toFixed(6))
            ];
            lines.push(row.join('\t'));
        }

        return lines.join('\n');
    }

    /**
     * Run OpenSim forward dynamics simulation
     *
     * @param {Object} params - Simulation parameters
     * @param {string} params.motionFile - Path to .mot file with muscle activations
     * @param {string} params.modelFile - Path to .osim model (optional, uses default)
     * @param {string} params.setupFile - Path to setup XML (optional)
     * @returns {Object} Results object {success, outputFile, stdout, stderr, forces}
     */
    async runForwardDynamics({ motionFile, modelFile, setupFile }) {
        const model = modelFile || path.join(this.config.modelsDir, this.config.defaultModel);
        const setup = setupFile || path.join(this.config.modelsDir, 'forward_dynamics_setup.xml');

        const timestamp = Date.now();
        const outputFile = path.join(
            this.config.resultsDir,
            `biomechanics_${timestamp}.sto`
        );

        // Construct OpenSim command
        // Note: Syntax may vary depending on OpenSim version
        const cmd = [
            this.config.opensimBin,
            'run-tool',
            setup,
            '-model', model,
            '-motion', motionFile,
            '-results', outputFile
        ].join(' ');

        try {
            // Execute OpenSim simulation
            const { stdout, stderr } = await execAsync(cmd, {
                timeout: this.config.timeout
            });

            // Extract force summaries
            const forces = await this.extractForces(outputFile);

            return {
                success: true,
                outputFile,
                stdout,
                stderr,
                forces
            };

        } catch (error) {
            return {
                success: false,
                outputFile: '',
                stdout: error.stdout || '',
                stderr: error.stderr || error.message,
                forces: {}
            };
        }
    }

    /**
     * Parse OpenSim .sto (storage) results file
     *
     * @param {string} stoFilePath - Path to .sto file
     * @returns {Object} Dictionary mapping column names to arrays
     */
    async parseResults(stoFilePath) {
        try {
            const content = await fs.readFile(stoFilePath, 'utf-8');
            const lines = content.split('\n');

            let headerComplete = false;
            let columns = [];
            const data = {};

            for (const line of lines) {
                // Skip empty lines
                if (!line.trim()) continue;

                // Detect end of header
                if (line.startsWith('endheader')) {
                    headerComplete = true;
                    continue;
                }

                if (!headerComplete) continue;

                // First line after header is column names
                if (columns.length === 0) {
                    columns = line.trim().split(/\s+/);
                    columns.forEach(col => data[col] = []);
                    continue;
                }

                // Data lines
                const values = line.trim().split(/\s+/);
                if (values.length !== columns.length) continue;  // Skip malformed lines

                columns.forEach((col, idx) => {
                    const value = parseFloat(values[idx]);
                    if (!isNaN(value)) {
                        data[col].push(value);
                    }
                });
            }

            return data;

        } catch (err) {
            console.error('Failed to parse .sto file:', err);
            return {};
        }
    }

    /**
     * Extract force/moment statistics from results
     *
     * @param {string} resultsFile - Path to .sto results file
     * @returns {Object} Force statistics by variable name
     */
    async extractForces(resultsFile) {
        const data = await this.parseResults(resultsFile);
        const forces = {};

        for (const [key, values] of Object.entries(data)) {
            const keyLower = key.toLowerCase();

            // Identify force/moment columns
            if (keyLower.includes('force') ||
                keyLower.includes('moment') ||
                keyLower.includes('torque') ||
                keyLower.includes('grf')) {

                forces[key] = {
                    mean: this._mean(values),
                    max: Math.max(...values),
                    min: Math.min(...values),
                    std: this._std(values),
                    rms: this._rms(values)
                };
            }
        }

        return forces;
    }

    /**
     * Calculate mean
     */
    _mean(values) {
        return values.reduce((a, b) => a + b, 0) / values.length;
    }

    /**
     * Calculate standard deviation
     */
    _std(values) {
        const mean = this._mean(values);
        const variance = values.reduce((sum, val) =>
            sum + Math.pow(val - mean, 2), 0) / values.length;
        return Math.sqrt(variance);
    }

    /**
     * Calculate RMS (root mean square)
     */
    _rms(values) {
        const sumSquares = values.reduce((sum, val) => sum + val * val, 0);
        return Math.sqrt(sumSquares / values.length);
    }

    /**
     * Create closed-loop feedback from biomechanical results
     *
     * Extracts parameters that can be fed back into HBCM simulation
     * to create physiologically-realistic coupling.
     *
     * @param {Object} kinematics - Parsed OpenSim results
     * @returns {Object} Feedback parameters
     */
    async createFeedback(kinematics) {
        const feedback = {
            cardiac_afterload_factor: 1.0,
            total_mechanical_power: 0.0,
            peak_ground_reaction_force: 0.0,
            metabolic_cost: 0.0
        };

        // Calculate total mechanical power from joint powers
        let total_power = 0.0;
        for (const [key, values] of Object.entries(kinematics)) {
            if (key.toLowerCase().includes('power')) {
                total_power += Math.abs(this._mean(values));
            }
        }

        feedback.total_mechanical_power = total_power;

        // Find peak ground reaction force
        for (const [key, values] of Object.entries(kinematics)) {
            if (key.toLowerCase().includes('grf') ||
                key.toLowerCase().includes('ground')) {
                const peak = Math.max(...values.map(Math.abs));
                feedback.peak_ground_reaction_force = Math.max(
                    feedback.peak_ground_reaction_force,
                    peak
                );
            }
        }

        // Estimate cardiac afterload adjustment
        // Higher mechanical work → increased cardiac load
        if (total_power > 0) {
            const normalized_power = Math.min(total_power / 100.0, 1.0);
            feedback.cardiac_afterload_factor = 1.0 + 0.5 * normalized_power;
        }

        // Estimate metabolic cost (mechanical work / efficiency ≈ 20-25%)
        feedback.metabolic_cost = total_power * 4.5;

        return feedback;
    }
}

module.exports = OpenSimBridge;
