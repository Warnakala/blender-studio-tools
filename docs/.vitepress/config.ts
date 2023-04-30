import { defineConfig } from 'vitepress'
import { html5Media } from 'markdown-it-html5-media'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  base: '/pipeline-and-tools/',
  title: "Blender Studio",
  description: "Documentation for the Blender Studio pipeline and tools.",
  lastUpdated: true,
  cleanUrls: true,
  themeConfig: {
    footer: {
      copyright: '(CC) Blender Foundation | studio.blender.org'
    },
    editLink: {
      pattern: 'https://projects.blender.org/studio/blender-studio-tools/_edit/master/docs/:path'
    },
    search: {
      provider: 'local'
    },
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Open Projects', link: '../films' },
      { text: 'Training', link: '../training' },
      { text: 'Blog', link: '../blog' },
      { text: 'Pipeline and Tools', link: '/' },
      { text: 'Characters', link: '../characters' }
    ],

    sidebar: [
      {
        text: 'Pipeline Overview',
        items: [
          { text: 'Introduction', link: '/pipeline-overview/introduction'},
          { text: 'Infrastructure', link: '/pipeline-overview/infrastructure'},
          { text: 'Rigging', link: '/pipeline-overview/rigging'},
        ]
      },
      {
        text: 'Naming Conventions',
        items: [
          { text: 'Introduction', link: '/naming-conventions/introduction'},
          { text: 'File Types', link: '/naming-conventions/file-types'},
          { text: 'In-file Prefixes', link: '/naming-conventions/in-file-prefixes'},
          { text: 'Examples', link: '/naming-conventions/examples'},
        ]
      },
      {
        text: 'User Guide',
        collapsed: false,
        items: [
          {text: 'Project Setup', link: '/user-guide/project-setup'},
          {
            text: 'Workstation',
            items: [
              { text: 'Introduction', link: '/user-guide/workstations/introduction'},
              { text: 'Installing Software', link: '/user-guide/workstations/installing-software'},
              { text: 'Running Blender', link: '/user-guide/workstations/running-blender'},
              { text: 'Troubleshooting', link: '/user-guide/workstations/troubleshooting'},

            ]
          }, 
          {text: 'SVN', link: '/user-guide/svn'},
          {text: 'Debugging', link: '/user-guide/debugging'}

        ]
      },
      {
        text: 'TD Guide',
        collapsed: false,
        items: [
          {text: 'Project Setup', link: '/td-guide/project-setup'},
          {
            text: 'Workstation',
            items: [
              { text: 'Introduction', link: '/td-guide/workstations/introduction'},

            ]
          },
        ]
      }
    ],
  },
  markdown: {
    config: (md) => {
      // Enable the markdown-it-html5-media plugin
      md.use(html5Media)
    }
  }
  
})
