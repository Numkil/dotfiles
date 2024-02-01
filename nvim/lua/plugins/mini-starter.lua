return {
  'echasnovski/mini.starter',
  config = function()
    require('utils').keymapSet('n', '<space><space><space>', ':lua MiniStarter.open()<CR>', { desc = 'Open the starting dashboard' })

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
              action = [[e ~/Documents/projects/numkil/dotfiles/nvim/init.lua]],
              section = 'Personal config',
            },
            {
              name = 'Bash config',
              action = [[e ~/Documents/projects/numkil/dotfiles/bash/custom/profile.sh]],
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
