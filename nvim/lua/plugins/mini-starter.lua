return {
  'echasnovski/mini.starter',
  config = function()
    vim.keymap.set('n', '<space><space><space>', ':lua MiniStarter.open()<CR>', { remap = true })

    local starter = require 'mini.starter'
    starter.setup {
      evaluate_single = true,
      items = {
        starter.sections.builtin_actions(),
        starter.sections.recent_files(10, false),
        starter.sections.recent_files(10, true),
        function()
          return {
            {
              name = 'Neovim config',
              action = [[e ~/Documents/projects/dotfiles/nvim/init.lua]],
              section = 'Personal config',
            },
            {
              name = 'Bash config',
              action = [[e ~/Documents/projects/dotfiles/bash/custom/profile.sh]],
              section = 'Personal config',
            },
          }
        end,
      },
      content_hooks = {
        starter.gen_hook.adding_bullet(),
        starter.gen_hook.indexing('all', { 'Builtin actions' }),
        starter.gen_hook.padding(3, 2),
      },
    }
  end,
}
