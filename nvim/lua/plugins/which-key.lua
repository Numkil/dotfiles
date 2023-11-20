return {
  'folke/which-key.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  keys = { '<leader>' },
  config = function()
    require('which-key').setup {
      plugins = {
        marks = true,
        registers = true,
        presets = {
          operators = true,
          motions = true,
          text_objects = true,
          windows = true,
          z = true,
          g = true,
        },
      },
    }

    -- document existing key chains
    require('which-key').register {
      ['<leader>c'] = { name = '[C]ode', _ = 'which_key_ignore' },
      ['<leader>d'] = { name = '[D]ocument', _ = 'which_key_ignore' },
      ['<leader>g'] = { name = '[G]it', _ = 'which_key_ignore' },
      ['<leader>h'] = { name = 'More git', _ = 'which_key_ignore' },
      ['<leader>r'] = { name = '[R]efactor', _ = 'which_key_ignore' },
      ['<leader>rr'] = { name = '[R]efactor code', _ = 'which_key_ignore' },
      ['<leader>s'] = { name = '[S]earch', _ = 'which_key_ignore' },
      ['<leader>w'] = { name = '[W]orkspace', _ = 'which_key_ignore' },
    }
  end,
}
