import { describe, expect, it } from 'vitest'

import { FORWARD_SQUARE_FRAMES, FORWARD_SQUARE_WIDTH } from '../components/thinking.js'

const FILLED = '▰'
const EMPTY = '▱'

describe('forward-square spinner frames', () => {
  it('sweeps the filled block strictly forward, one cell per frame, no bounce', () => {
    const positions = FORWARD_SQUARE_FRAMES.map(frame => [...frame].indexOf(FILLED))

    expect(positions).toEqual([...Array(FORWARD_SQUARE_WIDTH).keys()])
  })

  it('keeps every frame a fixed width with exactly one filled cell', () => {
    for (const cells of FORWARD_SQUARE_FRAMES.map(frame => [...frame])) {
      expect(cells).toHaveLength(FORWARD_SQUARE_WIDTH)
      expect(cells.filter(c => c === FILLED)).toHaveLength(1)
      expect(cells.filter(c => c === EMPTY)).toHaveLength(FORWARD_SQUARE_WIDTH - 1)
    }
  })
})

