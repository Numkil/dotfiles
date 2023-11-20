-- Enable the following language servers
return {
  -- scripting LSP
  phpactor = {},
  tsserver = {},
  rust_analyzer = {},
  lua_ls = {
    Lua = {
      workspace = { checkThirdParty = false },
      telemetry = { enable = false },
    },
  },
  bashls = {},
  -- templating LSP
  html = {
    filetypes = { 'twig', 'html' },
  },
  tailwindcss = {
    filetypes = { 'twig', 'html' },
  },
  -- htmx = {
  --   filetypes = { 'twig', 'html' },
  -- },
}
