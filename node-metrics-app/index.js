const express = require('express');
const client = require('prom-client');

function createApp() {
    const app = express();
    const register = new client.Registry();

    client.collectDefaultMetrics({ register });

    const customCounter = new client.Counter({
        name: 'my_custom_metric_total',
        help: 'A custom counter for testing Prometheus',
        registers: [register],
    });

    app.get('/healthz', (req, res) => {
        res.status(200).json({ status: 'ok' });
    });

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
