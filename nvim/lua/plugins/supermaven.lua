require('supermaven-nvim').setup {
  disable_inline_completion = false, -- disables inline completion for use with cmp
  keymaps = {
    accept_suggestion = '<C-CR>',
    clear_suggestion = '<C-]>',
    accept_word = '<C-j>',
  },
}
