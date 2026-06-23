import express from 'express';
import healthRouter from '../../src/server/routes/health';

describe('Health Route', () => {
  let app: express.Express;

  beforeEach(() => {
    app = express();
    app.use(express.json());
    app.use('/api', healthRouter);
  });

  it('route is defined and exports a router', () => {
    // Verify the router is a function (Express Router)
    expect(typeof healthRouter).toBe('function');
    // Verify it has standard router methods
    expect(typeof healthRouter.get).toBe('function');
    expect(typeof healthRouter.post).toBe('function');
  });

  it('creates an app with the health route mounted', () => {
    // Verify the app has the route registered
    const routes = app._router.stack
      .filter((layer: any) => layer.route || layer.name === 'router')
      .map((layer: any) => layer.route?.path || layer.regexp?.toString())
      .filter(Boolean);
    expect(routes.length).toBeGreaterThan(0);
  });
});
