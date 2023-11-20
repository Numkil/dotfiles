-- Set <space> as the leader key
-- See `:help mapleader`
--  NOTE: Must happen before plugins are required (otherwise wrong leader will be used)
vim.g.mapleader = ','
vim.g.maplocalleader = ','

-- Install package manager
--    https://github.com/folke/lazy.nvim
--    `:help lazy.nvim.txt` for more info
local lazypath = vim.fn.stdpath 'data' .. '/lazy/lazy.nvim'
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system {
    'git',
    'clone',
    '--filter=blob:none',
    'https://github.com/folke/lazy.nvim.git',
    '--branch=stable', -- latest stable release
    lazypath,
  }
end
vim.opt.rtp:prepend(lazypath)

-- Load plugins
require('lazy').setup({
  { import = 'plugins' },
}, {
  performance = {
    rtp = {
      disabled_plugins = {
        -- disable some plugins for better startup time
        'toHtml',
        'gzip',
        'zipPlugin',
        'tarPlugin',
        'netrwPlugin',
      },
    },
  },
})

-- Load base config
require 'config.options'
require 'config.keymaps'
require 'config.autocmd'

-- Load custom lua scripts that belong in their own file
require 'utils.phpactor-tools'

-- The line beneath this is called `modeline`. See `:help modeline`
-- vim: ts=2 sts=2 sw=2 et
