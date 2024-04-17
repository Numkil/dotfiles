return {
  -- Adds git related signs to the gutter, as well as utilities for managing changes
  'echasnovski/mini.diff',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('mini.diff').setup {
      view = {
        style = 'sign',
      },
    }
  end,
}
