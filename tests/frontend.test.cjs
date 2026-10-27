const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('templates/index.html', 'utf8');
const match = source.match(/        async function fetchRules\(\) \{[\s\S]*?\n        \}\n\n        async function getGeo/);
assert.ok(match, 'fetchRules must exist');
const func = match[0].slice(0, match[0].lastIndexOf('\n\n        async function getGeo'));

async function exercise(response) {
    const observed = { rendered: null, error: null };
    const context = {
        fetch: async () => response,
        statsHistory: { size: 1 },
        setLoading: () => {},
        renderRules: data => { observed.rendered = data; },
        showError: error => { observed.error = error; },
    };
    vm.runInNewContext(func + '\nthis.run = fetchRules;', context);
    await context.run();
    return observed;
}

test('valid ruleset JSON is rendered', async () => {
    const result = await exercise(new Response(JSON.stringify({nftables: []}), {
        status: 200, headers: {'content-type': 'application/json'},
    }));
    assert.deepEqual(result.rendered, {nftables: []});
    assert.equal(result.error, null);
});

test('JSON error detail reaches the user', async () => {
    const result = await exercise(new Response(JSON.stringify({detail: 'Firewall unavailable'}), {
        status: 503, headers: {'content-type': 'application/json; charset=utf-8'},
    }));
    assert.equal(result.error, 'Firewall unavailable');
});

for (const status of [200, 502]) {
    test('HTML response gives an informative error for status ' + status, async () => {
        const result = await exercise(new Response('<!DOCTYPE html>', {
            status, headers: {'content-type': 'text/html'},
        }));
        assert.equal(result.rendered, null);
        assert.equal(result.error, 'Failed to fetch rules: unexpected response (HTTP ' + status + ')');
    });
}
