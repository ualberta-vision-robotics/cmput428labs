// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-home",
    title: "home",
    section: "Navigation",
    handler: () => {
      window.location.href = "/cmput428labs/";
    },
  },{id: "nav-labs",
          title: "labs",
          description: "A growing collection of your cool projects.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/cmput428labs/projects/";
          },
        },{id: "projects-optic-flow",
          title: 'Optic Flow',
          description: "blah blah blah",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/1_project/";
            },},{id: "projects-tracking",
          title: 'Tracking',
          description: "",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/2_project/";
            },},{id: "projects-lab-2-1",
          title: 'lab 2.1',
          description: "a project that redirects to another website",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/3_project/";
            },},{id: "projects-lab-2-2",
          title: 'lab 2.2',
          description: "another without an image",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/4_project/";
            },},{id: "projects-lab3",
          title: 'lab3',
          description: "a project with a background image",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/5_project/";
            },},{id: "projects-project-6",
          title: 'project 6',
          description: "a project with no image",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/6_project/";
            },},{id: "projects-project-7",
          title: 'project 7',
          description: "with background image",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/7_project/";
            },},{id: "projects-project-8",
          title: 'project 8',
          description: "an other project with a background image and giscus comments",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/8_project/";
            },},{id: "projects-project-9",
          title: 'project 9',
          description: "another project with an image 🎉",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/projects/9_project/";
            },},{
      id: 'light-theme',
      title: 'Change theme to light',
      description: 'Change the theme of the site to Light',
      section: 'Theme',
      handler: () => {
        setThemeSetting("light");
      },
    },
    {
      id: 'dark-theme',
      title: 'Change theme to dark',
      description: 'Change the theme of the site to Dark',
      section: 'Theme',
      handler: () => {
        setThemeSetting("dark");
      },
    },
    {
      id: 'system-theme',
      title: 'Use system default theme',
      description: 'Change the theme of the site to System Default',
      section: 'Theme',
      handler: () => {
        setThemeSetting("system");
      },
    },];
