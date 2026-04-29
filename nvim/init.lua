-- Install and load all plugins
require 'config.pack'

-- noice and snacks must come first:
-- noice intercepts messages so nothing triggers "Press any key to continue"
-- snacks must register its VimEnter dashboard hook before anything else runs
require 'plugins.colourscheme'
require 'plugins.noice'
require 'plugins.snacks'

-- Load base config
require 'config.options'
require 'config.keymaps'
require 'config.autocmd'

-- Load custom lua libraries that belong in their own file
require 'utils.phpactor-tools'

-- Plugin setup
require 'plugins.lualine'
require 'plugins.mini-clue'
require 'plugins.mini-cursorword'
require 'plugins.mini-bracketed'
require 'plugins.mini-trailspace'
require 'plugins.guess-indent'
require 'plugins.hardtime'
require 'plugins.treesitter'
require 'plugins.mason'
require 'plugins.nvim-lspconfig'
require 'plugins.blink'
require 'plugins.luasnip'
require 'plugins.auto-pairs'
require 'plugins.conform'
require 'plugins.nvim-lint'
require 'plugins.gitsigns'
require 'plugins.canola'
require 'plugins.hop'
require 'plugins.todo-comments'
require 'plugins.projects'
require 'plugins.global-note'
require 'plugins.supermaven'
require 'plugins.multicursor'
require 'plugins.surround'
require 'plugins.substitute'
require 'plugins.tiny-code-action'

-- The line beneath this is called `modeline`. See `:help modeline`
-- vim: ts=2 sts=2 sw=2 et
