--  NOTE: Must happen before plugins are required (otherwise wrong leader will be used)
vim.g.mapleader = ','
vim.g.maplocalleader = ','

local lazypath = vim.fn.stdpath 'data' .. '/lazy/lazy.nvim'
if not vim.uv.fs_stat(lazypath) then
  local lazyrepo = 'https://github.com/folke/lazy.nvim.git'
  vim.fn.system { 'git', 'clone', '--filter=blob:none', '--branch=stable', lazyrepo, lazypath }
end
vim.opt.rtp:prepend(lazypath)

local opts = {
  spec = {
    { import = 'plugins' },
  },
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
}

require('lazy').setup(opts)
