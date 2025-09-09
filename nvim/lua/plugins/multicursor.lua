return {
  'jake-stewart/multicursor.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  branch = '1.0',
  config = function()
    local mc = require 'multicursor-nvim'
    mc.setup()

    require('utils').keymapSetList {
      {
        'n',
        '<c-N>',
        function()
          mc.matchAddCursor(1)
        end,
        { desc = 'Add a cursor and jump to the previous word under cursor' },
      },
      {
        'n',
        '<c-S>',
        function()
          mc.matchSkipCursor(1)
        end,
        { desc = 'Jump to the previous word under cursor but do not add a cursor' },
      },
    }

    -- Customize how cursors look.
    local hl = vim.api.nvim_set_hl
    hl(0, 'MultiCursorCursor', { reverse = true })
    hl(0, 'MultiCursorVisual', { link = 'Visual' })
    hl(0, 'MultiCursorSign', { link = 'SignColumn' })
    hl(0, 'MultiCursorMatchPreview', { link = 'Search' })
    hl(0, 'MultiCursorDisabledCursor', { reverse = true })
    hl(0, 'MultiCursorDisabledVisual', { link = 'Visual' })
    hl(0, 'MultiCursorDisabledSign', { link = 'SignColumn' })
  end,
}
