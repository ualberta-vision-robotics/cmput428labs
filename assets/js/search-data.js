// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-home",
    title: "Home",
    section: "Navigation",
    handler: () => {
      window.location.href = "/cmput428labs/";
    },
  },{id: "nav-policies",
          title: "Policies",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/cmput428labs/policies";
          },
        },{id: "dropdown-lab-1-1",
              title: "Lab 1.1",
              description: "",
              section: "Dropdown",
              handler: () => {
                window.location.href = "";
              },
            },{id: "dropdown-lab-1-2",
              title: "Lab 1.2",
              description: "",
              section: "Dropdown",
              handler: () => {
                window.location.href = "";
              },
            },{id: "dropdown-lab-2-1",
              title: "Lab 2.1",
              description: "",
              section: "Dropdown",
              handler: () => {
                window.location.href = "";
              },
            },{id: "dropdown-lab-2-2",
              title: "Lab 2.2",
              description: "",
              section: "Dropdown",
              handler: () => {
                window.location.href = "";
              },
            },{id: "dropdown-lab-3",
              title: "Lab 3",
              description: "",
              section: "Dropdown",
              handler: () => {
                window.location.href = "";
              },
            },{id: "projects-lab-1-1-optical-flow",
          title: 'Lab 1.1 Optical Flow',
          description: "",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/opticalflow";
            },},{id: "projects-lab-1-2-tracking",
          title: 'Lab 1.2 - Tracking',
          description: "",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/tracking";
            },},{id: "projects-lab-2-1-2d-projective-geometry-and-homography-estimation",
          title: 'Lab 2.1 - 2D Projective Geometry and Homography Estimation',
          description: "",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/2dgeometry";
            },},{id: "projects-lab-2-2-3d-projective-geometry-and-stereo-reconstruction",
          title: 'Lab 2.2 - 3D Projective Geometry and Stereo Reconstruction',
          description: "",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/3dgeometry";
            },},{id: "projects-lab-3-structure-from-motion",
          title: 'Lab 3 - Structure from Motion',
          description: "",
          section: "Projects",handler: () => {
              window.location.href = "/cmput428labs/structurefrommotion";
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
