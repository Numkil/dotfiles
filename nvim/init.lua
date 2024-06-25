-- Setup lazy.nvim
require 'config.lazy'

-- Load base config
require 'config.options'
require 'config.keymaps'
require 'config.autocmd'

-- Load custom lua libraries that belong in their own file
require 'utils.phpactor-tools'

-- The line beneath this is called `modeline`. See `:help modeline`
-- vim: ts=2 sts=2 sw=2 et
