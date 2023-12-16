-- NOTE: This is where your plugins related to LSP can be installed.
return {
  -- LSP Configuration & Plugins
  'neovim/nvim-lspconfig',
  event = 'BufEnter',
  dependencies = {
    -- Additional lua configuration, makes nvim stuff amazing!
    'folke/neodev.nvim',
    -- show diagnostic messages inline
    'https://git.sr.ht/~whynothugo/lsp_lines.nvim',
  },
  config = function()
    -- turn off virtual text as we replace with lsp_lines
    vim.diagnostic.config {
      virtual_text = false,
    }

    --  This function gets run when an LSP connects to a particular buffer.
    local on_attach = function(_, bufnr)
      local MiniExtra = require 'mini.extra'

      -- In this case, we create a function that lets us more easily define mappings specific
      -- for LSP related items. It sets the mode, buffer and description for us each time.
      local nmap = function(keys, func, desc)
        if desc then
          desc = 'LSP: ' .. desc
        end

        vim.keymap.set('n', keys, func, { buffer = bufnr, desc = desc })
      end

      nmap('<leader>rn', vim.lsp.buf.rename, '[R]e[n]ame')
      nmap('<leader>ca', vim.lsp.buf.code_action, '[C]ode [A]ction')

      nmap('gD', function()
        MiniExtra.pickers.lsp { scope = 'declaration' }
      end, '[G]oto [D]eclaration')

      nmap('gd', function()
        MiniExtra.pickers.lsp { scope = 'definition' }
      end, '[G]oto [D]efinition')

      nmap('<leader>ds', function()
        MiniExtra.pickers.lsp { scope = 'document_symbol' }
      end, '[D]ocument [S]ymbols')

      nmap('gI', function()
        MiniExtra.pickers.lsp { scope = 'implementation' }
      end, '[G]oto [I]mplementation')

      nmap('gr', function()
        MiniExtra.pickers.lsp { scope = 'references' }
      end, '[G]oto [R]eferences')

      nmap('<leader>D', function()
        MiniExtra.pickers.lsp { scope = 'type_definition' }
      end, 'Type [D]efinition')

      nmap('<leader>ws', function()
        MiniExtra.pickers.lsp { scope = 'workspace_symbol' }
      end, '[W]orkspace [S]ymbols')

      -- See `:help K` for why this keymap
      nmap('K', vim.lsp.buf.hover, 'Hover Documentation')
      nmap('<C-S-k>', vim.lsp.buf.signature_help, 'Signature Documentation')
      nmap('<leader>K', '<cmd>norm! K<cr>', 'Run keywordprg')

      -- Lesser used LSP functionality
      nmap('<leader>wa', vim.lsp.buf.add_workspace_folder, '[W]orkspace [A]dd Folder')
      nmap('<leader>wr', vim.lsp.buf.remove_workspace_folder, '[W]orkspace [R]emove Folder')
      nmap('<leader>wl', function()
        print(vim.inspect(vim.lsp.buf.list_workspace_folders()))
      end, '[W]orkspace [L]ist Folders')

      -- Create a command `:Format` local to the LSP buffer
      vim.api.nvim_buf_create_user_command(bufnr, 'Format', function(_)
        require('conform').format { bufnr = bufnr }
      end, { desc = 'Format current buffer with LSP' })
    end

    -- Setup neovim lua configuration
    require('neodev').setup()

    -- Setup lsp lines
    require('lsp_lines').setup {}

    -- nvim-cmp supports additional completion capabilities, so broadcast that to servers
    local capabilities = vim.lsp.protocol.make_client_capabilities()
    capabilities = require('cmp_nvim_lsp').default_capabilities(capabilities)

    for server_name, server_settings in pairs(require 'config.lsp-servers') do
      require('lspconfig')[server_name].setup {
        capabilities = capabilities,
        on_attach = on_attach,
        settings = server_settings,
        filetypes = (server_settings or {}).filetypes,
        init_options = (server_settings or {}).init_options,
      }
    end
  end,
}
