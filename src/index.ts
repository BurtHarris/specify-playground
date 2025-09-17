// This file serves as the entry point for the playground. It initializes the playground environment and may import and execute the specifications and tests.

import { initializePlayground } from './lib';
import './playground/demo.specify';
import './playground/examples/example.spec';

initializePlayground();