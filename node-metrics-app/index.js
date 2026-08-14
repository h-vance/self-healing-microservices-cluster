const express = require('express');
const client = require('prom-client');

function createApp({ chaosEnabled = process.env.CHAOS_ENABLED === 'true' } = {}) {
    const app = express();
    const register = new client.Registry();

    client.collectDefaultMetrics({ register });

    const customCounter = new client.Counter({
        name: 'my_custom_metric_total',
        help: 'A custom counter for testing Prometheus',
        registers: [register],
    });

    // Fault-injection state. Only mutable when CHAOS_ENABLED=true, so the
    // published image cannot be pushed into an unhealthy state by default.
    const chaos = { healthy: true, ballast: [] };

    // Registers itself with the registry; Prometheus scrapes it via /metrics,
    // which is what lets an alert rule fire on injected unhealthiness.
    new client.Gauge({
        name: 'app_health_status',
        help: 'Reports 1 when /healthz returns 200, 0 when fault injection has forced it unhealthy',
        registers: [register],
        collect() {
            this.set(chaos.healthy ? 1 : 0);
        },
    });

    app.get('/healthz', (req, res) => {
        if (!chaos.healthy) {
            // Liveness probe fails here, so the kubelet restarts the container.
            res.status(503).json({ status: 'unhealthy', reason: 'fault_injected' });
            return;
        }

        res.status(200).json({ status: 'ok' });
    });

    if (chaosEnabled) {
        // Flip /healthz to 503 so the liveness probe fails and the Deployment
        // controller has something real to recover from.
        app.post('/admin/toggle-health', (req, res) => {
            chaos.healthy = !chaos.healthy;
            res.status(200).json({ healthy: chaos.healthy });
        });

        // Allocate until the container exceeds its memory limit and the kubelet
        // OOM-kills it. Buffers are used so the allocation is not optimized away.
        app.post('/admin/exhaust-memory', (req, res) => {
            const chunkMb = Number(req.query.chunk_mb || 8);
            res.status(202).json({ status: 'allocating', chunk_mb: chunkMb });

            const grow = () => {
                chaos.ballast.push(Buffer.alloc(chunkMb * 1024 * 1024, 1));
                setImmediate(grow);
            };
            setImmediate(grow);
        });
    }

    app.get('/', (req, res) => {
        customCounter.inc();
        res.send('Hello! The custom metric has been incremented.');
    });

    app.get('/metrics', async (req, res, next) => {
        try {
            res.set('Content-Type', register.contentType);
            res.end(await register.metrics());
        } catch (error) {
            next(error);
        }
    });

    return { app, register };
}

function start() {
    const port = Number(process.env.PORT || 3000);
    const { app } = createApp();

    return app.listen(port, () => {
        console.log(`App running at http://localhost:${port}`);
    });
}

if (require.main === module) {
    start();
}

module.exports = { createApp, start };
