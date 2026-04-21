require('tiny-code-action').setup {
  picker = {
    'snacks',
    opts = {
      winborder = 'single',
    },
  },
}

require('utils').keymapSetList {
  {
    { 'n', 'x' },
    '<leader>ca',
    function()
      require('tiny-code-action').code_action()
    end,
    { desc = '[C]ode [A]ction' },
  },
}
