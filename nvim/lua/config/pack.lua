-- NOTE: Must happen before plugins are loaded (otherwise wrong leader will be used)
vim.g.mapleader = ','
vim.g.maplocalleader = ','

-- Disable some built-in plugins for better startup time
vim.g.loaded_gzip = 1
vim.g.loaded_zip = 1
vim.g.loaded_zipPlugin = 1
vim.g.loaded_tar = 1
vim.g.loaded_tarPlugin = 1

vim.pack.add {
  -- Shared dependencies (listed before plugins that need them)
  'https://github.com/nvim-lua/plenary.nvim',
  'https://github.com/MunifTanjim/nui.nvim',
  'https://github.com/nvim-tree/nvim-web-devicons',
  'https://github.com/rafamadriz/friendly-snippets',
  'https://github.com/rcarriga/nvim-notify',
  'https://github.com/folke/lazydev.nvim',
  'https://github.com/rachartier/tiny-code-action.nvim',
  'https://git.sr.ht/~whynothugo/lsp_lines.nvim',

  -- Colorscheme
  'https://github.com/sainnhe/gruvbox-material',

  -- UI
  'https://github.com/folke/snacks.nvim',
  'https://github.com/folke/noice.nvim',
  'https://github.com/nvim-lualine/lualine.nvim',

  -- Mini plugins
  'https://github.com/nvim-mini/mini.clue',
  'https://github.com/nvim-mini/mini.cursorword',
  'https://github.com/nvim-mini/mini.bracketed',
  'https://github.com/nvim-mini/mini.trailspace',

  -- Treesitter
  'https://github.com/nvim-treesitter/nvim-treesitter',
  'https://github.com/nvim-treesitter/nvim-treesitter-context',
  'https://github.com/nvim-treesitter/nvim-treesitter-textobjects',
  'https://github.com/JoosepAlviste/nvim-ts-context-commentstring',
  'https://github.com/HiPhish/rainbow-delimiters.nvim',
  'https://github.com/andymass/vim-matchup',

  -- LSP
  'https://github.com/neovim/nvim-lspconfig',
  'https://github.com/mason-org/mason.nvim',
  'https://github.com/mason-org/mason-lspconfig.nvim',
  'https://github.com/WhoIsSethDaniel/mason-tool-installer.nvim',

  -- Completion & snippets
  { src = 'https://github.com/saghen/blink.cmp', version = vim.version.range('*') },
  { src = 'https://github.com/L3MON4D3/LuaSnip', version = vim.version.range('2.x') },

  -- Editing tools
  'https://github.com/windwp/nvim-autopairs',
  'https://github.com/stevearc/conform.nvim',
  'https://github.com/mfussenegger/nvim-lint',
  'https://github.com/lewis6991/gitsigns.nvim',
  'https://github.com/stevearc/oil.nvim',
  { src = 'https://github.com/smoka7/hop.nvim', version = vim.version.range('*') },
  'https://github.com/folke/todo-comments.nvim',
  'https://github.com/DrKJeff16/project.nvim',
  'https://github.com/backdround/global-note.nvim',
  'https://github.com/supermaven-inc/supermaven-nvim',
  { src = 'https://github.com/jake-stewart/multicursor.nvim', version = '1.0' },
  { src = 'https://github.com/kylechui/nvim-surround', version = vim.version.range('*') },
  'https://github.com/gbprod/substitute.nvim',
  'https://github.com/NMAC427/guess-indent.nvim',
  'https://github.com/m4xshen/hardtime.nvim',
}
