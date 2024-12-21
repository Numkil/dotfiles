return {
  -- AI Assisted completion
  'supermaven-inc/supermaven-nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  config = function()
    require('supermaven-nvim').setup {
      disable_inline_completion = false, -- disables inline completion for use with cmp
      disable_keymaps = true, -- disables built in keymaps for more manual control
    }
  end,
}
