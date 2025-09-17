import { runTests } from '../src/playground/examples/example.spec';

describe('Playground Tests', () => {
    it('should run all example tests', async () => {
        const results = await runTests();
        expect(results).toBeTruthy();
    });
});