import {describe, it, expect} from 'vitest';
import {fmt, sci, hms24, hm24, durHM, DEG} from '../../engine/format.js';

describe('format.js — числа в стилі серії', () => {
  it('fmt: десяткова кома і справжній мінус', () => {
    expect(fmt(3.14159, 2)).toBe('3,14');
    expect(fmt(-57.8)).toBe('−57,8');
    expect(fmt(8)).toBe('8,0');
    expect(fmt(12, 0)).toBe('12');
  });
  it('sci: мантиса і степінь верхніми індексами', () => {
    expect(sci(1.602176634e-19)).toBe('1,602·10⁻¹⁹');
    expect(sci(6371e3, 2)).toBe('6,37·10⁶');
    expect(sci(0)).toBe('0,000');
  });
  it('час доби і тривалість', () => {
    expect(hms24(14.535)).toBe('14 г 32 хв 06 с');
    expect(hm24(-1)).toBe('23 г 00 хв');
    expect(durHM(122)).toBe('2 год 02 хв 00 с');
    expect(durHM(47.2)).toBe('47 хв 12 с');
  });
  it('DEG', () => { expect(180 * DEG).toBe(Math.PI); });
});
