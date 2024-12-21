return {
  'smoka7/hop.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  version = '*',
  config = function()
    local hop = require 'hop'
    hop.setup()
    local directions = require('hop.hint').HintDirection

    require('utils').keymapSetList {
      {
        { 'n', 'v' },
        'f',
        function()
          hop.hint_char1 { direction = directions.AFTER_CURSOR, current_line_only = true }
        end,
        { desc = 'Hop [f]orward in line' },
      },
      {
        { 'n', 'v' },
        'F',
        function()
          hop.hint_char1 { direction = directions.BEFORE_CURSOR, current_line_only = true }
        end,
        { desc = 'Hop backwards in line' },
      },
      {
        { 'n', 'v' },
        't',
        function()
          hop.hint_words { direction = directions.AFTER_CURSOR, current_line_only = false, hint_offset = -1 }
        end,
        { desc = 'Hop [t]o word' },
      },
      {
        { 'n', 'v' },
        'T',
        function()
          hop.hint_words { direction = directions.BEFORE_CURSOR, current_line_only = false, hint_offset = 1 }
        end,
        { desc = 'Hop backwards to word' },
      },
    }
  end,
}
