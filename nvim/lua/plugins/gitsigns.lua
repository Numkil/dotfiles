return {
  -- Adds git related signs to the gutter, as well as utilities for managing changes
  'lewis6991/gitsigns.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('gitsigns').setup {
      signs = {
        add = { text = '+' },
        change = { text = '~' },
        delete = { text = '_' },
        topdelete = { text = '‾' },
        changedelete = { text = '~' },
      },
      on_attach = function(bufnr)
        local gs = package.loaded.gitsigns
        require('utils').keymapSetList({
          -- navigation
          {
            'n',
            ']c',
            function()
              if vim.wo.diff then
                return ']c'
              end
              vim.schedule(function()
                gs.next_hunk()
              end)
              return '<Ignore>'
            end,
            { expr = true, desc = 'Jump to next hunk' },
          },
          {
            'n',
            '[c',
            function()
              if vim.wo.diff then
                return '[c'
              end
              vim.schedule(function()
                gs.prev_hunk()
              end)
              return '<Ignore>'
            end,
            { expr = true, desc = 'Jump to previous hunk' },
          },
          -- Actions
          {
            'n',
            '<leader>gb',
            function()
              gs.blame_line { full = true }
            end,
            { desc = 'Show [G]it [B]lame commit' },
          },
          { 'n', '<leader>gt', gs.toggle_current_line_blame, { desc = '[G]it toggle current line blame' } },
          { 'n', '<leader>gd', gs.diffthis, { desc = 'Show [G]it diff' } },
        }, bufnr)
      end,
    }
  end,
}
