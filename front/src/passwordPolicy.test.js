import { TextEncoder } from 'util';
import { isValidPassword } from './passwordPolicy';

global.TextEncoder = TextEncoder;

test.each(['spaces & symbols!', '안전한 암호! 123', 'x'.repeat(72)])('accepts supported password: %s', value => {
  expect(isValidPassword(value)).toBe(true);
});
test.each(['short', 'x'.repeat(73), '한'.repeat(25)])('rejects password outside character/byte bounds', value => {
  expect(isValidPassword(value)).toBe(false);
});
