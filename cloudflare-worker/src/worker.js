// Runtime entrypoint: helper constants/functions exported for Node regressions
// belong to a supporting module, not the workerd service export map.
import worker from './index.js';
export default worker;
