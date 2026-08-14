const assert = require('node:assert/strict');
const { once } = require('node:events');
const test = require('node:test');

const { createApp } = require('./index');

async function withServer(fn, options = {}) {
    const { app } = createApp(options);
    const server = app.listen(0);
    await once(server, 'listening');

    try {
        const { port } = server.address();
        await fn(`http://127.0.0.1:${port}`);
    } finally {
        server.close();
        await once(server, 'close');
    }
}

test('health endpoint reports ok', async () => {
    await withServer(async (baseUrl) => {
        const response = await fetch(`${baseUrl}/healthz`);

        assert.equal(response.status, 200);
        assert.deepEqual(await response.json(), { status: 'ok' });
    });
});

test('root endpoint increments custom metric', async () => {
    await withServer(async (baseUrl) => {
        const response = await fetch(`${baseUrl}/`);
        const metrics = await fetch(`${baseUrl}/metrics`);
        const body = await metrics.text();

        assert.equal(response.status, 200);
        assert.match(await response.text(), /custom metric has been incremented/);
        assert.match(body, /my_custom_metric_total 1/);
    });
});

test('metrics endpoint exposes Prometheus content type', async () => {
    await withServer(async (baseUrl) => {
        const response = await fetch(`${baseUrl}/metrics`);

        assert.equal(response.status, 200);
        assert.match(response.headers.get('content-type'), /text\/plain/);
    });
});

test('admin routes are absent unless chaos is enabled', async () => {
    await withServer(async (baseUrl) => {
        const response = await fetch(`${baseUrl}/admin/toggle-health`, { method: 'POST' });

        assert.equal(response.status, 404);
    }, { chaosEnabled: false });
});

test('toggling health makes the liveness endpoint fail', async () => {
    await withServer(async (baseUrl) => {
        const toggled = await fetch(`${baseUrl}/admin/toggle-health`, { method: 'POST' });
        assert.equal(toggled.status, 200);
        assert.deepEqual(await toggled.json(), { healthy: false });

        const unhealthy = await fetch(`${baseUrl}/healthz`);
        assert.equal(unhealthy.status, 503);
        assert.deepEqual(await unhealthy.json(), { status: 'unhealthy', reason: 'fault_injected' });

        const restored = await fetch(`${baseUrl}/admin/toggle-health`, { method: 'POST' });
        assert.deepEqual(await restored.json(), { healthy: true });
        assert.equal((await fetch(`${baseUrl}/healthz`)).status, 200);
    }, { chaosEnabled: true });
});

test('health gauge tracks injected state', async () => {
    await withServer(async (baseUrl) => {
        assert.match(await (await fetch(`${baseUrl}/metrics`)).text(), /app_health_status 1/);

        await fetch(`${baseUrl}/admin/toggle-health`, { method: 'POST' });

        assert.match(await (await fetch(`${baseUrl}/metrics`)).text(), /app_health_status 0/);
    }, { chaosEnabled: true });
});
