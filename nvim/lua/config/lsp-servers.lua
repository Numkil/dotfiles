-- Enable the following language servers
return {
  -- scripting LSP
  phpactor = {
    init_options = {
      ['language_server_worse_reflection.inlay_hints.enable'] = true,
      ['language_server_worse_reflection.inlay_hints.params'] = true,
      ['language_server_configuration.auto_config'] = false,
      ['code_transform.import_globals'] = true,
      ['language_server_php_cs_fixer.enabled'] = true,
      ['language_server_phpstan.enabled'] = false,
    },
  },
  tsserver = {},
  lua_ls = {
    -- cmd = {...},
    -- filetypes { ...},
    -- capabilities = {},
    settings = {
      Lua = {
        runtime = { version = 'LuaJIT' },
        workspace = {
          checkThirdParty = false,
          -- Tells lua_ls where to find all the Lua files that you have loaded
          -- for your neovim configuration.
          library = {
            '${3rd}/luv/library',
            unpack(vim.api.nvim_get_runtime_file('', true)),
          },
          -- If lua_ls is really slow on your computer, you can try this instead:
          -- library = { vim.env.VIMRUNTIME },
        },
        completion = {
          callSnippet = 'Replace',
        },
        -- You can toggle below to ignore Lua_LS's noisy `missing-fields` warnings
        -- diagnostics = { disable = { 'missing-fields' } },
      },
    },
  },
  bashls = {},
  -- templating LSP
  twiggy_language_server = {},
  html = {
    filetypes = { 'twig', 'html' },
  },
  tailwindcss = {
    filetypes = { 'twig', 'html' },
  },
  htmx = {
    filetypes = { 'twig', 'html' },
  },
}
