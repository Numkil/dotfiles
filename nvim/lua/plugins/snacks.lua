return {
  'folke/snacks.nvim',
  priority = 1000,
  ---@type snacks.Config
  opts = {
    dashboard = {
      sections = {
        { section = 'header' },
        { section = 'keys', gap = 1, padding = 1 },
        { pane = 2, icon = ' ', title = 'Recent Files', section = 'recent_files', indent = 2, padding = 2 },
        { pane = 2, icon = ' ', title = 'Recent Files in current directory', cwd = true, section = 'recent_files', indent = 2, padding = 3 },
        {
          pane = 2,
          icon = ' ',
          title = 'Git Status',
          section = 'terminal',
          enabled = function()
            return Snacks.git.get_root() ~= nil
          end,
          cmd = 'git status --short --branch --renames',
          height = 10,
          padding = 5,
          ttl = 5 * 60,
          indent = 3,
        },
        { section = 'startup' },
      },
    },
    bigfile = {},
    git = {},
    indent = {},
    input = {},
    scope = {},
    words = {},
  },
}
