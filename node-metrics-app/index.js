const express = require('express');
const client = require('prom-client');

const app = express();
const port = 3000;

// Create a Registry to store metrics
const register = new client.Registry();
client.collectDefaultMetrics({ register });

// Create a custom counter metric
const customCounter = new client.Counter({
    name: 'my_custom_metric_total',
    help: 'A custom counter for testing Prometheus'
});
register.registerMetric(customCounter);

// Increment the metric every time the home page is visited
app.get('/', (req, res) => {
    customCounter.inc();
    res.send('Hello! The custom metric has been incremented.');
});

// Expose the /metrics endpoint for Prometheus to scrape
app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
});

app.listen(port, () => {
    console.log(`App running at http://localhost:${port}`);
});